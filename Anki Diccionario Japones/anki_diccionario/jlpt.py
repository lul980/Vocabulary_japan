"""Nivel JLPT de cada palabra (N5 = más fácil, N1 = más difícil).

Usa data/jlpt.tsv.gz, generado desde open-anki-jlpt-decks (licencia MIT,
de Jamie Sinclair, basado en las listas de Jonathan Waller). Desde 2010 no
hay listas oficiales del JLPT, así que el nivel es una guía, no algo exacto.

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import gzip
import os
import re
from typing import Dict, List, Optional, Tuple

from .categories import to_hiragana
from .fields import is_kana_only

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
JLPT_GZ = os.path.join(ADDON_DIR, "data", "jlpt.tsv.gz")

_CLEAN_RE = re.compile(r"[〜～~\s]|[（(].*?[）)]")
_KANJI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々]")


def _clean(text: str) -> str:
    return _CLEAN_RE.sub("", text or "")


class JlptIndex:
    def __init__(self, path: str = JLPT_GZ):
        self.path = path
        self.by_pair: Dict[Tuple[str, str], int] = {}
        self.by_word: Dict[str, int] = {}
        self.by_kana: Dict[str, List[Tuple[str, int]]] = {}
        self.loaded = False

    @property
    def available(self) -> bool:
        return os.path.exists(self.path)

    def load(self) -> bool:
        if self.loaded:
            return True
        if not self.available:
            return False
        with gzip.open(self.path, "rt", encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 3 or parts[0].startswith("#"):
                    continue
                word, reading, level_text = parts
                level = int(level_text)
                word, reading_h = _clean(word), to_hiragana(_clean(reading))
                # Si una palabra aparece en varios niveles, nos quedamos con el más fácil
                for table, key in ((self.by_pair, (word, reading_h)), (self.by_word, word)):
                    if key and level > table.get(key, 0):
                        table[key] = level
                if reading_h:
                    self.by_kana.setdefault(reading_h, []).append((word, level))
        self.loaded = True
        return True

    def level(self, word: str, reading: str = "") -> Optional[int]:
        """5 para N5 ... 1 para N1, o None si no está en las listas."""
        if not self.loaded and not self.load():
            return None
        word = _clean(word)
        reading_h = to_hiragana(_clean(reading))
        if (word, reading_h) in self.by_pair:
            return self.by_pair[(word, reading_h)]
        if word in self.by_word:
            return self.by_word[word]

        # Misma lectura, escrita distinto. Solo cuenta si la lista la escribe
        # en kana (出来る -> できる) o si comparten algún kanji (終わる -> 終る,
        # ご飯 -> 御飯). Así 思い no se confunde con 重い.
        if is_kana_only(word):
            reading_h = to_hiragana(word)
        my_kanji = set(_KANJI_RE.findall(word))
        levels = [
            level for other, level in self.by_kana.get(reading_h, [])
            if is_kana_only(word) or is_kana_only(other) or (my_kanji & set(_KANJI_RE.findall(other)))
        ]
        return max(levels) if levels else None


_shared: Optional[JlptIndex] = None


def shared_jlpt() -> JlptIndex:
    global _shared
    if _shared is None:
        _shared = JlptIndex()
    return _shared

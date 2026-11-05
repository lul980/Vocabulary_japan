"""Clasificación gramatical con JMdict.

El complemento trae data/jmdict_pos.tsv.gz (palabra, lectura, categorías).
La primera vez lo convierte en una pequeña base SQLite dentro de
user_files/ (Anki conserva esa carpeta al actualizar el complemento) para
buscar rápido sin cargar todo el diccionario en memoria.

Categorías gramaticales de JMdict © EDRDG, licencia CC BY-SA 4.0.

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import gzip
import os
import re
import sqlite3
from typing import Dict, List, Optional, Tuple

from .fields import has_japanese, is_kana_only

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_GZ = os.path.join(ADDON_DIR, "data", "jmdict_pos.tsv.gz")
CACHE_DB = os.path.join(ADDON_DIR, "user_files", "jmdict_pos.sqlite")

# Grupos que se muestran en el panel y las etiquetas que caen en cada uno
GROUPS: Dict[str, Tuple[str, ...]] = {
    "verb": ("godan", "ichidan", "irregular", "verb_other"),
    "noun": ("noun", "suru"),
    "adjective": ("adj_i", "adj_na", "prenominal", "adj_other"),
    "pronoun": ("pronoun",),
    "adverb": ("adverb",),
    "particle": ("particle",),
    "conjunction": ("conjunction",),
    "interjection": ("interjection",),
    "counter": ("counter",),
    "numeral": ("numeral",),
    "expression": ("expression",),
    "affix": ("prefix", "suffix"),
    "auxiliary": ("auxiliary",),
}
TAG_TO_GROUP = {tag: group for group, tags in GROUPS.items() for tag in tags}

_KATA_TO_HIRA = {c: c - 0x60 for c in range(ord("ァ"), ord("ヶ") + 1)}
_PARENS_RE = re.compile(r"[（(【\[].*?[）)】\]]")
_SPLIT_RE = re.compile(r"[、,，/／;；・]")
_TILDE_RE = re.compile(r"[〜～~]")


def to_hiragana(text: str) -> str:
    return (text or "").translate(_KATA_TO_HIRA)


def _cleanup(text: str) -> str:
    text = _PARENS_RE.sub("", text or "")
    text = _TILDE_RE.sub("", text)
    return text.replace(" ", "").replace("　", "").strip()


class Classifier:
    """Busca palabras en el índice de JMdict."""

    def __init__(self, index_gz: str = INDEX_GZ, cache_db: str = CACHE_DB):
        self.index_gz = index_gz
        self.cache_db = cache_db
        self.source = ""
        self.db: Optional[sqlite3.Connection] = None

    @property
    def available(self) -> bool:
        return os.path.exists(self.index_gz)

    # ---------- base de datos ----------

    def _stamp(self) -> str:
        st = os.stat(self.index_gz)
        return f"{st.st_size}-{int(st.st_mtime)}"

    def open(self) -> bool:
        if self.db is not None:
            return True
        if not self.available:
            return False
        stamp = self._stamp()
        if os.path.exists(self.cache_db):
            try:
                db = sqlite3.connect(self.cache_db, check_same_thread=False)
                row = db.execute("select value from meta where key='stamp'").fetchone()
                if row and row[0] == stamp:
                    self.db = db
                    self.source = db.execute("select value from meta where key='source'").fetchone()[0]
                    return True
                db.close()
            except sqlite3.Error:
                pass
            os.remove(self.cache_db)
        self._build_cache(stamp)
        return self.db is not None

    def _build_cache(self, stamp: str) -> None:
        os.makedirs(os.path.dirname(self.cache_db), exist_ok=True)
        tmp = self.cache_db + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        db = sqlite3.connect(tmp)
        db.execute("create table words (kanji text, kana text, kana_h text, tags text, rank int)")
        db.execute("create table meta (key text primary key, value text)")
        source = "JMdict"
        rows = []
        with gzip.open(self.index_gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if parts[0] == "#JMdict":
                    source = f"JMdict {parts[1]}".strip()
                    continue
                if len(parts) != 4:
                    continue
                kanji, kana, tags, rank = parts
                rows.append((kanji, kana, to_hiragana(kana), tags, int(rank)))
        db.executemany("insert into words values (?,?,?,?,?)", rows)
        db.execute("create index idx_kanji on words(kanji)")
        db.execute("create index idx_kana on words(kana_h)")
        db.executemany("insert into meta values (?,?)", [("stamp", stamp), ("source", source)])
        db.commit()
        db.close()
        os.replace(tmp, self.cache_db)
        self.db = sqlite3.connect(self.cache_db, check_same_thread=False)
        self.source = source

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
            self.db = None

    # ---------- búsqueda ----------

    def _best(self, rows: List[Tuple[str, str, int]], prefer_kana: bool) -> Optional[List[str]]:
        if not rows:
            return None
        def score(row):
            kanji, _tags, rank = row
            common = 2 if rank & 2 else 0
            kana_ok = 4 if prefer_kana and (rank & 1 or not kanji) else 0
            return kana_ok + common
        best = max(rows, key=score)  # max() se queda con el primero en empate (orden de JMdict)
        return best[1].split(",")

    def _lookup(self, word: str, reading: str) -> Optional[List[str]]:
        if not word or self.db is None:
            return None
        reading_h = to_hiragana(reading)
        if is_kana_only(word):
            rows = self.db.execute(
                "select kanji, tags, rank from words where kana_h = ? order by rowid", (to_hiragana(word),)
            ).fetchall()
            return self._best(rows, prefer_kana=True)
        if reading_h:
            rows = self.db.execute(
                "select kanji, tags, rank from words where kanji = ? and kana_h = ? order by rowid",
                (word, reading_h),
            ).fetchall()
            found = self._best(rows, prefer_kana=False)
            if found:
                return found
        rows = self.db.execute(
            "select kanji, tags, rank from words where kanji = ? order by rowid", (word,)
        ).fetchall()
        return self._best(rows, prefer_kana=False)

    def classify(self, word: str, reading: str = "") -> List[str]:
        """Etiquetas de la palabra, en orden de importancia ([] si no se encontró)."""
        word = (word or "").strip()
        reading = (reading or "").strip()
        tags = self._lookup(word, reading)
        if tags:
            return tags

        # Variantes: sin "〜", sin paréntesis, solo la primera opción de "A、B"
        clean = _cleanup(word)
        clean_reading = _cleanup(reading)
        candidates = [clean] + [p for p in _SPLIT_RE.split(clean) if p and p != clean]
        readings = [clean_reading] + [p for p in _SPLIT_RE.split(clean_reading) if p and p != clean_reading]
        for i, cand in enumerate(candidates):
            if not has_japanese(cand):
                continue
            tags = self._lookup(cand, readings[i] if i < len(readings) else "")
            if tags:
                return tags

        # Verbos escritos con する: "勉強する" -> 勉強 (sustantivo + する)
        if clean.endswith("する") and len(clean) > 2:
            base_reading = clean_reading[:-2] if clean_reading.endswith("する") else clean_reading
            base = self._lookup(clean[:-2], base_reading)
            if base is not None:
                # Escrita con する ya es verbo: no la contamos además como sustantivo
                return ["irregular"] + [t for t in base if t not in ("noun", "suru", "irregular")]
        return []


def groups_for(tags: List[str]) -> List[str]:
    """Grupos del panel (verbo, sustantivo...) en el orden de las etiquetas."""
    out: List[str] = []
    for tag in tags:
        group = TAG_TO_GROUP.get(tag)
        if group and group not in out:
            out.append(group)
    return out


_shared: Optional[Classifier] = None


def shared_classifier() -> Classifier:
    """Una sola instancia por sesión de Anki (la base se abre una vez)."""
    global _shared
    if _shared is None:
        _shared = Classifier()
    return _shared

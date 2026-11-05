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
CACHE_DIR = os.path.join(ADDON_DIR, "user_files")

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
_WORD_RE = re.compile(r"[a-z]+")
_STOP = {"to", "the", "a", "an", "of", "be", "in", "on", "is", "it", "for", "with", "and", "or", "as",
         "at", "by", "one", "ones", "s", "something", "someone", "sth", "etc", "esp", "usu", "used", "e", "g"}


def _gloss_words(text: str) -> set:
    """Palabras clave de un significado en inglés (recortadas para ignorar plurales)."""
    return {w[:5] for w in _WORD_RE.findall((text or "").lower()) if w not in _STOP}


def to_hiragana(text: str) -> str:
    return (text or "").translate(_KATA_TO_HIRA)


def _cleanup(text: str) -> str:
    text = _PARENS_RE.sub("", text or "")
    text = _TILDE_RE.sub("", text)
    return text.replace(" ", "").replace("　", "").strip()


class Classifier:
    """Busca palabras en el índice de JMdict."""

    def __init__(self, index_gz: str = INDEX_GZ, cache_dir: str = CACHE_DIR):
        self.index_gz = index_gz
        self.cache_dir = cache_dir
        self.source = ""
        self.db: Optional[sqlite3.Connection] = None

    @property
    def available(self) -> bool:
        return os.path.exists(self.index_gz)

    # ---------- base de datos ----------
    #
    # Importante en Windows: un archivo abierto no se puede mover ni borrar, y
    # Anki mueve user_files/ al actualizar el complemento. Por eso la base se
    # abre solo mientras se lee el mazo (collector.py llama a close() al
    # terminar) y cada versión del índice usa su propio archivo, así nunca hay
    # que sobrescribir uno que otro programa tenga abierto.

    def _stamp(self) -> str:
        st = os.stat(self.index_gz)
        return f"{st.st_size}-{int(st.st_mtime)}"

    def _cache_path(self, stamp: str) -> str:
        return os.path.join(self.cache_dir, f"jmdict_pos-{stamp}.sqlite")

    def open(self) -> bool:
        if self.db is not None:
            return True
        if not self.available:
            return False
        path = self._cache_path(self._stamp())
        if os.path.exists(path):
            db = None
            try:
                db = sqlite3.connect(path, check_same_thread=False)
                self.source = db.execute("select value from meta where key='source'").fetchone()[0]
                self.db = db
                return True
            except (sqlite3.Error, TypeError):
                if db is not None:
                    db.close()
                _try_remove(path)
        self._build_cache(path)
        self._remove_old_caches(keep=path)
        return self.db is not None

    def _build_cache(self, path: str) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        _try_remove(tmp)
        db = sqlite3.connect(tmp)
        try:
            db.execute("create table words (kanji text, kana_h text, tags text, rank int, freq int, gloss text)")
            db.execute("create table meta (key text primary key, value text)")
            source = "JMdict"
            rows = []
            with gzip.open(self.index_gz, "rt", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.rstrip("\n").split("\t")
                    if parts[0] == "#JMdict":
                        source = f"JMdict {parts[1]}".strip()
                        continue
                    if len(parts) < 4:
                        continue
                    kanji, kana, tags, rank = parts[:4]
                    freq = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 99
                    gloss = parts[5] if len(parts) > 5 else ""
                    rows.append((kanji, to_hiragana(kana), tags, int(rank), freq, gloss))
            db.executemany("insert into words values (?,?,?,?,?,?)", rows)
            db.execute("create index idx_kanji on words(kanji)")
            db.execute("create index idx_kana on words(kana_h)")
            db.execute("insert into meta values ('source', ?)", (source,))
            db.commit()
        finally:
            db.close()
        os.replace(tmp, path)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.source = source

    def _remove_old_caches(self, keep: str) -> None:
        try:
            names = os.listdir(self.cache_dir)
        except OSError:
            return
        for name in names:
            full = os.path.join(self.cache_dir, name)
            if name.startswith("jmdict_pos") and full != keep:
                _try_remove(full)  # si está en uso, se borra la próxima vez

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
            self.db = None

    # ---------- búsqueda ----------

    def _best(self, rows: list, prefer_kana: bool, meaning: str) -> Optional[List[str]]:
        """Elige la entrada correcta cuando hay varias (homófonos).

        Orden: que se escriba en kana (si la palabra está en kana), que su
        significado se parezca al de tu tarjeta, que sea común y que sea frecuente.
        """
        if not rows:
            return None
        wanted = _gloss_words(meaning)

        def score(row):
            kanji, _tags, rank, freq, gloss = row
            kana_ok = 1 if prefer_kana and (rank & 1 or not kanji) else 0
            overlap = len(wanted & _gloss_words(gloss)) if wanted else 0
            return (kana_ok, overlap, 1 if rank & 2 else 0, -freq)

        best = max(rows, key=score)  # en empate se queda el primero (orden de JMdict)
        return best[1].split(",")

    _COLS = "kanji, tags, rank, freq, gloss"

    def _lookup(self, word: str, reading: str, meaning: str = "") -> Optional[List[str]]:
        if not word or self.db is None:
            return None
        reading_h = to_hiragana(reading)
        if is_kana_only(word):
            rows = self.db.execute(
                f"select {self._COLS} from words where kana_h = ? order by rowid", (to_hiragana(word),)
            ).fetchall()
            return self._best(rows, True, meaning)
        if reading_h:
            rows = self.db.execute(
                f"select {self._COLS} from words where kanji = ? and kana_h = ? order by rowid",
                (word, reading_h),
            ).fetchall()
            found = self._best(rows, False, meaning)
            if found:
                return found
        rows = self.db.execute(
            f"select {self._COLS} from words where kanji = ? order by rowid", (word,)
        ).fetchall()
        return self._best(rows, False, meaning)

    def classify(self, word: str, reading: str = "", meaning: str = "") -> List[str]:
        """Etiquetas de la palabra, en orden de importancia ([] si no se encontró).

        `meaning` (el significado de tu tarjeta) ayuda a elegir entre palabras
        que se leen igual, como いくら (幾ら, "cuánto") e いくら (huevas).
        """
        word = (word or "").strip()
        reading = (reading or "").strip()
        tags = self._lookup(word, reading, meaning)
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
            tags = self._lookup(cand, readings[i] if i < len(readings) else "", meaning)
            if tags:
                return tags

        # Verbos escritos con する: "勉強する" -> 勉強 (sustantivo + する)
        if clean.endswith("する") and len(clean) > 2:
            base_reading = clean_reading[:-2] if clean_reading.endswith("する") else clean_reading
            base = self._lookup(clean[:-2], base_reading, meaning)
            if base is not None:
                # Escrita con する ya es verbo: no la contamos además como sustantivo
                return ["irregular"] + [t for t in base if t not in ("noun", "suru", "irregular")]
        return []


def _try_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


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
    """Una sola instancia por sesión de Anki. Ojo: hay que cerrarla después de usarla."""
    global _shared
    if _shared is None:
        _shared = Classifier()
    return _shared

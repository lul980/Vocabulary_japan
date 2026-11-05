"""Colección "de mentiritas" para probar el add-on sin abrir Anki.

Abre el archivo SQLite de un mazo exportado (.apkg -> collection.anki21)
e imita las pocas funciones de la API de Anki que usa collector.py:
col.db.all, col.models.get y col.decks.*
"""

from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace


class _DB:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def all(self, sql: str, *args):
        return [list(r) for r in self._conn.execute(sql, args).fetchall()]


class _Models:
    def __init__(self, models: dict):
        self._models = {int(k): v for k, v in models.items()}

    def get(self, mid):
        return self._models.get(int(mid))


class _Decks:
    def __init__(self, decks: dict, current: int):
        self._decks = {int(k): v for k, v in decks.items()}
        self._current = current

    def all_names_and_ids(self):
        return [SimpleNamespace(name=d["name"], id=int(i)) for i, d in self._decks.items()]

    def deck_and_child_ids(self, did):
        name = self._decks[int(did)]["name"]
        return [i for i, d in self._decks.items() if d["name"] == name or d["name"].startswith(name + "::")]

    def get_current_id(self):
        return self._current


class FakeCollection:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        models, decks, conf = self.conn.execute("select models, decks, conf from col").fetchone()
        current = json.loads(conf or "{}").get("curDeck", 1)
        self.db = _DB(self.conn)
        self.models = _Models(json.loads(models))
        self.decks = _Decks(json.loads(decks), current)

"""Genera el índice de niveles JLPT que usa el complemento.

Lee las listas de vocabulario de open-anki-jlpt-decks (src/n1.csv ... n5.csv,
licencia MIT, de Jamie Sinclair, basadas en las listas de Jonathan Waller) y
guarda anki_diccionario/data/jlpt.tsv.gz con: palabra, lectura, nivel.

Desde 2010 no existen listas oficiales del JLPT; estas son las más usadas
por la comunidad.

Uso:
    python dev/build_jlpt_index.py ruta/a/open-anki-jlpt-decks/src
"""

from __future__ import annotations

import csv
import gzip
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "anki_diccionario", "data", "jlpt.tsv.gz")


def build(src_dir: str, out: str = OUT) -> dict:
    best = {}  # (palabra, lectura) -> nivel más fácil en que aparece
    for level in (5, 4, 3, 2, 1):
        path = os.path.join(src_dir, f"n{level}.csv")
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                word = (row.get("expression") or "").strip()
                reading = (row.get("reading") or "").strip()
                if not word:
                    continue
                key = (word, reading)
                if key not in best or level > best[key]:
                    best[key] = level
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8", compresslevel=9) as fh:
        fh.write("#JLPT\topen-anki-jlpt-decks\tMIT\n")
        for (word, reading), level in best.items():
            fh.write(f"{word}\t{reading}\t{level}\n")
    counts = {f"N{n}": sum(1 for v in best.values() if v == n) for n in (5, 4, 3, 2, 1)}
    return {"words": len(best), "bytes": os.path.getsize(out), **counts}


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else OUT))

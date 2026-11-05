"""Empaqueta el complemento como .ankiaddon (lo que se instala en Anki).

Uso:
    python dev/package.py
"""

from __future__ import annotations

import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "anki_diccionario")
OUT = os.path.join(ROOT, "dist", "anki_diccionario_japones.ankiaddon")
SKIP_DIRS = {"__pycache__", "user_files"}
SKIP_FILES = {"meta.json"}


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, dirs, files in os.walk(SRC):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if name in SKIP_FILES or name.endswith(".pyc"):
                    continue
                path = os.path.join(folder, name)
                z.write(path, os.path.relpath(path, SRC))
                count += 1
    print(f"{OUT} ({count} archivos, {os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()

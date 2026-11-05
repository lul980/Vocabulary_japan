"""Arma una página HTML independiente con el panel y un JSON de datos.

Sirve para ver el diseño en el navegador sin abrir Anki (y es la base del
futuro botón "Exportar").

Uso:
    python dev/build_preview.py datos.json salida.html [--dark] [--en]
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), "anki_diccionario", "web")


def read(name: str) -> str:
    with open(os.path.join(WEB, name), encoding="utf-8") as fh:
        return fh.read()


def build(data_json: str, dark: bool = False, lang: str = "es") -> str:
    data = json.loads(data_json)
    data.setdefault("language", lang)  # en Anki lo pone window.py
    safe_data = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diccionario japonés</title>
<style>{read("dashboard.css")}</style>
</head>
<body class="{'nightMode' if dark else ''}">
{read("dashboard.html")}
<script>{read("dashboard.js")}</script>
<script>AnkiDiccionario.render({safe_data});</script>
</body>
</html>
"""


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        page = build(fh.read(), dark="--dark" in sys.argv, lang="en" if "--en" in sys.argv else "es")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("Vista previa:", out)

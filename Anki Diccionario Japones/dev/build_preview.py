"""Arma una página HTML independiente con el panel y un JSON de datos.

Sirve para ver el diseño en el navegador sin abrir Anki (y es la base del
futuro botón "Exportar").

Uso:
    python dev/build_preview.py datos.json salida.html [--dark] [--en] [--anki]

--anki carga primero los estilos globales de Anki para ver el panel como dentro de la app.
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


def build(data_json: str, dark: bool = False, lang: str = "es", anki: bool = False) -> str:
    data = json.loads(data_json)
    data.setdefault("language", lang)  # en Anki lo pone window.py
    safe_data = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diccionario japonés</title>
{anki_css(anki)}<style>{read("dashboard.css")}</style>
</head>
<body class="{body_class(dark, anki)}">
{read("dashboard.html")}
<script>{read("dashboard.js")}</script>
<script>AnkiDiccionario.render({safe_data});</script>
</body>
</html>
"""


def anki_css(enabled: bool) -> str:
    """Con --anki se cargan antes los estilos globales de Anki (dev/anki_sim.css)."""
    if not enabled:
        return ""
    with open(os.path.join(HERE, "anki_sim.css"), encoding="utf-8") as fh:
        return f"<style>{fh.read()}</style>\n"


def body_class(dark: bool, anki: bool) -> str:
    classes = (["nightMode"] if dark else []) + (["isWin", "fancy"] if anki else [])
    return " ".join(classes)


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        page = build(fh.read(), dark="--dark" in sys.argv, lang="en" if "--en" in sys.argv else "es",
                     anki="--anki" in sys.argv)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("Vista previa:", out)

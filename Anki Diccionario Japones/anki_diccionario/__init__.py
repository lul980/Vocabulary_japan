"""Diccionario Japonés: ve tu progreso de vocabulario dentro de Anki.

Proyecto de Raul Juarez.
"""

try:
    from aqt import mw
except ImportError:  # fuera de Anki (pruebas): no cargamos la interfaz
    mw = None

if mw is not None:
    from . import window

    window.setup()

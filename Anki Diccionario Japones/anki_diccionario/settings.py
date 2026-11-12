"""Configuración del panel: valores por defecto, validación y fondo propio.

No depende de Anki (se puede probar fuera). window.py lo usa para guardar lo
que cambias en el panel de Configuración (⚙).

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import copy
import os
import re
import shutil
import time
from typing import Any, Dict, Optional, Tuple

from .fields import MAPPABLE

# Mismos ids que dev/build_themes.py (la prueba revisa que coincidan)
THEME_IDS = ("aizome", "solarized", "nord", "catppuccin", "rosepine", "gruvbox", "tokyonight")

DEFAULTS: Dict[str, Any] = {
    "deck": "",
    "language": "auto",
    "mature_interval_days": 21,
    "leech_lapses": 8,
    "word_status_mode": "all",
    "field_mapping": {},
    "theme": "aizome",
    "mode": "auto",  # "auto" sigue a Anki, "light" o "dark"
    "background": {
        "type": "theme",  # "theme", "color" o "image"
        "color": "#e5e9f0",
        "image": "",      # nombre del archivo dentro de user_files/
        "veil": 70,       # 0-95: cuánto color del tema cubre el fondo
        "blur": 0,        # 0-20 px
        "fit": "cover",   # "cover" (cubrir) o "tile" (mosaico)
    },
}

# Cambios que obligan a volver a leer el mazo (los de apariencia no)
NEEDS_REFRESH = {"language", "mature_interval_days", "leech_lapses", "word_status_mode", "field_mapping"}

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_BG_NAME_RE = re.compile(r"^background-\d+\.(png|jpe?g|webp|gif|bmp)$")


def with_defaults(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """La configuración del usuario completada con los valores por defecto."""
    out = copy.deepcopy(DEFAULTS)
    for key, value in (config or {}).items():
        if key == "background" and isinstance(value, dict):
            out["background"].update(value)
        else:
            out[key] = value
    return out


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def apply_settings(config: Dict[str, Any], changes: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Valida lo que manda el panel y lo mezcla con la configuración.

    Regresa (configuración nueva, hay_que_volver_a_leer_el_mazo).
    Cualquier valor raro se ignora o se ajusta a un rango válido.
    """
    cfg = with_defaults(config)
    refresh = False

    def set_value(key: str, value: Any) -> None:
        nonlocal refresh
        if cfg.get(key) != value:
            cfg[key] = value
            refresh = refresh or key in NEEDS_REFRESH

    if changes.get("theme") in THEME_IDS:
        set_value("theme", changes["theme"])
    if changes.get("mode") in ("auto", "light", "dark"):
        set_value("mode", changes["mode"])
    if changes.get("language") in ("auto", "es", "en"):
        set_value("language", changes["language"])
    if "mature_interval_days" in changes:
        set_value("mature_interval_days", _clamp_int(changes["mature_interval_days"], 1, 365, 21))
    if "leech_lapses" in changes:
        set_value("leech_lapses", _clamp_int(changes["leech_lapses"], 1, 99, 8))
    if changes.get("word_status_mode") in ("all", "any"):
        set_value("word_status_mode", changes["word_status_mode"])

    bg = changes.get("background")
    if isinstance(bg, dict):
        current = dict(cfg["background"])
        if bg.get("type") in ("theme", "color", "image"):
            current["type"] = bg["type"]
        if isinstance(bg.get("color"), str) and _HEX_RE.match(bg["color"]):
            current["color"] = bg["color"].lower()
        if "veil" in bg:
            current["veil"] = _clamp_int(bg["veil"], 0, 95, 70)
        if "blur" in bg:
            current["blur"] = _clamp_int(bg["blur"], 0, 20, 0)
        if bg.get("fit") in ("cover", "tile"):
            current["fit"] = bg["fit"]
        if current["type"] == "image" and not current.get("image"):
            current["type"] = "theme"  # no hay imagen elegida todavía
        set_value("background", current)
    return cfg, refresh


def apply_field_mapping(config: Dict[str, Any], notetype: str, mapping: Dict[str, Any],
                        field_names: Optional[list] = None) -> Dict[str, Any]:
    """Guarda los campos elegidos a mano para un tipo de nota.

    mapping: {clave: nombre_de_campo | "" (ninguno) | None (automático)}.
    Solo se guardan las claves conocidas y los campos que existen.
    """
    cfg = with_defaults(config)
    chosen = {}
    for key, value in (mapping or {}).items():
        if key not in MAPPABLE or value is None:
            continue
        if value == "" and key != "word":
            chosen[key] = ""
        elif isinstance(value, str) and (field_names is None or value in field_names):
            chosen[key] = value
    all_maps = dict(cfg.get("field_mapping") or {})
    if chosen:
        all_maps[notetype] = chosen
    else:
        all_maps.pop(notetype, None)
    cfg["field_mapping"] = all_maps
    return cfg


def reset(config: Dict[str, Any], scope: str) -> Dict[str, Any]:
    """'appearance' restablece tema, modo y fondo; 'all' todo menos el mazo elegido."""
    cfg = with_defaults(config)
    if scope == "appearance":
        for key in ("theme", "mode", "background"):
            cfg[key] = copy.deepcopy(DEFAULTS[key])
    elif scope == "all":
        deck = cfg.get("deck", "")
        cfg = copy.deepcopy(DEFAULTS)
        cfg["deck"] = deck
    return cfg


# --------------------------------------------------------------------------
# Imagen de fondo (se copia a user_files/, que Anki conserva al actualizar)
# --------------------------------------------------------------------------

def store_background(source: str, user_dir: str) -> str:
    """Copia la imagen elegida a user_files/ y regresa su nombre nuevo."""
    ext = os.path.splitext(source)[1].lower()
    if ext not in IMAGE_EXTS:
        raise ValueError(f"Formato no soportado: {ext or 'sin extensión'}")
    os.makedirs(user_dir, exist_ok=True)
    # Un nombre nuevo cada vez: así la página no muestra la imagen vieja guardada en caché
    name = f"background-{int(time.time() * 1000)}{'.jpg' if ext == '.jpeg' else ext}"
    shutil.copyfile(source, os.path.join(user_dir, name))
    clear_backgrounds(user_dir, keep=name)
    return name


def clear_backgrounds(user_dir: str, keep: str = "") -> None:
    try:
        names = os.listdir(user_dir)
    except OSError:
        return
    for name in names:
        if _BG_NAME_RE.match(name) and name != keep:
            try:
                os.remove(os.path.join(user_dir, name))
            except OSError:
                pass


def appearance(config: Dict[str, Any], url_base: str, user_dir: str) -> Dict[str, Any]:
    """Lo que la página necesita para pintarse (tema, modo y fondo)."""
    cfg = with_defaults(config)
    bg = dict(cfg["background"])
    image = bg.get("image") or ""
    exists = bool(image) and _BG_NAME_RE.match(image) and os.path.exists(os.path.join(user_dir, image))
    bg["url"] = f"{url_base}/user_files/{image}" if exists else ""
    if bg["type"] == "image" and not exists:
        bg["type"] = "theme"
    return {
        "theme": cfg["theme"] if cfg["theme"] in THEME_IDS else "aizome",
        "mode": cfg["mode"] if cfg["mode"] in ("auto", "light", "dark") else "auto",
        "background": bg,
        "language": cfg["language"],
    }

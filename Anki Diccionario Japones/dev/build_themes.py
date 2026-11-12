"""Temas de color del panel: los define, los valida y genera los archivos web.

Cada tema tiene versión clara y oscura, sacada de su paleta oficial:
  - Aizome: el diseño original (índigo).
  - Solarized (Ethan Schoonover): diseñada en el espacio de color CIELAB, con
    claro y oscuro simétricos en luminosidad.
  - Nord (Arctic Ice Studio), Catppuccin (Latte/Mocha), Rosé Pine (Dawn/Main),
    Gruvbox (morhetz) y Tokyo Night (Day/Night): paletas abiertas muy usadas.

Antes de escribir nada revisa, para cada tema y modo:
  - Contraste del texto (WCAG 2.x): texto e ink-2 >= 4.5:1, texto suave >= 4.5:1,
    portada >= 4.5:1, texto de botones >= 4.5:1, palabra resaltada >= 4.5:1.
  - Que la escala de estados (pendiente -> aprendiendo -> joven -> sabida) vaya
    de claro a oscuro (o al revés en modo oscuro) con pasos que se distingan.
Si algo falla, no escribe los archivos.

Uso:
    python dev/build_themes.py          # valida y genera web/themes.css y web/themes.js
    python dev/build_themes.py --check  # solo valida
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), "anki_diccionario", "web")

TOKENS = ("paper", "sheet", "ink", "ink-2", "ink-3", "rule", "cover", "cover-ink", "slip", "focus",
          "st-new", "st-learning", "st-young", "st-mature", "st-suspended", "st-leech", "hl")

THEMES = {
    "aizome": {
        "name": "Aizome",
        "desc": {"es": "El diseño original: índigo japonés (藍染).",
                 "en": "The original design: Japanese indigo (藍染)."},
        "light": dict(paper="#f1f4f7", sheet="#fbfcfd", ink="#18233a", ink2="#4b586e", ink3="#5f6b80",
                      rule="#d6dde6", cover="#1f3b73", cover_ink="#f4f7fb", slip="#f7f5ef", focus="#2f6fd6",
                      new="#dbe1e9", learning="#b3c7e6", young="#6488c5", mature="#1f3b73",
                      suspended="#98a2b3", leech="#c2452b", hl="#2f62b8"),
        "dark": dict(paper="#10151f", sheet="#182131", ink="#e5eaf2", ink2="#a8b3c5", ink3="#8f9bb0",
                     rule="#263248", cover="#172744", cover_ink="#e9eef7", slip="#e3e8f0", focus="#7fb0ff",
                     new="#232d3e", learning="#2d4a7a", young="#4f7bc4", mature="#a9c3ef",
                     suspended="#5d687c", leech="#ef7d61", hl="#8db2f2"),
    },
    "solarized": {
        "name": "Solarized",
        "desc": {"es": "Diseñada en CIELAB: claro y oscuro con el mismo contraste percibido.",
                 "en": "Designed in CIELAB: light and dark with the same perceived contrast."},
        # base03 002b36, base02 073642, base01 586e75, base00 657b83, base0 839496,
        # base1 93a1a1, base2 eee8d5, base3 fdf6e3, blue 268bd2, orange cb4b16
        "light": dict(paper="#eee8d5", sheet="#fdf6e3", ink="#073642", ink2="#4c6168", ink3="#52666d",
                      rule="#d9d2bd", cover="#073642", cover_ink="#fdf6e3", slip="#fdf6e3", focus="#268bd2",
                      new="#ddd6c1", learning="#97bfe0", young="#268bd2", mature="#174f78",
                      suspended="#93a1a1", leech="#cb4b16", hl="#1c6aa3"),
        "dark": dict(paper="#002b36", sheet="#073642", ink="#eee8d5", ink2="#93a1a1", ink3="#93a1a1",
                     rule="#164852", cover="#073642", cover_ink="#eee8d5", slip="#eee8d5", focus="#268bd2",
                     new="#0f4350", learning="#165c80", young="#268bd2", mature="#8cc4ec",
                     suspended="#586e75", leech="#e2662f", hl="#6fb4e6"),
    },
    "nord": {
        "name": "Nord",
        "desc": {"es": "Azules árticos, fríos y suaves; pensada para leer sin cansarse.",
                 "en": "Cool, soft arctic blues, made for calm reading."},
        # nord0 2e3440 .. nord3 4c566a, nord4 d8dee9, nord5 e5e9f0, nord6 eceff4,
        # nord8 88c0d0, nord9 81a1c1, nord10 5e81ac, nord11 bf616a
        "light": dict(paper="#e5e9f0", sheet="#eceff4", ink="#2e3440", ink2="#434c5e", ink3="#4c566a",
                      rule="#cdd4e0", cover="#3b4252", cover_ink="#eceff4", slip="#eceff4", focus="#5e81ac",
                      new="#d3d9e4", learning="#aec2da", young="#81a1c1", mature="#4a6890",
                      suspended="#9aa3b4", leech="#bf616a", hl="#4a6890"),
        "dark": dict(paper="#2e3440", sheet="#3b4252", ink="#eceff4", ink2="#d8dee9", ink3="#b4bccb",
                     rule="#4c566a", cover="#3b4252", cover_ink="#eceff4", slip="#e5e9f0", focus="#88c0d0",
                     new="#434c5e", learning="#4f6a8f", young="#81a1c1", mature="#a3d0dc",
                     suspended="#616e88", leech="#d0707a", hl="#88c0d0"),
    },
    "catppuccin": {
        "name": "Catppuccin",
        "desc": {"es": "Pastel y cálida (Latte y Mocha); de las más populares hoy.",
                 "en": "Warm pastels (Latte and Mocha); one of today's most popular."},
        "light": dict(paper="#eff1f5", sheet="#f8f9fb", ink="#4c4f69", ink2="#5c5f77", ink3="#5c5f77",
                      rule="#ccd0da", cover="#8839ef", cover_ink="#eff1f5", slip="#eff1f5", focus="#1e66f5",
                      new="#dce0e8", learning="#c3aaf6", young="#a678f3", mature="#7a2ee0",
                      suspended="#9ca0b0", leech="#d20f39", hl="#7a2ee0"),
        "dark": dict(paper="#181825", sheet="#1e1e2e", ink="#cdd6f4", ink2="#bac2de", ink3="#a6adc8",
                     rule="#313244", cover="#313244", cover_ink="#cdd6f4", slip="#cdd6f4", focus="#89b4fa",
                     new="#313244", learning="#5a4a80", young="#9a7fd6", mature="#cba6f7",
                     suspended="#6c7086", leech="#f38ba8", hl="#cba6f7"),
    },
    "rosepine": {
        "name": "Rosé Pine",
        "desc": {"es": "Tonos apagados de pino y rosa, con luz suave (Dawn y Main).",
                 "en": "Muted pine and rose tones with soft light (Dawn and Main)."},
        "light": dict(paper="#faf4ed", sheet="#fffaf3", ink="#464261", ink2="#5f5a7a", ink3="#6b6688",
                      rule="#dfdad9", cover="#286983", cover_ink="#fffaf3", slip="#fffaf3", focus="#286983",
                      new="#e8e0d7", learning="#a3c4cc", young="#56949f", mature="#286983",
                      suspended="#9893a5", leech="#b4637a", hl="#286983"),
        "dark": dict(paper="#191724", sheet="#1f1d2e", ink="#e0def4", ink2="#908caa", ink3="#908caa",
                     rule="#403d52", cover="#26233a", cover_ink="#e0def4", slip="#e0def4", focus="#9ccfd8",
                     new="#2a2740", learning="#2c5466", young="#31748f", mature="#9ccfd8",
                     suspended="#524f67", leech="#eb6f92", hl="#ebbcba"),
    },
    "gruvbox": {
        "name": "Gruvbox",
        "desc": {"es": "Retro y cálida, tonos tierra con buen contraste.",
                 "en": "Retro and warm, earthy tones with solid contrast."},
        "light": dict(paper="#f2e5bc", sheet="#fbf1c7", ink="#3c3836", ink2="#504945", ink3="#665c54",
                      rule="#d5c4a1", cover="#3c3836", cover_ink="#fbf1c7", slip="#fbf1c7", focus="#076678",
                      new="#e3d3a6", learning="#a9ba8a", young="#689d6a", mature="#356748",
                      suspended="#a89984", leech="#9d0006", hl="#af3a03"),
        "dark": dict(paper="#282828", sheet="#32302f", ink="#ebdbb2", ink2="#d5c4a1", ink3="#bdae93",
                     rule="#504945", cover="#3c3836", cover_ink="#ebdbb2", slip="#ebdbb2", focus="#83a598",
                     new="#3c3836", learning="#4b5a3d", young="#689d6a", mature="#8ec07c",
                     suspended="#665c54", leech="#fb4934", hl="#fe8019"),
    },
    "tokyonight": {
        "name": "Tokyo Night",
        "desc": {"es": "Azules de noche en Tokio con acentos morados (Day y Night).",
                 "en": "Tokyo night blues with purple accents (Day and Night)."},
        # Day: bg e1e2e7, bg_dark d0d5e3, bg_highlight c4c8da, fg 3760bf, dark5 68709a,
        # blue 2e7de9, magenta 9854f1, red f52a65, terminal_black a1a6c5
        # Night: bg 1a1b26, bg_dark 16161e, bg_highlight 292e42, fg c0caf5, fg_dark a9b1d6,
        # dark5 737aa2, blue 7aa2f7, blue0 3d59a1, cyan 7dcfff, magenta bb9af7, red f7768e
        "light": dict(paper="#e1e2e7", sheet="#eceef3", ink="#2b3152", ink2="#3d4675", ink3="#565e8a",
                      rule="#c4c8da", cover="#3760bf", cover_ink="#eceef3", slip="#eceef3", focus="#2e7de9",
                      new="#d0d5e3", learning="#9bb3ec", young="#5b8fe9", mature="#2f55a8",
                      suspended="#a1a6c5", leech="#e5245c", hl="#8445e0"),
        "dark": dict(paper="#16161e", sheet="#1a1b26", ink="#c0caf5", ink2="#a9b1d6", ink3="#8f97c0",
                     rule="#292e42", cover="#24283b", cover_ink="#c0caf5", slip="#c0caf5", focus="#7aa2f7",
                     new="#292e42", learning="#3d59a1", young="#7aa2f7", mature="#a8c4fb",
                     suspended="#414868", leech="#f7768e", hl="#bb9af7"),
    },
}

KEYMAP = {"ink2": "ink-2", "ink3": "ink-3", "cover_ink": "cover-ink", "new": "st-new",
          "learning": "st-learning", "young": "st-young", "mature": "st-mature",
          "suspended": "st-suspended", "leech": "st-leech"}


# --------------------------------------------------------------------------
# Color: contraste WCAG y luminosidad CIELAB
# --------------------------------------------------------------------------

def _rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    r, g, b = (_lin(c) for c in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lab_l(hex_color: str) -> float:
    y = luminance(hex_color)
    f = y ** (1 / 3) if y > 216 / 24389 else (24389 / 27 * y + 16) / 116
    return 116 * f - 16


# --------------------------------------------------------------------------
# Validación
# --------------------------------------------------------------------------

def check_theme(tid: str, mode: str, t: dict) -> list:
    errors = []

    def need(label, a, b, minimum):
        value = contrast(t[a], t[b])
        if value < minimum:
            errors.append(f"{tid}/{mode}: {label} {value:.2f}:1 < {minimum}:1 ({t[a]} sobre {t[b]})")

    for bg in ("paper", "sheet"):
        need(f"texto sobre {bg}", "ink", bg, 7.0)
        need(f"texto secundario sobre {bg}", "ink2", bg, 4.5)
        need(f"texto suave sobre {bg}", "ink3", bg, 4.5)
    need("portada", "cover_ink", "cover", 4.5)
    need("texto de botones", "paper", "mature", 4.5)
    need("palabra resaltada", "hl", "sheet", 4.5)
    need("difíciles (gráfico)", "leech", "sheet", 3.0)
    need("jóvenes (gráfico)", "young", "sheet", 2.0)

    # Escala de estados: pendiente -> aprendiendo -> joven -> sabida
    ramp = [lab_l(t[k]) for k in ("new", "learning", "young", "mature")]
    steps = [ramp[i] - ramp[i + 1] for i in range(3)]
    if mode == "dark":
        steps = [-s for s in steps]
    if any(s < 8 for s in steps):
        errors.append(f"{tid}/{mode}: escala de estados con pasos muy chicos (L*: {[round(x) for x in ramp]})")
    gap = abs(lab_l(t["new"]) - lab_l(t["paper"]))
    if gap < 2.5:
        errors.append(f"{tid}/{mode}: las pendientes casi no se ven sobre el fondo (ΔL* {gap:.1f})")
    if abs(lab_l(t["rule"]) - lab_l(t["sheet"])) < 4:
        errors.append(f"{tid}/{mode}: las líneas divisorias casi no se ven")
    return errors


def report() -> list:
    errors = []
    for tid, theme in THEMES.items():
        for mode in ("light", "dark"):
            t = theme[mode]
            missing = [k for k in ("paper", "sheet", "ink", "ink2", "ink3", "rule", "cover", "cover_ink", "slip",
                                   "focus", "new", "learning", "young", "mature", "suspended", "leech", "hl")
                       if k not in t]
            if missing:
                errors.append(f"{tid}/{mode}: faltan {missing}")
                continue
            errors += check_theme(tid, mode, t)
            print(f"  {tid:11} {mode:5}  texto {contrast(t['ink'], t['paper']):5.2f}  "
                  f"suave {min(contrast(t['ink3'], t['paper']), contrast(t['ink3'], t['sheet'])):4.2f}  "
                  f"botón {contrast(t['paper'], t['mature']):4.2f}  resaltado {contrast(t['hl'], t['sheet']):4.2f}  "
                  f"escala L* {[round(lab_l(t[k])) for k in ('new', 'learning', 'young', 'mature')]}")
    return errors


# --------------------------------------------------------------------------
# Generar archivos
# --------------------------------------------------------------------------

def css_block(selector: str, t: dict, dark: bool) -> str:
    lines = [f"{selector} {{", f"  color-scheme: {'dark' if dark else 'light'};"]
    for key, value in t.items():
        lines.append(f"  --{KEYMAP.get(key, key)}: {value};")
    lines.append("}")
    return "\n".join(lines)


def build() -> None:
    css = ["/* Generado por dev/build_themes.py: no editar a mano. */", ""]
    for tid, theme in THEMES.items():
        css.append(css_block(f'.adic[data-theme="{tid}"]', theme["light"], False))
        css.append(css_block(f'.adic[data-theme="{tid}"].is-dark', theme["dark"], True))
        css.append("")
    with open(os.path.join(WEB, "themes.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(css))

    meta = [{"id": tid, "name": th["name"], "desc": th["desc"],
             "light": {KEYMAP.get(k, k): v for k, v in th["light"].items()},
             "dark": {KEYMAP.get(k, k): v for k, v in th["dark"].items()}}
            for tid, th in THEMES.items()]
    with open(os.path.join(WEB, "themes.js"), "w", encoding="utf-8") as fh:
        fh.write("/* Generado por dev/build_themes.py: no editar a mano. */\n")
        fh.write("window.ADIC_THEMES = " + json.dumps(meta, ensure_ascii=False, indent=1) + ";\n")


if __name__ == "__main__":
    print("Contraste (WCAG) y escala de estados por tema:")
    problems = report()
    if problems:
        print("\nProblemas:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    if "--check" not in sys.argv:
        build()
        print("\nOK: web/themes.css y web/themes.js generados.")

"""Convierte JMdict en el índice de categorías que usa el complemento.

Lee el JMdict oficial (JMdict_e.gz, en XML) y guarda solo lo necesario:
palabra (kanji), lectura (kana) y sus categorías gramaticales. El resultado
es anki_diccionario/data/jmdict_pos.tsv.gz (unos pocos MB).

Uso:
    python dev/build_pos_index.py JMdict_e.gz

JMdict es propiedad del Electronic Dictionary Research and Development Group
(EDRDG) y se usa bajo la licencia Creative Commons BY-SA 4.0.
https://www.edrdg.org/edrdg/licence.html
"""

from __future__ import annotations

import gzip
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "anki_diccionario", "data", "jmdict_pos.tsv.gz")

# Etiquetas que sí se toman de los sentidos secundarios
SECONDARY = {"vt", "vi", "suru"}

# Prioridades que JMdict considera "palabra común"
COMMON = {"news1", "ichi1", "spec1", "spec2", "gai1"}


def map_pos(code: str) -> str:
    """Código de JMdict -> etiqueta del complemento ('' = se ignora)."""
    if code.startswith("v5"):
        return "godan"
    if code in ("v1", "v1-s"):
        return "ichidan"
    if code in ("vk", "vs-i", "vs-s", "vz"):
        return "irregular"
    if code == "vs":
        return "suru"
    if code in ("vt", "vi"):
        return code  # transitivo / intransitivo (para filtros futuros)
    if code.startswith(("v2", "v4")) or code in ("vn", "vr", "vs-c", "v-unspec"):
        return "verb_other"
    if code in ("adj-i", "adj-ix"):
        return "adj_i"
    if code == "adj-na":
        return "adj_na"
    if code == "adj-pn":
        return "prenominal"
    if code in ("adj-t", "adj-f", "adj-kari", "adj-ku", "adj-shiku", "adj-nari"):
        return "adj_other"
    if code in ("n", "n-adv", "n-t", "n-pr"):
        return "noun"
    if code == "pn":
        return "pronoun"
    if code in ("adv", "adv-to"):
        return "adverb"
    if code == "prt":
        return "particle"
    if code == "conj":
        return "conjunction"
    if code == "int":
        return "interjection"
    if code in ("aux", "aux-v", "aux-adj", "cop", "cop-da"):
        return "auxiliary"
    if code == "ctr":
        return "counter"
    if code == "num":
        return "numeral"
    if code == "exp":
        return "expression"
    if code in ("pref", "n-pref"):
        return "prefix"
    if code in ("suf", "n-suf"):
        return "suffix"
    return ""  # adj-no, unc y otros: no aportan categoría


_ENTITY_RE = re.compile(r"&([A-Za-z0-9][A-Za-z0-9-]*);")
_DOCTYPE_RE = re.compile(r"<!DOCTYPE.*?\]>", re.DOTALL)
_DATE_RE = re.compile(r"JMdict created: (\d{4}-\d{2}-\d{2})")
_STANDARD = {"amp", "lt", "gt", "quot", "apos"}


def read_xml(path: str) -> Tuple[str, str]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    found = _DATE_RE.search(text)
    date = found.group(1) if found else ""
    # Las etiquetas vienen como entidades (&v5r;). Las dejamos como texto
    # ("v5r") para conservar el código en lugar de su descripción.
    text = _DOCTYPE_RE.sub("", text, count=1)
    text = _ENTITY_RE.sub(lambda m: m.group(0) if m.group(1) in _STANDARD else m.group(1), text)
    return text, date


def parse_entries(text: str):
    for _, elem in ET.iterparse(io.BytesIO(text.encode("utf-8")), events=("end",)):
        if elem.tag != "entry":
            continue
        kanji = [(k.findtext("keb"), {p.text for p in k.findall("ke_pri")}) for k in elem.findall("k_ele")]
        readings = []
        for r in elem.findall("r_ele"):
            readings.append({
                "text": r.findtext("reb"),
                "nokanji": r.find("re_nokanji") is not None,
                "restr": [x.text for x in r.findall("re_restr")],
                "pri": {p.text for p in r.findall("re_pri")},
            })
        senses = []
        last_pos: List[str] = []
        for s in elem.findall("sense"):
            pos = [p.text for p in s.findall("pos")] or last_pos  # el pos se hereda
            last_pos = pos
            senses.append({
                "pos": pos,
                "stagk": [x.text for x in s.findall("stagk")],
                "stagr": [x.text for x in s.findall("stagr")],
                "misc": [x.text for x in s.findall("misc")],
                "gloss": [g.text or "" for g in s.findall("gloss")],
            })
        elem.clear()
        yield kanji, readings, senses


def entry_rows(kanji, readings, senses):
    """Una fila por cada combinación válida kanji + lectura."""
    uk = bool(senses) and "uk" in senses[0]["misc"]
    kanji_common = any(pri & COMMON for _, pri in kanji)
    for r in readings:
        pairs = []
        if r["nokanji"] or not kanji:
            pairs.append(("", r["pri"]))
        else:
            for k, kpri in kanji:
                if not r["restr"] or k in r["restr"]:
                    pairs.append((k, kpri))
        for k, kpri in pairs:
            # La categoría sale del significado principal: el primer sentido que
            # aplica y que tiene categoría. De los demás solo tomamos
            # transitividad y si lleva する, para que usos raros (行く como
            # auxiliar) no inflen las categorías.
            tags: List[str] = []
            glosses: List[str] = []
            main_found = False
            for s in senses:
                if s["stagk"] and k not in s["stagk"]:
                    continue
                if s["stagr"] and r["text"] not in s["stagr"]:
                    continue
                if len(glosses) < 8:
                    glosses.extend(s["gloss"][:3])
                added_main = False
                for code in s["pos"]:
                    tag = map_pos(code)
                    if not tag or tag in tags:
                        continue
                    if not main_found or tag in SECONDARY:
                        tags.append(tag)
                        added_main = added_main or tag not in SECONDARY
                main_found = main_found or added_main
            if not tags:
                continue
            common = bool(r["pri"] & COMMON) or bool(kpri & COMMON) or (not k and kanji_common)
            # rango: bit 1 = común, bit 0 = suele escribirse en kana (uk)
            rank = (2 if common else 0) | (1 if (uk or not k) else 0)
            # frecuencia: banda nf01-nf48 de JMdict (menor = más frecuente)
            bands = [int(p[2:]) for p in (r["pri"] | kpri) if p.startswith("nf") and p[2:].isdigit()]
            freq = min(bands) if bands else (60 if common else 99)
            gloss = "; ".join(glosses).replace("\t", " ").replace("\n", " ")[:90]
            yield k, r["text"], ",".join(tags), rank, freq, gloss


_KATA = {c: c - 0x60 for c in range(ord("ァ"), ord("ヶ") + 1)}


def hira(text: str) -> str:
    return text.translate(_KATA)


def build(src: str, out: str = OUT) -> Dict[str, int]:
    text, date = read_xml(src)
    seen = set()
    rows = []
    entries = 0
    by_kana: Dict[str, set] = {}
    by_kanji: Dict[str, set] = {}
    for kanji, readings, senses in parse_entries(text):
        entries += 1
        for row in entry_rows(kanji, readings, senses):
            key = row[:3]
            if key not in seen:
                seen.add(key)
                rows.append(row + (entries,))
                by_kana.setdefault(hira(row[1]), set()).add(entries)
                if row[0]:
                    by_kanji.setdefault(row[0], set()).add(entries)

    # El significado solo hace falta para desempatar palabras que comparten
    # lectura o kanji con otra entrada; en las demás lo omitimos (pesa menos).
    def needs_gloss(row) -> bool:
        return len(by_kana[hira(row[1])]) > 1 or (row[0] and len(by_kanji[row[0]]) > 1)

    rows = [r[:5] + ((r[5] if needs_gloss(r) else ""),) for r in rows]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8", compresslevel=9) as fh:
        fh.write(f"#JMdict\t{date}\tEDRDG CC BY-SA 4.0\n")
        for k, r, tags, rank, freq, gloss in rows:
            fh.write(f"{k}\t{r}\t{tags}\t{rank}\t{freq}\t{gloss}\n" if gloss else f"{k}\t{r}\t{tags}\t{rank}\t{freq}\n")
    return {"entries": entries, "rows": len(rows), "bytes": os.path.getsize(out), "date": date}


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    print(build(src, out))

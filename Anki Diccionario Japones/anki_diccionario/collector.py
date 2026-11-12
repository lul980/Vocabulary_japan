"""Lee tu colección de Anki y arma los datos del panel.

Toda la lógica que toca la colección vive aquí. La ventana (HTML/JS) solo
recibe el diccionario que regresa `build_dashboard_data`, convertido a JSON.
Así, más adelante, el mismo JSON puede exportarse a una página aparte.

Solo usa partes estables de la API de Anki (col.db, col.models, col.decks)
y las tablas cards/notes/revlog, que no han cambiado en años.

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from .categories import GROUPS, Classifier, shared_classifier
from .jlpt import JlptIndex, shared_jlpt
from .fields import MAPPABLE, detect_fields, extract_entry, has_japanese

DATA_VERSION = 1

DEFAULT_SETTINGS = {
    "mature_interval_days": 21,  # definición estándar de Anki para "madura"
    "leech_lapses": 8,           # mismo umbral que Anki usa para sanguijuelas
    "word_status_mode": "all",   # "all": todas sus tarjetas maduras | "any": basta una
}

# Orden de avance de los estados (de menos a más)
STATUS_ORDER = ("new", "learning", "young", "mature")


# --------------------------------------------------------------------------
# Mazos
# --------------------------------------------------------------------------

def _all_decks(col) -> List[Tuple[str, int]]:
    try:
        items = col.decks.all_names_and_ids()
        return [(d.name, int(d.id)) for d in items]
    except AttributeError:  # versiones viejas
        return [(d["name"], int(d["id"])) for d in col.decks.all()]


def _deck_and_children(col, deck_id: int) -> List[int]:
    try:
        return [int(x) for x in col.decks.deck_and_child_ids(deck_id)]
    except AttributeError:
        name = dict((i, n) for n, i in _all_decks(col)).get(deck_id, "")
        return [i for n, i in _all_decks(col) if n == name or n.startswith(name + "::")]


def _current_deck_id(col) -> Optional[int]:
    for attr in ("get_current_id", "selected"):
        fn = getattr(col.decks, attr, None)
        if fn:
            try:
                return int(fn())
            except Exception:
                pass
    return None


def deck_list(col) -> List[Dict[str, Any]]:
    """Todos los mazos con su número de tarjetas (sumando submazos)."""
    own: Dict[int, int] = {}
    for did, count in col.db.all(
        "select case when odid then odid else did end, count() from cards group by 1"
    ):
        own[int(did)] = int(count)
    decks = _all_decks(col)
    id_to_name = {i: n for n, i in decks}
    result = []
    for name, did in decks:
        total = sum(c for d, c in own.items()
                    if id_to_name.get(d) == name or id_to_name.get(d, "").startswith(name + "::"))
        if total:
            result.append({"id": did, "name": name, "cards": total})
    result.sort(key=lambda d: d["name"].lower())
    return result


def resolve_deck_id(col, wanted_name: str = "") -> Optional[int]:
    """Elige el mazo: el de la configuración, el actual o el más grande."""
    decks = deck_list(col)
    if not decks:
        return None
    if wanted_name:
        for d in decks:
            if d["name"] == wanted_name:
                return d["id"]
    current = _current_deck_id(col)
    if current and any(d["id"] == current for d in decks):
        return current
    return max(decks, key=lambda d: d["cards"])["id"]


# --------------------------------------------------------------------------
# Estado de cada tarjeta y de cada palabra
# --------------------------------------------------------------------------

def card_status(ctype: int, queue: int, ivl: int, mature_ivl: int) -> str:
    if queue == -1:
        return "suspended"
    if ctype == 0:
        return "new"
    if ctype in (1, 3):  # aprendiendo o reaprendiendo
        return "learning"
    return "mature" if ivl >= mature_ivl else "young"


def word_status(card_statuses: List[str], mode: str) -> str:
    active = [s for s in card_statuses if s != "suspended"]
    if not active:
        return "suspended"
    if mode == "any":
        return max(active, key=STATUS_ORDER.index)
    # mode "all": la palabra está madura solo si TODAS sus tarjetas lo están
    if all(s == "mature" for s in active):
        return "mature"
    if all(s == "new" for s in active):
        return "new"
    if "learning" in active:
        return "learning"
    return "young"


# --------------------------------------------------------------------------
# Datos del panel
# --------------------------------------------------------------------------

def _ids_sql(ids: List[int]) -> str:
    return "(" + ",".join(str(int(i)) for i in ids) + ")"


def build_dashboard_data(col, deck_id: Optional[int], config: Optional[Dict[str, Any]] = None,
                         classifier: Optional[Classifier] = None,
                         jlpt: Optional[JlptIndex] = None) -> Dict[str, Any]:
    config = config or {}
    settings = dict(DEFAULT_SETTINGS)
    for key in settings:
        if key in config:
            settings[key] = config[key]
    mature_ivl = int(settings["mature_interval_days"])
    leech_lapses = int(settings["leech_lapses"])
    mode = settings["word_status_mode"] if settings["word_status_mode"] in ("all", "any") else "all"
    overrides: Dict[str, Dict[str, str]] = config.get("field_mapping") or {}

    decks = deck_list(col)
    names = {d["id"]: d["name"] for d in decks}
    data: Dict[str, Any] = {
        "version": DATA_VERSION,
        "generated_at": int(time.time() * 1000),
        "deck": {"id": deck_id, "name": names.get(deck_id, "")} if deck_id else None,
        "decks": decks,
        "settings": settings,
        "fields": [],
        "skipped": 0,
        "jlpt": {"available": False, "source": "open-anki-jlpt-decks (MIT)"},
        "categories": {"available": False, "source": "", "unmatched": 0,
                       "groups": {k: list(v) for k, v in GROUPS.items()}},
        "words": [],
    }
    if not deck_id:
        return data

    ids = _ids_sql(_deck_and_children(col, deck_id))
    rows = col.db.all(
        f"""select c.id, c.nid, c.type, c.queue, c.ivl, c.lapses, c.reps,
                   n.mid, n.flds, n.tags
            from cards c join notes n on n.id = c.nid
            where c.did in {ids} or c.odid in {ids}
            order by c.nid, c.ord"""
    )

    # Primer repaso y fecha en que maduró cada tarjeta (desde el historial)
    card_filter = f"select id from cards where did in {ids} or odid in {ids}"
    first_seen = dict(col.db.all(
        f"select cid, min(id) from revlog where ease > 0 and cid in ({card_filter}) group by cid"
    ))
    matured_at = dict(col.db.all(
        f"select cid, min(id) from revlog where ivl >= {mature_ivl} and cid in ({card_filter}) group by cid"
    ))

    # Agrupar tarjetas por nota (una nota = una palabra)
    notes: Dict[int, Dict[str, Any]] = {}
    for cid, nid, ctype, queue, ivl, lapses, reps, mid, flds, tags in rows:
        note = notes.get(nid)
        if note is None:
            note = notes[nid] = {"mid": mid, "flds": flds, "tags": tags, "cards": []}
        note["cards"].append({
            "status": card_status(ctype, queue, ivl, mature_ivl),
            "ivl": max(int(ivl), 0),
            "lapses": int(lapses),
            "reps": int(reps),
            "first": first_seen.get(cid),
            "matured": matured_at.get(cid),
        })

    # Detectar campos una vez por tipo de nota
    mappings: Dict[int, Dict[str, Any]] = {}
    usage: Dict[int, int] = {}
    for nid, note in notes.items():
        mid = note["mid"]
        usage[mid] = usage.get(mid, 0) + 1
        if mid in mappings:
            continue
        model = col.models.get(mid) or {}
        field_names = [f["name"] for f in model.get("flds", [])]
        sort_idx = model.get("sortf", 0)
        sort_field = field_names[sort_idx] if 0 <= sort_idx < len(field_names) else None
        samples = [n["flds"].split("\x1f") for n in notes.values() if n["mid"] == mid][:60]
        override = overrides.get(model.get("name", ""))
        mapping = detect_fields(field_names, samples, sort_field, override)
        # Lo que detectaría solo (para mostrar "Automático (...)" en Configuración)
        auto = detect_fields(field_names, samples, sort_field) if override else mapping
        mappings[mid] = {"notetype": model.get("name", "?"), "names": field_names,
                         "auto": {k: auto.get(k) for k in MAPPABLE}, **mapping}

    words: List[Dict[str, Any]] = []
    skipped = 0
    for nid in sorted(notes):
        note = notes[nid]
        mapping = mappings[note["mid"]]
        values = dict(zip(mapping["names"], note["flds"].split("\x1f")))
        entry = extract_entry(values, mapping)
        if not has_japanese(entry["word"]):
            skipped += 1  # p. ej. la nota de bienvenida de Kaishi
            continue

        cards = note["cards"]
        statuses = [c["status"] for c in cards]
        status = word_status(statuses, mode)
        active = [c for c in cards if c["status"] != "suspended"] or cards
        intervals = [c["ivl"] for c in active]
        firsts = [c["first"] for c in cards if c["first"]]
        matured = [c["matured"] for c in active if c["matured"]]
        if mode == "all":
            matured_ms = max(matured) if matured and len(matured) == len(active) else None
        else:
            matured_ms = min(matured) if matured else None
        lapses = max(c["lapses"] for c in cards)
        tags = note["tags"].lower().split()

        words.append({
            "id": nid,
            "word": entry["word"],
            "reading": entry["reading"],
            "meaning": entry["meaning"],
            "status": status,
            "interval": (min(intervals) if mode == "all" else max(intervals)) if intervals else 0,
            "lapses": lapses,
            "reviews": sum(c["reps"] for c in cards),
            "leech": "leech" in tags or lapses >= leech_lapses,
            "first_review": min(firsts) if firsts else None,
            "matured": matured_ms if status == "mature" else None,
            # Oración de ejemplo: segmentos [texto, furigana, resaltado]
            "sentence": entry["sentence"],
            "sentence_meaning": entry["sentence_meaning"],
            "audio": entry["audio"],
        })

    # Categorías gramaticales con JMdict
    # La base se cierra al terminar: si queda abierta, Windows no deja que Anki
    # actualice el complemento ("Acceso denegado" en user_files).
    clf = classifier or shared_classifier()
    unmatched = 0
    for w in words:
        w["tags"] = []
    try:
        if clf.open():
            for w in words:
                w["tags"] = clf.classify(w["word"], w["reading"], w["meaning"])
                if not w["tags"]:
                    unmatched += 1
            data["categories"].update({"available": True, "source": clf.source, "unmatched": unmatched})
    finally:
        clf.close()

    # Nivel JLPT (5 = N5 ... 1 = N1, None = no está en las listas)
    index = jlpt or shared_jlpt()
    has_jlpt = index.load()
    for w in words:
        w["jlpt"] = index.level(w["word"], w["reading"]) if has_jlpt else None
    data["jlpt"]["available"] = has_jlpt

    data["words"] = words
    data["skipped"] = skipped
    data["fields"] = [
        {
            "notetype": m["notetype"],
            "notes": usage.get(mid, 0),
            "word": m.get("word"),
            "reading": m.get("reading") or m.get("furigana"),
            "meaning": m.get("meaning"),
            "sentence": m.get("sentence_furigana") or m.get("sentence"),
            "audio": ", ".join(x for x in (m.get("word_audio"), m.get("sentence_audio")) if x) or None,
            "source": m.get("source"),
            # Para el panel de Configuración: campos del tipo de nota, qué se usa y qué eligió el usuario
            "names": m.get("names", []),
            "detected": {k: m.get(k) for k in MAPPABLE},
            "auto": m.get("auto", {}),
            "override": dict(overrides.get(m.get("notetype", ""), {})),
        }
        for mid, m in mappings.items()
    ]
    return data


def summarize(data: Dict[str, Any]) -> Dict[str, int]:
    """Conteo rápido por estado (útil para pruebas y para la consola)."""
    counts = {k: 0 for k in ("mature", "young", "learning", "new", "suspended", "leech")}
    for w in data["words"]:
        counts[w["status"]] += 1
        if w["leech"]:
            counts["leech"] += 1
    counts["total"] = len(data["words"])
    return counts

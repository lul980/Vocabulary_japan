"""Pruebas del lector de mazos, sin abrir Anki.

Uso:
    python dev/test_collector.py                      # solo pruebas de campos
    python dev/test_collector.py ruta/al/mazo.apkg    # además, lee un mazo real
    python dev/test_collector.py ruta/collection.anki21 --json salida.json
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from anki_diccionario import fields  # noqa: E402
from anki_diccionario.categories import Classifier, groups_for  # noqa: E402
from anki_diccionario.collector import (  # noqa: E402
    build_dashboard_data, card_status, resolve_deck_id, summarize, word_status,
)
from fake_collection import FakeCollection  # noqa: E402


def check(label, got, expected):
    ok = got == expected
    print(("  ok   " if ok else "  FALLA") + f" {label}: {got!r}" + ("" if ok else f" (esperaba {expected!r})"))
    return ok


def test_fields() -> bool:
    print("Campos y texto")
    results = [
        check("furigana base", fields.furigana_base("日本[にほん]語[ご]"), "日本語"),
        check("furigana lectura", fields.furigana_reading("日本[にほん]語[ご]"), "にほんご"),
        check("furigana con okurigana", fields.furigana_reading(" 食[た]べる"), "たべる"),
        check("limpiar html", fields.clean_text("<b>私</b>&nbsp;[sound:a.mp3]<br>"), "私"),
    ]

    # Nombres de campos de mazos populares
    decks = {
        "Kaishi 1.5k": (["Word", "Word Reading", "Word Meaning", "Word Furigana", "Word Audio",
                         "Sentence", "Sentence Meaning", "Sentence Furigana", "Notes", "Frequency"],
                        ("Word", "Word Reading", "Word Meaning")),
        "Core 2k/6k": (["Optimized-Voc-Index", "Vocabulary-Kanji", "Vocabulary-Furigana",
                        "Vocabulary-Kana", "Vocabulary-English", "Vocabulary-Audio", "Vocabulary-Pos",
                        "Caution", "Expression", "Reading", "Sentence-Kana", "Sentence-English"],
                       ("Vocabulary-Kanji", "Vocabulary-Kana", "Vocabulary-English")),
        "Lapis (Yomitan)": (["Expression", "ExpressionFurigana", "ExpressionReading", "ExpressionAudio",
                             "SelectionText", "MainDefinition", "Sentence", "SentenceFurigana", "Picture"],
                            ("Expression", "ExpressionReading", "MainDefinition")),
        "Básico": (["Front", "Back"], ("Front", None, "Back")),
        "Japonés": (["単語", "読み", "意味", "例文"], ("単語", "読み", "意味")),
    }
    for name, (names, (w, r, m)) in decks.items():
        got = fields.detect_fields(names, [])
        results.append(check(name, (got["word"], got["reading"], got["meaning"]), (w, r, m)))

    # Nombres sin sentido: tiene que adivinar por el contenido
    samples = [["猫", "ねこ", "cat"], ["食べる", "たべる", "to eat"], ["学校", "がっこう", "school"]]
    got = fields.detect_fields(["A", "B", "C"], samples)
    results.append(check("por contenido", (got["word"], got["reading"], got["meaning"], got["source"]),
                         ("A", "B", "C", "content")))

    print("Estados")
    results += [
        check("nueva", card_status(0, 0, 0, 21), "new"),
        check("suspendida", card_status(2, -1, 40, 21), "suspended"),
        check("reaprendiendo", card_status(3, 1, 0, 21), "learning"),
        check("joven", card_status(2, 2, 20, 21), "young"),
        check("madura", card_status(2, 2, 21, 21), "mature"),
        check("2 tarjetas, modo all", word_status(["mature", "new"], "all"), "young"),
        check("2 tarjetas, modo any", word_status(["mature", "new"], "any"), "mature"),
        check("todas suspendidas", word_status(["suspended"], "all"), "suspended"),
    ]
    return all(results)


MINI_INDEX = """#JMdict\t2026-01-01\tEDRDG CC BY-SA 4.0
私\tわたし\tpronoun,noun\t2
直ぐ\tすぐ\tadverb,adj_na\t3
勉強\tべんきょう\tnoun,suru,vt\t2
好き\tすき\tadj_na,noun\t2
食べる\tたべる\tichidan,vt\t2
\tテレビ\tnoun\t3
\tさん\tsuffix\t3
食べ物\tたべもの\tnoun\t2
着る\tきる\tichidan,vt\t2
切る\tきる\tgodan,vt\t2
要る\tいる\tgodan,vi\t3\t27\tto be needed; to be necessary
居る\tいる\tichidan,vi\t3\t60\tto be (of animate objects); to exist; to stay
"""


def mini_classifier() -> Classifier:
    import gzip
    tmp = tempfile.mkdtemp(prefix="adic-pos-")
    gz = os.path.join(tmp, "mini.tsv.gz")
    with gzip.open(gz, "wt", encoding="utf-8") as fh:
        fh.write(MINI_INDEX)
    return Classifier(gz, os.path.join(tmp, "cache.sqlite"))


def test_categories() -> bool:
    print("Categorías (índice de prueba)")
    clf = mini_classifier()
    if not clf.open():
        print("  FALLA no se pudo abrir el índice")
        return False
    return all([
        check("fuente", clf.source, "JMdict 2026-01-01"),
        check("kanji + lectura", clf.classify("私", "わたし"), ["pronoun", "noun"]),
        check("solo kana (uk)", clf.classify("すぐ", "すぐ"), ["adverb", "adj_na"]),
        check("lectura en hiragana de palabra katakana", clf.classify("テレビ", "てれび"), ["noun"]),
        check("con 〜", clf.classify("〜さん", "さん"), ["suffix"]),
        check("varias formas", clf.classify("食べ物、食物", "たべもの"), ["noun"]),
        check("verbo con する", clf.classify("勉強する", "べんきょうする"), ["irregular", "vt"]),
        check("sin lectura", clf.classify("好き"), ["adj_na", "noun"]),
        check("no está", clf.classify("ゾゾゾ", "ぞぞぞ"), []),
        check("homófono por significado", clf.classify("いる", "いる", "to have, to exist (animate)"), ["ichidan", "vi"]),
        check("homófono sin significado", clf.classify("いる", "いる"), ["godan", "vi"]),
        check("grupos", groups_for(["adj_na", "noun", "vt"]), ["adjective", "noun"]),
        check("grupos verbo", groups_for(["godan", "vt", "suru"]), ["verb", "noun"]),
    ])


def open_collection(path: str) -> FakeCollection:
    if path.endswith(".apkg") or path.endswith(".colpkg"):
        tmp = tempfile.mkdtemp(prefix="adic-")
        with zipfile.ZipFile(path) as z:
            name = "collection.anki21" if "collection.anki21" in z.namelist() else "collection.anki2"
            z.extract(name, tmp)
        path = os.path.join(tmp, name)
    return FakeCollection(path)


def test_deck(path: str, json_out: str = "") -> None:
    print(f"\nMazo: {path}")
    col = open_collection(path)
    deck_id = resolve_deck_id(col)
    data = build_dashboard_data(col, deck_id, {})
    print("  mazo elegido:", data["deck"])
    for f in data["fields"]:
        print("  campos:", f)
    print("  notas ignoradas (sin japonés):", data["skipped"])
    print("  conteo:", summarize(data))
    for w in data["words"][:5]:
        print("   ", w["word"], "|", w["reading"], "|", w["meaning"], "|", w["status"])
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        print("  JSON guardado en", json_out)


if __name__ == "__main__":
    ok = test_fields() & test_categories()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_out = ""
    if "--json" in sys.argv:
        json_out = sys.argv[sys.argv.index("--json") + 1]
        args = [a for a in args if a != json_out]
    if args:
        test_deck(args[0], json_out)
    sys.exit(0 if ok else 1)

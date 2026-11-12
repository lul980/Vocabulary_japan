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
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from anki_diccionario import fields  # noqa: E402
from anki_diccionario.categories import Classifier, groups_for  # noqa: E402
from anki_diccionario.jlpt import JlptIndex  # noqa: E402
from anki_diccionario import settings as adic_settings  # noqa: E402
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
        check("oración con furigana y <b>",
              fields.parse_rich("この 古[ふる]い<b>完[かん] 全[ぜん]</b>な 形[かたち]。"),
              [["この", "", 0], ["古", "ふる", 0], ["い", "", 0], ["完全", "かんぜん", 1], ["な", "", 0], ["形", "かたち", 0], ["。", "", 0]]),
        check("oración sin furigana", fields.parse_rich("私は<b>勉強</b>します。"),
              [["私は", "", 0], ["勉強", "", 1], ["します。", "", 0]]),
        check("archivos de audio (sin rutas)", fields.sound_files("[sound:a.mp3] [sound:../x/b.ogg]"), ["a.mp3", "b.ogg"]),
    ]

    print("Campos elegidos a mano (Configuración)")
    kaishi = ["Word", "Word Reading", "Word Meaning", "Word Audio", "Sentence", "Sentence Meaning", "Sentence Audio"]
    got = fields.detect_fields(kaishi, [], override={"sentence": "Sentence Meaning"})
    results.append(check("cambiar uno deja los demás automáticos",
                         (got["word"], got["reading"], got["sentence"], got["source"]),
                         ("Word", "Word Reading", "Sentence Meaning", "config")))
    got = fields.detect_fields(kaishi, [], override={"word_audio": ""})
    results.append(check("\"ninguno\" apaga el campo", (got["word_audio"], got["sentence_audio"]), (None, "Sentence Audio")))
    got = fields.detect_fields(kaishi, [], override={"word": "No existe"})
    results.append(check("un campo que ya no existe se ignora", (got["word"], got["source"]), ("Word", "name")))

    print("Oración y audio por nombre de campo")
    extras = {
        "Kaishi": (["Word", "Word Reading", "Word Meaning", "Word Furigana", "Word Audio", "Sentence",
                    "Sentence Meaning", "Sentence Furigana", "Sentence Audio"],
                   ("Sentence", "Sentence Furigana", "Sentence Meaning", "Word Audio", "Sentence Audio")),
        "Core 2k/6k": (["Vocabulary-Kanji", "Vocabulary-Kana", "Vocabulary-English", "Vocabulary-Audio",
                        "Expression", "Reading", "Sentence-Kana", "Sentence-English", "Sentence-Audio"],
                       ("Expression", None, "Sentence-English", "Vocabulary-Audio", "Sentence-Audio")),
        "Lapis": (["Expression", "ExpressionFurigana", "ExpressionReading", "ExpressionAudio", "MainDefinition",
                   "Sentence", "SentenceFurigana", "SentenceAudio"],
                  ("Sentence", "SentenceFurigana", None, "ExpressionAudio", "SentenceAudio")),
        "Básico": (["Front", "Back"], (None, None, None, None, None)),
    }
    for name, (names, want) in extras.items():
        got = fields.detect_fields(names, [])
        results.append(check(name, tuple(got[k] for k in ("sentence", "sentence_furigana", "sentence_meaning",
                                                          "word_audio", "sentence_audio")), want))

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
    return Classifier(gz, os.path.join(tmp, "cache"))


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


def test_jlpt() -> bool:
    print("Niveles JLPT (lista de prueba)")
    import gzip
    tmp = tempfile.mkdtemp(prefix="adic-jlpt-")
    gz = os.path.join(tmp, "jlpt.tsv.gz")
    with gzip.open(gz, "wt", encoding="utf-8") as fh:
        fh.write("#JLPT\tprueba\tMIT\n会う\tあう\t5\n終る\tおわる\t5\n重い\tおもい\t5\n"
                 "できる\tできる\t5\n直ぐ\tすぐ\t5\n～円\t～えん\t5\n完全\tかんぜん\t3\n完全\tかんぜん\t2\n")
    j = JlptIndex(gz)
    return all([
        check("exacta", j.level("会う", "あう"), 5),
        check("el nivel más fácil si se repite", j.level("完全", "かんぜん"), 3),
        check("okurigana distinta (終わる/終る)", j.level("終わる", "おわる"), 5),
        check("la lista en kana (出来る/できる)", j.level("出来る", "できる"), 5),
        check("tu palabra en kana (すぐ/直ぐ)", j.level("すぐ", "すぐ"), 5),
        check("con 〜", j.level("〜円", "えん"), 5),
        check("homófono sin kanji en común (思い/重い)", j.level("思い", "おもい"), None),
    ])


def open_files_in(folder: str) -> list:
    """Archivos de `folder` que este proceso tiene abiertos (solo Linux)."""
    fd_dir = "/proc/self/fd"
    if not os.path.isdir(fd_dir):
        return []
    folder = os.path.realpath(folder)
    found = []
    for fd in os.listdir(fd_dir):
        try:
            target = os.readlink(os.path.join(fd_dir, fd))
        except OSError:
            continue
        if target.startswith(folder):
            found.append(target)
    return found


def test_cache_released() -> bool:
    """Reproduce el error de Windows al actualizar: user_files no debe quedar abierto."""
    print("Caché liberada al terminar (para poder actualizar en Windows)")
    clf = mini_classifier()
    os.makedirs(clf.cache_dir, exist_ok=True)
    old = os.path.join(clf.cache_dir, "jmdict_pos.sqlite")  # caché de la versión anterior
    open(old, "w").close()
    col_dir = tempfile.mkdtemp(prefix="adic-col-")
    import sqlite3
    db = sqlite3.connect(os.path.join(col_dir, "c.anki21"))
    db.executescript("""
        create table col (models text, decks text, conf text);
        create table notes (id int, mid int, flds text, tags text, sfld text);
        create table cards (id int, nid int, did int, odid int, ord int, type int, queue int, ivl int, lapses int, reps int, due int);
        create table revlog (id int, cid int, usn int, ease int, ivl int, lastIvl int, factor int, time int, type int);
    """)
    import json as _json
    db.execute("insert into col values (?,?,?)", (
        _json.dumps({"1": {"name": "Básico", "flds": [{"name": "Word"}, {"name": "Word Reading"}, {"name": "Word Meaning"}], "sortf": 0}}),
        _json.dumps({"5": {"name": "Japonés"}}), _json.dumps({"curDeck": 5})))
    db.execute("insert into notes values (10, 1, ?, '', '私')", ("私\x1fわたし\x1fI",))
    db.execute("insert into cards values (100, 10, 5, 0, 0, 0, 0, 0, 0, 0, 1)")
    db.commit()
    db.close()
    col = FakeCollection(os.path.join(col_dir, "c.anki21"))
    data = build_dashboard_data(col, 5, {}, classifier=clf)
    data = build_dashboard_data(col, 5, {}, classifier=clf)  # "Actualizar"
    still_open = open_files_in(clf.cache_dir)
    backup = clf.cache_dir + "_backup"
    os.rename(clf.cache_dir, backup)  # lo mismo que hace Anki al actualizar
    os.rename(backup, clf.cache_dir)
    return all([
        check("clasificó", data["words"][0]["tags"], ["pronoun", "noun"]),
        check("base cerrada", clf.db, None),
        check("archivos abiertos en user_files", still_open, []),
        check("caché vieja borrada", os.path.exists(old), False),
    ])


def test_settings() -> bool:
    """Parte 5: lo que manda el panel de Configuración se valida antes de guardarse."""
    print("Configuración (temas, fondo, campos)")
    import build_themes
    S = adic_settings
    oks = [check("temas iguales en Python y en build_themes", list(S.THEME_IDS), list(build_themes.THEMES))]

    cfg, refresh = S.apply_settings({}, {"theme": "nord", "mode": "dark"})
    oks += [check("tema y modo", (cfg["theme"], cfg["mode"]), ("nord", "dark")),
            check("cambiar el tema no relee el mazo", refresh, False)]
    cfg2, refresh = S.apply_settings(cfg, {"theme": "<b>", "mode": "neón", "language": "fr"})
    oks += [check("valores desconocidos se ignoran", (cfg2["theme"], cfg2["mode"], cfg2["language"]), ("nord", "dark", "auto")),
            check("sin cambios no relee", refresh, False)]
    cfg3, refresh = S.apply_settings(cfg, {"mature_interval_days": "9999", "leech_lapses": -3})
    oks += [check("números se ajustan al rango", (cfg3["mature_interval_days"], cfg3["leech_lapses"]), (365, 1)),
            check("cambiar números relee el mazo", refresh, True)]
    _, refresh = S.apply_settings({"mature_interval_days": 21}, {"mature_interval_days": 21})
    oks.append(check("mismo valor no relee", refresh, False))

    cfg4, _ = S.apply_settings({}, {"background": {"type": "color", "color": "#AABBCC", "veil": 300, "blur": "x", "fit": "raro"}})
    bg = cfg4["background"]
    oks += [check("fondo de color", (bg["type"], bg["color"]), ("color", "#aabbcc")),
            check("velo y desenfoque en rango", (bg["veil"], bg["blur"], bg["fit"]), (95, 0, "cover"))]
    cfg5, _ = S.apply_settings({}, {"background": {"type": "image", "color": "red; x"}})
    oks += [check("imagen sin archivo -> tema", cfg5["background"]["type"], "theme"),
            check("color inválido se ignora", cfg5["background"]["color"], "#e5e9f0")]

    names = ["Word", "Sentence", "Audio"]
    m = S.apply_field_mapping({}, "Kaishi", {"sentence": "Sentence", "word_audio": "", "meaning": "NoExiste",
                                           "word": "", "inventado": "Word", "reading": None}, names)
    oks.append(check("campos elegidos", m["field_mapping"], {"Kaishi": {"sentence": "Sentence", "word_audio": ""}}))
    m = S.apply_field_mapping(m, "Kaishi", {"reading": None}, names)
    oks.append(check("todo automático borra el tipo", m["field_mapping"], {}))
    detected = fields.detect_fields(["Word", "Word Reading", "Word Meaning", "Sentence", "Word Audio"], [],
                                    override={"sentence": "", "word_audio": "Word Audio", "meaning": "Nada"})
    oks += [check("override: ninguno", detected["sentence"], None),
            check("override: campo elegido", detected["word_audio"], "Word Audio"),
            check("override: campo inexistente se ignora", detected["meaning"], "Word Meaning"),
            check("override: origen", detected["source"], "config")]

    full = {"deck": "Kaishi", "theme": "gruvbox", "mode": "light", "leech_lapses": 4,
            "field_mapping": {"X": {"sentence": ""}}, "background": {"type": "color", "color": "#000000"}}
    a = S.reset(full, "appearance")
    oks += [check("reset apariencia", (a["theme"], a["mode"], a["background"]["type"]), ("aizome", "auto", "theme")),
            check("reset apariencia conserva lo demás", (a["leech_lapses"], a["field_mapping"]), (4, {"X": {"sentence": ""}}))]
    b = S.reset(full, "all")
    oks.append(check("reset todo conserva el mazo", (b["deck"], b["leech_lapses"], b["field_mapping"]), ("Kaishi", 8, {})))

    user = tempfile.mkdtemp(prefix="adic-user-")
    src = os.path.join(tempfile.mkdtemp(prefix="adic-pics-"), "foto.JPEG")
    with open(src, "wb") as fh:
        fh.write(b"\xff\xd8\xff")
    open(os.path.join(user, "jmdict_pos-1-2.sqlite"), "w").close()
    first = S.store_background(src, user)
    time.sleep(0.002)  # el nombre lleva los milisegundos
    second = S.store_background(src, user)
    try:
        S.store_background(os.path.join(user, "nota.txt"), user)
        bad = "aceptó"
    except ValueError:
        bad = "rechazó"
    files = sorted(os.listdir(user))
    oks += [check("imagen copiada con nombre nuevo", (first.endswith(".jpg"), first != second), (True, True)),
            check("solo queda la última imagen", files, sorted([second, "jmdict_pos-1-2.sqlite"])),
            check("archivo que no es imagen", bad, "rechazó")]

    ui = S.appearance({"background": {"type": "image", "image": second}}, "/_addons/x", user)
    oks.append(check("url del fondo", ui["background"]["url"], f"/_addons/x/user_files/{second}"))
    ui = S.appearance({"theme": "borrado", "background": {"type": "image", "image": "../../secreto.png"}}, "/_addons/x", user)
    oks.append(check("nombre raro o tema borrado -> por defecto", (ui["theme"], ui["background"]["type"], ui["background"]["url"]), ("aizome", "theme", "")))
    S.clear_backgrounds(user)
    oks.append(check("quitar fondo no toca la caché", os.listdir(user), ["jmdict_pos-1-2.sqlite"]))
    with open(os.path.join(os.path.dirname(HERE), "anki_diccionario", "config.json"), encoding="utf-8") as fh:
        oks.append(check("config.json = valores por defecto", json.load(fh), S.DEFAULTS))
    return all(oks)


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
    ok = test_fields() & test_categories() & test_jlpt() & test_cache_released() & test_settings()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_out = ""
    if "--json" in sys.argv:
        json_out = sys.argv[sys.argv.index("--json") + 1]
        args = [a for a in args if a != json_out]
    if args:
        test_deck(args[0], json_out)
    sys.exit(0 if ok else 1)

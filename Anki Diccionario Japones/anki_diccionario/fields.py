"""Detección de campos y limpieza de texto.

Este módulo no depende de Anki, así que se puede probar fuera de la app.
Sirve para cualquier mazo: busca qué campo tiene la palabra, cuál la
lectura y cuál el significado, primero por el nombre del campo y, si no
lo encuentra, mirando el contenido de algunas notas.

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import html
import os
import re
from typing import Dict, List, Optional, Sequence

# --------------------------------------------------------------------------
# Limpieza de texto
# --------------------------------------------------------------------------

_SOUND_RE = re.compile(r"\[sound:[^\]]*\]")
_BR_RE = re.compile(r"<br\s*/?>|</div>|</p>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
# Mismo formato que usa el filtro {{furigana:}} de Anki: "日本[にほん]語[ご]"
_FURIGANA_RE = re.compile(r" ?([^ >\[\]]+?)\[(.+?)\]")

_JAPANESE_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ヵヶ]")
_KANA_ONLY_RE = re.compile(r"^[぀-ヿー・\s]+$")
_LATIN_RE = re.compile(r"[A-Za-z]")


def clean_text(value: str) -> str:
    """Quita audio, HTML y espacios de sobra de un campo de Anki."""
    if not value:
        return ""
    text = _SOUND_RE.sub("", value)
    text = _BR_RE.sub(" ", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text).replace("\xa0", " ")
    return _SPACE_RE.sub(" ", text).strip()


def has_furigana(text: str) -> bool:
    return bool(_FURIGANA_RE.search(text))


def furigana_base(text: str) -> str:
    """'日本[にほん]語[ご]' -> '日本語'"""
    return _FURIGANA_RE.sub(r"\1", text).replace(" ", "")


def furigana_reading(text: str) -> str:
    """'日本[にほん]語[ご]' -> 'にほんご'"""
    return _FURIGANA_RE.sub(r"\2", text).replace(" ", "")


def has_japanese(text: str) -> bool:
    return bool(_JAPANESE_RE.search(text or ""))


def is_kana_only(text: str) -> bool:
    return bool(text) and bool(_KANA_ONLY_RE.match(text))


# --------------------------------------------------------------------------
# Detección de campos por nombre
# --------------------------------------------------------------------------

# Palabras que delatan que un campo NO es la palabra/lectura/significado
# principal (por ejemplo "Sentence Meaning" o "Word Audio").
_EXCLUDE = (
    "sentence", "example", "audio", "sound", "image", "picture", "photo",
    "notes", "note", "pitch", "frequency", "freq", "tag", "hint", "mnemonic",
    "例文", "音声", "画像",
)

# Los nombres más específicos van primero: en Core 2k/6k "Expression" es la
# oración y la palabra está en "Vocabulary-Kanji".
_WORD_EXACT = (
    "vocabulary kanji", "vocab kanji", "target word", "word", "vocab", "vocabulary",
    "expression", "kanji", "japanese", "term", "front", "単語", "語彙", "表現", "言葉",
)
_WORD_CONTAINS = ("word", "vocab", "expression", "単語", "語彙")
_WORD_BLOCK = ("reading", "meaning", "furigana", "kana", "english", "definition",
               "translation", "gloss", "type", "pos")

_READING_EXACT = (
    "word reading", "vocabulary kana", "vocab kana", "vocabulary reading", "vocab reading",
    "expression reading", "reading", "kana", "hiragana", "yomi", "読み", "読み方", "かな", "ふりがな",
)
_READING_CONTAINS = ("reading", "kana", "読み")

_FURIGANA_EXACT = ("word furigana", "vocabulary furigana", "vocab furigana", "expression furigana", "furigana")
_FURIGANA_CONTAINS = ("furigana",)

_MEANING_EXACT = (
    "word meaning", "vocabulary english", "vocab english", "vocabulary meaning", "vocab meaning",
    "meaning", "english", "definition", "main definition", "glossary", "gloss", "translation",
    "back", "意味", "英語",
)
_MEANING_CONTAINS = ("meaning", "english", "definition", "translation", "gloss", "意味")


_CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")


def _norm(name: str) -> str:
    """'Vocabulary-Kanji' -> 'vocabulary kanji', 'ExpressionReading' -> 'expression reading'"""
    name = _CAMEL_RE.sub(" ", name)
    return _SPACE_RE.sub(" ", name.lower().replace("-", " ").replace("_", " ")).strip()


def _pick(names: Sequence[str], exact: Sequence[str], contains: Sequence[str],
          block: Sequence[str] = (), taken: Sequence[str] = ()) -> Optional[str]:
    normalized = [(n, _norm(n)) for n in names if n not in taken]
    for wanted in exact:
        for original, low in normalized:
            if low == wanted:
                return original
    for original, low in normalized:
        if any(x in low for x in _EXCLUDE) or any(x in low for x in block):
            continue
        if any(x in low for x in contains):
            return original
    return None


def detect_by_name(field_names: Sequence[str]) -> Dict[str, Optional[str]]:
    word = _pick(field_names, _WORD_EXACT, _WORD_CONTAINS, block=_WORD_BLOCK)
    taken = [word] if word else []
    reading = _pick(field_names, _READING_EXACT, _READING_CONTAINS, taken=taken)
    furigana = _pick(field_names, _FURIGANA_EXACT, _FURIGANA_CONTAINS, taken=taken)
    meaning = _pick(field_names, _MEANING_EXACT, _MEANING_CONTAINS, taken=taken)
    return {"word": word, "reading": reading, "furigana": furigana, "meaning": meaning}


# --------------------------------------------------------------------------
# Oración de ejemplo y audio
# --------------------------------------------------------------------------

_SENT = ("sentence", "example", "例文")
_SENT_MEANING = ("meaning", "english", "translation", "eng", "意味", "訳")
_AUDIO = ("audio", "sound", "音声")
_SENT_BLOCK = _SENT_MEANING + _AUDIO + ("furigana", "reading", "kana", "image", "picture", "photo")
_WORD_AUDIO_EXACT = ("word audio", "vocab audio", "vocabulary audio", "expression audio",
                     "audio", "sound", "音声")


def detect_extras(field_names: Sequence[str], taken: Sequence[Optional[str]] = ()) -> Dict[str, Optional[str]]:
    """Campos de oración, su furigana, su traducción y el audio (palabra y oración).

    Kaishi: Sentence, Sentence Furigana, Sentence Meaning, Word Audio, Sentence Audio.
    Core 2k/6k: Expression (la oración), Sentence-English, Vocabulary-Audio, Sentence-Audio.
    Lapis/Yomitan: Sentence, SentenceFurigana, ExpressionAudio, SentenceAudio.
    """
    named = [(n, _norm(n)) for n in field_names if n not in taken]

    def first(test) -> Optional[str]:
        for original, low in named:
            if test(low):
                return original
        return None

    has = lambda low, words: any(w in low for w in words)  # noqa: E731
    sentence = first(lambda low: low in ("sentence", "example sentence", "example", "例文")) or \
        first(lambda low: has(low, _SENT) and not has(low, _SENT_BLOCK))
    if not sentence:
        # Core 2k/6k: la oración vive en "Expression" cuando la palabra está en otro campo
        sentence = first(lambda low: low == "expression")
    sentence_furigana = first(lambda low: has(low, _SENT) and "furigana" in low)
    sentence_meaning = first(lambda low: has(low, _SENT) and has(low, _SENT_MEANING) and not has(low, _AUDIO))
    sentence_audio = first(lambda low: has(low, _SENT) and has(low, _AUDIO))
    word_audio = first(lambda low: low in _WORD_AUDIO_EXACT) or \
        first(lambda low: has(low, _AUDIO) and not has(low, _SENT))
    return {
        "sentence": sentence,
        "sentence_furigana": sentence_furigana,
        "sentence_meaning": sentence_meaning,
        "word_audio": word_audio,
        "sentence_audio": sentence_audio,
    }


_BOLD_SPLIT_RE = re.compile(r"(</?(?:b|strong)\b[^>]*>)", re.IGNORECASE)


def parse_rich(value: str) -> List[List]:
    """Texto de Anki -> segmentos [texto, lectura, resaltado].

    Entiende la furigana de Anki ("古[ふる]い") y el <b> con el que los mazos
    marcan la palabra dentro de la oración. Ejemplo:
    'この 古[ふる]い<b>寺[てら]</b>' -> [["この","",0], ["古","ふる",0], ["い","",0], ["寺","てら",1]]
    """
    segments: List[List] = []
    bold = False
    for part in _BOLD_SPLIT_RE.split(value or ""):
        if _BOLD_SPLIT_RE.fullmatch(part or ""):
            bold = not part.startswith("</")
            continue
        # Como clean_text, pero sin recortar los espacios de las orillas
        text = _BR_RE.sub(" ", _SOUND_RE.sub("", part))
        text = html.unescape(_TAG_RE.sub("", text)).replace("\xa0", " ")
        text = _SPACE_RE.sub(" ", text)
        if not text:
            continue
        pos = 0
        for m in _FURIGANA_RE.finditer(text):
            if m.start() > pos:
                segments.append([text[pos:m.start()], "", int(bold)])
            segments.append([m.group(1), m.group(2), int(bold)])
            pos = m.end()
        if pos < len(text):
            segments.append([text[pos:], "", int(bold)])
    # Los espacios que separan grupos de furigana no se usan en japonés
    out: List[List] = []
    for t, r, h in segments:
        if has_japanese(t) or r:
            t = t.replace(" ", "")
        if not t:
            continue
        if out and not r and not out[-1][1] and out[-1][2] == h:
            out[-1][0] += t  # junta texto seguido con el mismo formato
        elif out and r and out[-1][1] and out[-1][2] == h:
            # 少[しょう] 女[じょ] -> 少女[しょうじょ]: una sola furigana para kanji
            # seguidos, así no quedan huecos cuando la lectura es más ancha
            out[-1][0] += t
            out[-1][1] += r
        else:
            out.append([t, r, h])
    if out:
        out[0][0] = out[0][0].lstrip()
        out[-1][0] = out[-1][0].rstrip()
    return [s for s in out if s[0]]


_SOUND_FILE_RE = re.compile(r"\[sound:([^\]]+)\]")


def sound_files(value: str) -> List[str]:
    """Archivos de audio de un campo ("[sound:x.mp3]" -> ["x.mp3"]), solo el nombre."""
    return [os.path.basename(f.strip()) for f in _SOUND_FILE_RE.findall(value or "") if f.strip()]


# --------------------------------------------------------------------------
# Detección por contenido (cuando los nombres no ayudan)
# --------------------------------------------------------------------------

def detect_by_content(field_names: Sequence[str], samples: List[List[str]]) -> Dict[str, Optional[str]]:
    """Mira unas cuantas notas y adivina qué campo es cuál.

    - Palabra: campo corto con japonés (y que no sea solo kana si hay otro mejor).
    - Lectura: campo corto solo con kana.
    - Significado: campo corto con letras latinas y sin japonés.
    """
    stats = []
    for i, name in enumerate(field_names):
        values = [clean_text(row[i]) for row in samples if i < len(row)]
        values = [v for v in values if v]
        if not values:
            stats.append(None)
            continue
        n = len(values)
        avg_len = sum(len(v) for v in values) / n
        jp = sum(1 for v in values if has_japanese(v)) / n
        kana = sum(1 for v in values if is_kana_only(v)) / n
        latin = sum(1 for v in values if _LATIN_RE.search(v) and not has_japanese(v)) / n
        stats.append({"name": name, "avg": avg_len, "jp": jp, "kana": kana, "latin": latin})

    def best(score_fn, exclude=()):
        scored = [(score_fn(s), s["name"]) for s in stats if s and s["name"] not in exclude]
        scored = [x for x in scored if x[0] > 0]
        return max(scored)[1] if scored else None

    word = best(lambda s: (s["jp"] - 0.5 * s["kana"]) / (1 + s["avg"] / 12) if s["avg"] <= 20 and s["jp"] >= 0.6 else 0)
    reading = best(lambda s: s["kana"] / (1 + s["avg"] / 12) if s["avg"] <= 20 and s["kana"] >= 0.6 else 0,
                   exclude=(word,))
    meaning = best(lambda s: s["latin"] / (1 + s["avg"] / 40) if s["avg"] <= 80 and s["latin"] >= 0.6 else 0,
                   exclude=(word, reading))
    return {"word": word, "reading": reading, "furigana": None, "meaning": meaning}


def detect_fields(field_names: Sequence[str], samples: List[List[str]],
                  sort_field: Optional[str] = None,
                  override: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    """Decide qué campos usar para un tipo de nota.

    Orden de prioridad: configuración del usuario > nombre del campo >
    contenido de las notas > campo de ordenación del tipo de nota.
    Regresa también "source" para mostrarle al usuario de dónde salió.
    """
    names = list(field_names)
    result = _detect_main(names, samples, sort_field)
    result.update(detect_extras(names, taken=[result.get(k) for k in ("word", "reading", "furigana", "meaning")]))

    # Lo que elijas en Configuración gana; lo demás se queda automático.
    # "" significa "ninguno" (por ejemplo, para no usar un campo de audio).
    applied = False
    for key, value in (override or {}).items():
        if key not in MAPPABLE:
            continue
        if value == "" or value is None:
            result[key] = None
            applied = True
        elif value in names:
            result[key] = value
            applied = True
    if applied:
        result["source"] = "config"
    if not result.get("word"):
        result["word"] = sort_field if sort_field in names else (names[0] if names else None)
    return result


# Campos que se pueden elegir a mano (Configuración o field_mapping en config.json)
MAPPABLE = ("word", "reading", "furigana", "meaning", "sentence", "sentence_furigana",
            "sentence_meaning", "word_audio", "sentence_audio")


def _detect_main(names: List[str], samples: List[List[str]], sort_field: Optional[str]) -> Dict[str, Optional[str]]:
    result = detect_by_name(names)
    result["source"] = "name"

    if not result["word"] or not result["meaning"] or not (result["reading"] or result["furigana"]):
        guess = detect_by_content(names, samples)
        for key in ("word", "reading", "meaning"):
            if not result[key] and guess[key] and guess[key] not in result.values():
                result[key] = guess[key]
                result["source"] = "content"

    if not result["word"]:
        result["word"] = sort_field if sort_field in names else (names[0] if names else None)
        result["source"] = "fallback"
    return result


def extract_entry(values: Dict[str, str], mapping: Dict[str, Optional[str]]) -> Dict[str, str]:
    """Saca palabra, lectura y significado limpios de una nota."""
    raw_word = clean_text(values.get(mapping.get("word") or "", ""))
    word, reading = raw_word, ""

    # Algunos mazos guardan la palabra con furigana: "日本[にほん]"
    if has_furigana(raw_word):
        word = furigana_base(raw_word)
        reading = furigana_reading(raw_word)

    if mapping.get("reading"):
        value = clean_text(values.get(mapping["reading"], ""))
        if value:
            reading = furigana_reading(value) if has_furigana(value) else value
    if not reading and mapping.get("furigana"):
        value = clean_text(values.get(mapping["furigana"], ""))
        if value:
            reading = furigana_reading(value) if has_furigana(value) else value

    meaning = clean_text(values.get(mapping.get("meaning") or "", ""))

    # Oración: mejor la versión con furigana; si no hay, la normal
    sentence: List[List] = []
    for key in ("sentence_furigana", "sentence"):
        raw = values.get(mapping.get(key) or "", "")
        if raw and has_japanese(raw):
            sentence = parse_rich(raw)
            break

    word_audio = sound_files(values.get(mapping.get("word_audio") or "", ""))
    if not word_audio:  # algunos mazos meten el audio en el mismo campo de la palabra
        word_audio = sound_files(values.get(mapping.get("word") or "", ""))
    return {
        "word": word,
        "reading": reading,
        "meaning": meaning,
        "sentence": sentence,
        "sentence_meaning": clean_text(values.get(mapping.get("sentence_meaning") or "", "")),
        "audio": {
            "word": word_audio,
            "sentence": sound_files(values.get(mapping.get("sentence_audio") or "", "")),
        },
    }

**deck**: nombre del mazo que se abre al principio. Se guarda solo cuando eliges uno en la ventana. Vacío = el mazo que tengas seleccionado en Anki.

**language**: `"auto"` (el idioma de Anki), `"es"` o `"en"`.

**mature_interval_days**: a partir de cuántos días de intervalo una palabra cuenta como *sabida*. Anki usa 21.

**leech_lapses**: con cuántos fallos una palabra se marca como *difícil*. Anki usa 8. También cuentan las notas con la etiqueta `leech`.

**word_status_mode**: qué hacer cuando una palabra tiene varias tarjetas (por ejemplo, reconocimiento y producción).
- `"all"`: la palabra es sabida solo si todas sus tarjetas están maduras.
- `"any"`: basta con que una esté madura.

**field_mapping**: si la detección automática se equivoca de campo, dile cuál usar para cada tipo de nota. Ejemplo:

```
"field_mapping": {
    "Kaishi 1.5k": {
        "word": "Word",
        "reading": "Word Reading",
        "meaning": "Word Meaning"
    }
}
```

`reading` puede omitirse si la palabra ya trae furigana, como `日本[にほん]`.

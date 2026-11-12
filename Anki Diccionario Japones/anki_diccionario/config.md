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

También puedes indicar la oración y el audio: `sentence`, `sentence_furigana`, `sentence_meaning`, `word_audio` y `sentence_audio`. Ejemplo para Kaishi:

```
"Kaishi 1.5k": {
    "word": "Word",
    "sentence_furigana": "Sentence Furigana",
    "sentence_meaning": "Sentence Meaning",
    "word_audio": "Word Audio",
    "sentence_audio": "Sentence Audio"
}
```

---

Lo de abajo se cambia más fácil desde el engrane ⚙ de la ventana (**Configuración**); aquí solo se explica qué guarda cada opción.

**theme**: tema de colores. `"aizome"` (el original, por defecto), `"solarized"`, `"nord"`, `"catppuccin"`, `"rosepine"`, `"gruvbox"` o `"tokyonight"`.

**mode**: `"auto"` (claro u oscuro igual que Anki), `"light"` o `"dark"`.

**background**: el fondo de la ventana.
- `type`: `"theme"` (el del tema), `"color"` o `"image"`.
- `color`: color en formato `#rrggbb` cuando `type` es `"color"`.
- `image`: nombre del archivo de la imagen dentro de `user_files/`. Lo pone el botón **Elegir imagen…**; no lo escribas a mano.
- `veil`: de 0 a 95. Qué tanto cubre el color del tema a la imagen o al color (más velo = el texto se lee mejor).
- `blur`: desenfoque de la imagen, de 0 a 20 píxeles.
- `fit`: `"cover"` (cubre la ventana) o `"tile"` (mosaico).

En **Campos de tu mazo**, elegir "Ninguno" guarda `""` en `field_mapping`; por ejemplo, `"word_audio": ""` para no usar el audio de la palabra.

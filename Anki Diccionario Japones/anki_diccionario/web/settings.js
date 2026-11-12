/* Diccionario japonés: panel de Configuración (⚙).
   Tema de colores, modo claro/oscuro, fondo propio (color o imagen), idioma,
   cuándo una palabra cuenta como sabida o difícil, y qué campos usar del mazo.

   Los cambios de apariencia se ven al instante; Python los valida y los guarda
   en la configuración del complemento (settings.py).

   dashboard.js lo crea con window.AdicSettings(ctx). Proyecto de Raul Juarez. */

(function () {
  "use strict";

  const I18N = {
    es: {
      title: "Configuración",
      intro: "Personaliza el diccionario. Los cambios de apariencia se ven al momento y se guardan solos.",
      look: "Apariencia",
      theme: "Tema de colores",
      themeNote: "Los temas vienen de paletas abiertas muy usadas (Solarized, Nord, Catppuccin, Rosé Pine, Gruvbox y Tokyo Night). Todos pasan la prueba de contraste WCAG: el texto principal tiene al menos 7:1 y el resto al menos 4.5:1, en claro y en oscuro.",
      mode: "Claro u oscuro",
      modes: { auto: "Igual que Anki", light: "Claro", dark: "Oscuro" },
      bg: "Fondo",
      bgTypes: { theme: "Del tema", color: "Color", image: "Imagen" },
      suggested: "Sugeridos (fondos de los mismos temas)",
      custom: "Otro color",
      pick: "Elegir imagen…",
      change: "Cambiar imagen…",
      clear: "Quitar imagen",
      noImage: "Todavía no eliges una imagen.",
      imageReady: "Imagen guardada en el complemento: no se pierde si mueves el archivo original.",
      veil: "Velo del tema sobre el fondo",
      veilHint: "Más velo = el texto se lee mejor.",
      blur: "Desenfoque",
      fit: "Ajuste",
      fits: { cover: "Cubrir la ventana", tile: "Mosaico" },
      contrastOk: (r) => `El texto se lee bien sobre este fondo (${r}:1).`,
      contrastLow: (r) => `Poco contraste (${r}:1): sube el velo o elige otro color. Lo recomendado es al menos 4.5:1 (WCAG).`,
      imageTip: "Con imágenes, un velo de 60 % o más ayuda a que el texto se lea.",
      progress: "Progreso",
      matureDays: "Una palabra cuenta como sabida cuando su intervalo llega a",
      days: "días",
      matureHint: "Anki usa 21 días para las tarjetas maduras.",
      leech: "Una palabra es difícil cuando la has fallado",
      times: "veces o más",
      leechHint: "Anki marca como sanguijuela (leech) a partir de 8 fallos.",
      multi: "Palabras con varias tarjetas (reconocimiento y producción)",
      multis: { all: "Sabida si todas están maduras", any: "Sabida si al menos una lo está" },
      language: "Idioma",
      languages: { auto: "Igual que Anki", es: "Español", en: "English" },
      fields: "Campos de tu mazo",
      fieldsIntro: "El complemento los detecta solo. Si algo sale mal, elige aquí el campo correcto.",
      notesCount: (n) => `${n} notas`,
      keys: {
        word: "Palabra", reading: "Lectura", furigana: "Palabra con furigana", meaning: "Significado",
        sentence: "Oración", sentence_furigana: "Oración con furigana", sentence_meaning: "Traducción de la oración",
        word_audio: "Audio de la palabra", sentence_audio: "Audio de la oración",
      },
      auto: (f) => `Automático (${f || "ninguno"})`,
      none: "Ninguno",
      reset: "Restablecer",
      resetLook: "Restablecer apariencia",
      resetAll: "Restablecer todo",
      resetConfirm: "¿Seguro? Pulsa otra vez",
      saved: "Guardado.",
      savedRefresh: "Guardado. Actualizando tu mazo…",
      previewOnly: "Vista previa: fuera de Anki los cambios no se guardan.",
    },
    en: {
      title: "Settings",
      intro: "Customize the dictionary. Appearance changes show right away and save automatically.",
      look: "Appearance",
      theme: "Color theme",
      themeNote: "Themes come from widely used open palettes (Solarized, Nord, Catppuccin, Rosé Pine, Gruvbox and Tokyo Night). All pass the WCAG contrast check: main text at least 7:1 and everything else at least 4.5:1, in light and dark.",
      mode: "Light or dark",
      modes: { auto: "Same as Anki", light: "Light", dark: "Dark" },
      bg: "Background",
      bgTypes: { theme: "Theme", color: "Color", image: "Image" },
      suggested: "Suggested (backgrounds from the same themes)",
      custom: "Other color",
      pick: "Choose image…",
      change: "Change image…",
      clear: "Remove image",
      noImage: "No image chosen yet.",
      imageReady: "Image saved inside the add-on: it stays even if you move the original file.",
      veil: "Theme veil over the background",
      veilHint: "More veil = easier to read.",
      blur: "Blur",
      fit: "Fit",
      fits: { cover: "Cover the window", tile: "Tile" },
      contrastOk: (r) => `Text reads well on this background (${r}:1).`,
      contrastLow: (r) => `Low contrast (${r}:1): raise the veil or pick another color. At least 4.5:1 is recommended (WCAG).`,
      imageTip: "With images, a veil of 60% or more keeps text readable.",
      progress: "Progress",
      matureDays: "A word counts as known when its interval reaches",
      days: "days",
      matureHint: "Anki uses 21 days for mature cards.",
      leech: "A word is difficult once you've failed it",
      times: "times or more",
      leechHint: "Anki marks leeches at 8 lapses.",
      multi: "Words with several cards (recognition and production)",
      multis: { all: "Known when all are mature", any: "Known when at least one is" },
      language: "Language",
      languages: { auto: "Same as Anki", es: "Español", en: "English" },
      fields: "Your deck's fields",
      fieldsIntro: "The add-on detects them on its own. If something looks wrong, pick the right field here.",
      notesCount: (n) => `${n} notes`,
      keys: {
        word: "Word", reading: "Reading", furigana: "Word with furigana", meaning: "Meaning",
        sentence: "Sentence", sentence_furigana: "Sentence with furigana", sentence_meaning: "Sentence translation",
        word_audio: "Word audio", sentence_audio: "Sentence audio",
      },
      auto: (f) => `Automatic (${f || "none"})`,
      none: "None",
      reset: "Reset",
      resetLook: "Reset appearance",
      resetAll: "Reset everything",
      resetConfirm: "Sure? Press again",
      saved: "Saved.",
      savedRefresh: "Saved. Updating your deck…",
      previewOnly: "Preview: outside Anki changes aren't saved.",
    },
  };

  const FIELD_KEYS = ["word", "reading", "furigana", "meaning", "sentence", "sentence_furigana",
    "sentence_meaning", "word_audio", "sentence_audio"];

  // Fondos sugeridos: los colores de fondo de los mismos temas investigados
  const SWATCHES = {
    light: ["#f1f4f7", "#fdf6e3", "#eceff4", "#eff1f5", "#faf4ed", "#fbf1c7", "#e1e2e7"],
    dark: ["#10151f", "#002b36", "#2e3440", "#1e1e2e", "#191724", "#282828", "#1a1b26"],
  };

  // ---------- contraste (WCAG) ----------

  function rgb(hex) {
    const h = String(hex || "#000000").replace("#", "");
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  }
  const lin = (c) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  function luminance(hex) {
    const [r, g, b] = rgb(hex).map(lin);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }
  function contrast(a, b) {
    const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  }
  function mix(hexA, hexB, amountB) {
    const a = rgb(hexA);
    const b = rgb(hexB);
    return "#" + a.map((v, i) => Math.round((v * (1 - amountB) + b[i] * amountB) * 255).toString(16).padStart(2, "0")).join("");
  }

  window.AdicSettings = function createSettings(ctx) {
    const { $, esc, fmt, send } = ctx;
    let s = I18N.es;
    let data = null;
    let statusTimer = 0;

    function ui() { return ctx.getUi(); }

    function save(changes, refreshes) {
      const status = $("set-status");
      if (!ctx.insideAnki()) {
        status.textContent = s.previewOnly;
        return;
      }
      send("adic:settings:" + JSON.stringify(changes));
      status.textContent = refreshes ? s.savedRefresh : s.saved;
      clearTimeout(statusTimer);
      statusTimer = setTimeout(() => { status.textContent = ""; }, 2500);
    }

    // Cambia la apariencia al instante y la guarda
    function update(changes, live) {
      const next = JSON.parse(JSON.stringify(ui()));
      Object.keys(changes).forEach((k) => {
        if (k === "background") Object.assign(next.background, changes.background);
        else next[k] = changes[k];
      });
      ctx.applyAppearance(next);
      if (!live) save(changes, false);
      drawLook();
    }

    // ---------- secciones ----------

    function toggle(id, options, current) {
      return `<div class="toggle" role="group" id="${id}">${Object.keys(options).map((k) =>
        `<button type="button" data-value="${k}" aria-pressed="${String(current) === k}">${esc(options[k])}</button>`
      ).join("")}</div>`;
    }

    function themeCard(th) {
      const mode = ctx.isDark() ? "dark" : "light";
      const c = th[mode];
      const ramp = ["st-new", "st-learning", "st-young", "st-mature"].map((k) =>
        `<i style="background:${c[k]}"></i>`).join("");
      return `<button type="button" class="theme-card" data-theme-id="${th.id}" aria-pressed="${ui().theme === th.id}">
          <span class="theme-mock" style="background:${c.paper}" aria-hidden="true">
            <span class="mock-cover" style="background:${c.cover}"></span>
            <span class="mock-sheet" style="background:${c.sheet};color:${c.ink}">
              <b style="color:${c.ink}">語</b><span class="mock-hl" style="color:${c.hl}">彙</span>
              <span class="mock-ramp">${ramp}</span>
            </span>
          </span>
          <span class="theme-name">${esc(th.name)}</span>
          <span class="theme-desc">${esc(th.desc[ctx.lang()] || th.desc.es)}</span>
        </button>`;
    }

    function drawLook() {
      const u = ui();
      const themes = window.ADIC_THEMES || [];
      $("set-themes").innerHTML = themes.map(themeCard).join("");
      $("set-mode").outerHTML = toggle("set-mode", s.modes, u.mode);
      $("set-bg-type").outerHTML = toggle("set-bg-type", s.bgTypes, u.background.type);

      const bg = u.background;
      $("set-bg-color-box").hidden = bg.type !== "color";
      $("set-bg-image-box").hidden = bg.type !== "image";
      $("set-bg-sliders").hidden = bg.type === "theme";
      $("set-fit-row").hidden = bg.type !== "image";

      const mode = ctx.isDark() ? "dark" : "light";
      $("set-swatches").innerHTML = SWATCHES[mode].map((hex) =>
        `<button type="button" class="swatch-btn" data-color="${hex}" aria-pressed="${bg.color === hex}" title="${hex}" style="background:${hex}"></button>`
      ).join("");
      $("set-color").value = bg.color || "#ffffff";

      $("set-image-name").textContent = bg.url ? s.imageReady : s.noImage;
      $("set-pick").textContent = bg.url ? s.change : s.pick;
      $("set-clear").hidden = !bg.url;

      $("set-veil").value = bg.veil;
      $("set-veil-value").textContent = `${bg.veil} %`;
      $("set-blur").value = bg.blur;
      $("set-blur-value").textContent = `${bg.blur} px`;
      $("set-fit").outerHTML = toggle("set-fit", s.fits, bg.fit);

      // Contraste real del texto sobre el fondo elegido (con el velo encima)
      const note = $("set-contrast");
      if (bg.type === "color") {
        const theme = (themes.find((th) => th.id === u.theme) || themes[0] || {})[mode] || {};
        const effective = mix(bg.color, theme.paper || "#ffffff", (bg.veil || 0) / 100);
        const ratio = Math.min(contrast(theme.ink || "#000000", effective), contrast(theme["ink-2"] || "#000000", effective));
        const shown = (Math.floor(ratio * 10) / 10).toFixed(1);
        note.textContent = ratio >= 4.5 ? s.contrastOk(shown) : s.contrastLow(shown);
        note.classList.toggle("is-warning", ratio < 4.5);
      } else if (bg.type === "image") {
        note.textContent = s.imageTip;
        note.classList.toggle("is-warning", bg.veil < 60);
      } else {
        note.textContent = "";
      }
    }

    function drawProgress() {
      const st = (data && data.settings) || {};
      $("set-mature").value = st.mature_interval_days || 21;
      $("set-leech").value = st.leech_lapses || 8;
      $("set-multi").outerHTML = toggle("set-multi", s.multis, st.word_status_mode || "all");
      $("set-lang").outerHTML = toggle("set-lang", s.languages, ui().language || "auto");
    }

    function drawFields() {
      const list = (data && data.fields) || [];
      $("set-fields").innerHTML = list.map((f, idx) => {
        const names = f.names || [];
        const override = f.override || {};
        const rows = FIELD_KEYS.map((key) => {
          const auto = (f.auto || f.detected || {})[key];
          const chosen = Object.prototype.hasOwnProperty.call(override, key) ? override[key] : "__auto";
          const opts = [`<option value="__auto">${esc(s.auto(auto))}</option>`]
            .concat(names.map((n) => `<option value="${esc(n)}"${chosen === n ? " selected" : ""}>${esc(n)}</option>`));
          if (key !== "word") opts.push(`<option value=""${chosen === "" ? " selected" : ""}>${esc(s.none)}</option>`);
          return `<label class="field-row"><span>${esc(s.keys[key])}</span>
              <select data-notetype="${idx}" data-key="${key}">${opts.join("")}</select></label>`;
        }).join("");
        return `<div class="field-block"><h4>${esc(f.notetype)} <span>${esc(s.notesCount(fmt(f.notes)))}</span></h4>${rows}</div>`;
      }).join("");
    }

    function shell() {
      $("settings").innerHTML = `
        <div class="settings-head">
          <h2 class="settings-title">${esc(s.title)}</h2>
          <p class="settings-intro">${esc(s.intro)}</p>
          <p class="set-status" id="set-status" aria-live="polite"></p>
        </div>

        <section class="set-section">
          <h3>${esc(s.look)}</h3>
          <h4 class="set-label">${esc(s.theme)}</h4>
          <div class="theme-grid" id="set-themes"></div>
          <p class="set-note">${esc(s.themeNote)}</p>

          <h4 class="set-label">${esc(s.mode)}</h4>
          <div id="set-mode"></div>

          <h4 class="set-label">${esc(s.bg)}</h4>
          <div id="set-bg-type"></div>
          <div class="bg-box" id="set-bg-color-box" hidden>
            <p class="set-hint">${esc(s.suggested)}</p>
            <div class="swatch-row"><div class="swatch-list" id="set-swatches"></div>
              <label class="color-input"><input type="color" id="set-color"><span>${esc(s.custom)}</span></label></div>
          </div>
          <div class="bg-box" id="set-bg-image-box" hidden>
            <div class="image-row">
              <button type="button" class="set-btn" id="set-pick"></button>
              <button type="button" class="link-button" id="set-clear"></button>
            </div>
            <p class="set-hint" id="set-image-name"></p>
          </div>
          <div class="bg-box" id="set-bg-sliders" hidden>
            <label class="slider-row"><span>${esc(s.veil)}</span><input type="range" id="set-veil" min="0" max="95" step="5"><output id="set-veil-value"></output></label>
            <p class="set-hint">${esc(s.veilHint)}</p>
            <label class="slider-row"><span>${esc(s.blur)}</span><input type="range" id="set-blur" min="0" max="20" step="1"><output id="set-blur-value"></output></label>
            <div class="slider-row" id="set-fit-row"><span>${esc(s.fit)}</span><div id="set-fit"></div></div>
            <p class="set-note" id="set-contrast"></p>
          </div>
        </section>

        <section class="set-section">
          <h3>${esc(s.progress)}</h3>
          <label class="number-row"><span>${esc(s.matureDays)}</span>
            <input type="number" id="set-mature" min="1" max="365"><span>${esc(s.days)}</span></label>
          <p class="set-hint">${esc(s.matureHint)}</p>
          <label class="number-row"><span>${esc(s.leech)}</span>
            <input type="number" id="set-leech" min="1" max="99"><span>${esc(s.times)}</span></label>
          <p class="set-hint">${esc(s.leechHint)}</p>
          <h4 class="set-label">${esc(s.multi)}</h4>
          <div id="set-multi"></div>
        </section>

        <section class="set-section">
          <h3>${esc(s.language)}</h3>
          <div id="set-lang"></div>
        </section>

        <section class="set-section">
          <h3>${esc(s.fields)}</h3>
          <p class="set-hint">${esc(s.fieldsIntro)}</p>
          <div id="set-fields"></div>
        </section>

        <section class="set-section">
          <h3>${esc(s.reset)}</h3>
          <div class="image-row">
            <button type="button" class="set-btn" id="set-reset-look" data-label="${esc(s.resetLook)}">${esc(s.resetLook)}</button>
            <button type="button" class="set-btn is-danger" id="set-reset-all" data-label="${esc(s.resetAll)}">${esc(s.resetAll)}</button>
          </div>
        </section>`;
    }

    // ---------- eventos (delegados: el panel se redibuja) ----------

    function wire() {
      const root = $("settings");
      root.addEventListener("click", (ev) => {
        const t = ev.target;
        const card = t.closest("[data-theme-id]");
        if (card) { update({ theme: card.dataset.themeId }); return; }
        const swatch = t.closest("[data-color]");
        if (swatch) { update({ background: { color: swatch.dataset.color } }); return; }
        const btn = t.closest("button[data-value]");
        if (btn) {
          const group = btn.parentElement.id;
          const v = btn.dataset.value;
          if (group === "set-mode") update({ mode: v });
          else if (group === "set-bg-type") {
            if (v === "image" && !ui().background.url) { ctx.applyAppearance(Object.assign({}, ui(), { background: Object.assign({}, ui().background, { type: "image" }) })); drawLook(); return; }
            update({ background: { type: v } });
          } else if (group === "set-fit") update({ background: { fit: v } });
          else if (group === "set-multi") { save({ word_status_mode: v }, true); markPressed(btn); }
          else if (group === "set-lang") { save({ language: v }, true); markPressed(btn); }
          return;
        }
        if (t.closest("#set-pick")) { if (ctx.insideAnki()) send("adic:pickbg"); else $("set-status").textContent = s.previewOnly; return; }
        if (t.closest("#set-clear")) { if (ctx.insideAnki()) send("adic:clearbg"); return; }
        const reset = t.closest("#set-reset-look, #set-reset-all");
        if (reset) confirmTwice(reset, reset.id === "set-reset-all" ? "adic:reset:all" : "adic:reset:appearance");
      });

      // Deslizadores: se ve en vivo mientras arrastras y se guarda al soltar
      root.addEventListener("input", (ev) => {
        if (ev.target.id === "set-veil") update({ background: { veil: Number(ev.target.value) } }, true);
        else if (ev.target.id === "set-blur") update({ background: { blur: Number(ev.target.value) } }, true);
        else if (ev.target.id === "set-color") update({ background: { color: ev.target.value } }, true);
      });
      root.addEventListener("change", (ev) => {
        const t = ev.target;
        if (t.id === "set-veil") save({ background: { veil: Number(t.value) } }, false);
        else if (t.id === "set-blur") save({ background: { blur: Number(t.value) } }, false);
        else if (t.id === "set-color") save({ background: { color: t.value, type: "color" } }, false);
        else if (t.id === "set-mature") saveNumber(t, "mature_interval_days", 1, 365, 21);
        else if (t.id === "set-leech") saveNumber(t, "leech_lapses", 1, 99, 8);
        else if (t.matches("select[data-notetype]")) saveFields(Number(t.dataset.notetype));
      });
    }

    // Los números releen el mazo: se mandan una sola vez y ya ajustados al rango
    const sentNumbers = {};
    function saveNumber(input, key, low, high, fallback) {
      const raw = parseInt(input.value, 10);
      const value = Number.isFinite(raw) ? Math.min(high, Math.max(low, raw)) : fallback;
      input.value = value;
      const current = key in sentNumbers ? sentNumbers[key] : ((data && data.settings) || {})[key];
      if (value === current) return;
      sentNumbers[key] = value;
      save({ [key]: value }, true);
    }

    function markPressed(btn) {
      btn.parentElement.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    }

    function saveFields(idx) {
      const f = (data.fields || [])[idx];
      if (!f) return;
      const mapping = {};
      $("set-fields").querySelectorAll(`select[data-notetype="${idx}"]`).forEach((sel) => {
        if (sel.value !== "__auto") mapping[sel.dataset.key] = sel.value;
      });
      if (!ctx.insideAnki()) { $("set-status").textContent = s.previewOnly; return; }
      send("adic:fields:" + JSON.stringify({ notetype: f.notetype, mapping, names: f.names || [] }));
      $("set-status").textContent = s.savedRefresh;
    }

    // Sin ventanas de confirmación: el botón pide un segundo clic
    function confirmTwice(btn, cmd) {
      if (btn.dataset.armed) {
        delete btn.dataset.armed;
        btn.textContent = btn.dataset.label;
        if (ctx.insideAnki()) { send(cmd); $("set-status").textContent = s.saved; } else $("set-status").textContent = s.previewOnly;
        return;
      }
      btn.dataset.armed = "1";
      btn.textContent = s.resetConfirm;
      setTimeout(() => { delete btn.dataset.armed; btn.textContent = btn.dataset.label; }, 3000);
    }

    // ---------- API para dashboard.js ----------

    let built = false;
    function render(model) {
      s = I18N[ctx.lang()] || I18N.es;
      data = model.data;
      Object.keys(sentNumbers).forEach((k) => { delete sentNumbers[k]; });  // ya viene lo guardado
      shell();
      built = true;
      drawLook();
      drawProgress();
      drawFields();
    }

    function refreshLook() { if (built) drawLook(); }

    wire();
    return { render, refreshLook, contrast };
  };
})();

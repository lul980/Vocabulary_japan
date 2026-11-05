/* Diccionario japonés: lógica del panel.
   Recibe el JSON que arma collector.py (AnkiDiccionario.render(data)) y dibuja todo.
   No depende de Anki: la misma página puede abrirse sola con un JSON exportado. */

(function () {
  "use strict";

  // Orden de los estados: de más avanzado a menos (leyenda y orden "por estado")
  const STATUS = ["mature", "young", "learning", "new", "suspended"];
  const STATUS_VAR = {
    mature: "--st-mature", young: "--st-young", learning: "--st-learning",
    new: "--st-new", suspended: "--st-suspended", leech: "--st-leech",
  };

  // Acepta números ya formateados ("1", "1,500")
  const plural = (n, one, many) => (Number(String(n).replace(/[^\d.-]/g, "")) === 1 ? one : many);

  const I18N = {
    es: {
      tabProgress: "Progreso",
      tabDictionary: "Diccionario",
      catsTitle: "Por categoría",
      catsSub: "Cuántas sabes de cada tipo de palabra.",
      catsNote: (src) => `Una palabra puede estar en varias categorías: 好き es adjetivo な y también sustantivo. Categorías de ${src} (© EDRDG, CC BY-SA 4.0).`,
      catsUnavailable: "No se encontró el diccionario de categorías. Vuelve a instalar el complemento.",
      countOf: (k, n) => `<b>${k}</b> de ${n}`,
      groups: {
        verb: ["Verbos", "動詞"], noun: ["Sustantivos", "名詞"], adjective: ["Adjetivos", "形容詞"],
        pronoun: ["Pronombres", "代名詞"], adverb: ["Adverbios", "副詞"], particle: ["Partículas", "助詞"],
        conjunction: ["Conjunciones", "接続詞"], interjection: ["Interjecciones", "感動詞"],
        counter: ["Contadores", "助数詞"], numeral: ["Números", "数詞"], expression: ["Expresiones", "表現"],
        affix: ["Prefijos y sufijos", "接辞"], auxiliary: ["Auxiliares", "助動詞"], none: ["Sin categoría", ""],
      },
      subs: {
        godan: "godan 五段", ichidan: "ichidan 一段", irregular: "irregulares する・来る", verb_other: "otros",
        suru: "con する", adj_i: "い", adj_na: "な", prenominal: "連体詞", adj_other: "otros",
        prefix: "prefijos", suffix: "sufijos",
      },
      tags: {
        godan: "verbo godan", ichidan: "verbo ichidan", irregular: "verbo irregular", verb_other: "verbo",
        suru: "sustantivo con する", noun: "sustantivo", adj_i: "adjetivo い", adj_na: "adjetivo な",
        prenominal: "prenominal 連体詞", adj_other: "adjetivo", pronoun: "pronombre", adverb: "adverbio",
        particle: "partícula", conjunction: "conjunción", interjection: "interjección", counter: "contador",
        numeral: "número", expression: "expresión", prefix: "prefijo", suffix: "sufijo", auxiliary: "auxiliar",
        vt: "transitivo", vi: "intransitivo",
      },
      tipType: "Tipo",
      noType: "sin categoría",
      soonTitle: "Tu diccionario llega en la siguiente versión",
      soonBody: "Aquí vas a poder ver todas tus palabras, buscarlas por kanji, lectura o significado, y filtrarlas por categoría, estado y nivel JLPT. Así se verán tus palabras con sus categorías:",
      sourceCats: (src) => `Categorías gramaticales: ${src}, © EDRDG, licencia CC BY-SA 4.0.`,
      sourceUnmatched: (n) => `${n} ${plural(n, "palabra no aparece", "palabras no aparecen")} en JMdict y ${plural(n, "queda", "quedan")} como “Sin categoría”.`,
      title: "Diccionario japonés",
      subtitle: "Tu progreso con el vocabulario de Anki",
      deckLabel: "Mazo",
      refresh: "Actualizar",
      loading: "Leyendo tu mazo…",
      status: { mature: "Sabidas", young: "Jóvenes", learning: "Aprendiendo", new: "Pendientes",
                suspended: "Suspendidas", leech: "Difíciles" },
      statusOne: { mature: "Sabida", young: "Joven", learning: "Aprendiendo", new: "Pendiente",
                   suspended: "Suspendida", leech: "difícil" },
      heroCaption: (k, total, deck) => `${plural(k, "palabra sabida", "palabras sabidas")} de ${total} en ${deck}`,
      percentLabel: "del mazo",
      inProgress: "en progreso",
      leechLabel: "difíciles",
      definition: (d) => `Sabida: su intervalo ya llega a ${d} días o más. Joven: ya la repasas, pero con menos de ${d} días.`,
      mapTitle: "Tu mazo, palabra por palabra",
      mapSub: (n) => `Cada cuadro es una de tus ${n} palabras. Pasa el cursor para verla.`,
      orderDeck: "Orden del mazo",
      orderStatus: "Por estado",
      mapAria: (n, k) => `Mapa de ${n} palabras; ${k} sabidas.`,
      rhythmTitle: "Palabras nuevas por semana",
      chartEmpty: "Cuando repases tus primeras palabras, aquí verás cuántas empiezas cada semana.",
      weekTip: (n, d) => `Semana del ${d}: ${n} ${plural(n, "nueva", "nuevas")}`,
      thisWeek: "esta semana",
      projDone: "Ya empezaste todas las palabras del mazo.",
      projLeft: (n) => `Te faltan <b>${n}</b> ${plural(n, "palabra", "palabras")} por empezar.`,
      projRate: (k, r, w) => ` A tu ritmo de las últimas ${k} semanas (unas <b>${r}</b> por semana), las habrás visto todas en unas <b>${w}</b> ${plural(w, "semana", "semanas")}.`,
      projWeek: (a, b) => ` Esta semana llevas ${a} ${plural(a, "nueva", "nuevas")} y ${b} ${plural(b, "maduró", "maduraron")}.`,
      recentTitle: "Recién aprendidas",
      hardTitle: "Te cuestan trabajo",
      recentEmpty: "Las palabras que llegues a dominar aparecerán aquí.",
      hardEmpty: "Ninguna palabra te ha costado trabajo todavía.",
      lapses: (n) => `${n} ${plural(n, "fallo", "fallos")}`,
      tipInterval: "Intervalo",
      tipLapses: "Fallos",
      tipReviews: "Repasos",
      tipFirst: "Primera vez",
      days: (n) => `${n} ${plural(n, "día", "días")}`,
      noDeckTitle: "No hay mazos con tarjetas",
      noDeckBody: "Crea o importa un mazo en Anki y vuelve a abrir esta ventana.",
      noWordsTitle: "Este mazo no tiene palabras en japonés",
      noWordsBody: "Elige otro mazo arriba. Si este sí tiene japonés, revisa abajo qué campos se usaron y ajústalos en la configuración del complemento.",
      sourceTitle: "Cómo se leyó tu mazo",
      sourceCols: ["Tipo de nota", "Notas", "Palabra", "Lectura", "Significado", "Detectado por"],
      sourceKinds: { name: "nombre del campo", content: "contenido", config: "tu configuración", fallback: "campo principal" },
      none: "ninguno",
      skipped: (n) => `Se ${plural(n, "ignoró", "ignoraron")} ${n} ${plural(n, "nota", "notas")} sin texto en japonés, como las notas de bienvenida.`,
      howToChange: "Para cambiar los campos o qué cuenta como sabida, abre Herramientas › Complementos, elige Diccionario japonés y pulsa Configuración.",
      updated: (d) => `Actualizado a las ${d}`,
    },
    en: {
      tabProgress: "Progress",
      tabDictionary: "Dictionary",
      catsTitle: "By category",
      catsSub: "How many you know of each kind of word.",
      catsNote: (src) => `A word can belong to several categories: 好き is a な-adjective and also a noun. Categories from ${src} (© EDRDG, CC BY-SA 4.0).`,
      catsUnavailable: "The category dictionary is missing. Reinstall the add-on.",
      countOf: (k, n) => `<b>${k}</b> of ${n}`,
      groups: {
        verb: ["Verbs", "動詞"], noun: ["Nouns", "名詞"], adjective: ["Adjectives", "形容詞"],
        pronoun: ["Pronouns", "代名詞"], adverb: ["Adverbs", "副詞"], particle: ["Particles", "助詞"],
        conjunction: ["Conjunctions", "接続詞"], interjection: ["Interjections", "感動詞"],
        counter: ["Counters", "助数詞"], numeral: ["Numerals", "数詞"], expression: ["Expressions", "表現"],
        affix: ["Prefixes and suffixes", "接辞"], auxiliary: ["Auxiliaries", "助動詞"], none: ["Uncategorized", ""],
      },
      subs: {
        godan: "godan 五段", ichidan: "ichidan 一段", irregular: "irregular する・来る", verb_other: "other",
        suru: "with する", adj_i: "い", adj_na: "な", prenominal: "連体詞", adj_other: "other",
        prefix: "prefixes", suffix: "suffixes",
      },
      tags: {
        godan: "godan verb", ichidan: "ichidan verb", irregular: "irregular verb", verb_other: "verb",
        suru: "noun with する", noun: "noun", adj_i: "い-adjective", adj_na: "な-adjective",
        prenominal: "prenominal 連体詞", adj_other: "adjective", pronoun: "pronoun", adverb: "adverb",
        particle: "particle", conjunction: "conjunction", interjection: "interjection", counter: "counter",
        numeral: "numeral", expression: "expression", prefix: "prefix", suffix: "suffix", auxiliary: "auxiliary",
        vt: "transitive", vi: "intransitive",
      },
      tipType: "Type",
      noType: "uncategorized",
      soonTitle: "Your dictionary arrives in the next version",
      soonBody: "Here you'll see all your words, search them by kanji, reading or meaning, and filter by category, status and JLPT level. This is how your words will look with their categories:",
      sourceCats: (src) => `Grammatical categories: ${src}, © EDRDG, CC BY-SA 4.0 license.`,
      sourceUnmatched: (n) => `${n} ${plural(n, "word isn't", "words aren't")} in JMdict and ${plural(n, "shows", "show")} as “Uncategorized”.`,
      title: "Japanese dictionary",
      subtitle: "Your progress with your Anki vocabulary",
      deckLabel: "Deck",
      refresh: "Refresh",
      loading: "Reading your deck…",
      status: { mature: "Known", young: "Young", learning: "Learning", new: "Not started",
                suspended: "Suspended", leech: "Difficult" },
      statusOne: { mature: "Known", young: "Young", learning: "Learning", new: "Not started",
                   suspended: "Suspended", leech: "difficult" },
      heroCaption: (k, total, deck) => `known ${plural(k, "word", "words")} out of ${total} in ${deck}`,
      percentLabel: "of the deck",
      inProgress: "in progress",
      leechLabel: "difficult",
      definition: (d) => `Known: its interval has reached ${d} days or more. Young: in review, but under ${d} days.`,
      mapTitle: "Your deck, word by word",
      mapSub: (n) => `Each square is one of your ${n} words. Hover to see it.`,
      orderDeck: "Deck order",
      orderStatus: "By status",
      mapAria: (n, k) => `Map of ${n} words; ${k} known.`,
      rhythmTitle: "New words per week",
      chartEmpty: "Once you review your first words, you'll see how many you start each week.",
      weekTip: (n, d) => `Week of ${d}: ${n} new`,
      thisWeek: "this week",
      projDone: "You've started every word in this deck.",
      projLeft: (n) => `<b>${n}</b> ${plural(n, "word", "words")} left to start.`,
      projRate: (k, r, w) => ` At your pace over the last ${k} weeks (about <b>${r}</b> a week), you'll have seen them all in about <b>${w}</b> ${plural(w, "week", "weeks")}.`,
      projWeek: (a, b) => ` This week: ${a} new, ${b} matured.`,
      recentTitle: "Recently learned",
      hardTitle: "Giving you trouble",
      recentEmpty: "Words you master will show up here.",
      hardEmpty: "No word has given you trouble yet.",
      lapses: (n) => `${n} ${plural(n, "lapse", "lapses")}`,
      tipInterval: "Interval",
      tipLapses: "Lapses",
      tipReviews: "Reviews",
      tipFirst: "First seen",
      days: (n) => `${n} ${plural(n, "day", "days")}`,
      noDeckTitle: "No decks with cards",
      noDeckBody: "Create or import a deck in Anki, then open this window again.",
      noWordsTitle: "This deck has no Japanese words",
      noWordsBody: "Pick another deck above. If this one does have Japanese, check which fields were used below and adjust them in the add-on config.",
      sourceTitle: "How your deck was read",
      sourceCols: ["Note type", "Notes", "Word", "Reading", "Meaning", "Detected by"],
      sourceKinds: { name: "field name", content: "content", config: "your config", fallback: "sort field" },
      none: "none",
      skipped: (n) => `${n} ${plural(n, "note", "notes")} without Japanese text ${plural(n, "was", "were")} skipped, such as welcome notes.`,
      howToChange: "To change the fields or what counts as known, open Tools › Add-ons, select Japanese dictionary and click Config.",
      updated: (d) => `Updated at ${d}`,
    },
  };

  let lang = "es";
  let t = I18N.es;
  let model = null;
  let order = "deck";
  let grid = null;
  let focusIndex = -1;
  let animFrame = 0;
  let activeTab = "progress";

  const $ = (id) => document.getElementById(id);
  const send = (cmd) => { if (typeof window.pycmd === "function") window.pycmd(cmd); };
  const locale = () => (lang === "es" ? "es-MX" : "en-US");
  const fmt = (n) => new Intl.NumberFormat(locale()).format(n);
  const fmtDate = (ms) => new Intl.DateTimeFormat(locale(), { day: "numeric", month: "short" }).format(new Date(ms));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cssVar = (name) => getComputedStyle($("adic")).getPropertyValue(name).trim();
  const reducedMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ruby(word, reading) {
    if (!reading || reading === word) return esc(word);
    return `<ruby>${esc(word)}<rt>${esc(reading)}</rt></ruby>`;
  }

  function applyI18n() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const value = t[el.dataset.i18n];
      if (typeof value === "string") el.textContent = value;
    });
  }

  function pickLanguage(pref) {
    if (pref === "es" || pref === "en") return pref;
    const nav = (navigator.language || "es").toLowerCase();
    return nav.startsWith("es") ? "es" : "en";
  }

  // ------------------------------------------------------------------
  // Datos
  // ------------------------------------------------------------------

  function prepare(data) {
    const words = data.words || [];
    const counts = { mature: 0, young: 0, learning: 0, new: 0, suspended: 0, leech: 0 };
    words.forEach((w) => {
      counts[w.status] += 1;
      if (w.leech) counts.leech += 1;
    });
    return { data, words, counts, total: words.length };
  }

  // ------------------------------------------------------------------
  // Encabezado y estados de carga
  // ------------------------------------------------------------------

  function fillDeckSelect(data) {
    const select = $("deck-select");
    const current = data.deck ? String(data.deck.id) : "";
    select.innerHTML = (data.decks || []).map((d) =>
      `<option value="${d.id}"${String(d.id) === current ? " selected" : ""}>${esc(d.name)} (${fmt(d.cards)})</option>`
    ).join("");
    select.disabled = !(data.decks || []).length;
  }

  function setLoading() {
    $("page").setAttribute("aria-busy", "true");
    $("loading").hidden = false;
    $("refresh").disabled = true;
    ["hero", "progress", "deckmap", "cats", "lower", "empty", "source"].forEach((id) => { $(id).hidden = true; });
  }

  function showEmpty(title, body) {
    $("empty").hidden = false;
    $("empty-title").textContent = title;
    $("empty-body").textContent = body;
  }

  // ------------------------------------------------------------------
  // Resumen
  // ------------------------------------------------------------------

  function renderHero() {
    const { counts, total, data } = model;
    const deckName = data.deck ? data.deck.name : "";
    $("known-count").textContent = fmt(counts.mature);
    $("hero-caption").textContent = t.heroCaption(counts.mature, fmt(total), deckName);

    const active = total - counts.suspended;
    const pct = active ? Math.round((counts.mature / active) * 100) : 0;
    const stats = [
      `<div class="hero-stat"><strong>${pct} %</strong><span>${t.percentLabel}</span></div>`,
      `<div class="hero-stat"><strong>${fmt(counts.young + counts.learning)}</strong><span>${t.inProgress}</span></div>`,
    ];
    if (counts.leech) {
      stats.push(`<div class="hero-stat"><strong>${fmt(counts.leech)}</strong><span><i class="swatch flag" aria-hidden="true"></i>${t.leechLabel}</span></div>`);
    }
    $("hero-side").innerHTML = stats.join("");
  }

  function renderProgress() {
    const { counts, total, data } = model;
    const bar = $("segbar");
    // La barra muestra solo palabras activas: las suspendidas no cuentan para el porcentaje
    const active = STATUS.filter((s) => s !== "suspended");
    bar.innerHTML = active.filter((s) => counts[s] > 0).map((s) =>
      `<span style="flex:${counts[s]};background:var(${STATUS_VAR[s]})" title="${esc(t.status[s])}: ${fmt(counts[s])}"></span>`
    ).join("");
    bar.setAttribute("aria-label", active.map((s) => `${t.status[s]} ${fmt(counts[s])}`).join(", ") + ` / ${fmt(total - counts.suspended)}`);

    const items = STATUS.filter((s) => s !== "suspended" || counts[s] > 0).map((s) =>
      `<li><i class="swatch${s === "suspended" ? " is-suspended" : ""}" style="background:var(${STATUS_VAR[s]})"></i>${esc(t.status[s])} <b>${fmt(counts[s])}</b></li>`
    );
    if (counts.leech) {
      items.push(`<li><i class="swatch" style="background:var(--st-leech)"></i>${esc(t.status.leech)} <b>${fmt(counts.leech)}</b></li>`);
    }
    $("legend").innerHTML = items.join("");
    $("definition-note").textContent = t.definition(data.settings ? data.settings.mature_interval_days : 21);
  }

  // ------------------------------------------------------------------
  // Mapa del mazo (canvas: aguanta mazos de 15,000+ palabras)
  // ------------------------------------------------------------------

  function orderedWords() {
    if (order === "deck") return model.words;
    const rank = (w) => STATUS.indexOf(w.status);
    return model.words.map((w, i) => [w, i]).sort((a, b) => rank(a[0]) - rank(b[0]) || a[1] - b[1]).map((x) => x[0]);
  }

  function layoutGrid(n, width) {
    const targetHeight = n > 6000 ? 340 : 300;
    let pitch = Math.floor(Math.sqrt((width * targetHeight) / Math.max(n, 1)));
    pitch = Math.max(4, Math.min(18, pitch));
    const gap = pitch >= 10 ? 2 : 1;
    const cols = Math.max(1, Math.floor((width + gap) / pitch));
    const rows = Math.ceil(n / cols);
    return { pitch, gap, cell: pitch - gap, cols, rows, height: rows * pitch - gap };
  }

  function setupGrid(animate) {
    grid = { items: orderedWords(), colors: {} };
    Object.keys(STATUS_VAR).forEach((k) => { grid.colors[k] = cssVar(STATUS_VAR[k]); });
    grid.colors.ink = cssVar("--ink");
    grid.colors.paper = cssVar("--paper");
    $("grid").setAttribute("aria-label", t.mapAria(fmt(model.total), fmt(model.counts.mature)));
    $("map-sub").textContent = t.mapSub(fmt(model.total));

    cancelAnimationFrame(animFrame);
    if (animate && !reducedMotion()) {
      const start = performance.now();
      const step = (now) => {
        const p = Math.min(1, (now - start) / 900);
        drawGrid(1 - Math.pow(1 - p, 3));
        if (p < 1) animFrame = requestAnimationFrame(step);
      };
      animFrame = requestAnimationFrame(step);
    } else {
      drawGrid(1);
    }
  }

  function cellColor(w) {
    if (w.status === "suspended") return null;
    if (w.leech) return grid.colors.leech;
    return grid.colors[w.status];
  }

  // progress < 1 = animación de "teñido": las palabras se tiñen en orden
  function drawGrid(progress) {
    if (!grid) return;
    const canvas = $("grid");
    const width = $("grid-wrap").clientWidth;
    const n = grid.items.length;
    const L = layoutGrid(n, width);
    grid.layout = L;

    const dpr = window.devicePixelRatio || 1;
    canvas.style.height = L.height + "px";
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(L.height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, L.height);

    const radius = L.cell >= 8 ? 2 : 0;
    const dyed = progress >= 1 ? n : Math.floor(n * progress);
    for (let i = 0; i < n; i++) {
      const w = grid.items[i];
      const x = (i % L.cols) * L.pitch;
      const y = Math.floor(i / L.cols) * L.pitch;
      const color = i < dyed ? cellColor(w) : grid.colors.new;
      if (color === null) {
        ctx.strokeStyle = grid.colors.suspended;
        ctx.lineWidth = 1;
        ctx.strokeRect(x + 0.5, y + 0.5, L.cell - 1, L.cell - 1);
        continue;
      }
      ctx.fillStyle = color;
      if (radius) {
        ctx.beginPath();
        roundRect(ctx, x, y, L.cell, L.cell, radius);
        ctx.fill();
      } else {
        ctx.fillRect(x, y, L.cell, L.cell);
      }
    }

    if (focusIndex >= 0 && focusIndex < n && progress >= 1) {
      const x = (focusIndex % L.cols) * L.pitch;
      const y = Math.floor(focusIndex / L.cols) * L.pitch;
      ctx.lineWidth = 2;
      ctx.strokeStyle = grid.colors.paper;
      ctx.strokeRect(x - 1, y - 1, L.cell + 2, L.cell + 2);
      ctx.strokeStyle = grid.colors.ink;
      ctx.strokeRect(x - 3, y - 3, L.cell + 6, L.cell + 6);
    }
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function showTip(index) {
    const tip = $("tip");
    if (!grid || !grid.layout || index < 0 || index >= grid.items.length) {
      tip.hidden = true;
      return;
    }
    const w = grid.items[index];
    const L = grid.layout;
    const statusKey = w.status;
    const swatchColor = w.leech && statusKey !== "suspended" ? "var(--st-leech)" : `var(${STATUS_VAR[statusKey]})`;
    const rows = [`<dt>${t.tipType}</dt><dd>${esc(tagLabels(w.tags).slice(0, 2).join(", ") || t.noType)}</dd>`];
    if (w.status !== "new") {
      rows.push(`<dt>${t.tipInterval}</dt><dd>${t.days(w.interval)}</dd>`);
      rows.push(`<dt>${t.tipReviews}</dt><dd>${fmt(w.reviews)}</dd>`);
      if (w.lapses) rows.push(`<dt>${t.tipLapses}</dt><dd>${fmt(w.lapses)}</dd>`);
      if (w.first_review) rows.push(`<dt>${t.tipFirst}</dt><dd>${fmtDate(w.first_review)}</dd>`);
    }
    tip.innerHTML =
      `<div class="tip-word" lang="ja">${ruby(w.word, w.reading)}</div>` +
      `<div class="tip-meaning">${esc(w.meaning)}</div>` +
      `<dl><dt>${lang === "es" ? "Estado" : "Status"}</dt><dd><span class="tip-status"><i class="swatch${statusKey === "suspended" ? " is-suspended" : ""}" style="background:${swatchColor}"></i>${esc(t.statusOne[statusKey])}${w.leech ? ", " + esc(t.statusOne.leech) : ""}</span></dd>${rows.join("")}</dl>`;
    tip.hidden = false;

    const wrapWidth = $("grid-wrap").clientWidth;
    const cx = (index % L.cols) * L.pitch;
    const cy = Math.floor(index / L.cols) * L.pitch;
    const tipWidth = tip.offsetWidth;
    let left = cx + L.pitch + 12;
    if (left + tipWidth > wrapWidth) left = cx - tipWidth - 12;
    tip.style.left = Math.max(0, left) + "px";
    tip.style.top = Math.max(0, cy - 24) + "px";
  }

  function indexFromEvent(ev) {
    if (!grid || !grid.layout) return -1;
    const rect = $("grid").getBoundingClientRect();
    const L = grid.layout;
    const col = Math.floor((ev.clientX - rect.left) / L.pitch);
    const row = Math.floor((ev.clientY - rect.top) / L.pitch);
    if (col < 0 || col >= L.cols || row < 0) return -1;
    const i = row * L.cols + col;
    return i < grid.items.length ? i : -1;
  }

  function wireGrid() {
    const canvas = $("grid");
    canvas.addEventListener("mousemove", (ev) => {
      const i = indexFromEvent(ev);
      if (i === focusIndex) return;
      focusIndex = i;
      drawGrid(1);
      showTip(i);
    });
    canvas.addEventListener("mouseleave", () => {
      focusIndex = -1;
      drawGrid(1);
      showTip(-1);
    });
    canvas.addEventListener("keydown", (ev) => {
      if (!grid || !grid.layout) return;
      const L = grid.layout;
      const n = grid.items.length;
      const moves = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: L.cols, ArrowUp: -L.cols };
      if (ev.key in moves) {
        ev.preventDefault();
        focusIndex = Math.min(n - 1, Math.max(0, (focusIndex < 0 ? 0 : focusIndex + moves[ev.key])));
      } else if (ev.key === "Home") {
        focusIndex = 0;
      } else if (ev.key === "End") {
        focusIndex = n - 1;
      } else if (ev.key === "Escape") {
        focusIndex = -1;
      } else {
        return;
      }
      drawGrid(1);
      showTip(focusIndex);
    });
    canvas.addEventListener("focus", () => {
      if (focusIndex < 0) { focusIndex = 0; drawGrid(1); showTip(0); }
    });
    canvas.addEventListener("blur", () => { focusIndex = -1; drawGrid(1); showTip(-1); });

    $("order-toggle").addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-order]");
      if (!btn || btn.dataset.order === order) return;
      order = btn.dataset.order;
      document.querySelectorAll("#order-toggle button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      focusIndex = -1;
      showTip(-1);
      setupGrid(false);
    });
  }


  // ------------------------------------------------------------------
  // Pestañas (Progreso siempre es la principal)
  // ------------------------------------------------------------------

  const TABS = ["progress", "dictionary"];

  function showTab(name, focus) {
    activeTab = name;
    TABS.forEach((tab) => {
      const btn = $("tab-" + tab);
      const selected = tab === name;
      btn.setAttribute("aria-selected", String(selected));
      btn.tabIndex = selected ? 0 : -1;
      $("panel-" + tab).hidden = !selected;
      if (selected && focus) btn.focus();
    });
    // El canvas no se puede medir mientras está oculto: se redibuja al volver
    if (name === "progress" && model && model.total) {
      drawGrid(1);
      renderWeeks();
    }
  }

  function wireTabs() {
    TABS.forEach((tab) => {
      $("tab-" + tab).addEventListener("click", () => showTab(tab, false));
    });
    $("tabs").addEventListener("keydown", (ev) => {
      if (ev.key !== "ArrowRight" && ev.key !== "ArrowLeft") return;
      const i = TABS.indexOf(activeTab);
      const next = TABS[(i + (ev.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length];
      showTab(next, true);
    });
  }

  // ------------------------------------------------------------------
  // Categorías gramaticales
  // ------------------------------------------------------------------

  function tagLabels(tags) {
    const list = (tags || []).filter((tag) => t.tags[tag]);
    const hasVerb = list.some((tag) => ["godan", "ichidan", "irregular", "verb_other"].includes(tag));
    return list
      .filter((tag) => !(tag === "noun" && list.includes("suru")))
      .filter((tag) => hasVerb || (tag !== "vt" && tag !== "vi"))
      .map((tag) => t.tags[tag]);
  }

  function groupsOf(w, tagToGroup) {
    const out = [];
    (w.tags || []).forEach((tag) => {
      const g = tagToGroup[tag];
      if (g && !out.includes(g)) out.push(g);
    });
    return out;
  }

  function renderCategories() {
    const cats = model.data.categories || {};
    const list = $("cat-list");
    $("cats-sub").textContent = t.catsSub;
    if (!cats.available) {
      list.innerHTML = "";
      $("cats-note").textContent = t.catsUnavailable;
      return;
    }
    const groups = cats.groups || {};
    const tagToGroup = {};
    Object.keys(groups).forEach((g) => groups[g].forEach((tag) => { tagToGroup[tag] = g; }));

    const blank = () => ({ total: 0, mature: 0, young: 0, learning: 0, new: 0, suspended: 0, subs: {} });
    const stats = {};
    model.words.forEach((w) => {
      let gs = groupsOf(w, tagToGroup);
      if (!gs.length) gs = ["none"];
      gs.forEach((g) => {
        const st = stats[g] || (stats[g] = blank());
        st.total += 1;
        st[w.status] += 1;
        if (w.status === "suspended") return;
        (groups[g] || []).forEach((tag) => {
          if (!(w.tags || []).includes(tag) || !t.subs[tag]) return;
          const sub = st.subs[tag] || (st.subs[tag] = { total: 0, mature: 0 });
          sub.total += 1;
          if (w.status === "mature") sub.mature += 1;
        });
      });
    });

    const order = Object.keys(stats).sort((a, b) =>
      (a === "none") - (b === "none") || stats[b].total - stats[a].total);
    list.innerHTML = order.map((g) => {
      const st = stats[g];
      const [name, jp] = t.groups[g] || [g, ""];
      const active = st.total - st.suspended;
      const segs = ["mature", "young", "learning", "new"].filter((s) => st[s] > 0).map((s) =>
        `<span style="flex:${st[s]};background:var(${STATUS_VAR[s]})" title="${esc(t.status[s])}: ${fmt(st[s])}"></span>`
      ).join("");
      const subs = (groups[g] || []).filter((tag) => st.subs[tag]).map((tag) =>
        `<span>${esc(t.subs[tag])} ${t.countOf(fmt(st.subs[tag].mature), fmt(st.subs[tag].total))}</span>`
      ).join("");
      const label = `${name}: ${STATUS.map((s) => `${t.status[s]} ${fmt(st[s])}`).join(", ")}`;
      return `<li class="cat${g === "none" ? " is-none" : ""}">
          <div class="cat-name"><strong>${esc(name)}</strong>${jp ? `<span class="jp" lang="ja">${jp}</span>` : ""}</div>
          <div class="segbar" role="img" aria-label="${esc(label)}">${segs || `<span class="rest" style="flex:1"></span>`}</div>
          <div class="cat-count">${t.countOf(fmt(st.mature), fmt(active))}</div>
          ${subs ? `<div class="cat-subs">${subs}</div>` : ""}
        </li>`;
    }).join("");
    $("cats-note").textContent = t.catsNote(cats.source || "JMdict");
  }

  function chipsHtml(tags) {
    const labels = tagLabels(tags);
    if (!labels.length) return `<span class="chips"><span class="chip">${esc(t.noType)}</span></span>`;
    return `<span class="chips">${labels.map((l, i) => `<span class="chip${i === 0 ? " is-primary" : ""}">${esc(l)}</span>`).join("")}</span>`;
  }

  // Vista previa en la pestaña Diccionario: palabras variadas con sus etiquetas
  function renderSoon() {
    const seen = new Set();
    const picks = [];
    for (const w of model.words) {
      const key = (w.tags || [])[0] || "none";
      if (seen.has(key) || !(w.tags || []).length) continue;
      seen.add(key);
      picks.push(w);
      if (picks.length >= 8) break;
    }
    $("soon-preview").innerHTML = picks.map((w) =>
      `<li><span class="w" lang="ja">${ruby(w.word, w.reading)}</span><span class="m">${esc(w.meaning)}</span>${chipsHtml(w.tags)}</li>`
    ).join("");
  }

  // ------------------------------------------------------------------
  // Ritmo semanal
  // ------------------------------------------------------------------

  function weekStart(ms) {
    const d = new Date(ms);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // lunes
    return d.getTime();
  }

  function addWeeks(ms, k) {
    const d = new Date(ms);
    d.setDate(d.getDate() + 7 * k);
    return d.getTime();
  }

  function weeklyStats(weeksBack) {
    const current = weekStart(Date.now());
    const starts = [];
    for (let k = weeksBack - 1; k >= 0; k--) starts.push(addWeeks(current, -k));
    const index = new Map(starts.map((s, i) => [s, i]));
    const fresh = new Array(weeksBack).fill(0);
    let maturedThisWeek = 0;
    let firstEver = null;
    model.words.forEach((w) => {
      if (w.first_review) {
        firstEver = firstEver === null ? w.first_review : Math.min(firstEver, w.first_review);
        const i = index.get(weekStart(w.first_review));
        if (i !== undefined) fresh[i] += 1;
      }
      if (w.matured && weekStart(w.matured) === current) maturedThisWeek += 1;
    });
    return { starts, fresh, maturedThisWeek, firstEver };
  }

  function niceMax(v) {
    if (v <= 5) return 5;
    const mag = Math.pow(10, Math.floor(Math.log10(v)));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * mag >= v) return m * mag;
    return 10 * mag;
  }

  function renderWeeks() {
    const box = $("week-chart");
    const W = 12;
    const s = weeklyStats(W);
    box.innerHTML = "";
    if (s.firstEver === null) {
      box.innerHTML = `<p class="chart-empty">${esc(t.chartEmpty)}</p>`;
    } else {
      drawWeekChart(box, s);
    }

    // Proyección: promedio de las últimas semanas completas
    const remaining = model.counts.new;
    let text;
    if (remaining === 0) {
      text = t.projDone;
    } else {
      text = t.projLeft(fmt(remaining));
      const complete = s.fresh.slice(0, -1);
      let k = Math.min(4, complete.length);
      if (s.firstEver !== null) {
        const weeksSinceStart = Math.floor((weekStart(Date.now()) - weekStart(s.firstEver)) / (7 * 864e5));
        k = Math.max(0, Math.min(k, weeksSinceStart));
      }
      const recent = k ? complete.slice(-k) : [];
      const rate = recent.length ? recent.reduce((a, b) => a + b, 0) / recent.length : 0;
      if (rate >= 1) text += t.projRate(k, fmt(Math.round(rate)), Math.ceil(remaining / rate));
    }
    if (s.firstEver !== null) text += t.projWeek(fmt(s.fresh[s.fresh.length - 1]), fmt(s.maturedThisWeek));
    $("projection").innerHTML = text;
  }

  function drawWeekChart(box, s) {
    const width = Math.max(260, box.clientWidth || 420);
    const height = 168;
    const m = { top: 20, right: 4, bottom: 24, left: 30 };
    const plotW = width - m.left - m.right;
    const plotH = height - m.top - m.bottom;
    const n = s.fresh.length;
    const band = plotW / n;
    const barW = Math.min(24, band * 0.62);
    const max = niceMax(Math.max(...s.fresh, 1));
    const y = (v) => m.top + plotH - (v / max) * plotH;
    const labelEvery = band < 34 ? 3 : 2;

    const parts = [];
    parts.push(`<g class="axis">`);
    [0, max / 2, max].forEach((v) => {
      parts.push(`<line x1="${m.left}" x2="${width - m.right}" y1="${y(v)}" y2="${y(v)}"></line>`);
      parts.push(`<text x="${m.left - 8}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`);
    });
    s.starts.forEach((start, i) => {
      const last = i === n - 1;
      if (!last && (n - 1 - i) % labelEvery !== 0) return;
      const cx = m.left + band * i + band / 2;
      const label = last ? t.thisWeek : fmtDate(start);
      parts.push(`<text x="${cx}" y="${height - 6}" text-anchor="${last ? "end" : "middle"}" ${last ? `dx="${barW / 2 + 2}"` : ""}>${esc(label)}</text>`);
    });
    parts.push(`</g>`);

    const peak = s.fresh.indexOf(Math.max(...s.fresh));
    s.fresh.forEach((v, i) => {
      const x = m.left + band * i + (band - barW) / 2;
      const top = y(v);
      const h = m.top + plotH - top;
      const cls = i === n - 1 ? "bar is-current" : "bar";
      parts.push(`<rect class="bar-hit" data-i="${i}" x="${m.left + band * i}" y="${m.top}" width="${band}" height="${plotH}"></rect>`);
      if (v > 0) {
        const r = Math.min(4, h, barW / 2);
        parts.push(`<path class="${cls}" data-bar="${i}" d="M${x},${top + h} V${top + r} Q${x},${top} ${x + r},${top} H${x + barW - r} Q${x + barW},${top} ${x + barW},${top + r} V${top + h} Z"></path>`);
      }
      if (v > 0 && (i === peak || i === n - 1)) {
        parts.push(`<text class="value" x="${x + barW / 2}" y="${top - 6}" text-anchor="middle">${fmt(v)}</text>`);
      }
    });

    box.innerHTML = `<svg viewBox="0 0 ${width} ${height}" height="${height}" role="img" aria-label="${esc(t.rhythmTitle)}">${parts.join("")}</svg><div class="tip" hidden></div>`;

    const tip = box.querySelector(".tip");
    box.querySelectorAll(".bar-hit").forEach((hit) => {
      hit.addEventListener("mouseenter", () => {
        const i = Number(hit.dataset.i);
        box.querySelectorAll(".bar").forEach((b) => b.classList.toggle("is-hover", b.dataset.bar === String(i)));
        tip.textContent = t.weekTip(fmt(s.fresh[i]), fmtDate(s.starts[i]));
        tip.hidden = false;
        const cx = m.left + band * i + band / 2;
        const left = Math.min(Math.max(0, cx - tip.offsetWidth / 2), width - tip.offsetWidth);
        tip.style.left = left + "px";
        tip.style.top = Math.max(0, y(s.fresh[i]) - 44) + "px";
      });
      hit.addEventListener("mouseleave", () => {
        tip.hidden = true;
        box.querySelectorAll(".bar").forEach((b) => b.classList.remove("is-hover"));
      });
    });
  }

  // ------------------------------------------------------------------
  // Listas de palabras
  // ------------------------------------------------------------------

  function renderLists() {
    const recent = model.words.filter((w) => w.status === "mature" && w.matured)
      .sort((a, b) => b.matured - a.matured).slice(0, 6);
    $("recent-list").innerHTML = recent.length
      ? recent.map((w) => `<li><span class="w" lang="ja">${ruby(w.word, w.reading)}</span><span class="m">${esc(w.meaning)}</span><span class="d">${fmtDate(w.matured)}</span></li>`).join("")
      : `<li class="list-empty">${esc(t.recentEmpty)}</li>`;

    const hard = model.words.filter((w) => w.lapses > 0 && w.status !== "suspended")
      .sort((a, b) => (b.leech - a.leech) || (b.lapses - a.lapses)).slice(0, 6);
    $("hard-list").innerHTML = hard.length
      ? hard.map((w) => `<li><span class="w" lang="ja">${ruby(w.word, w.reading)}</span><span class="m">${esc(w.meaning)}</span><span class="d">${t.lapses(fmt(w.lapses))}</span></li>`).join("")
      : `<li class="list-empty">${esc(t.hardEmpty)}</li>`;
  }

  // ------------------------------------------------------------------
  // Cómo se leyó el mazo
  // ------------------------------------------------------------------

  function renderSource() {
    const data = model.data;
    const rows = (data.fields || []).map((f) => `<tr>
        <td>${esc(f.notetype)}</td><td>${fmt(f.notes)}</td>
        <td>${f.word ? `<code>${esc(f.word)}</code>` : t.none}</td>
        <td>${f.reading ? `<code>${esc(f.reading)}</code>` : t.none}</td>
        <td>${f.meaning ? `<code>${esc(f.meaning)}</code>` : t.none}</td>
        <td>${esc(t.sourceKinds[f.source] || f.source || "")}</td></tr>`).join("");
    const head = t.sourceCols.map((c) => `<th scope="col">${esc(c)}</th>`).join("");
    let html = `<table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>`;
    if (data.skipped) html += `<p>${esc(t.skipped(fmt(data.skipped)))}</p>`;
    const cats = data.categories || {};
    if (cats.available) {
      if (cats.unmatched) html += `<p>${esc(t.sourceUnmatched(fmt(cats.unmatched)))}</p>`;
      html += `<p>${esc(t.sourceCats(cats.source || "JMdict"))}</p>`;
    }
    html += `<p>${esc(t.howToChange)}</p>`;
    if (data.generated_at) {
      html += `<p>${esc(t.updated(new Intl.DateTimeFormat(locale(), { hour: "numeric", minute: "2-digit" }).format(new Date(data.generated_at))))}</p>`;
    }
    $("source-body").innerHTML = html;
    $("source").hidden = false;
  }

  // ------------------------------------------------------------------
  // Entrada principal
  // ------------------------------------------------------------------

  function render(data) {
    lang = pickLanguage(data.language);
    t = I18N[lang];
    applyI18n();
    model = prepare(data);
    fillDeckSelect(data);

    $("page").setAttribute("aria-busy", "false");
    $("loading").hidden = true;
    $("refresh").disabled = false;
    ["hero", "progress", "deckmap", "cats", "lower", "empty", "source"].forEach((id) => { $(id).hidden = true; });

    if (!data.deck) {
      showEmpty(t.noDeckTitle, t.noDeckBody);
      return;
    }
    if (!model.total) {
      showEmpty(t.noWordsTitle, t.noWordsBody);
      renderSource();
      $("source").querySelector("details").open = true;
      return;
    }
    ["hero", "progress", "deckmap", "cats", "lower"].forEach((id) => { $(id).hidden = false; });
    renderHero();
    renderProgress();
    focusIndex = -1;
    setupGrid(activeTab === "progress");
    renderCategories();
    renderWeeks();
    renderLists();
    renderSoon();
    renderSource();
  }

  let resizeTimer = 0;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (!model || !model.total || activeTab !== "progress") return;
      drawGrid(1);
      renderWeeks();
    }, 80);
  }

  function init() {
    applyI18n();
    wireGrid();
    wireTabs();
    $("refresh").addEventListener("click", () => { setLoading(); send("adic:refresh"); });
    $("deck-select").addEventListener("change", (ev) => { setLoading(); send("adic:deck:" + ev.target.value); });
    window.addEventListener("resize", onResize);
    // Los datos los manda Python con AnkiDiccionario.render(...) cuando la página está lista
  }

  window.AnkiDiccionario = { render, setLoading };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

/* Diccionario japonés: pestaña Diccionario.
   Lista de todas las palabras con búsqueda (kanji, kana, rōmaji o significado),
   filtros (estado, categoría, JLPT, kanji compartido), orden y un botón que
   abre la tarjeta en el explorador de Anki.

   dashboard.js crea el diccionario con window.AdicDictionary(ctx) y le pasa
   sus herramientas compartidas (formato, furigana, textos, pestañas).

   Proyecto de Raul Juarez. */

(function () {
  "use strict";

  const PAGE = 100; // filas que se dibujan de golpe (el resto al bajar)

  const I18N = {
    es: {
      searchLabel: "Buscar",
      searchPlaceholder: "Busca por kanji, kana, rōmaji o significado: 学校, がっこう, gakkou, school",
      all: "Todas",
      progress: "En progreso",
      leech: "Difíciles",
      catLabel: "Categoría",
      catAll: "Todas las categorías",
      catNone: "Sin categoría",
      jlptLabel: "JLPT",
      jlptAll: "Todos los niveles",
      jlptNone: "Sin nivel",
      sortLabel: "Ordenar",
      sorts: {
        deck: "Orden del mazo", recent: "Recién aprendidas", lapses: "Más fallos",
        interval: "Intervalo más largo", kana: "Por lectura (あいうえお)",
      },
      relevance: "Más parecidas primero",
      count: (shown, total) => (shown === total ? `${total} palabras` : `${shown} de ${total} palabras`),
      kanjiFilter: (k) => `Con el kanji ${k}`,
      removeKanji: (k) => `Quitar el filtro del kanji ${k}`,
      clear: "Quitar filtros",
      more: (n) => `Mostrar más (${n} restantes)`,
      emptyTitle: "Ninguna palabra coincide",
      emptyBody: "Prueba con otra búsqueda o quita los filtros.",
      open: "Abrir en Anki",
      openTitle: "Abrir esta tarjeta en el explorador de Anki",
      opened: "Abierta en Anki",
      openOutside: "Solo funciona dentro de Anki",
      detailKanji: "Palabras con el mismo kanji",
      detailStats: "Repaso",
      matured: "Sabida desde",
      jlptBadge: (n) => `N${n}`,
      showDetail: "Ver detalle de",
    },
    en: {
      searchLabel: "Search",
      searchPlaceholder: "Search by kanji, kana, rōmaji or meaning: 学校, がっこう, gakkou, school",
      all: "All",
      progress: "In progress",
      leech: "Difficult",
      catLabel: "Category",
      catAll: "All categories",
      catNone: "Uncategorized",
      jlptLabel: "JLPT",
      jlptAll: "All levels",
      jlptNone: "No level",
      sortLabel: "Sort",
      sorts: {
        deck: "Deck order", recent: "Recently learned", lapses: "Most lapses",
        interval: "Longest interval", kana: "By reading (あいうえお)",
      },
      relevance: "Best matches first",
      count: (shown, total) => (shown === total ? `${total} words` : `${shown} of ${total} words`),
      kanjiFilter: (k) => `With the kanji ${k}`,
      removeKanji: (k) => `Remove the ${k} kanji filter`,
      clear: "Clear filters",
      more: (n) => `Show more (${n} left)`,
      emptyTitle: "No words match",
      emptyBody: "Try another search or clear the filters.",
      open: "Open in Anki",
      openTitle: "Open this card in Anki's browser",
      opened: "Opened in Anki",
      openOutside: "Only works inside Anki",
      detailKanji: "Words with the same kanji",
      detailStats: "Review",
      matured: "Known since",
      jlptBadge: (n) => `N${n}`,
      showDetail: "Show details for",
    },
  };

  // ------------------------------------------------------------------
  // Texto japonés: kana, kanji y rōmaji
  // ------------------------------------------------------------------

  const KANJI_RE = /[㐀-䶿一-鿿々]/g;
  const JAPANESE_RE = /[぀-ヿ㐀-䶿一-鿿]/;

  function toHiragana(text) {
    return String(text || "").replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60));
  }

  // Tabla de rōmaji (Hepburn + variantes comunes de teclado)
  const ROMAJI = (() => {
    const t = {};
    const rows = {
      "": "あいうえお", k: "かきくけこ", g: "がぎぐげご", s: "さしすせそ", z: "ざじずぜぞ",
      t: "たちつてと", d: "だぢづでど", n: "なにぬねの", h: "はひふへほ", b: "ばびぶべぼ",
      p: "ぱぴぷぺぽ", m: "まみむめも", r: "らりるれろ",
    };
    const vowels = "aiueo";
    Object.keys(rows).forEach((c) => [...rows[c]].forEach((k, i) => { t[c + vowels[i]] = k; }));
    Object.assign(t, {
      ya: "や", yu: "ゆ", yo: "よ", wa: "わ", wo: "を",
      shi: "し", chi: "ち", tsu: "つ", fu: "ふ", ji: "じ", dzu: "づ",
      sha: "しゃ", shu: "しゅ", sho: "しょ", she: "しぇ",
      cha: "ちゃ", chu: "ちゅ", cho: "ちょ", che: "ちぇ",
      ja: "じゃ", ju: "じゅ", jo: "じょ", je: "じぇ",
      fa: "ふぁ", fi: "ふぃ", fe: "ふぇ", fo: "ふぉ", ti: "てぃ", di: "でぃ",
      la: "ぁ", li: "ぃ", lu: "ぅ", le: "ぇ", lo: "ぉ", xa: "ぁ", xi: "ぃ", xu: "ぅ", xe: "ぇ", xo: "ぉ",
    });
    // Combinaciones con ya/yu/yo: kya, nya, ryo...
    const ySmall = { a: "ゃ", u: "ゅ", o: "ょ" };
    "kgnhbpmr".split("").forEach((c) => Object.keys(ySmall).forEach((v) => {
      t[c + "y" + v] = t[c + "i"] + ySmall[v];
    }));
    [["sy", "し"], ["zy", "じ"], ["jy", "じ"], ["ty", "ち"], ["cy", "ち"], ["dy", "ぢ"]].forEach(([p, k]) =>
      Object.keys(ySmall).forEach((v) => { t[p + v] = k + ySmall[v]; }));
    // Variantes Kunrei: si, zi, ti, tu, hu, zi
    Object.assign(t, { si: "し", zi: "じ", tu: "つ", hu: "ふ" });
    return t;
  })();

  // Vocal de cada kana, para leer "ー" (コーヒー -> こおひい)
  const VOWEL_OF = (() => {
    const map = {};
    Object.keys(ROMAJI).forEach((r) => {
      const kana = ROMAJI[r];
      const v = { a: "あ", i: "い", u: "う", e: "え", o: "お" }[r[r.length - 1]];
      if (v) map[kana[kana.length - 1]] = v;
    });
    return map;
  })();

  function expandLongVowels(kana) {
    let out = "";
    for (const c of kana) out += c === "ー" ? (VOWEL_OF[out[out.length - 1]] || "") : c;
    return out;
  }

  /** "gakkou" -> "がっこう"; null si no es rōmaji válido. */
  function romajiToKana(input) {
    const s = String(input || "").toLowerCase()
      .replace(/[āâ]/g, "aa").replace(/[īî]/g, "ii").replace(/[ūû]/g, "uu")
      .replace(/[ēê]/g, "ee").replace(/[ōô]/g, "ou").replace(/\s+/g, "");
    if (!s || !/^[a-z'-]+$/.test(s)) return null;
    const isVowel = (c) => !!c && c.length === 1 && "aiueo".includes(c);
    let out = "";
    let i = 0;
    while (i < s.length) {
      const c = s[i];
      const next = s[i + 1];
      if (c === "-") { out += "ー"; i += 1; continue; }
      if (c === "'") { i += 1; continue; }
      if (c === "n" && (next === undefined || next === "'" || (!isVowel(next) && next !== "y"))) {
        // ん: al final, antes de consonante, con apóstrofo o "nn"
        out += "ん";
        i += next === "'" || (next === "n" && !isVowel(s[i + 2]) && s[i + 2] !== "y") ? 2 : 1;
        continue;
      }
      // Consonante doble = っ (gakkou, matte, matcha)
      if (next && c === next && !isVowel(c) && c !== "n") { out += "っ"; i += 1; continue; }
      if (c === "t" && next === "c" && s[i + 2] === "h") { out += "っ"; i += 1; continue; }
      let matched = false;
      for (const len of [3, 2, 1]) {
        const chunk = s.slice(i, i + len);
        if (ROMAJI[chunk]) { out += ROMAJI[chunk]; i += len; matched = true; break; }
      }
      if (!matched) return null;
    }
    return out;
  }

  function escapeRegex(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // ------------------------------------------------------------------
  // Diccionario
  // ------------------------------------------------------------------

  window.AdicDictionary = function createDictionary(ctx) {
    const { $, esc, fmt, fmtDate, ruby, send } = ctx;
    let d = I18N.es;
    let words = [];
    let groupsMap = {};
    let kanjiCount = new Map();
    let filtered = [];
    let shown = 0;
    let observer = null;
    let searchTimer = 0;
    const state = { q: "", status: "all", cat: "", jlpt: "", kanji: "", sort: "deck" };
    const openRows = new Set();

    // ---------- preparación ----------

    function prepareWords(model) {
      const cats = model.data.categories || {};
      groupsMap = cats.groups || {};
      const tagToGroup = {};
      Object.keys(groupsMap).forEach((g) => groupsMap[g].forEach((tag) => { tagToGroup[tag] = g; }));
      kanjiCount = new Map();
      words = model.words.map((w, index) => {
        const kana = toHiragana(w.reading || w.word);
        const kanji = [...new Set((w.word.match(KANJI_RE) || []))];
        kanji.forEach((k) => kanjiCount.set(k, (kanjiCount.get(k) || 0) + 1));
        const groups = [];
        (w.tags || []).forEach((tag) => {
          const g = tagToGroup[tag];
          if (g && !groups.includes(g)) groups.push(g);
        });
        return Object.assign(w, {
          _index: index,
          _kana: kana,
          _kanaLoose: expandLongVowels(kana),
          _mean: (w.meaning || "").toLowerCase(),
          _kanji: kanji,
          _groups: groups,
        });
      });
    }

    // ---------- controles ----------

    function statusOptions() {
      const t = ctx.t();
      const count = (fn) => words.filter(fn).length;
      const opts = [
        ["all", d.all, words.length],
        ["mature", t.status.mature, count((w) => w.status === "mature")],
        ["progress", d.progress, count((w) => w.status === "young" || w.status === "learning")],
        ["new", t.status.new, count((w) => w.status === "new")],
        ["leech", d.leech, count((w) => w.leech)],
        ["suspended", t.status.suspended, count((w) => w.status === "suspended")],
      ];
      return opts.filter(([key, , n]) => key === "all" || key === "mature" || key === "progress" || key === "new" || n > 0);
    }

    function renderControls() {
      const t = ctx.t();
      $("dict-q").placeholder = d.searchPlaceholder;
      $("dict-q-label").textContent = d.searchLabel;
      $("dict-cat-label").textContent = d.catLabel;
      $("dict-jlpt-label").textContent = d.jlptLabel;
      $("dict-sort-label").textContent = d.sortLabel;
      $("dict-clear").textContent = d.clear;
      $("dict-empty-title").textContent = d.emptyTitle;
      $("dict-empty-body").textContent = d.emptyBody;
      $("dict-empty-clear").textContent = d.clear;

      $("dict-status").innerHTML = statusOptions().map(([key, label, n]) =>
        `<button type="button" data-status="${key}" aria-pressed="${state.status === key}">${esc(label)} <span class="n">${fmt(n)}</span></button>`
      ).join("");

      // Categorías con sus subtipos (verbos godan, ichidan...)
      const groupCount = (g) => words.filter((w) => (g === "none" ? !w._groups.length : w._groups.includes(g))).length;
      const tagCount = (tag) => words.filter((w) => (w.tags || []).includes(tag)).length;
      const opts = [`<option value="">${esc(d.catAll)}</option>`];
      Object.keys(groupsMap)
        .map((g) => [g, groupCount(g)])
        .filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1])
        .forEach(([g, n]) => {
          opts.push(`<option value="g:${g}">${esc((t.groups[g] || [g])[0])} (${fmt(n)})</option>`);
          (groupsMap[g] || []).filter((tag) => t.subs[tag]).forEach((tag) => {
            const c = tagCount(tag);
            if (c) opts.push(`<option value="t:${tag}"> ${esc(t.subs[tag])} (${fmt(c)})</option>`);
          });
        });
      const none = groupCount("none");
      if (none) opts.push(`<option value="g:none">${esc(d.catNone)} (${fmt(none)})</option>`);
      $("dict-cat").innerHTML = opts.join("");
      $("dict-cat").value = state.cat;

      const jl = [`<option value="">${esc(d.jlptAll)}</option>`];
      [5, 4, 3, 2, 1].forEach((n) => {
        const c = words.filter((w) => w.jlpt === n).length;
        if (c) jl.push(`<option value="${n}">N${n} (${fmt(c)})</option>`);
      });
      const noLevel = words.filter((w) => !w.jlpt).length;
      if (noLevel) jl.push(`<option value="none">${esc(d.jlptNone)} (${fmt(noLevel)})</option>`);
      $("dict-jlpt").innerHTML = jl.join("");
      $("dict-jlpt").value = state.jlpt;

      $("dict-sort").innerHTML = Object.keys(d.sorts).map((k) =>
        `<option value="${k}">${esc(k === "deck" && state.q ? d.relevance : d.sorts[k])}</option>`).join("");
      $("dict-sort").value = state.sort;
    }

    // ---------- filtrar y ordenar ----------

    function matchQuery(w, q) {
      if (JAPANESE_RE.test(q)) {
        const qk = toHiragana(q);
        return w.word.includes(q) || w._kana.includes(qk) || w._kanaLoose.includes(expandLongVowels(qk));
      }
      const lower = q.toLowerCase();
      if (new RegExp("(^|[^a-z])" + escapeRegex(lower)).test(w._mean)) return true;
      const kana = romajiToKana(lower);
      return !!kana && w._kanaLoose.includes(kana);
    }

    function relevance(w, q) {
      const qk = JAPANESE_RE.test(q) ? toHiragana(q) : romajiToKana(q.toLowerCase());
      if (w.word === q || (qk && (w._kana === qk || w._kanaLoose === qk))) return 0;
      if (w.word.startsWith(q) || (qk && w._kanaLoose.startsWith(qk))) return 1;
      const m = w._mean;
      const lq = q.toLowerCase();
      if (m === lq || m.startsWith(lq + ",") || m.startsWith(lq + ";") || m.startsWith("to " + lq)) return 1;
      return 2;
    }

    function applyFilters() {
      const q = state.q.trim();
      filtered = words.filter((w) => {
        if (state.status === "progress" && w.status !== "young" && w.status !== "learning") return false;
        if (state.status === "leech" && !w.leech) return false;
        if (["mature", "new", "suspended"].includes(state.status) && w.status !== state.status) return false;
        if (state.cat) {
          const [kind, value] = state.cat.split(":");
          if (kind === "g" && (value === "none" ? w._groups.length : !w._groups.includes(value))) return false;
          if (kind === "t" && !(w.tags || []).includes(value)) return false;
        }
        if (state.jlpt === "none" && w.jlpt) return false;
        if (state.jlpt && state.jlpt !== "none" && w.jlpt !== Number(state.jlpt)) return false;
        if (state.kanji && !w.word.includes(state.kanji)) return false;
        if (q && !matchQuery(w, q)) return false;
        return true;
      });

      const by = {
        deck: (a, b) => a._index - b._index,
        recent: (a, b) => (b.matured || 0) - (a.matured || 0) || (b.first_review || 0) - (a.first_review || 0) || a._index - b._index,
        lapses: (a, b) => b.lapses - a.lapses || a._index - b._index,
        interval: (a, b) => b.interval - a.interval || a._index - b._index,
        kana: (a, b) => a._kana.localeCompare(b._kana, "ja") || a._index - b._index,
      }[state.sort] || ((a, b) => a._index - b._index);
      if (q && state.sort === "deck") {
        const score = new Map(filtered.map((w) => [w, relevance(w, q)]));
        filtered.sort((a, b) => score.get(a) - score.get(b) || a._index - b._index);
      } else {
        filtered.sort(by);
      }
    }

    // ---------- dibujar ----------

    function statusLabel(w) {
      const t = ctx.t();
      const color = w.leech && w.status !== "suspended" ? "var(--st-leech)" : `var(${ctx.STATUS_VAR[w.status]})`;
      const text = t.statusOne[w.status] + (w.leech ? ", " + t.statusOne.leech : "");
      return `<span class="entry-status"><i class="swatch${w.status === "suspended" ? " is-suspended" : ""}" style="background:${color}"></i>${esc(text)}</span>`;
    }

    function rowHtml(w) {
      const isOpen = openRows.has(w.id);
      const chips = ctx.tagLabels(w.tags).map((l, i) => `<span class="chip${i === 0 ? " is-primary" : ""}">${esc(l)}</span>`).join("");
      const jlpt = w.jlpt ? `<span class="jlpt" title="JLPT N${w.jlpt}">${d.jlptBadge(w.jlpt)}</span>` : "";
      return `<li class="entry${isOpen ? " is-open" : ""}" data-id="${w.id}">
          <div class="entry-main">
            <button type="button" class="entry-word" lang="ja" aria-expanded="${isOpen}" aria-label="${esc(d.showDetail)} ${esc(w.word)}">${ruby(w.word, w.reading)}</button>
            <div class="entry-body">
              <p class="entry-meaning">${esc(w.meaning)}</p>
              <p class="entry-meta">${statusLabel(w)}${chips}${jlpt}</p>
            </div>
            <button type="button" class="entry-open" title="${esc(d.openTitle)}">
              <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M6.5 3.5H4A1.5 1.5 0 0 0 2.5 5v7A1.5 1.5 0 0 0 4 13.5h7a1.5 1.5 0 0 0 1.5-1.5V9.5M9 2.5h4.5V7M13.5 2.5 7.5 8.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>${esc(d.open)}</span>
            </button>
          </div>
          ${isOpen ? detailHtml(w) : ""}
        </li>`;
    }

    function detailHtml(w) {
      const t = ctx.t();
      const kanji = w._kanji.map((k) =>
        `<button type="button" class="kanji-btn" data-kanji="${esc(k)}" lang="ja" title="${esc(d.kanjiFilter(k))}"><span class="k">${esc(k)}</span><span class="n">${fmt(kanjiCount.get(k) || 0)}</span></button>`
      ).join("");
      const stats = [];
      if (w.status !== "new") {
        stats.push([t.tipInterval, t.days(w.interval)]);
        stats.push([t.tipReviews, fmt(w.reviews)]);
        stats.push([t.tipLapses, fmt(w.lapses)]);
        if (w.first_review) stats.push([t.tipFirst, fmtDate(w.first_review)]);
        if (w.matured) stats.push([d.matured, fmtDate(w.matured)]);
      } else {
        stats.push([t.status.new, "—"]);
      }
      return `<div class="entry-detail">
          ${kanji ? `<div class="detail-block"><h3>${esc(d.detailKanji)}</h3><div class="kanji-list">${kanji}</div></div>` : ""}
          <div class="detail-block"><h3>${esc(d.detailStats)}</h3><dl class="detail-stats">${stats.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl></div>
        </div>`;
    }

    function renderActive() {
      const box = $("dict-active");
      box.innerHTML = state.kanji
        ? `<span class="active-pill" lang="ja">${esc(d.kanjiFilter(state.kanji))}<button type="button" class="pill-x" id="dict-kanji-x" aria-label="${esc(d.removeKanji(state.kanji))}">×</button></span>`
        : "";
      const dirty = state.q || state.status !== "all" || state.cat || state.jlpt || state.kanji;
      $("dict-clear").hidden = !dirty;
    }

    function renderList() {
      applyFilters();
      renderActive();
      shown = 0;
      $("dict-count").textContent = d.count(fmt(filtered.length), fmt(words.length));
      $("dict-list").innerHTML = "";
      $("dict-empty").hidden = filtered.length > 0;
      appendRows();
    }

    function appendRows() {
      const next = filtered.slice(shown, shown + PAGE);
      $("dict-list").insertAdjacentHTML("beforeend", next.map(rowHtml).join(""));
      shown += next.length;
      const left = filtered.length - shown;
      const more = $("dict-more");
      more.hidden = left <= 0;
      more.textContent = left > 0 ? d.more(fmt(left)) : "";
    }

    // ---------- eventos ----------

    function wire() {
      $("dict-q").addEventListener("input", (ev) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
          state.q = ev.target.value;
          renderControlsLight();
          renderList();
        }, 120);
      });
      $("dict-status").addEventListener("click", (ev) => {
        const btn = ev.target.closest("button[data-status]");
        if (!btn) return;
        state.status = btn.dataset.status;
        $("dict-status").querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        renderList();
      });
      $("dict-cat").addEventListener("change", (ev) => { state.cat = ev.target.value; renderList(); });
      $("dict-jlpt").addEventListener("change", (ev) => { state.jlpt = ev.target.value; renderList(); });
      $("dict-sort").addEventListener("change", (ev) => { state.sort = ev.target.value; renderList(); });
      $("dict-more").addEventListener("click", appendRows);
      $("dict-clear").addEventListener("click", () => open({}));
      $("dict-empty-clear").addEventListener("click", () => open({}));
      $("dict-active").addEventListener("click", (ev) => {
        if (ev.target.closest("#dict-kanji-x")) { state.kanji = ""; renderList(); }
      });

      $("dict-list").addEventListener("click", (ev) => {
        const row = ev.target.closest(".entry");
        if (!row) return;
        const id = Number(row.dataset.id);
        const w = words.find((x) => x.id === id);
        if (!w) return;

        if (ev.target.closest(".entry-open")) {
          openInAnki(ev.target.closest(".entry-open"), id);
        } else if (ev.target.closest(".kanji-btn")) {
          const k = ev.target.closest(".kanji-btn").dataset.kanji;
          state.kanji = k;
          state.q = "";
          $("dict-q").value = "";
          renderControlsLight();
          renderList();
          window.scrollTo(0, 0);
        } else if (ev.target.closest(".entry-word")) {
          if (openRows.has(id)) openRows.delete(id); else openRows.add(id);
          const html = rowHtml(w);
          row.insertAdjacentHTML("afterend", html);
          row.remove();
          const fresh = $("dict-list").querySelector(`.entry[data-id="${id}"] .entry-word`);
          if (fresh) fresh.focus();
        }
      });

      // Cargar más filas al acercarse al final de la lista
      if ("IntersectionObserver" in window) {
        observer = new IntersectionObserver((entries) => {
          if (entries.some((e) => e.isIntersecting) && shown < filtered.length) appendRows();
        }, { rootMargin: "400px" });
        observer.observe($("dict-more"));
      }
    }

    function openInAnki(btn, id) {
      const label = btn.querySelector("span");
      const inside = typeof window.pycmd === "function";
      if (inside) send("adic:browse:" + id);
      label.textContent = inside ? d.opened : d.openOutside;
      btn.classList.add("is-done");
      setTimeout(() => {
        label.textContent = d.open;
        btn.classList.remove("is-done");
      }, 1800);
    }

    // El texto de "Orden del mazo" cambia a "Más parecidas primero" al buscar
    function renderControlsLight() {
      const opt = $("dict-sort").querySelector('option[value="deck"]');
      if (opt) opt.textContent = state.q.trim() ? d.relevance : d.sorts.deck;
    }

    // ---------- API para dashboard.js ----------

    function render(model) {
      d = I18N[ctx.lang()] || I18N.es;
      prepareWords(model);
      // Las filas abiertas que ya no existen se olvidan
      [...openRows].forEach((id) => { if (!words.some((w) => w.id === id)) openRows.delete(id); });
      renderControls();
      renderList();
    }

    /** Abre la pestaña con filtros nuevos, p. ej. {cat: "g:verb"} o {q: "完全"}. */
    function open(filters) {
      Object.assign(state, { q: "", status: "all", cat: "", jlpt: "", kanji: "", sort: "deck" }, filters || {});
      $("dict-q").value = state.q;
      renderControls();
      renderList();
      ctx.showTab("dictionary");
      window.scrollTo(0, 0);
    }

    wire();
    return { render, open, romajiToKana };
  };
})();

/* Diccionario japonés: pestaña Repasar.
   Práctica libre con tus palabras difíciles o en aprendizaje: eliges el grupo
   y cuántas, se escogen al azar, y marcas si la sabías. NO cambia nada en
   Anki (ni intervalos ni estadísticas): todo vive solo en esta ventana.

   dashboard.js lo crea con window.AdicReview(ctx).

   Proyecto de Raul Juarez. */

(function () {
  "use strict";

  const I18N = {
    es: {
      setupTitle: "Repaso rápido",
      setupBody: "Practica aquí mismo con palabras al azar. Es solo práctica: no cambia tus intervalos ni tus estadísticas de Anki.",
      groupLabel: "Qué quieres repasar",
      groups: {
        hard: ["Te cuestan trabajo", ""],
        learning: ["Estás aprendiendo", "Palabras en aprendizaje o todavía jóvenes."],
      },
      hardDesc: (min, leech) => (min === "leech"
        ? `Marcadas como difíciles: ${leech} fallos o más.`
        : min === 1 ? "Palabras que has fallado al menos una vez." : `Palabras que has fallado ${min} veces o más.`),
      minLabel: "A partir de cuántos fallos",
      minN: (n) => `${n} o más`,
      minLeech: (leech) => `Difíciles (${leech} o más)`,
      available: (n) => (n === 1 ? "1 palabra" : `${n} palabras`),
      emptyGroup: "Todavía no tienes palabras aquí.",
      amountLabel: "Cuántas palabras",
      all: (n) => `Todas (${n})`,
      other: "Otra cantidad",
      start: (n) => `Empezar con ${n} ${n === 1 ? "palabra" : "palabras"}`,
      startEmpty: "Elige un grupo con palabras",
      progress: (i, n) => `Palabra ${i} de ${n}`,
      score: (ok, bad) => `${ok} sabías, ${bad} no`,
      show: "Mostrar respuesta",
      knew: "La sabía",
      didnt: "No la sabía",
      finish: "Terminar",
      keysFront: "Espacio para voltear",
      keysBack: "1 = no la sabía, 2 = la sabía",
      lapsesInAnki: (n) => `${n} ${n === 1 ? "fallo" : "fallos"} en Anki`,
      resultTitle: (ok, n) => `Sabías ${ok} de ${n}`,
      resultPerfect: "Las recordaste todas.",
      resultBody: "Repasa las que fallaste o ábrelas en Anki para ver la tarjeta completa.",
      missedTitle: "Las que no sabías",
      retryMissed: (n) => `Repasar las ${n} que fallé`,
      again: "Nuevo repaso",
      open: "Abrir en Anki",
      openTitle: "Abrir esta tarjeta en el explorador de Anki",
      opened: "Abierta en Anki",
      openOutside: "Solo funciona dentro de Anki",
    },
    en: {
      setupTitle: "Quick review",
      setupBody: "Practice right here with random words. It's practice only: it doesn't change your intervals or your Anki statistics.",
      groupLabel: "What to review",
      groups: {
        hard: ["Giving you trouble", ""],
        learning: ["Still learning", "Words in learning or still young."],
      },
      hardDesc: (min, leech) => (min === "leech"
        ? `Marked as difficult: ${leech}+ lapses.`
        : min === 1 ? "Words you've failed at least once." : `Words you've failed ${min} times or more.`),
      minLabel: "Minimum lapses",
      minN: (n) => `${n}+`,
      minLeech: (leech) => `Difficult (${leech}+)`,
      available: (n) => (n === 1 ? "1 word" : `${n} words`),
      emptyGroup: "No words here yet.",
      amountLabel: "How many words",
      all: (n) => `All (${n})`,
      other: "Other amount",
      start: (n) => `Start with ${n} ${n === 1 ? "word" : "words"}`,
      startEmpty: "Pick a group that has words",
      progress: (i, n) => `Word ${i} of ${n}`,
      score: (ok, bad) => `${ok} known, ${bad} not`,
      show: "Show answer",
      knew: "I knew it",
      didnt: "I didn't",
      finish: "Finish",
      keysFront: "Space to flip",
      keysBack: "1 = didn't know, 2 = knew it",
      lapsesInAnki: (n) => `${n} ${n === 1 ? "lapse" : "lapses"} in Anki`,
      resultTitle: (ok, n) => `You knew ${ok} of ${n}`,
      resultPerfect: "You remembered them all.",
      resultBody: "Review the ones you missed or open them in Anki to see the full card.",
      missedTitle: "The ones you didn't know",
      retryMissed: (n) => `Review the ${n} I missed`,
      again: "New review",
      open: "Open in Anki",
      openTitle: "Open this card in Anki's browser",
      opened: "Opened in Anki",
      openOutside: "Only works inside Anki",
    },
  };

  const AMOUNTS = [10, 20, 50];

  // Fisher-Yates: mezcla justa
  function shuffle(list) {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  window.AdicReview = function createReview(ctx) {
    const { $, esc, fmt, send } = ctx;
    let r = I18N.es;
    let words = [];
    // minLapses: 1, 2, 3, 5 o "leech" (las "Difíciles"); null = elegir solo
    const setup = { group: "hard", amount: 20, custom: "", minLapses: null };
    let leechLapses = 8;
    // Sesión en curso: solo vive en memoria, nunca se manda a Anki
    let session = null; // { cards, index, revealed, results: [{w, knew}] }

    // ---------- grupos ----------

    // Palabras con al menos `min` fallos ("leech" = las marcadas como difíciles)
    function hardPool(min) {
      return words.filter((w) => w.status !== "suspended" &&
        (min === "leech" ? w.leech : w.lapses >= min || w.leech));
    }

    function minOptions() {
      const nums = [1, 2, 3, 5].filter((n) => n < leechLapses);
      return nums.map((n) => [n, r.minN(n), hardPool(n).length])
        .concat([["leech", r.minLeech(leechLapses), hardPool("leech").length]]);
    }

    // Por defecto: las "Difíciles" si hay; si no, desde 1 fallo
    function currentMin() {
      const opts = minOptions();
      const chosen = opts.find(([key]) => key === setup.minLapses);
      if (chosen && chosen[2] > 0) return chosen[0];
      const leech = opts.find(([key]) => key === "leech");
      return leech && leech[2] > 0 ? "leech" : 1;
    }

    function pool(group) {
      if (group === "hard") return hardPool(currentMin());
      return words.filter((w) => w.status === "learning" || w.status === "young");
    }

    function chosenAmount(available) {
      if (setup.amount === "all") return available;
      if (setup.amount === "custom") {
        const n = parseInt(setup.custom, 10);
        return Number.isFinite(n) && n > 0 ? Math.min(n, available) : 0;
      }
      return Math.min(setup.amount, available);
    }

    // ---------- pantallas ----------

    function show(screen) {
      ["review-setup", "review-session", "review-result"].forEach((id) => { $(id).hidden = id !== screen; });
    }

    function renderSetup() {
      show("review-setup");
      $("review-setup-title").textContent = r.setupTitle;
      $("review-setup-body").textContent = r.setupBody;
      $("review-group-label").textContent = r.groupLabel;
      $("review-amount-label").textContent = r.amountLabel;

      // Si el grupo elegido está vacío, saltamos al otro
      if (!pool(setup.group).length && pool(setup.group === "hard" ? "learning" : "hard").length) {
        setup.group = setup.group === "hard" ? "learning" : "hard";
      }

      const min = currentMin();
      $("review-groups").innerHTML = ["hard", "learning"].map((g) => {
        const n = pool(g).length;
        const [title, fixedDesc] = r.groups[g];
        const desc = g === "hard" ? r.hardDesc(min, leechLapses) : fixedDesc;
        return `<button type="button" class="review-group" data-group="${g}" aria-pressed="${setup.group === g}"${n ? "" : " disabled"}>
            <span class="rg-title">${esc(title)}</span>
            <span class="rg-desc">${esc(desc)}</span>
            <span class="rg-count">${n ? esc(r.available(fmt(n))) : esc(r.emptyGroup)}</span>
          </button>`;
      }).join("");

      // A partir de cuántos fallos (solo para "Te cuestan trabajo")
      $("review-min-block").hidden = setup.group !== "hard";
      $("review-min-label").textContent = r.minLabel;
      $("review-mins").innerHTML = minOptions().map(([key, label, n]) =>
        `<button type="button" data-min="${key}" aria-pressed="${key === min}"${n ? "" : " disabled"}>${esc(label)} <span class="n">${fmt(n)}</span></button>`
      ).join("");

      const available = pool(setup.group).length;
      const chips = AMOUNTS.filter((n) => n < available).map((n) =>
        `<button type="button" data-amount="${n}" aria-pressed="${setup.amount === n}">${n}</button>`);
      chips.push(`<button type="button" data-amount="all" aria-pressed="${setup.amount === "all" || (typeof setup.amount === "number" && setup.amount >= available)}">${esc(r.all(fmt(available)))}</button>`);
      chips.push(`<button type="button" data-amount="custom" aria-pressed="${setup.amount === "custom"}">${esc(r.other)}</button>`);
      $("review-amounts").innerHTML = chips.join("");
      $("review-custom").hidden = setup.amount !== "custom";
      $("review-custom").max = String(available || 1);
      $("review-custom").value = setup.custom;

      updateStart();
    }

    function updateStart() {
      const n = chosenAmount(pool(setup.group).length);
      $("review-start").disabled = n === 0;
      $("review-start").textContent = n ? r.start(n) : r.startEmpty;
    }

    function startSession(cards) {
      session = { cards, index: 0, revealed: false, results: [] };
      renderCard();
      const btn = $("review-reveal");
      if (btn) btn.focus();
    }

    function renderCard() {
      show("review-session");
      const s = session;
      const w = s.cards[s.index];
      const ok = s.results.filter((x) => x.knew).length;
      $("review-progress-text").textContent = r.progress(s.index + 1, s.cards.length);
      $("review-score").textContent = r.score(ok, s.results.length - ok);
      $("review-bar").style.width = `${(s.index / s.cards.length) * 100}%`;
      $("review-finish").textContent = r.finish;

      // La furigana se dibuja siempre pero oculta, para que la palabra no brinque al voltear
      $("review-word").innerHTML = ctx.ruby(w.word, w.reading);
      $("review-card").classList.toggle("is-revealed", s.revealed);

      const chips = ctx.tagLabels(w.tags).slice(0, 3).map((l, i) =>
        `<span class="chip${i === 0 ? " is-primary" : ""}">${esc(l)}</span>`).join("");
      const jlpt = w.jlpt ? `<span class="jlpt">N${w.jlpt}</span>` : "";
      const lapses = w.lapses ? `<span class="review-lapses">${esc(r.lapsesInAnki(w.lapses))}</span>` : "";
      $("review-answer").innerHTML = s.revealed
        ? `<p class="review-meaning">${esc(w.meaning)}</p>
           <p class="review-meta">${chips}${jlpt}${lapses}</p>`
        : "";
      $("review-answer").hidden = !s.revealed;

      $("review-actions").innerHTML = s.revealed
        ? `<button type="button" class="review-btn is-miss" id="review-didnt">${esc(r.didnt)} <kbd>1</kbd></button>
           <button type="button" class="review-btn is-hit" id="review-knew">${esc(r.knew)} <kbd>2</kbd></button>`
        : `<button type="button" class="review-btn is-main" id="review-reveal">${esc(r.show)} <kbd>␣</kbd></button>`;
      $("review-keys").textContent = s.revealed ? r.keysBack : r.keysFront;
    }

    function reveal() {
      if (!session || session.revealed) return;
      session.revealed = true;
      renderCard();
      $("review-knew").focus();
    }

    function grade(knew) {
      if (!session || !session.revealed) return;
      session.results.push({ w: session.cards[session.index], knew });
      session.index += 1;
      session.revealed = false;
      if (session.index >= session.cards.length) {
        renderResult();
      } else {
        renderCard();
        $("review-reveal").focus();
      }
    }

    function renderResult() {
      show("review-result");
      const s = session;
      const n = s.results.length;
      const ok = s.results.filter((x) => x.knew).length;
      const missed = s.results.filter((x) => !x.knew).map((x) => x.w);
      $("review-result-title").textContent = r.resultTitle(fmt(ok), fmt(n));
      $("review-result-body").textContent = missed.length ? r.resultBody : r.resultPerfect;
      $("review-result-bar").innerHTML = n
        ? `<span style="flex:${ok};background:var(--st-young)"></span><span style="flex:${n - ok};background:var(--st-leech)"></span>`
        : "";
      $("review-missed-title").textContent = r.missedTitle;
      $("review-missed-title").hidden = !missed.length;
      $("review-missed").innerHTML = missed.map((w) =>
        `<li data-id="${w.id}">
           <span class="w" lang="ja">${ctx.ruby(w.word, w.reading)}</span>
           <span class="m">${esc(w.meaning)}</span>
           <button type="button" class="entry-open review-open" title="${esc(r.openTitle)}">
             <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M6.5 3.5H4A1.5 1.5 0 0 0 2.5 5v7A1.5 1.5 0 0 0 4 13.5h7a1.5 1.5 0 0 0 1.5-1.5V9.5M9 2.5h4.5V7M13.5 2.5 7.5 8.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
             <span>${esc(r.open)}</span>
           </button>
         </li>`).join("");
      $("review-retry").hidden = !missed.length;
      $("review-retry").textContent = r.retryMissed(fmt(missed.length));
      $("review-again").textContent = r.again;
      session.missed = missed;
      $(missed.length ? "review-retry" : "review-again").focus();
    }

    // ---------- eventos ----------

    function wire() {
      $("review-groups").addEventListener("click", (ev) => {
        const btn = ev.target.closest("button[data-group]");
        if (!btn || btn.disabled) return;
        setup.group = btn.dataset.group;
        renderSetup();
      });
      $("review-mins").addEventListener("click", (ev) => {
        const btn = ev.target.closest("button[data-min]");
        if (!btn || btn.disabled) return;
        setup.minLapses = btn.dataset.min === "leech" ? "leech" : Number(btn.dataset.min);
        renderSetup();
      });
      $("review-amounts").addEventListener("click", (ev) => {
        const btn = ev.target.closest("button[data-amount]");
        if (!btn) return;
        const v = btn.dataset.amount;
        setup.amount = v === "all" || v === "custom" ? v : Number(v);
        renderSetup();
        if (v === "custom") $("review-custom").focus();
      });
      $("review-custom").addEventListener("input", (ev) => { setup.custom = ev.target.value; updateStart(); });
      $("review-start").addEventListener("click", () => {
        const list = pool(setup.group);
        const n = chosenAmount(list.length);
        if (n) startSession(shuffle(list).slice(0, n));
      });
      $("review-actions").addEventListener("click", (ev) => {
        if (ev.target.closest("#review-reveal")) reveal();
        else if (ev.target.closest("#review-knew")) grade(true);
        else if (ev.target.closest("#review-didnt")) grade(false);
      });
      $("review-finish").addEventListener("click", () => {
        if (session && session.results.length) renderResult();
        else { session = null; renderSetup(); }
      });
      $("review-retry").addEventListener("click", () => {
        if (session && session.missed && session.missed.length) startSession(shuffle(session.missed));
      });
      $("review-again").addEventListener("click", () => { session = null; renderSetup(); });
      $("review-missed").addEventListener("click", (ev) => {
        const btn = ev.target.closest(".review-open");
        if (!btn) return;
        const id = Number(btn.closest("li").dataset.id);
        const label = btn.querySelector("span");
        const inside = typeof window.pycmd === "function";
        if (inside) send("adic:browse:" + id);
        label.textContent = inside ? r.opened : r.openOutside;
        btn.classList.add("is-done");
        setTimeout(() => { label.textContent = r.open; btn.classList.remove("is-done"); }, 1800);
      });

      // Atajos: Espacio/Enter voltea; 1 o ← = no la sabía; 2 o → = la sabía
      document.addEventListener("keydown", (ev) => {
        if (!ctx.isActive() || !session || $("review-session").hidden) return;
        if (ev.target.closest && ev.target.closest("input, select, textarea")) return;
        if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
        if (!session.revealed && (ev.key === " " || ev.key === "Enter")) {
          ev.preventDefault();
          reveal();
        } else if (session.revealed && (ev.key === "1" || ev.key === "ArrowLeft")) {
          ev.preventDefault();
          grade(false);
        } else if (session.revealed && (ev.key === "2" || ev.key === "ArrowRight")) {
          ev.preventDefault();
          grade(true);
        }
      });
    }

    // ---------- API para dashboard.js ----------

    function render(model) {
      r = I18N[ctx.lang()] || I18N.es;
      words = model.words;
      leechLapses = Number((model.data.settings || {}).leech_lapses) || 8;
      // Si hay un repaso a la mitad, no lo interrumpimos al pulsar Actualizar
      if (!session) renderSetup();
    }

    /** Abre la pestaña con un grupo ya elegido ("hard" o "learning"). */
    function open(group) {
      if (group) setup.group = group;
      session = null;
      renderSetup();
      ctx.showTab("review");
    }

    wire();
    return { render, open, shuffle };
  };
})();

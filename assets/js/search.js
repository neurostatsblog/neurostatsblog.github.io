// Pagefind-backed search for the /search/ page.
//
// Reads ?q= on load, runs queries on input (debounced), and keeps the URL
// in sync so each query is bookmarkable. Pagefind's index lives at
// /pagefind/pagefind.js — built by the CI workflow after `jekyll build`.
(function () {
  const input  = document.getElementById("search-input");
  const status = document.getElementById("search-status");
  const list   = document.getElementById("search-results");
  const form   = document.getElementById("search-form");
  if (!input || !status || !list || !form) return;

  // Don't reload the page when the user hits Enter — the input listener
  // already keeps results live and the URL in sync.
  form.addEventListener("submit", (e) => e.preventDefault());

  let pagefindPromise = null;
  function loadPagefind() {
    if (!pagefindPromise) {
      // The form carries the baseurl-aware path to pagefind.js, set by Liquid.
      // Resolve it against the page URL so dynamic import gets an absolute URL
      // (relative module specifiers aren't allowed in dynamic import).
      const path = form.dataset.pagefindUrl || "/pagefind/pagefind.js";
      const url = new URL(path, window.location.href).href;
      pagefindPromise = import(url).then(async (pf) => {
        await pf.options({ excerptLength: 30 });
        return pf;
      });
    }
    return pagefindPromise;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderResults(query, results) {
    if (!query) {
      status.textContent = "";
      list.innerHTML = "";
      return;
    }
    if (results.length === 0) {
      status.textContent = `No results for "${query}".`;
      list.innerHTML = "";
      return;
    }
    status.textContent = `${results.length} result${results.length === 1 ? "" : "s"} for "${query}".`;
    list.innerHTML = results
      .map((r) => {
        const title = escapeHtml(r.meta?.title || "(untitled)");
        const date  = r.meta?.date ? escapeHtml(r.meta.date) : "";
        // r.excerpt is HTML from Pagefind with <mark> highlights around the matches.
        return `
          <li class="post-item">
            <article>
              <div class="post-meta">
                ${date ? `<time class="post-date">${date}</time>` : ""}
              </div>
              <h2 class="post-title">
                <a href="${escapeHtml(r.url)}">${title}</a>
              </h2>
              <p class="post-excerpt">${r.excerpt}</p>
            </article>
          </li>`;
      })
      .join("");
  }

  async function runSearch(query) {
    if (!query) {
      renderResults("", []);
      return;
    }
    status.textContent = "Searching…";
    try {
      const pf = await loadPagefind();
      const search = await pf.search(query);
      const top = search.results.slice(0, 20);
      const data = await Promise.all(top.map((r) => r.data()));
      // The user may have typed more characters by the time results land.
      if (input.value.trim() !== query) return;
      renderResults(query, data);
    } catch (err) {
      console.error(err);
      status.textContent = "Search index unavailable.";
      list.innerHTML = "";
    }
  }

  let debounceTimer = null;
  function scheduleSearch(query) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runSearch(query), 150);
  }

  input.addEventListener("input", () => {
    const q = input.value.trim();
    const url = new URL(window.location);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState(null, "", url);
    scheduleSearch(q);
  });

  // Initial query from the URL (?q=...).
  const initial = new URLSearchParams(window.location.search).get("q") || "";
  if (initial) {
    input.value = initial;
    runSearch(initial);
  }
  input.focus();
})();

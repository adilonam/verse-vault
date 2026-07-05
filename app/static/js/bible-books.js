(() => {
  const searchInput = document.querySelector(".bible-toolbar .search-input");
  const grid = document.querySelector(".book-grid");
  const emptyEl = document.querySelector(".book-grid__empty");
  const previewEl = document.getElementById("bible-preview");
  const labelEl = document.getElementById("bible-preview-label");
  const bodyEl = document.getElementById("bible-preview-body");
  const notesEl = document.getElementById("bible-preview-notes");
  const notesTextEl = document.getElementById("bible-preview-notes-text");
  const continueEl = document.getElementById("bible-preview-continue");
  const booksJsonEl = document.getElementById("bible-search-books");

  if (!searchInput || !grid || !previewEl || !labelEl || !bodyEl) return;

  const cards = grid.querySelectorAll(".book-card");
  const versionAbbr = previewEl.dataset.versionAbbr || "KJV";
  let allBooks = [];

  try {
    allBooks = JSON.parse(booksJsonEl?.textContent || "[]");
  } catch {
    allBooks = [];
  }

  const booksByNameLength = [...allBooks].sort(
    (a, b) => b.name.length - a.name.length,
  );

  let fetchToken = 0;

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function parsePassageQuery(raw) {
    const trimmed = raw.trim();
    if (!trimmed) return null;

    const lower = trimmed.toLowerCase();
    let matched = null;
    let rest = "";

    for (const book of booksByNameLength) {
      const nameLower = book.name.toLowerCase();
      if (lower === nameLower || lower.startsWith(`${nameLower} `)) {
        matched = book;
        rest = trimmed.slice(book.name.length).trim();
        break;
      }
    }

    if (!matched) return null;

    const passageMatch = rest.match(/^(\d+)(?::(\d+))?(?:\b|$)/);
    if (!passageMatch) {
      return { ...matched, chapter: null, verse: null };
    }

    return {
      ...matched,
      chapter: Number.parseInt(passageMatch[1], 10),
      verse: passageMatch[2] ? Number.parseInt(passageMatch[2], 10) : null,
    };
  }

  function bookNameFromQuery(raw) {
    const parsed = parsePassageQuery(raw);
    if (parsed) return parsed.name;
    const trimmed = raw.trim();
    if (!trimmed) return "";
    return trimmed.replace(/\s+\d+(?::\d+)?(?:-\d+(?::\d+)?)?\s*$/, "").trim();
  }

  function hidePreview() {
    previewEl.hidden = true;
    notesEl.hidden = true;
    if (continueEl) continueEl.hidden = true;
    bodyEl.classList.remove("bible-preview__body--hint");
  }

  function showChapterPreview(parsed) {
    previewEl.hidden = false;
    notesEl.hidden = true;
    if (continueEl) continueEl.hidden = true;
    labelEl.textContent = `${parsed.name.toUpperCase()} · CHAPTER ${parsed.chapter}`;
    bodyEl.classList.add("bible-preview__body--hint");

    const exampleRef = `${parsed.name} ${parsed.chapter}:1`;
    const href = `/continue?book=${parsed.id}&chapter=${parsed.chapter}&verse=1`;
    bodyEl.innerHTML = `Add a verse number to look up a specific verse — e.g. <a href="${href}" class="bible-preview__example">${escapeHtml(exampleRef)}</a>`;
  }

  async function showVersePreview(parsed) {
    previewEl.hidden = false;
    labelEl.textContent = `${parsed.name.toUpperCase()} ${parsed.chapter}:${parsed.verse} · ${versionAbbr}`;
    bodyEl.classList.remove("bible-preview__body--hint");
    bodyEl.textContent = "Loading…";
    notesEl.hidden = true;
    if (continueEl) {
      continueEl.href = `/continue?book=${parsed.id}&chapter=${parsed.chapter}&verse=${parsed.verse}`;
      continueEl.hidden = false;
    }

    const token = ++fetchToken;
    const params = new URLSearchParams({
      book: String(parsed.id),
      chapter: String(parsed.chapter),
      verse: String(parsed.verse),
    });

    try {
      const [verseRes, noteRes] = await Promise.all([
        fetch(`/api/bible/verse?${params}`),
        fetch(`/api/notes/passage?${params}`),
      ]);

      if (token !== fetchToken) return;

      if (verseRes.ok) {
        const data = await verseRes.json();
        bodyEl.textContent = data.text;
      } else {
        bodyEl.textContent = "Verse not found.";
      }

      notesEl.hidden = false;
      if (noteRes.ok) {
        const note = await noteRes.json();
        if (note && note.id) {
          notesTextEl.innerHTML = `<a href="/notes/${note.id}">View note on this verse</a>`;
        } else {
          notesTextEl.textContent = "No notes taken on this verse yet";
        }
      } else {
        notesTextEl.textContent = "No notes taken on this verse yet";
      }
    } catch {
      if (token !== fetchToken) return;
      bodyEl.textContent = "Could not load verse.";
      notesEl.hidden = true;
    }
  }

  async function updatePreview() {
    const parsed = parsePassageQuery(searchInput.value);
    if (!parsed || !parsed.chapter) {
      hidePreview();
      return;
    }

    if (parsed.verse) {
      await showVersePreview(parsed);
      return;
    }

    showChapterPreview(parsed);
  }

  function filterBooks() {
    const query = bookNameFromQuery(searchInput.value).toLowerCase();
    let visible = 0;

    cards.forEach((card) => {
      const name = (card.dataset.bookName || "").toLowerCase();
      const match = !query || name.includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });

    if (emptyEl) {
      emptyEl.hidden = visible > 0 || !query;
    }
  }

  async function onSearchInput() {
    filterBooks();
    await updatePreview();
  }

  searchInput.addEventListener("input", () => {
    void onSearchInput();
  });
})();

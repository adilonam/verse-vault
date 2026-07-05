(() => {
  const list = document.querySelector(".notes-list");
  const countEl = document.querySelector(".notes-count");
  const searchInput = document.querySelector(".notes-toolbar .search-input");
  const emptyEl = document.querySelector(".notes-list__empty");
  if (!list) return;

  function updateCount(visible) {
    if (!countEl) return;
    const remaining =
      visible ?? list.querySelectorAll(".note-card:not([hidden])").length;
    countEl.textContent = `${remaining} note${remaining === 1 ? "" : "s"}`;
  }

  function filterNotes() {
    const query = (searchInput?.value || "").trim().toLowerCase();
    let visible = 0;

    list.querySelectorAll(".note-card").forEach((card) => {
      const text = (
        card.querySelector(".note-card__body")?.textContent || ""
      ).toLowerCase();
      const match = !query || text.includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });

    if (emptyEl) {
      emptyEl.hidden = visible > 0 || !query;
    }

    updateCount(visible);
  }

  if (searchInput) {
    searchInput.addEventListener("input", filterNotes);
  }

  list.addEventListener("click", async (event) => {
    const button = event.target.closest(".note-card__delete-btn");
    if (!button) return;

    const noteId = button.dataset.noteId;
    const title = button.dataset.noteTitle || "this note";
    if (!noteId) return;

    if (!(await window.confirmDelete(`Delete "${title}"?`))) return;

    button.disabled = true;

    try {
      const response = await fetch(`/api/notes/${noteId}`, { method: "DELETE" });
      if (!response.ok) {
        button.disabled = false;
        return;
      }
      button.closest(".note-card")?.remove();
      filterNotes();
    } catch {
      button.disabled = false;
    }
  });
})();

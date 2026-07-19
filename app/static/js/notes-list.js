(() => {
  const list = document.querySelector(".notes-list");
  const countEl = document.querySelector(".notes-count");
  const searchInput = document.querySelector(".notes-toolbar .search-input");
  const emptyEl = document.querySelector(".notes-list__empty");
  const importBtn = document.getElementById("notes-import-btn");
  const importFile = document.getElementById("notes-import-file");
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

  if (importBtn && importFile) {
    importBtn.addEventListener("click", () => {
      importFile.click();
    });

    importFile.addEventListener("change", async () => {
      const file = importFile.files?.[0];
      importFile.value = "";
      if (!file) return;

      importBtn.disabled = true;
      try {
        const body = new FormData();
        body.append("file", file);
        const response = await fetch("/api/notes/import", {
          method: "POST",
          body,
        });
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          const message =
            detail?.detail || "Import failed. Check the CSV and try again.";
          window.alert(typeof message === "string" ? message : "Import failed.");
          return;
        }
        const result = await response.json();
        const parts = [`Added ${result.added}`, `skipped ${result.skipped}`];
        if (result.errors) parts.push(`errors ${result.errors}`);
        window.alert(`Import complete: ${parts.join(", ")}.`);
        if (result.added > 0) {
          window.location.reload();
        }
      } catch {
        window.alert("Import failed. Check the CSV and try again.");
      } finally {
        importBtn.disabled = false;
      }
    });
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

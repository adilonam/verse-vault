(() => {
  const list = document.querySelector(".collections-list");
  const countEl = document.querySelector(".collections-count");
  const searchInput = document.querySelector(".collections-toolbar .search-input");
  const emptyEl = document.querySelector(".collections-list__empty");
  if (!list) return;

  function updateCount() {
    if (!countEl) return;
    const remaining = list.querySelectorAll(".collection-card:not([hidden])").length;
    countEl.textContent = `${remaining} collection${remaining === 1 ? "" : "s"}`;
  }

  function filterCollections() {
    if (!searchInput) return;
    const query = searchInput.value.trim().toLowerCase();
    let visible = 0;

    list.querySelectorAll(".collection-card").forEach((card) => {
      const text = card.textContent.toLowerCase();
      const match = !query || text.includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });

    if (emptyEl) {
      emptyEl.hidden = visible > 0 || !query;
    }

    updateCount();
  }

  if (searchInput) {
    searchInput.addEventListener("input", filterCollections);
  }

  list.addEventListener("click", async (event) => {
    const button = event.target.closest(".collection-card__delete-btn");
    if (!button) return;

    const collectionId = button.dataset.collectionId;
    const name = button.dataset.collectionName || "this collection";
    if (!collectionId) return;

    if (!(await window.confirmDelete(`Delete "${name}"?`))) return;

    button.disabled = true;

    try {
      const response = await fetch(`/api/collections/${collectionId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        button.disabled = false;
        return;
      }
      button.closest(".collection-card")?.remove();
      filterCollections();
    } catch {
      button.disabled = false;
    }
  });
})();

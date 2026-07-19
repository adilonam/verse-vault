(() => {
  let modal = null;
  let listEl = null;
  let cancelBtn = null;
  let loading = false;

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.removeEventListener("keydown", onKeydown);
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeModal();
    }
  }

  function ensureModal() {
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "confirm-modal settings-modal";
    modal.id = "bible-version-modal";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="confirm-modal__backdrop" data-settings-dismiss></div>
      <div
        class="confirm-modal__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="bible-version-title"
      >
        <header class="confirm-modal__header">
          <h2 class="confirm-modal__title" id="bible-version-title">Bible version</h2>
        </header>
        <p class="confirm-modal__message">
          Choose which translation to read. Notes and progress stay on the same verses.
        </p>
        <div class="settings-modal__list thin-scrollbar" id="bible-version-list" role="listbox" aria-label="Bible versions"></div>
        <div class="confirm-modal__actions">
          <button type="button" class="confirm-modal__cancel" id="bible-version-cancel">
            Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    listEl = modal.querySelector("#bible-version-list");
    cancelBtn = modal.querySelector("#bible-version-cancel");

    cancelBtn.addEventListener("click", closeModal);
    modal
      .querySelector("[data-settings-dismiss]")
      .addEventListener("click", closeModal);

    return modal;
  }

  async function applyVersion(bibleVersionId) {
    if (loading) return;
    loading = true;
    try {
      const response = await fetch("/api/settings/bible-version", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bible_version_id: bibleVersionId }),
      });
      if (!response.ok) {
        throw new Error("Failed to save Bible version");
      }
      location.reload();
    } catch (_err) {
      loading = false;
    }
  }

  function renderVersions(data) {
    listEl.innerHTML = "";
    data.versions.forEach((version) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "settings-modal__option";
      btn.setAttribute("role", "option");
      btn.setAttribute(
        "aria-selected",
        version.id === data.bible_version_id ? "true" : "false"
      );
      if (version.id === data.bible_version_id) {
        btn.classList.add("settings-modal__option--current");
      }
      btn.innerHTML = `
        <span class="settings-modal__abbr">${version.abbreviation}</span>
        <span class="settings-modal__name">${version.version}</span>
      `;
      btn.addEventListener("click", () => {
        if (version.id === data.bible_version_id) {
          closeModal();
          return;
        }
        applyVersion(version.id);
      });
      listEl.appendChild(btn);
    });
  }

  window.openBibleVersionSettings = async function openBibleVersionSettings() {
    ensureModal();
    modal.hidden = false;
    document.addEventListener("keydown", onKeydown);
    listEl.innerHTML = `<p class="settings-modal__loading">Loading…</p>`;
    cancelBtn.focus();

    try {
      const response = await fetch("/api/settings");
      if (!response.ok) {
        throw new Error("Failed to load settings");
      }
      const data = await response.json();
      renderVersions(data);
      const current =
        listEl.querySelector(".settings-modal__option--current") ||
        listEl.querySelector(".settings-modal__option");
      if (current) current.focus();
      else cancelBtn.focus();
    } catch (_err) {
      listEl.innerHTML = `<p class="settings-modal__loading">Could not load versions.</p>`;
      cancelBtn.focus();
    }
  };
})();

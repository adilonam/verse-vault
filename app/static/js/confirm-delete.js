(() => {
  let modal = null;
  let messageEl = null;
  let cancelBtn = null;
  let confirmBtn = null;
  let resolvePending = null;

  function closeModal(result) {
    if (!modal) return;
    modal.hidden = true;
    document.removeEventListener("keydown", onKeydown);
    if (resolvePending) {
      resolvePending(result);
      resolvePending = null;
    }
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeModal(false);
    }
  }

  function ensureModal() {
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "confirm-modal";
    modal.id = "confirm-delete-modal";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="confirm-modal__backdrop" data-confirm-dismiss></div>
      <div
        class="confirm-modal__dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-delete-title"
        aria-describedby="confirm-delete-message"
      >
        <header class="confirm-modal__header">
          <span class="confirm-modal__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m2 0v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6h12z" />
              <path d="M10 11v6M14 11v6" />
            </svg>
          </span>
          <h2 class="confirm-modal__title" id="confirm-delete-title">Delete</h2>
        </header>
        <p class="confirm-modal__message" id="confirm-delete-message"></p>
        <div class="confirm-modal__actions">
          <button type="button" class="confirm-modal__cancel" id="confirm-delete-cancel">
            Cancel
          </button>
          <button type="button" class="confirm-modal__confirm" id="confirm-delete-confirm">
            Delete
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    messageEl = modal.querySelector("#confirm-delete-message");
    cancelBtn = modal.querySelector("#confirm-delete-cancel");
    confirmBtn = modal.querySelector("#confirm-delete-confirm");

    cancelBtn.addEventListener("click", () => closeModal(false));
    confirmBtn.addEventListener("click", () => closeModal(true));
    modal.querySelector("[data-confirm-dismiss]").addEventListener("click", () => closeModal(false));

    return modal;
  }

  window.confirmDelete = function confirmDelete(message) {
    return new Promise((resolve) => {
      if (resolvePending) {
        resolvePending(false);
      }
      resolvePending = resolve;

      ensureModal();
      messageEl.textContent = message;
      modal.hidden = false;
      document.addEventListener("keydown", onKeydown);
      cancelBtn.focus();
    });
  };
})();

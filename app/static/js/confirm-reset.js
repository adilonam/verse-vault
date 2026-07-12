(() => {
  let modal = null;
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
    modal.id = "confirm-reset-modal";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="confirm-modal__backdrop" data-confirm-dismiss></div>
      <div
        class="confirm-modal__dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-reset-title"
        aria-describedby="confirm-reset-message"
      >
        <header class="confirm-modal__header">
          <span class="confirm-modal__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
          </span>
          <h2 class="confirm-modal__title" id="confirm-reset-title">Reset reading progress</h2>
        </header>
        <p class="confirm-modal__message" id="confirm-reset-message">
          Reset reading progress? All chapter completion will be cleared.
        </p>
        <div class="confirm-modal__actions">
          <button type="button" class="confirm-modal__cancel" id="confirm-reset-cancel">
            Cancel
          </button>
          <button type="button" class="confirm-modal__confirm" id="confirm-reset-confirm">
            Reset
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    cancelBtn = modal.querySelector("#confirm-reset-cancel");
    confirmBtn = modal.querySelector("#confirm-reset-confirm");

    cancelBtn.addEventListener("click", () => closeModal(false));
    confirmBtn.addEventListener("click", () => closeModal(true));
    modal
      .querySelector("[data-confirm-dismiss]")
      .addEventListener("click", () => closeModal(false));

    return modal;
  }

  window.confirmResetReading = function confirmResetReading() {
    return new Promise((resolve) => {
      if (resolvePending) {
        resolvePending(false);
      }
      resolvePending = resolve;

      ensureModal();
      modal.hidden = false;
      document.addEventListener("keydown", onKeydown);
      cancelBtn.focus();
    });
  };
})();

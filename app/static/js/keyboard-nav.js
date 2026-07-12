(() => {
  const FOCUSABLE =
    'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  const ARROWS = new Set(["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]);

  function isHiddenInput(el) {
    if (!el || el.tagName !== "INPUT") return false;
    const type = (el.type || "").toLowerCase();
    return type === "radio" || type === "checkbox";
  }

  function isVisible(el) {
    if (!el || el.disabled) return false;
    if (el.closest("[hidden]")) return false;
    if (el.getAttribute("aria-hidden") === "true") return false;
    const style = window.getComputedStyle(el);
    if (style.visibility === "hidden" || style.display === "none") return false;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0 && !isHiddenInput(el)) return false;
    return true;
  }

  function focusRect(el) {
    const host =
      el.closest(".color-option") ||
      (isHiddenInput(el) ? el.closest("label") : null) ||
      el;
    return host.getBoundingClientRect();
  }

  function openModalRoot() {
    return (
      document.querySelector(".confirm-modal:not([hidden])") ||
      document.querySelector(".collection-modal:not([hidden])")
    );
  }

  function isToolbarSearchInput(el) {
    if (!el || el.tagName !== "INPUT") return false;
    if (!el.classList.contains("search-input")) return false;
    return Boolean(
      el.closest(".bible-toolbar, .notes-toolbar, .collections-toolbar")
    );
  }

  function getPageSearchInput() {
    const el =
      document.querySelector(".bible-toolbar .search-input") ||
      document.querySelector(".notes-toolbar .search-input") ||
      document.querySelector(".collections-toolbar .search-input");
    return el && isVisible(el) ? el : null;
  }

  function getFocusables(scope) {
    return Array.from((scope || document).querySelectorAll(FOCUSABLE))
      .filter(isVisible)
      .filter((el) => !isToolbarSearchInput(el));
  }

  function centerOf(rect) {
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
  }

  function findInDirection(current, key, candidates) {
    const fromC = centerOf(focusRect(current));
    let best = null;
    let bestScore = Infinity;

    for (const el of candidates) {
      if (el === current) continue;
      const toC = centerOf(focusRect(el));
      const dx = toC.x - fromC.x;
      const dy = toC.y - fromC.y;

      let primary;
      let secondary;
      if (key === "ArrowLeft") {
        if (dx >= -4) continue;
        primary = -dx;
        secondary = Math.abs(dy);
      } else if (key === "ArrowRight") {
        if (dx <= 4) continue;
        primary = dx;
        secondary = Math.abs(dy);
      } else if (key === "ArrowUp") {
        if (dy >= -4) continue;
        primary = -dy;
        secondary = Math.abs(dx);
      } else if (key === "ArrowDown") {
        if (dy <= 4) continue;
        primary = dy;
        secondary = Math.abs(dx);
      } else {
        continue;
      }

      const score =
        key === "ArrowUp" || key === "ArrowDown"
          ? primary * 1000 + secondary
          : primary + secondary * 3;
      if (score < bestScore) {
        bestScore = score;
        best = el;
      }
    }
    return best;
  }

  function isTextEntry(el) {
    if (!el || !el.tagName) return false;
    const tag = el.tagName;
    if (tag === "TEXTAREA" || tag === "SELECT") return true;
    if (el.isContentEditable) return true;
    if (tag !== "INPUT") return false;
    const type = (el.type || "text").toLowerCase();
    return ![
      "button",
      "submit",
      "reset",
      "checkbox",
      "radio",
      "file",
      "image",
      "range",
      "color",
    ].includes(type);
  }

  function ownsVerticalArrows(el, key) {
    if (!el || !el.classList || !el.classList.contains("verse-line")) return false;
    const reader = el.closest(".reader-text");
    if (!reader) return true;
    const verseLines = reader.querySelectorAll(".verse-line");
    const index = Array.prototype.indexOf.call(verseLines, el);
    if (index < 0) return true;
    if (key === "ArrowDown" && index === verseLines.length - 1) return false;
    if (key === "ArrowUp" && index === 0) return false;
    return true;
  }

  function ownsAllArrows(el) {
    if (!el) return false;
    if (el.classList && el.classList.contains("reader-resizer")) return true;
    return el.getAttribute("role") === "separator";
  }

  function handleEscape(event) {
    const modal = openModalRoot();
    if (modal) {
      const cancel =
        modal.querySelector(".confirm-modal__cancel") ||
        modal.querySelector(".collection-modal__cancel") ||
        modal.querySelector("[data-confirm-dismiss]");
      if (cancel) {
        event.preventDefault();
        cancel.click();
        return true;
      }
    }

    const editCancel = document.getElementById("edit-cancel-btn");
    const detail =
      document.getElementById("note-detail") ||
      document.getElementById("collection-detail");
    if (
      editCancel &&
      detail &&
      detail.dataset.mode === "edit" &&
      isVisible(editCancel)
    ) {
      event.preventDefault();
      editCancel.click();
      return true;
    }

    if (isTextEntry(document.activeElement)) {
      event.preventDefault();
      document.activeElement.blur();
      return true;
    }

    const back =
      document.querySelector(".note-detail__back") ||
      document.querySelector(".collection-detail__back");
    if (back) {
      event.preventDefault();
      back.click();
      return true;
    }

    if (document.querySelector(".chapter-select")) {
      event.preventDefault();
      location.href = "/bible";
      return true;
    }

    if (document.querySelector(".app-shell--reader")) {
      const bookId = document.querySelector(".reader-text")?.dataset.bookId;
      if (bookId) {
        event.preventDefault();
        location.href = `/bible/${bookId}`;
        return true;
      }
    }

    if (location.pathname === "/collections/new") {
      event.preventDefault();
      location.href = "/collections";
      return true;
    }

    if (
      location.pathname === "/bible" ||
      location.pathname === "/notes" ||
      location.pathname === "/collections"
    ) {
      event.preventDefault();
      location.href = "/";
      return true;
    }

    return false;
  }

  function focusElement(el) {
    if (!el) return;
    el.focus({ preventScroll: true });
    el.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  // Hidden reset: Ctrl+Shift+R opens confirm modal (no dashboard button).
  function handleHiddenReset(event) {
    if (
      event.ctrlKey &&
      event.shiftKey &&
      !event.altKey &&
      !event.metaKey &&
      (event.key === "R" || event.key === "r")
    ) {
      event.preventDefault();
      if (openModalRoot()) return true;
      if (typeof window.confirmResetReading !== "function") return true;
      window.confirmResetReading().then((confirmed) => {
        if (!confirmed) return;
        fetch("/reset-reading", { method: "POST", redirect: "follow" }).then(
          () => {
            location.href = "/";
          }
        );
      });
      return true;
    }
    return false;
  }

  function onKeydown(event) {
    if (event.defaultPrevented) return;
    if (handleHiddenReset(event)) return;
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    const key = event.key;
    const active = document.activeElement;

    if (key === "Escape") {
      handleEscape(event);
      return;
    }

    if (key === "s" || key === "S") {
      if (!isTextEntry(active)) {
        const search = getPageSearchInput();
        if (search) {
          event.preventDefault();
          focusElement(search);
          return;
        }
      }
      return;
    }

    if (key === "Enter") {
      const openModal = openModalRoot();
      if (openModal && openModal.classList.contains("confirm-modal")) {
        const confirm = openModal.querySelector(".confirm-modal__confirm");
        if (confirm) {
          event.preventDefault();
          confirm.click();
          return;
        }
      }

      if (isTextEntry(active) || !active || active === document.body) return;
      const tag = active.tagName;
      if (tag === "INPUT") {
        const type = (active.type || "").toLowerCase();
        if (type === "radio" || type === "checkbox") {
          event.preventDefault();
          active.click();
        }
        return;
      }
      if (tag === "BUTTON" || tag === "A" || tag === "SELECT") {
        return;
      }
      event.preventDefault();
      active.click();
      return;
    }

    if (!ARROWS.has(key)) return;
    if (isTextEntry(active)) return;
    if (ownsAllArrows(active)) return;
    if (ownsVerticalArrows(active, key) && (key === "ArrowUp" || key === "ArrowDown")) {
      return;
    }

    const modal = openModalRoot();
    const candidates = getFocusables(modal || document);
    if (!candidates.length) return;

    let current = active;
    if (!current || current === document.body || !candidates.includes(current)) {
      event.preventDefault();
      const start = candidates[0];
      const next = findInDirection(start, key, candidates) || start;
      focusElement(next);
      return;
    }

    const next = findInDirection(current, key, candidates);
    if (!next) return;

    event.preventDefault();
    focusElement(next);
  }

  function initialFocus() {
    const active = document.activeElement;
    if (active && active !== document.body && active !== document.documentElement) {
      return;
    }
    const preferred =
      document.querySelector(".nav-card--active") ||
      document.querySelector(".verse-line--current") ||
      document.querySelector(".app-tab--active") ||
      document.querySelector(".filter-btn--active") ||
      getFocusables()[0];
    if (preferred) preferred.focus({ preventScroll: true });
  }

  document.addEventListener("keydown", onKeydown);

  window.verseVaultKbd = {
    focusFirstIn(root) {
      const el = getFocusables(root)[0];
      if (el) focusElement(el);
      return el;
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialFocus);
  } else {
    requestAnimationFrame(initialFocus);
  }
})();

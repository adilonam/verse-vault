(() => {
  const layout = document.querySelector(".reader-layout");
  const resizer = document.querySelector(".reader-resizer");
  if (!layout || !resizer) return;

  const STORAGE_KEY = "verse-vault-reader-split";
  const MIN = 25;
  const MAX = 75;
  const STEP = 2;
  // Must match the CSS breakpoint where .reader-layout collapses to a
  // single column and .reader-resizer is hidden (see app.css @media 699px).
  const STACKED_QUERY = "(max-width: 699px)";

  let dragging = false;

  function isStacked() {
    return window.matchMedia(STACKED_QUERY).matches;
  }

  function applySplit(percent) {
    const clamped = Math.min(MAX, Math.max(MIN, percent));
    layout.style.setProperty("--reader-split", `${clamped}%`);
    resizer.setAttribute("aria-valuenow", String(Math.round(clamped)));
    return clamped;
  }

  function loadSplit() {
    let stored = null;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
    } catch (err) {
      stored = null;
    }
    if (!stored) return;
    const value = parseFloat(stored);
    if (!Number.isNaN(value)) applySplit(value);
  }

  function saveSplit(percent) {
    try {
      localStorage.setItem(STORAGE_KEY, String(percent));
    } catch (err) {
      /* ignore storage failures (private mode, quota, etc.) */
    }
  }

  function splitFromClientX(clientX) {
    const rect = layout.getBoundingClientRect();
    const resizerWidth = resizer.offsetWidth;
    const available = rect.width - resizerWidth;
    if (available <= 0) return applySplit(50);
    const x = clientX - rect.left;
    return applySplit((x / available) * 100);
  }

  function startDrag(event) {
    if (isStacked()) return;
    dragging = true;
    document.body.classList.add("reader-resizing");
    if (event.pointerId !== undefined && resizer.setPointerCapture) {
      try {
        resizer.setPointerCapture(event.pointerId);
      } catch (err) {
        /* setPointerCapture can throw if the pointer is already gone */
      }
    }
    event.preventDefault();
  }

  function onMove(event) {
    if (!dragging) return;
    let clientX = event.clientX;
    if (clientX === undefined && event.touches && event.touches[0]) {
      clientX = event.touches[0].clientX;
    }
    if (clientX === undefined) return;
    event.preventDefault();
    splitFromClientX(clientX);
  }

  function stopDrag() {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove("reader-resizing");
    const split = layout.style.getPropertyValue("--reader-split");
    if (split) saveSplit(parseFloat(split));
  }

  // Prefer Pointer Events (covers mouse, touch and pen with one code path).
  // Fall back to mouse events for older engines where pointer events are
  // unavailable.
  if (window.PointerEvent) {
    resizer.addEventListener("pointerdown", startDrag);
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", stopDrag);
    document.addEventListener("pointercancel", stopDrag);
  } else {
    resizer.addEventListener("mousedown", startDrag);
    resizer.addEventListener("touchstart", startDrag, { passive: false });
    document.addEventListener("mousemove", onMove);
    document.addEventListener("touchmove", onMove, { passive: false });
    document.addEventListener("mouseup", stopDrag);
    document.addEventListener("touchend", stopDrag);
  }

  resizer.addEventListener("dblclick", () => {
    if (isStacked()) return;
    saveSplit(applySplit(50));
  });

  resizer.addEventListener("keydown", (event) => {
    if (isStacked()) return;
    const current = parseFloat(
      layout.style.getPropertyValue("--reader-split") || "50"
    );
    let next = current;
    if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      next = current - STEP;
    } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      next = current + STEP;
    } else if (event.key === "Home") {
      next = MIN;
    } else if (event.key === "End") {
      next = MAX;
    } else {
      return;
    }
    event.preventDefault();
    saveSplit(applySplit(next));
  });

  loadSplit();
})();

(() => {
  const layout = document.querySelector(".reader-layout");
  const resizer = document.querySelector(".reader-resizer");
  if (!layout || !resizer) return;

  const STORAGE_KEY = "verse-vault-reader-split";
  const MIN = 25;
  const MAX = 75;
  const STEP = 2;

  let dragging = false;

  function applySplit(percent) {
    const clamped = Math.min(MAX, Math.max(MIN, percent));
    layout.style.setProperty("--reader-split", `${clamped}%`);
    resizer.setAttribute("aria-valuenow", String(Math.round(clamped)));
    return clamped;
  }

  function loadSplit() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    const value = parseFloat(stored);
    if (!Number.isNaN(value)) applySplit(value);
  }

  function saveSplit(percent) {
    localStorage.setItem(STORAGE_KEY, String(percent));
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
    if (window.matchMedia("(max-width: 900px)").matches) return;
    dragging = true;
    document.body.classList.add("reader-resizing");
    event.preventDefault();
  }

  function onMove(event) {
    if (!dragging) return;
    const clientX = event.touches ? event.touches[0].clientX : event.clientX;
    splitFromClientX(clientX);
  }

  function stopDrag() {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove("reader-resizing");
    const split = layout.style.getPropertyValue("--reader-split");
    if (split) saveSplit(parseFloat(split));
  }

  resizer.addEventListener("mousedown", startDrag);
  resizer.addEventListener("touchstart", startDrag, { passive: false });
  document.addEventListener("mousemove", onMove);
  document.addEventListener("touchmove", onMove, { passive: false });
  document.addEventListener("mouseup", stopDrag);
  document.addEventListener("touchend", stopDrag);

  resizer.addEventListener("keydown", (event) => {
    const current = parseFloat(
      layout.style.getPropertyValue("--reader-split") || "50"
    );
    let next = current;
    if (event.key === "ArrowLeft") next = current - STEP;
    else if (event.key === "ArrowRight") next = current + STEP;
    else return;
    event.preventDefault();
    saveSplit(applySplit(next));
  });

  loadSplit();
})();

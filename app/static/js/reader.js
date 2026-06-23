(() => {
  const reader = document.querySelector(".reader-text");
  if (!reader) return;

  const bookId = Number(reader.dataset.bookId);
  const chapter = Number(reader.dataset.chapter);
  const verses = [...reader.querySelectorAll(".verse-line")];

  if (!verses.length) return;

  let currentIndex = verses.findIndex((verse) =>
    verse.classList.contains("verse-line--current")
  );
  if (currentIndex < 0) currentIndex = 0;

  let saveTimer = null;

  function updateTabIndices() {
    verses.forEach((verse, index) => {
      verse.setAttribute("tabindex", index === currentIndex ? "0" : "-1");
    });
  }

  function scrollToCurrent() {
    verses[currentIndex].scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function savePosition() {
    const verse = Number(verses[currentIndex].dataset.verse);
    fetch("/api/reading/position", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        book_id: bookId,
        chapter,
        verse,
      }),
    }).catch(() => {});
  }

  function queueSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(savePosition, 200);
  }

  function selectVerse(index) {
    if (index < 0 || index >= verses.length || index === currentIndex) return;

    verses[currentIndex].classList.remove("verse-line--current");
    verses[currentIndex].setAttribute("aria-selected", "false");

    currentIndex = index;

    verses[currentIndex].classList.add("verse-line--current");
    verses[currentIndex].setAttribute("aria-selected", "true");
    updateTabIndices();
    verses[currentIndex].focus({ preventScroll: true });

    scrollToCurrent();
    queueSave();
  }

  verses.forEach((verse, index) => {
    verse.setAttribute("role", "option");
    verse.setAttribute(
      "aria-selected",
      verse.classList.contains("verse-line--current") ? "true" : "false"
    );
    verse.addEventListener("click", () => selectVerse(index));
  });

  reader.setAttribute("role", "listbox");
  reader.setAttribute("aria-label", "Chapter verses");

  document.addEventListener("keydown", (event) => {
    const tag = event.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      selectVerse(currentIndex + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      selectVerse(currentIndex - 1);
    }
  });

  updateTabIndices();
  verses[currentIndex].focus({ preventScroll: true });
  scrollToCurrent();
})();

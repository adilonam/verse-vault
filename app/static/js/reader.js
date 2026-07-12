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

  function dispatchVerseChange() {
    const verse = Number(verses[currentIndex].dataset.verse);
    document.dispatchEvent(
      new CustomEvent("verse-change", {
        detail: { bookId, chapter, verse },
      })
    );
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
    savePosition();
    dispatchVerseChange();
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

  const chapterNav = document.querySelector(".reader-panel .chapter-nav");

  function focusChapterNav() {
    if (!chapterNav) return;
    const link = chapterNav.querySelector("a.chapter-nav__btn");
    if (link) link.focus({ preventScroll: true });
  }

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (!(target instanceof Element) || !target.classList.contains("verse-line")) {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (currentIndex < verses.length - 1) {
        selectVerse(currentIndex + 1);
      } else {
        focusChapterNav();
      }
    } else if (event.key === "ArrowUp") {
      if (currentIndex > 0) {
        event.preventDefault();
        selectVerse(currentIndex - 1);
      }
    }
  });

  if (chapterNav) {
    chapterNav.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowUp") return;
      const target = event.target;
      if (!(target instanceof Element) || !chapterNav.contains(target)) return;
      event.preventDefault();
      verses[currentIndex].focus({ preventScroll: true });
    });
  }

  updateTabIndices();
  verses[currentIndex].focus({ preventScroll: true });
  scrollToCurrent();
  savePosition();
  dispatchVerseChange();
})();

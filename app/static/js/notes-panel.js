(() => {
  const panel = document.querySelector(".notes-panel");
  if (!panel) return;

  const titleInput = document.getElementById("note-title");
  const bodyInput = document.getElementById("note-body");
  const saveBtn = document.getElementById("note-save-btn");
  const deleteBtn = document.getElementById("note-delete-btn");
  const collectionBtn = document.getElementById("note-collection-btn");
  const modal = document.getElementById("collection-modal");
  const modalList = document.getElementById("collection-modal-list");
  const modalCancel = document.getElementById("collection-modal-cancel");
  const modalBackdrop = document.getElementById("collection-modal-backdrop");

  if (!titleInput || !bodyInput || !saveBtn || !deleteBtn) return;

  let bookId = Number(panel.dataset.bookId);
  let chapter = Number(panel.dataset.chapter);
  let verse = Number(panel.dataset.verse);
  let noteId = null;

  function passageParams() {
    return new URLSearchParams({
      book: String(bookId),
      chapter: String(chapter),
      verse: String(verse),
    });
  }

  function clearFields() {
    titleInput.value = "";
    bodyInput.value = "";
    noteId = null;
    panel.dataset.noteId = "";
  }

  function populateFields(note) {
    if (!note) {
      clearFields();
      return;
    }
    titleInput.value = note.title;
    bodyInput.value = note.body;
    noteId = note.id;
    panel.dataset.noteId = String(note.id);
  }

  async function loadNote() {
    try {
      const response = await fetch(`/api/notes/passage?${passageParams()}`);
      if (!response.ok) return;
      const note = await response.json();
      populateFields(note);
    } catch {
      clearFields();
    }
  }

  function flashButton(button, label, duration = 1500) {
    const original = button.textContent;
    button.textContent = label;
    button.disabled = true;
    window.setTimeout(() => {
      button.textContent = original;
      button.disabled = false;
    }, duration);
  }

  async function saveNote() {
    try {
      const response = await fetch("/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: titleInput.value.trim(),
          body: bodyInput.value.trim(),
          book_id: bookId,
          chapter,
          verse,
        }),
      });
      if (!response.ok) return;
      const note = await response.json();
      populateFields(note);
      flashButton(saveBtn, "Saved");
    } catch {
      /* ignore */
    }
  }

  async function deleteNote() {
    if (!noteId && !titleInput.value && !bodyInput.value) return;

    try {
      const response = await fetch(`/api/notes/passage?${passageParams()}`, {
        method: "DELETE",
      });
      if (response.status === 404) {
        clearFields();
        return;
      }
      if (!response.ok) return;
      clearFields();
      flashButton(deleteBtn, "Deleted");
    } catch {
      /* ignore */
    }
  }

  function closeCollectionModal() {
    if (!modal) return;
    modal.hidden = true;
  }

  function openCollectionModal() {
    if (!modal) return;
    modal.hidden = false;
    loadCollectionOptions();
  }

  function renderCollectionList(collections) {
    if (!modalList) return;
    modalList.replaceChildren();

    if (!collections.length) {
      const empty = document.createElement("li");
      empty.className = "collection-modal__empty";
      empty.textContent = "No collections yet. Create one from the Collections tab.";
      modalList.appendChild(empty);
      return;
    }

    for (const collection of collections) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "collection-modal__item";
      button.dataset.collectionId = String(collection.id);

      const name = document.createElement("span");
      name.className = "collection-modal__item-name";
      name.textContent = collection.name;

      const count = document.createElement("span");
      count.className = "collection-modal__item-count";
      const verseLabel = collection.verse_count === 1 ? "verse" : "verses";
      count.textContent = `${collection.verse_count} ${verseLabel}`;

      button.append(name, count);
      button.addEventListener("click", () => addToCollection(collection.id, button));
      item.appendChild(button);
      modalList.appendChild(item);
    }
  }

  async function loadCollectionOptions() {
    if (!modalList) return;
    modalList.replaceChildren();
    const loading = document.createElement("li");
    loading.className = "collection-modal__empty";
    loading.textContent = "Loading collections…";
    modalList.appendChild(loading);

    try {
      const response = await fetch("/api/collections");
      if (!response.ok) {
        renderCollectionList([]);
        return;
      }
      const collections = await response.json();
      renderCollectionList(collections);
    } catch {
      renderCollectionList([]);
    }
  }

  async function addToCollection(collectionId, button) {
    if (button) button.disabled = true;
    try {
      const response = await fetch("/api/notes/add-to-collection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: titleInput.value.trim(),
          body: bodyInput.value.trim(),
          book_id: bookId,
          chapter,
          verse,
          collection_id: collectionId,
        }),
      });
      if (!response.ok) {
        if (button) button.disabled = false;
        return;
      }
      const note = await response.json();
      populateFields(note);
      closeCollectionModal();
      if (collectionBtn) {
        flashButton(collectionBtn, "Added");
      }
    } catch {
      if (button) button.disabled = false;
    }
  }

  saveBtn.addEventListener("click", saveNote);
  deleteBtn.addEventListener("click", deleteNote);

  if (collectionBtn) {
    collectionBtn.addEventListener("click", openCollectionModal);
  }

  if (modalCancel) {
    modalCancel.addEventListener("click", closeCollectionModal);
  }

  if (modalBackdrop) {
    modalBackdrop.addEventListener("click", closeCollectionModal);
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal && !modal.hidden) {
      closeCollectionModal();
    }
  });

  document.addEventListener("verse-change", (event) => {
    const detail = event.detail;
    if (!detail) return;
    bookId = Number(detail.bookId);
    chapter = Number(detail.chapter);
    verse = Number(detail.verse);
    panel.dataset.bookId = String(bookId);
    panel.dataset.chapter = String(chapter);
    panel.dataset.verse = String(verse);
    closeCollectionModal();
    loadNote();
  });

  loadNote();
})();

(() => {
  const root = document.getElementById("collection-detail");
  if (!root) return;

  const collectionId = Number(root.dataset.collectionId);
  const editToggleBtn = document.getElementById("edit-toggle-btn");
  const collectionView = document.getElementById("collection-view");
  const collectionEditForm = document.getElementById("collection-edit-form");
  const editCancelBtn = document.getElementById("edit-cancel-btn");
  const editNameInput = document.getElementById("edit-name");
  const editDescriptionInput = document.getElementById("edit-description");
  const editColorOptions = document.getElementById("edit-color-options");
  const collectionTitle = document.getElementById("collection-title");
  const collectionDescription = document.getElementById("collection-description");
  const collectionIcon = document.getElementById("collection-icon");
  const verseTags = document.getElementById("verse-tags");
  const versesEmpty = document.getElementById("verses-empty");
  const verseAddRow = document.getElementById("verse-add-row");
  const verseInput = document.getElementById("verse-input");
  const verseAddBtn = document.getElementById("verse-add-btn");
  const noteList = document.getElementById("note-list");
  const notesEmpty = document.getElementById("notes-empty");
  const noteAddForm = document.getElementById("note-add-form");
  const noteTitleInput = document.getElementById("note-title-input");
  const noteBodyInput = document.getElementById("note-body-input");
  const noteRefInput = document.getElementById("note-ref-input");
  const noteAddBtn = document.getElementById("note-add-btn");
  const verseCountLabel = document.getElementById("verse-count-label");
  const noteCountLabel = document.getElementById("note-count-label");

  let editing = false;
  let savedFormState = null;

  function apiUrl(path) {
    return `/api/collections/${collectionId}${path}`;
  }

  function setEditing(active) {
    editing = active;
    const mode = active ? "edit" : "view";
    root.dataset.mode = mode;
    root.classList.toggle("collection-detail--view", !active);
    root.classList.toggle("collection-detail--edit", active);

    collectionView.hidden = active;
    collectionEditForm.hidden = !active;
    verseAddRow.hidden = !active;
    noteAddForm.hidden = !active;

    root.querySelectorAll(".collection-detail__verse-remove").forEach((btn) => {
      btn.hidden = !active;
    });
    root.querySelectorAll(".collection-detail__note-remove").forEach((btn) => {
      btn.hidden = !active;
    });

    if (active) {
      savedFormState = {
        name: editNameInput.value,
        description: editDescriptionInput.value,
        color: getSelectedColor(),
      };
      editNameInput.focus();
    }
  }

  function getSelectedColor() {
    const checked = editColorOptions.querySelector('input[name="edit-color"]:checked');
    return checked ? checked.value : "gold";
  }

  function updateColorSelection() {
    editColorOptions.querySelectorAll(".color-option").forEach((option) => {
      const input = option.querySelector(".color-option__input");
      option.classList.toggle("color-option--selected", input.checked);
    });
  }

  function setCollectionIconColor(color) {
    collectionIcon.className = `collection-detail__icon collection-detail__icon--${color}`;
  }

  function updateVerseCount(count) {
    verseCountLabel.textContent = `${count} verse${count === 1 ? "" : "s"}`;
  }

  function updateNoteCount(count) {
    noteCountLabel.textContent = `${count} note${count === 1 ? "" : "s"}`;
  }

  function updateEmptyStates() {
    const verseCount = verseTags.querySelectorAll("[data-verse-ref-id]").length;
    versesEmpty.hidden = verseCount > 0;
    updateVerseCount(verseCount);

    const noteCount = noteList.querySelectorAll("[data-note-id]").length;
    notesEmpty.hidden = noteCount > 0;
    updateNoteCount(noteCount);
  }

  function createVerseTag(ref) {
    const tag = document.createElement("span");
    tag.className = "collection-detail__verse-tag collection-detail__verse-tag--linked";
    tag.dataset.verseRefId = String(ref.verse_ref_id);
    tag.dataset.bookId = String(ref.book_id);
    tag.dataset.chapter = String(ref.chapter);
    tag.dataset.verse = String(ref.verse);

    const link = document.createElement("a");
    link.className = "collection-detail__verse-tag-link";
    link.href = `/continue?book=${ref.book_id}&chapter=${ref.chapter}&verse=${ref.verse}`;
    link.innerHTML =
      '<span class="collection-detail__verse-tag-icon" aria-hidden="true">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' +
      "</span>" +
      ref.reference;

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "collection-detail__verse-remove";
    removeBtn.setAttribute("aria-label", `Remove ${ref.reference}`);
    removeBtn.textContent = "×";
    removeBtn.hidden = !editing;
    removeBtn.addEventListener("click", () => removeVerse(ref.verse_ref_id, tag));

    tag.appendChild(link);
    tag.appendChild(removeBtn);
    return tag;
  }

  function createNoteCard(note) {
    const card = document.createElement("article");
    card.className = "note-card";
    card.dataset.noteId = String(note.id);

    const hasPassage =
      note.book_id !== null && note.chapter !== null && note.verse !== null;
    const tagHtml = hasPassage
      ? `<a href="/continue?book=${note.book_id}&chapter=${note.chapter}&verse=${note.verse}" class="note-card__tag">
          <span class="note-card__tag-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </span>
          ${note.scripture_reference}
        </a>`
      : `<span class="note-card__tag">
          <span class="note-card__tag-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </span>
          ${note.scripture_reference}
        </span>`;

    card.innerHTML = `
      <div class="note-card__head">
        <h3 class="note-card__title"></h3>
        <div class="note-card__actions">
          <time class="note-card__date"></time>
          <button type="button" class="collection-detail__note-remove" aria-label="Remove note from collection" ${editing ? "" : "hidden"}>
            Remove
          </button>
        </div>
      </div>
      <p class="note-card__preview"></p>
      ${tagHtml}
    `;

    card.querySelector(".note-card__title").textContent = note.title || "Untitled";
    const dateEl = card.querySelector(".note-card__date");
    dateEl.textContent = note.date_label;
    dateEl.dateTime = note.created_at;
    card.querySelector(".note-card__preview").textContent = note.body_preview;

    card.querySelector(".collection-detail__note-remove").addEventListener("click", () => {
      removeNote(note.id, card);
    });

    return card;
  }

  async function saveCollection(event) {
    event.preventDefault();
    const payload = {
      name: editNameInput.value.trim(),
      description: editDescriptionInput.value.trim(),
      color: getSelectedColor(),
    };
    if (!payload.name) return;

    try {
      const response = await fetch(apiUrl(""), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) return;

      const data = await response.json();
      collectionTitle.textContent = data.name;
      collectionDescription.textContent = data.description || "No description";
      collectionDescription.classList.toggle(
        "collection-detail__description--empty",
        !data.description
      );
      setCollectionIconColor(data.color);
      savedFormState = {
        name: data.name,
        description: data.description,
        color: data.color,
      };
      setEditing(false);
    } catch {
      /* ignore */
    }
  }

  function restoreFormState() {
    if (!savedFormState) return;
    editNameInput.value = savedFormState.name;
    editDescriptionInput.value = savedFormState.description;
    const colorInput = editColorOptions.querySelector(
      `input[name="edit-color"][value="${savedFormState.color}"]`
    );
    if (colorInput) {
      colorInput.checked = true;
      updateColorSelection();
    }
  }

  async function addVerse() {
    const reference = verseInput.value.trim();
    if (!reference) return;

    const existing = Array.from(verseTags.querySelectorAll("[data-verse-ref-id]")).some(
      (tag) => tag.querySelector(".collection-detail__verse-tag-link")?.textContent.trim().endsWith(reference) ||
        tag.textContent.includes(reference)
    );
    if (existing) {
      verseInput.value = "";
      return;
    }

    try {
      const response = await fetch(apiUrl("/verses"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference }),
      });
      if (!response.ok) return;

      const ref = await response.json();
      const duplicate = verseTags.querySelector(
        `[data-verse-ref-id="${ref.verse_ref_id}"]`
      );
      if (!duplicate) {
        verseTags.appendChild(createVerseTag(ref));
      }
      verseInput.value = "";
      updateEmptyStates();
    } catch {
      /* ignore */
    }
  }

  async function removeVerse(verseRefId, tagEl) {
    try {
      const response = await fetch(apiUrl(`/verses/${verseRefId}`), {
        method: "DELETE",
      });
      if (!response.ok) return;
      tagEl.remove();
      updateEmptyStates();
    } catch {
      /* ignore */
    }
  }

  async function addNote() {
    const reference = noteRefInput.value.trim();
    if (!reference) return;

    const payload = {
      title: noteTitleInput.value.trim(),
      body: noteBodyInput.value.trim(),
      reference,
    };

    try {
      const response = await fetch(apiUrl("/notes"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) return;

      const note = await response.json();
      const duplicate = noteList.querySelector(`[data-note-id="${note.id}"]`);
      if (!duplicate) {
        noteList.prepend(createNoteCard(note));
      }

      noteTitleInput.value = "";
      noteBodyInput.value = "";
      noteRefInput.value = "";
      updateEmptyStates();
    } catch {
      /* ignore */
    }
  }

  async function removeNote(noteId, cardEl) {
    try {
      const response = await fetch(apiUrl(`/notes/${noteId}`), {
        method: "DELETE",
      });
      if (!response.ok) return;
      cardEl.remove();
      updateEmptyStates();
    } catch {
      /* ignore */
    }
  }

  editToggleBtn.addEventListener("click", () => {
    setEditing(true);
  });

  editCancelBtn.addEventListener("click", () => {
    restoreFormState();
    setEditing(false);
  });

  collectionEditForm.addEventListener("submit", async (event) => {
    await saveCollection(event);
  });

  editColorOptions.addEventListener("change", updateColorSelection);

  verseAddBtn.addEventListener("click", addVerse);
  verseInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addVerse();
    }
  });

  noteAddBtn.addEventListener("click", addNote);

  root.querySelectorAll(".collection-detail__verse-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tag = btn.closest("[data-verse-ref-id]");
      if (!tag) return;
      removeVerse(Number(tag.dataset.verseRefId), tag);
    });
  });

  root.querySelectorAll(".collection-detail__note-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      const card = btn.closest("[data-note-id]");
      if (!card) return;
      removeNote(Number(card.dataset.noteId), card);
    });
  });

  setEditing(false);
})();

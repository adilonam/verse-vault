(() => {
  const root = document.getElementById("note-detail");
  if (!root) return;

  const noteId = Number(root.dataset.noteId);
  const editToggleBtn = document.getElementById("edit-toggle-btn");
  const noteView = document.getElementById("note-view");
  const noteEditForm = document.getElementById("note-edit-form");
  const editCancelBtn = document.getElementById("edit-cancel-btn");
  const editTitleInput = document.getElementById("edit-title");
  const editBodyInput = document.getElementById("edit-body");
  const editReferenceInput = document.getElementById("edit-reference");
  const noteTitle = document.getElementById("note-title");
  const noteBody = document.getElementById("note-body");
  const noteRefView = document.getElementById("note-ref-view");
  const noteRefText = document.getElementById("note-ref-text");

  let savedFormState = null;

  function apiUrl() {
    return `/api/notes/${noteId}`;
  }

  function setEditing(active) {
    const mode = active ? "edit" : "view";
    root.dataset.mode = mode;
    root.classList.toggle("note-detail--view", !active);
    root.classList.toggle("note-detail--edit", active);

    noteView.hidden = active;
    noteEditForm.hidden = !active;

    if (active) {
      savedFormState = {
        title: editTitleInput.value,
        body: editBodyInput.value,
        reference: editReferenceInput.value,
      };
      editTitleInput.focus();
    }
  }

  function updateScriptureTag(data) {
    const hasPassage =
      data.book_id !== null && data.chapter !== null && data.verse !== null;

    noteRefText.textContent = data.scripture_reference;

    if (hasPassage) {
      const href = `/continue?book=${data.book_id}&chapter=${data.chapter}&verse=${data.verse}`;
      if (noteRefView.querySelector("a.note-detail__tag")) {
        noteRefView.querySelector("a.note-detail__tag").href = href;
      } else {
        noteRefView.innerHTML = `
          <a href="${href}" class="note-detail__tag note-detail__tag--linked" id="note-ref-link">
            <span class="note-detail__tag-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            </span>
            <span id="note-ref-text">${data.scripture_reference}</span>
          </a>
        `;
      }
    } else {
      noteRefView.innerHTML = `
        <span class="note-detail__tag" id="note-ref-link">
          <span class="note-detail__tag-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </span>
          <span id="note-ref-text">${data.scripture_reference}</span>
        </span>
      `;
    }
  }

  async function saveNote(event) {
    event.preventDefault();
    const payload = {
      title: editTitleInput.value.trim(),
      body: editBodyInput.value.trim(),
      reference: editReferenceInput.value.trim(),
    };
    if (!payload.title || !payload.reference) return;

    try {
      const response = await fetch(apiUrl(), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) return;

      const data = await response.json();
      noteTitle.textContent = data.title;
      noteBody.textContent = data.body;
      updateScriptureTag(data);
      savedFormState = {
        title: data.title,
        body: data.body,
        reference: data.scripture_reference,
      };
      editTitleInput.value = data.title;
      editBodyInput.value = data.body;
      editReferenceInput.value = data.scripture_reference;
      setEditing(false);
    } catch {
      /* ignore */
    }
  }

  function restoreFormState() {
    if (!savedFormState) return;
    editTitleInput.value = savedFormState.title;
    editBodyInput.value = savedFormState.body;
    editReferenceInput.value = savedFormState.reference;
  }

  editToggleBtn.addEventListener("click", () => {
    setEditing(true);
  });

  editCancelBtn.addEventListener("click", () => {
    restoreFormState();
    setEditing(false);
  });

  noteEditForm.addEventListener("submit", saveNote);

  setEditing(false);
})();

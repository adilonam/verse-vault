from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.db.base import engine
from app.db.models.notes import Note
from app.db.verse_refs import (
    format_scripture_reference,
    get_or_create_verse_ref,
    parse_reference_string,
)


@dataclass(frozen=True)
class NoteData:
    id: int
    title: str
    body: str
    scripture_reference: str
    book_id: int | None
    chapter: int | None
    verse: int | None
    created_at: datetime
    updated_at: datetime
    date_label: str


def _to_note_data(note: Note) -> NoteData:
    verse_ref = note.verse_ref
    return NoteData(
        id=note.id,
        title=note.title,
        body=note.body,
        scripture_reference=note.scripture_reference,
        book_id=verse_ref.book_id if verse_ref else None,
        chapter=verse_ref.chapter if verse_ref else None,
        verse=verse_ref.verse if verse_ref else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
        date_label=note.created_at.strftime("%b %d, %Y"),
    )


def _migrate_notes_verse_ref_id(db: Session) -> None:
    columns = {
        row[1] for row in db.execute(text("PRAGMA table_info(notes)")).all()
    }
    if "verse_ref_id" not in columns:
        db.execute(
            text(
                "ALTER TABLE notes ADD COLUMN verse_ref_id INTEGER "
                "REFERENCES verse_refs(id) ON DELETE SET NULL"
            )
        )

    notes = db.scalars(
        select(Note).where(Note.verse_ref_id.is_(None))
    ).all()
    for note in notes:
        parsed = parse_reference_string(db, note.scripture_reference)
        if parsed is None:
            continue
        book_id, chapter, verse = parsed
        verse_ref = get_or_create_verse_ref(db, book_id, chapter, verse)
        note.verse_ref_id = verse_ref.id


def init_notes_tables() -> None:
    Note.__table__.create(bind=engine, checkfirst=True)

    with Session(engine) as db:
        _migrate_notes_verse_ref_id(db)
        db.commit()


def get_notes(db: Session) -> list[NoteData]:
    rows = db.scalars(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .order_by(Note.created_at.desc())
    ).all()
    return [_to_note_data(row) for row in rows]


def get_note_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Note)) or 0


def get_note_by_id(db: Session, note_id: int) -> NoteData | None:
    note = db.scalar(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .where(Note.id == note_id)
    )
    return _to_note_data(note) if note else None


def get_note_by_verse_ref_id(db: Session, verse_ref_id: int) -> NoteData | None:
    note = db.scalar(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .where(Note.verse_ref_id == verse_ref_id)
    )
    return _to_note_data(note) if note else None


def get_note_by_reference(db: Session, scripture_reference: str) -> NoteData | None:
    note = db.scalar(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .where(Note.scripture_reference == scripture_reference)
    )
    return _to_note_data(note) if note else None


def get_note_for_passage(
    db: Session,
    book_name: str,
    chapter: int,
    verse: int,
) -> NoteData | None:
    reference = format_scripture_reference(book_name, chapter, verse)
    parsed = parse_reference_string(db, reference)
    if parsed is not None:
        book_id, chapter_num, verse_num = parsed
        verse_ref = get_or_create_verse_ref(db, book_id, chapter_num, verse_num)
        note = get_note_by_verse_ref_id(db, verse_ref.id)
        if note is not None:
            return note
    return get_note_by_reference(db, reference)


def upsert_note(
    db: Session,
    title: str,
    body: str,
    book_id: int,
    chapter: int,
    verse: int,
    *,
    book_name: str | None = None,
) -> NoteData:
    verse_ref = get_or_create_verse_ref(
        db,
        book_id,
        chapter,
        verse,
        book_name=book_name,
    )
    reference = verse_ref.reference
    now = datetime.now()
    note = db.scalar(select(Note).where(Note.verse_ref_id == verse_ref.id))
    if note is None:
        note = db.scalar(select(Note).where(Note.scripture_reference == reference))
    if note is None:
        note = Note(
            title=title,
            body=body,
            scripture_reference=reference,
            verse_ref_id=verse_ref.id,
            created_at=now,
            updated_at=now,
        )
        db.add(note)
    else:
        note.title = title
        note.body = body
        note.scripture_reference = reference
        note.verse_ref_id = verse_ref.id
        note.updated_at = now
    db.commit()
    db.refresh(note)
    return _to_note_data(note)


def update_note(
    db: Session,
    note_id: int,
    *,
    title: str,
    body: str,
    reference: str,
) -> NoteData | None:
    note = db.scalar(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .where(Note.id == note_id)
    )
    if note is None:
        return None

    cleaned_reference = reference.strip()
    if not cleaned_reference:
        raise ValueError("Verse reference is required")

    parsed = parse_reference_string(db, cleaned_reference)
    if parsed is None:
        raise ValueError(f"Invalid verse reference: {cleaned_reference}")

    book_id, chapter, verse = parsed
    verse_ref = get_or_create_verse_ref(db, book_id, chapter, verse)

    note.title = title.strip()
    note.body = body.strip()
    note.scripture_reference = verse_ref.reference
    note.verse_ref_id = verse_ref.id
    note.updated_at = datetime.now()
    db.commit()
    db.refresh(note)
    return get_note_by_id(db, note_id)


def delete_note_by_id(db: Session, note_id: int) -> bool:
    note = db.get(Note, note_id)
    if note is None:
        return False
    db.delete(note)
    db.commit()
    return True


def delete_note_for_passage(
    db: Session,
    book_name: str,
    chapter: int,
    verse: int,
) -> bool:
    reference = format_scripture_reference(book_name, chapter, verse)
    parsed = parse_reference_string(db, reference)
    if parsed is not None:
        book_id, chapter_num, verse_num = parsed
        verse_ref = get_or_create_verse_ref(db, book_id, chapter_num, verse_num)
        note = db.scalar(select(Note).where(Note.verse_ref_id == verse_ref.id))
        if note is not None:
            db.delete(note)
            db.commit()
            return True
    note = db.scalar(select(Note).where(Note.scripture_reference == reference))
    if note is None:
        return False
    db.delete(note)
    db.commit()
    return True

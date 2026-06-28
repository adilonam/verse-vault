import re

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.base import engine
from app.db.bible import get_book_name
from app.db.models.verse_refs import VerseRef

_REFERENCE_PATTERN = re.compile(r"^(.+?)\s+(\d+):(\d+)")


def format_scripture_reference(
    book_name: str,
    chapter: int,
    verse: int | None = None,
) -> str:
    if verse is not None:
        return f"{book_name} {chapter}:{verse}"
    return f"{book_name} {chapter}"


def _book_name_lookup(db: Session) -> dict[str, int]:
    rows = db.execute(text('SELECT b, n FROM key_english')).all()
    return {row[1].casefold(): row[0] for row in rows}


def lookup_book_id(db: Session, book_name: str) -> int | None:
    return _book_name_lookup(db).get(book_name.casefold())


def parse_reference_string(
    db: Session,
    reference: str,
) -> tuple[int, int, int] | None:
    match = _REFERENCE_PATTERN.match(reference.strip())
    if match is None:
        return None
    book_name, chapter_str, verse_str = match.groups()
    book_id = lookup_book_id(db, book_name.strip())
    if book_id is None:
        return None
    return book_id, int(chapter_str), int(verse_str)


def get_or_create_verse_ref(
    db: Session,
    book_id: int,
    chapter: int,
    verse: int,
    *,
    book_name: str | None = None,
) -> VerseRef:
    existing = db.scalar(
        select(VerseRef).where(
            VerseRef.book_id == book_id,
            VerseRef.chapter == chapter,
            VerseRef.verse == verse,
        )
    )
    if existing is not None:
        return existing

    if book_name is None:
        book_name = get_book_name(db, book_id)
    verse_ref = VerseRef(
        book_id=book_id,
        chapter=chapter,
        verse=verse,
        reference=format_scripture_reference(book_name, chapter, verse),
    )
    db.add(verse_ref)
    db.flush()
    return verse_ref


def init_verse_refs_tables() -> None:
    VerseRef.__table__.create(bind=engine, checkfirst=True)

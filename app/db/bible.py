from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.bible import VERSE_TABLE_MODELS, BibleVersionKey, KeyEnglish, VerseMixin


@dataclass(frozen=True)
class BibleBook:
    id: int
    name: str
    testament: str
    chapter_count: int
    progress_percent: int
    last_chapter: int
    last_verse: int


@dataclass(frozen=True)
class BibleVerse:
    number: int
    text: str


@dataclass(frozen=True)
class GlobalVerse:
    book_id: int
    chapter: int
    verse: int
    text: str


def _normalize_verse_text(text: str) -> str:
    """Some translation tables store JSON-style escaped quotes (e.g. \\\")."""
    return text.replace('\\"', '"')


def get_verse_model(version_table: str) -> type[VerseMixin]:
    try:
        return VERSE_TABLE_MODELS[version_table]
    except KeyError as exc:
        raise ValueError(f"Invalid bible version table: {version_table}") from exc


def get_bible_version(db: Session, version_id: int) -> BibleVersionKey:
    version = db.get(BibleVersionKey, version_id)
    if version is None:
        raise ValueError(f"Bible version id {version_id} not found in bible_version_key")
    return version


def get_book_name(db: Session, book_id: int) -> str:
    book = db.get(KeyEnglish, book_id)
    return book.n if book else f"Book {book_id}"


def get_chapter_count(db: Session, version_table: str, book_id: int) -> int:
    verse_model = get_verse_model(version_table)
    chapter_count = db.scalar(
        select(func.max(verse_model.c)).where(verse_model.b == book_id)
    )
    return chapter_count or 0


def get_books(
    db: Session,
    version_table: str,
    progress: dict[int, object],
    testament_filter: str = "all",
) -> list[BibleBook]:
    verse_model = get_verse_model(version_table)
    rows = db.execute(
        select(KeyEnglish.b, KeyEnglish.n, func.max(verse_model.c))
        .join(verse_model, verse_model.b == KeyEnglish.b)
        .group_by(KeyEnglish.b, KeyEnglish.n)
        .order_by(KeyEnglish.b)
    ).all()

    books: list[BibleBook] = []
    for book_id, name, chapter_count in rows:
        testament = "Old" if book_id <= 39 else "New"
        if testament_filter == "old" and testament != "Old":
            continue
        if testament_filter == "new" and testament != "New":
            continue
        book_progress = progress.get(book_id)
        books.append(
            BibleBook(
                id=book_id,
                name=name,
                testament=testament,
                chapter_count=chapter_count,
                progress_percent=book_progress.percent if book_progress else 0,
                last_chapter=book_progress.last_chapter if book_progress else 1,
                last_verse=book_progress.last_verse if book_progress else 1,
            )
        )
    return books


def get_verse_text(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
    verse: int,
) -> str | None:
    verse_model = get_verse_model(version_table)
    row = db.scalars(
        select(verse_model)
        .where(
            verse_model.b == book_id,
            verse_model.c == chapter,
            verse_model.v == verse,
        )
        .limit(1)
    ).first()
    return _normalize_verse_text(row.t) if row else None


def get_chapter_verses(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
) -> list[BibleVerse]:
    verse_model = get_verse_model(version_table)
    rows = db.scalars(
        select(verse_model)
        .where(verse_model.b == book_id, verse_model.c == chapter)
        .order_by(verse_model.v)
    ).all()
    return [
        BibleVerse(number=row.v, text=_normalize_verse_text(row.t)) for row in rows
    ]


def get_verse_count_in_chapter(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
) -> int:
    verse_model = get_verse_model(version_table)
    count = db.scalar(
        select(func.count())
        .select_from(verse_model)
        .where(verse_model.b == book_id, verse_model.c == chapter)
    )
    return count or 0


def get_total_verse_count(db: Session, version_table: str) -> int:
    verse_model = get_verse_model(version_table)
    return db.scalar(select(func.count()).select_from(verse_model)) or 0


def get_verse_by_global_index(
    db: Session,
    version_table: str,
    index: int,
) -> GlobalVerse:
    verse_model = get_verse_model(version_table)
    row = db.scalars(
        select(verse_model)
        .order_by(verse_model.b, verse_model.c, verse_model.v)
        .offset(index)
        .limit(1)
    ).first()
    if row is None:
        raise ValueError(f"Verse index {index} out of range for {version_table}")
    return GlobalVerse(
        book_id=row.b,
        chapter=row.c,
        verse=row.v,
        text=_normalize_verse_text(row.t),
    )


def get_verse_of_day(db: Session, version_table: str) -> tuple[str, str]:
    """Return (text, reference) for today's verse.

    index = (year * 10000 + month * 100 + day) % total_verse_count
    """
    today = date.today()
    total = get_total_verse_count(db, version_table)
    if total == 0:
        raise ValueError(f"No verses found in {version_table}")

    index = (today.year * 10000 + today.month * 100 + today.day) % total
    verse = get_verse_by_global_index(db, version_table, index)
    book_name = get_book_name(db, verse.book_id)
    reference = f"{book_name} {verse.chapter}:{verse.verse}"
    return verse.text, reference

from dataclasses import dataclass

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.db.base import engine
from app.db.bible import get_total_verse_count, get_verse_counts_by_book
from app.db.models.reading import BookProgress, ReadingPosition
from app.db.notes import count_unique_noted_verses, get_noted_verse_counts_by_book

DEFAULT_POSITION = (45, 8, 1)


@dataclass(frozen=True)
class ReadingPositionData:
    book_id: int
    chapter: int
    verse: int


@dataclass(frozen=True)
class BookProgressData:
    percent: int
    last_chapter: int
    last_verse: int


def _migrate_book_progress_columns(db: Session) -> None:
    columns = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(book_progress)")).all()
    }
    if "last_chapter" not in columns:
        db.execute(
            text(
                "ALTER TABLE book_progress "
                "ADD COLUMN last_chapter INTEGER NOT NULL DEFAULT 1"
            )
        )
    if "last_verse" not in columns:
        db.execute(
            text(
                "ALTER TABLE book_progress "
                "ADD COLUMN last_verse INTEGER NOT NULL DEFAULT 1"
            )
        )


def init_reading_tables() -> None:
    ReadingPosition.__table__.create(bind=engine, checkfirst=True)
    BookProgress.__table__.create(bind=engine, checkfirst=True)

    with Session(engine) as db:
        _migrate_book_progress_columns(db)

        position = db.get(ReadingPosition, 1)
        if position is None:
            book_id, chapter, verse = DEFAULT_POSITION
            db.add(ReadingPosition(id=1, book_id=book_id, chapter=chapter, verse=verse))

        db.commit()


def get_reading_position(db: Session) -> ReadingPositionData:
    position = db.get(ReadingPosition, 1)
    if position is None:
        book_id, chapter, verse = DEFAULT_POSITION
        return ReadingPositionData(book_id, chapter, verse)
    return ReadingPositionData(
        book_id=position.book_id,
        chapter=position.chapter,
        verse=position.verse,
    )


def get_book_last_position(db: Session, book_id: int) -> tuple[int, int]:
    progress = db.get(BookProgress, book_id)
    if progress is None:
        return (1, 1)
    return (progress.last_chapter, progress.last_verse)


def set_reading_position(db: Session, book_id: int, chapter: int, verse: int) -> None:
    position = db.get(ReadingPosition, 1)
    if position is None:
        db.add(ReadingPosition(id=1, book_id=book_id, chapter=chapter, verse=verse))
    else:
        position.book_id = book_id
        position.chapter = chapter
        position.verse = verse
    db.commit()


def _noted_percent(noted: int, total: int) -> int:
    if total <= 0 or noted <= 0:
        return 0
    return min(100, max(1, round((noted / total) * 100)))


def calculate_book_progress(
    db: Session,
    version_table: str,
    book_id: int,
) -> int:
    totals = get_verse_counts_by_book(db, version_table)
    noted = get_noted_verse_counts_by_book(db)
    return _noted_percent(noted.get(book_id, 0), totals.get(book_id, 0))


def save_reading_progress(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
    verse: int,
) -> int:
    """Save reading position; progress percent comes from noted verses."""
    position = db.get(ReadingPosition, 1)
    if position is None:
        db.add(ReadingPosition(id=1, book_id=book_id, chapter=chapter, verse=verse))
    else:
        position.book_id = book_id
        position.chapter = chapter
        position.verse = verse

    progress = db.get(BookProgress, book_id)
    if progress is None:
        db.add(
            BookProgress(
                book_id=book_id,
                percent=0,
                last_chapter=chapter,
                last_verse=verse,
            )
        )
    else:
        progress.last_chapter = chapter
        progress.last_verse = verse

    db.commit()
    return calculate_book_progress(db, version_table, book_id)


def get_all_book_progress(
    db: Session,
    version_table: str,
) -> dict[int, BookProgressData]:
    rows = db.scalars(select(BookProgress)).all()
    last_positions = {
        row.book_id: (row.last_chapter, row.last_verse) for row in rows
    }
    totals = get_verse_counts_by_book(db, version_table)
    noted = get_noted_verse_counts_by_book(db)

    book_ids = set(totals) | set(last_positions) | set(noted)
    return {
        book_id: BookProgressData(
            percent=_noted_percent(noted.get(book_id, 0), totals.get(book_id, 0)),
            last_chapter=last_positions.get(book_id, (1, 1))[0],
            last_verse=last_positions.get(book_id, (1, 1))[1],
        )
        for book_id in book_ids
    }


def get_book_progress(db: Session, version_table: str) -> dict[int, int]:
    return {
        book_id: data.percent
        for book_id, data in get_all_book_progress(db, version_table).items()
    }


def get_overall_progress_percent(db: Session, version_table: str) -> int:
    total = get_total_verse_count(db, version_table)
    noted = count_unique_noted_verses(db)
    return _noted_percent(noted, total)


def reset_reading(db: Session) -> None:
    db.execute(delete(BookProgress))
    position = db.get(ReadingPosition, 1)
    if position is None:
        db.add(ReadingPosition(id=1, book_id=1, chapter=1, verse=1))
    else:
        position.book_id = 1
        position.chapter = 1
        position.verse = 1
    db.commit()

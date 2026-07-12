from dataclasses import dataclass

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.db.base import engine
from app.db.bible import get_chapter_count, get_verse_count_in_chapter
from app.db.models.reading import BookProgress, ReadingPosition

DEFAULT_POSITION = (45, 8, 1)

SAMPLE_PROGRESS: dict[int, int] = {
    1: 100,
    2: 72,
    19: 45,
    40: 100,
    44: 60,
    66: 0,
}


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

        progress_count = db.scalar(select(func.count()).select_from(BookProgress)) or 0
        if progress_count == 0:
            db.add_all(
                BookProgress(book_id=book_id, percent=percent)
                for book_id, percent in SAMPLE_PROGRESS.items()
            )
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


def calculate_book_progress(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
    verse: int,
) -> int:
    chapter_count = get_chapter_count(db, version_table, book_id)
    if chapter_count == 0:
        return 0

    verses_in_chapter = get_verse_count_in_chapter(
        db, version_table, book_id, chapter
    )
    if verses_in_chapter == 0:
        verses_in_chapter = 1

    progress_ratio = ((chapter - 1) + verse / verses_in_chapter) / chapter_count
    return min(100, round(progress_ratio * 100))


def save_reading_progress(
    db: Session,
    version_table: str,
    book_id: int,
    chapter: int,
    verse: int,
) -> int:
    position = db.get(ReadingPosition, 1)
    if position is None:
        db.add(ReadingPosition(id=1, book_id=book_id, chapter=chapter, verse=verse))
    else:
        position.book_id = book_id
        position.chapter = chapter
        position.verse = verse

    percent = calculate_book_progress(db, version_table, book_id, chapter, verse)
    progress = db.get(BookProgress, book_id)
    if progress is None:
        db.add(
            BookProgress(
                book_id=book_id,
                percent=percent,
                last_chapter=chapter,
                last_verse=verse,
            )
        )
    else:
        progress.percent = percent
        progress.last_chapter = chapter
        progress.last_verse = verse

    db.commit()
    return percent


def get_all_book_progress(db: Session) -> dict[int, BookProgressData]:
    rows = db.scalars(select(BookProgress)).all()
    return {
        row.book_id: BookProgressData(
            percent=row.percent,
            last_chapter=row.last_chapter,
            last_verse=row.last_verse,
        )
        for row in rows
    }


def get_book_progress(db: Session) -> dict[int, int]:
    return {book_id: data.percent for book_id, data in get_all_book_progress(db).items()}


def get_overall_progress_percent(db: Session) -> int:
    progress = get_book_progress(db)
    total = sum(progress.get(book_id, 0) for book_id in range(1, 67))
    return round(total / 66)


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

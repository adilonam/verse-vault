from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.db.bible import get_bible_version
from app.db.reading import save_reading_progress
from app.web.schemas.reading import ReadingPositionResponse, ReadingPositionUpdate

router = APIRouter(prefix="/api/reading", tags=["reading"])


@router.post("/position", response_model=ReadingPositionResponse)
def update_reading_position(
    payload: ReadingPositionUpdate,
    db: Session = Depends(get_db),
) -> ReadingPositionResponse:
    bible_version = get_bible_version(db, settings.bible_version_id)
    book_progress_percent = save_reading_progress(
        db,
        bible_version.table,
        payload.book_id,
        payload.chapter,
        payload.verse,
    )
    return ReadingPositionResponse(
        book_id=payload.book_id,
        chapter=payload.chapter,
        verse=payload.verse,
        book_progress_percent=book_progress_percent,
    )

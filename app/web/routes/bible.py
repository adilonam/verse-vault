from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.bible import get_book_name, get_verse_text
from app.db.settings import get_active_bible_version
from app.web.schemas.bible import VerseLookupResponse

router = APIRouter(prefix="/api/bible", tags=["bible"])


@router.get("/verse", response_model=VerseLookupResponse)
def lookup_verse(
    book: int = Query(ge=1, le=66),
    chapter: int = Query(ge=1),
    verse: int = Query(ge=1),
    db: Session = Depends(get_db),
) -> VerseLookupResponse:
    bible_version = get_active_bible_version(db)
    text = get_verse_text(db, bible_version.table, book, chapter, verse)
    if text is None:
        raise HTTPException(status_code=404, detail="Verse not found")

    book_name = get_book_name(db, book)
    return VerseLookupResponse(
        text=text,
        reference=f"{book_name} {chapter}:{verse}",
        version=bible_version.abbreviation,
        book_id=book,
        chapter=chapter,
        verse=verse,
    )

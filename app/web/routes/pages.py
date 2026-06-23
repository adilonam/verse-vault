from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.db.bible import (
    get_bible_version,
    get_book_name,
    get_books,
    get_chapter_count,
    get_chapter_verses,
)
from app.db.reading import (
    get_all_book_progress,
    get_book_last_position,
    get_overall_progress_percent,
    get_reading_position,
    reset_reading,
    set_reading_position,
)
from app.web.content.home import build_home_page

router = APIRouter()
templates = Jinja2Templates(directory=settings.templates_dir)

CHAPTER_SECTIONS: dict[tuple[int, int], str] = {
    (45, 8): "Life Through the Spirit",
}


def _bible_version_or_500(db: Session):
    try:
        return get_bible_version(db, settings.bible_version_id)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    position = get_reading_position(db)
    book_name = get_book_name(db, position.book_id)
    progress_percent = get_overall_progress_percent(db)

    page = build_home_page(
        bible_version=bible_version,
        continue_book=book_name,
        continue_chapter=position.chapter,
        continue_verse=position.verse,
        progress_percent=progress_percent,
    )

    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"page": page, "bible_version": bible_version},
    )


@router.post("/reset-reading", name="reset_reading")
async def reset_reading_status(db: Session = Depends(get_db)) -> RedirectResponse:
    reset_reading(db)
    return RedirectResponse(url="/", status_code=303)


@router.get("/bible", response_class=HTMLResponse, name="bible")
async def bible(
    request: Request,
    db: Session = Depends(get_db),
    testament: str = "all",
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    if testament not in {"all", "old", "new"}:
        testament = "all"

    progress = get_all_book_progress(db)
    books = get_books(
        db,
        bible_version.table,
        progress,
        testament_filter=testament,
    )

    return templates.TemplateResponse(
        request,
        "pages/bible.html",
        {
            "bible_version": bible_version,
            "books": books,
            "testament": testament,
        },
    )


@router.get("/continue", response_class=HTMLResponse, name="continue_reading")
async def continue_reading(
    request: Request,
    db: Session = Depends(get_db),
    book: int | None = None,
    chapter: int | None = None,
    verse: int | None = None,
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    position = get_reading_position(db)

    if book is None and chapter is None:
        book_id = position.book_id
        chapter_num = position.chapter
        current_verse = position.verse
    else:
        book_id = book if book is not None else position.book_id
        saved_chapter, saved_verse = get_book_last_position(db, book_id)

        if chapter is None:
            chapter_num = saved_chapter
        else:
            chapter_num = chapter

        if verse is not None:
            current_verse = verse
        elif chapter is None or chapter_num == saved_chapter:
            current_verse = saved_verse
        else:
            current_verse = 1

        set_reading_position(db, book_id, chapter_num, current_verse)

    book_name = get_book_name(db, book_id)
    verses = get_chapter_verses(
        db,
        bible_version.table,
        book_id,
        chapter_num,
    )
    if not verses:
        raise HTTPException(status_code=404, detail="Chapter not found")

    chapter_count = get_chapter_count(
        db,
        bible_version.table,
        book_id,
    )

    return templates.TemplateResponse(
        request,
        "pages/continue.html",
        {
            "bible_version": bible_version,
            "book_id": book_id,
            "book_name": book_name,
            "chapter": chapter_num,
            "verses": verses,
            "current_verse": current_verse,
            "section_title": CHAPTER_SECTIONS.get((book_id, chapter_num)),
            "prev_chapter": chapter_num - 1 if chapter_num > 1 else None,
            "next_chapter": chapter_num + 1 if chapter_num < chapter_count else None,
        },
    )

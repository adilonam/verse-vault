from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.db.bible import (
    book_exists,
    get_book_name,
    get_books,
    get_chapter_count,
    get_chapter_verses,
)
from app.db.models.bible import KeyEnglish
from app.db.collections import (
    COLLECTION_COLORS,
    create_collection,
    get_collection_count,
    get_collection_detail,
    get_collections,
)
from app.db.notes import get_note_by_id, get_note_count, get_notes
from app.db.reading import (
    get_all_book_progress,
    get_book_last_position,
    get_overall_progress_percent,
    get_reading_position,
    reset_reading,
    save_reading_progress,
)
from app.db.settings import get_active_bible_version
from app.web.content.home import build_home_page

router = APIRouter()
templates = Jinja2Templates(directory=settings.templates_dir)

CHAPTER_SECTIONS: dict[tuple[int, int], str] = {
    (45, 8): "Life Through the Spirit",
}

COLLECTION_COLOR_OPTIONS = [
    {"id": "gold", "label": "Gold"},
    {"id": "sage", "label": "Sage"},
    {"id": "rose", "label": "Rose"},
    {"id": "steel", "label": "Steel"},
    {"id": "amber", "label": "Amber"},
    {"id": "muted", "label": "Muted"},
]


def _bible_version_or_500(db: Session):
    try:
        return get_active_bible_version(db)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    position = get_reading_position(db)
    book_name = get_book_name(db, position.book_id)
    progress_percent = get_overall_progress_percent(db, bible_version.table)

    page = build_home_page(
        db=db,
        bible_version=bible_version,
        continue_book=book_name,
        continue_chapter=position.chapter,
        continue_verse=position.verse,
        progress_percent=progress_percent,
        note_count=get_note_count(db),
        collection_count=get_collection_count(db),
    )

    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"page": page},
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

    progress = get_all_book_progress(db, bible_version.table)
    books = get_books(
        db,
        bible_version.table,
        progress,
        testament_filter=testament,
    )
    search_books = get_books(
        db,
        bible_version.table,
        progress,
        testament_filter="all",
    )

    return templates.TemplateResponse(
        request,
        "pages/bible.html",
        {
            "bible_version": bible_version,
            "books": books,
            "search_books": [
                {"id": book.id, "name": book.name} for book in search_books
            ],
            "testament": testament,
        },
    )


@router.get("/bible/{book_id}", response_class=HTMLResponse, name="bible_chapters")
async def bible_chapters(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    book_row = db.get(KeyEnglish, book_id)
    if book_row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    chapter_count = get_chapter_count(db, bible_version.table, book_id)
    if chapter_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    return templates.TemplateResponse(
        request,
        "pages/bible_chapters.html",
        {
            "bible_version": bible_version,
            "book_id": book_id,
            "book_name": book_row.n,
            "chapter_count": chapter_count,
        },
    )


@router.get("/collections", response_class=HTMLResponse, name="collections")
async def collections_page(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    collections_list = get_collections(db)

    return templates.TemplateResponse(
        request,
        "pages/collections.html",
        {
            "bible_version": bible_version,
            "collections": collections_list,
            "collection_count": len(collections_list),
        },
    )


COLLECTION_COLOR_OPTIONS = [
    {"id": "gold", "label": "Gold"},
    {"id": "sage", "label": "Sage"},
    {"id": "rose", "label": "Rose"},
    {"id": "steel", "label": "Steel"},
    {"id": "amber", "label": "Amber"},
    {"id": "muted", "label": "Muted"},
]


def _empty_collection_form() -> dict[str, object]:
    return {
        "name": "",
        "description": "",
        "color": "gold",
        "verse_refs": [],
    }


@router.get("/collections/new", response_class=HTMLResponse, name="collection_new")
async def collection_new(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)

    return templates.TemplateResponse(
        request,
        "pages/collection_new.html",
        {
            "bible_version": bible_version,
            "colors": COLLECTION_COLOR_OPTIONS,
            "form": _empty_collection_form(),
        },
    )


@router.post(
    "/collections/new",
    name="collection_create",
    response_model=None,
)
async def collection_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("gold"),
    verse_refs: list[str] = Form(default=[]),
):
    cleaned_name = name.strip()
    if not cleaned_name:
        bible_version = _bible_version_or_500(db)
        return templates.TemplateResponse(
            request,
            "pages/collection_new.html",
            {
                "bible_version": bible_version,
                "colors": COLLECTION_COLOR_OPTIONS,
                "form": {
                    "name": name,
                    "description": description,
                    "color": color if color in COLLECTION_COLORS else "gold",
                    "verse_refs": verse_refs,
                },
            },
            status_code=400,
        )

    create_collection(
        db,
        name=cleaned_name,
        description=description,
        color=color,
        verse_refs=verse_refs,
    )
    return RedirectResponse(url="/collections", status_code=303)


@router.get(
    "/collections/{collection_id}",
    response_class=HTMLResponse,
    name="collection_detail",
)
async def collection_detail(
    request: Request,
    collection_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    collection = get_collection_detail(db, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    return templates.TemplateResponse(
        request,
        "pages/collection_detail.html",
        {
            "bible_version": bible_version,
            "collection": collection,
            "colors": COLLECTION_COLOR_OPTIONS,
        },
    )


@router.get("/notes", response_class=HTMLResponse, name="notes")
async def notes(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    notes_list = get_notes(db)

    return templates.TemplateResponse(
        request,
        "pages/notes.html",
        {
            "bible_version": bible_version,
            "notes": notes_list,
            "note_count": len(notes_list),
        },
    )


@router.get(
    "/notes/{note_id}",
    response_class=HTMLResponse,
    name="note_detail",
)
async def note_detail(
    request: Request,
    note_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    bible_version = _bible_version_or_500(db)
    note = get_note_by_id(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return templates.TemplateResponse(
        request,
        "pages/note_detail.html",
        {
            "bible_version": bible_version,
            "note": note,
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

    save_reading_progress(
        db,
        bible_version.table,
        book_id,
        chapter_num,
        current_verse,
    )

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

    if chapter_num > 1:
        prev_book = book_id
        prev_chapter = chapter_num - 1
    elif book_id > 1 and book_exists(db, book_id - 1):
        prev_book = book_id - 1
        prev_chapter = get_chapter_count(
            db,
            bible_version.table,
            prev_book,
        )
    else:
        prev_book = None
        prev_chapter = None

    if chapter_num < chapter_count:
        next_book = book_id
        next_chapter = chapter_num + 1
    elif book_exists(db, book_id + 1):
        next_book = book_id + 1
        next_chapter = 1
    else:
        next_book = None
        next_chapter = None

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
            "prev_book": prev_book,
            "prev_chapter": prev_chapter,
            "next_book": next_book,
            "next_chapter": next_chapter,
        },
    )

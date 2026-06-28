from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.bible import get_book_name
from app.db.collections import (
    add_note_to_collection,
    add_verse_to_collection,
    get_collection_detail,
    get_collection_list,
    link_note_to_collection,
    remove_note_from_collection,
    remove_verse_from_collection,
    update_collection,
)
from app.db.verse_refs import parse_reference_string
from app.web.schemas.collections import (
    CollectionDetailResponse,
    CollectionListItem,
    CollectionNoteAdd,
    CollectionNoteResponse,
    CollectionUpdate,
    CollectionVerseAdd,
    CollectionVerseRefResponse,
)

router = APIRouter(prefix="/api/collections", tags=["collections"])


def _to_detail_response(detail) -> CollectionDetailResponse:
    return CollectionDetailResponse(
        id=detail.id,
        name=detail.name,
        description=detail.description,
        color=detail.color,
        verse_count=detail.verse_count,
        verse_refs=[
            CollectionVerseRefResponse(
                verse_ref_id=ref.verse_ref_id,
                reference=ref.reference,
                book_id=ref.book_id,
                chapter=ref.chapter,
                verse=ref.verse,
            )
            for ref in detail.verse_refs
        ],
        notes=[
            CollectionNoteResponse(
                id=note.id,
                title=note.title,
                body_preview=note.body_preview,
                scripture_reference=note.scripture_reference,
                book_id=note.book_id,
                chapter=note.chapter,
                verse=note.verse,
                created_at=note.created_at,
                date_label=note.date_label,
            )
            for note in detail.notes
        ],
    )


def _to_note_response(note) -> CollectionNoteResponse:
    return CollectionNoteResponse(
        id=note.id,
        title=note.title,
        body_preview=note.body_preview,
        scripture_reference=note.scripture_reference,
        book_id=note.book_id,
        chapter=note.chapter,
        verse=note.verse,
        created_at=note.created_at,
        date_label=note.date_label,
    )


def _to_verse_response(verse_ref) -> CollectionVerseRefResponse:
    return CollectionVerseRefResponse(
        verse_ref_id=verse_ref.verse_ref_id,
        reference=verse_ref.reference,
        book_id=verse_ref.book_id,
        chapter=verse_ref.chapter,
        verse=verse_ref.verse,
    )


@router.get("", response_model=list[CollectionListItem])
def list_collections(db: Session = Depends(get_db)) -> list[CollectionListItem]:
    items = get_collection_list(db)
    return [
        CollectionListItem(
            id=item.id,
            name=item.name,
            verse_count=item.verse_count,
        )
        for item in items
    ]


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
) -> CollectionDetailResponse:
    detail = get_collection_detail(db, collection_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _to_detail_response(detail)


@router.patch("/{collection_id}", response_model=CollectionDetailResponse)
def patch_collection(
    collection_id: int,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
) -> CollectionDetailResponse:
    try:
        detail = update_collection(
            db,
            collection_id,
            name=payload.name,
            description=payload.description,
            color=payload.color,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if detail is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _to_detail_response(detail)


@router.post("/{collection_id}/verses", response_model=CollectionVerseRefResponse)
def add_collection_verse(
    collection_id: int,
    payload: CollectionVerseAdd,
    db: Session = Depends(get_db),
) -> CollectionVerseRefResponse:
    book_name = None
    if payload.book_id is not None:
        book_name = get_book_name(db, payload.book_id)

    try:
        verse_ref = add_verse_to_collection(
            db,
            collection_id,
            book_id=payload.book_id,
            chapter=payload.chapter,
            verse=payload.verse,
            reference=payload.reference,
            book_name=book_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if verse_ref is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _to_verse_response(verse_ref)


@router.delete("/{collection_id}/verses/{verse_ref_id}", status_code=204)
def delete_collection_verse(
    collection_id: int,
    verse_ref_id: int,
    db: Session = Depends(get_db),
) -> None:
    if not remove_verse_from_collection(db, collection_id, verse_ref_id):
        raise HTTPException(status_code=404, detail="Verse not found in collection")


@router.post("/{collection_id}/notes", response_model=CollectionNoteResponse)
def add_collection_note(
    collection_id: int,
    payload: CollectionNoteAdd,
    db: Session = Depends(get_db),
) -> CollectionNoteResponse:
    if payload.note_id is not None:
        note = link_note_to_collection(db, collection_id, payload.note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Collection or note not found")
        return _to_note_response(note)

    book_id = payload.book_id
    chapter = payload.chapter
    verse = payload.verse
    if payload.reference is not None:
        parsed = parse_reference_string(db, payload.reference)
        if parsed is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid verse reference: {payload.reference}",
            )
        book_id, chapter, verse = parsed

    if book_id is None or chapter is None or verse is None:
        raise HTTPException(
            status_code=400,
            detail="Provide note_id or book_id, chapter, and verse",
        )

    book_name = get_book_name(db, book_id)
    try:
        note = add_note_to_collection(
            db,
            book_id=book_id,
            chapter=chapter,
            verse=verse,
            title=payload.title,
            body=payload.body,
            collection_id=collection_id,
            book_name=book_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    linked = link_note_to_collection(db, collection_id, note.id)
    assert linked is not None
    return _to_note_response(linked)


@router.delete("/{collection_id}/notes/{note_id}", status_code=204)
def delete_collection_note(
    collection_id: int,
    note_id: int,
    db: Session = Depends(get_db),
) -> None:
    if not remove_note_from_collection(db, collection_id, note_id):
        raise HTTPException(status_code=404, detail="Note not found in collection")

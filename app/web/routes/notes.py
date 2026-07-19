import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.bible import get_book_name
from app.db.collections import add_note_to_collection
from app.db.notes import (
    NOTE_CSV_HEADERS,
    count_notes_by_title_and_body,
    delete_note_by_id,
    delete_note_for_passage,
    delete_notes_by_title_and_body,
    get_note_by_id,
    get_note_for_passage,
    get_notes,
    import_notes_from_rows,
    update_note,
    upsert_note,
)
from app.web.schemas.notes import (
    NoteAddToCollection,
    NoteDetailResponse,
    NoteImportResponse,
    NoteMatchBody,
    NoteMatchCountResponse,
    NoteMatchDeleteResponse,
    NoteResponse,
    NoteUpdate,
    NoteUpsert,
)

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _to_response(note) -> NoteResponse:
    return NoteResponse(
        id=note.id,
        title=note.title,
        body=note.body,
        scripture_reference=note.scripture_reference,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _to_detail_response(note) -> NoteDetailResponse:
    return NoteDetailResponse(
        id=note.id,
        title=note.title,
        body=note.body,
        scripture_reference=note.scripture_reference,
        book_id=note.book_id,
        chapter=note.chapter,
        verse=note.verse,
        created_at=note.created_at,
        updated_at=note.updated_at,
        date_label=note.date_label,
    )


@router.get("/passage", response_model=NoteResponse | None)
def get_note_for_passage_endpoint(
    book: int = Query(ge=1, le=66),
    chapter: int = Query(ge=1),
    verse: int = Query(ge=1),
    db: Session = Depends(get_db),
) -> NoteResponse | None:
    book_name = get_book_name(db, book)
    note = get_note_for_passage(db, book_name, chapter, verse)
    if note is None:
        return None
    return _to_response(note)


@router.post("", response_model=NoteResponse)
def save_note(
    payload: NoteUpsert,
    db: Session = Depends(get_db),
) -> NoteResponse:
    book_name = get_book_name(db, payload.book_id)
    note = upsert_note(
        db,
        payload.title,
        payload.body,
        payload.book_id,
        payload.chapter,
        payload.verse,
        book_name=book_name,
    )
    return _to_response(note)


@router.post("/add-to-collection", response_model=NoteResponse)
def add_note_to_collection_endpoint(
    payload: NoteAddToCollection,
    db: Session = Depends(get_db),
) -> NoteResponse:
    book_name = get_book_name(db, payload.book_id)
    try:
        note = add_note_to_collection(
            db,
            book_id=payload.book_id,
            chapter=payload.chapter,
            verse=payload.verse,
            title=payload.title,
            body=payload.body,
            collection_id=payload.collection_id,
            book_name=book_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(note)


@router.delete("/passage", status_code=204)
def delete_note_for_passage_endpoint(
    book: int = Query(ge=1, le=66),
    chapter: int = Query(ge=1),
    verse: int = Query(ge=1),
    db: Session = Depends(get_db),
) -> None:
    book_name = get_book_name(db, book)
    if not delete_note_for_passage(db, book_name, chapter, verse):
        raise HTTPException(status_code=404, detail="Note not found")


@router.get("/export")
def export_notes_csv(
    db: Session = Depends(get_db),
) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=NOTE_CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for note in get_notes(db):
        writer.writerow(
            {
                "title": note.title,
                "body": note.body,
                "scripture_reference": note.scripture_reference,
                "book_id": note.book_id if note.book_id is not None else "",
                "chapter": note.chapter if note.chapter is not None else "",
                "verse": note.verse if note.verse is not None else "",
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            }
        )
    buffer.seek(0)
    filename = f"verse-vault-notes-{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=NoteImportResponse)
async def import_notes_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> NoteImportResponse:
    filename = (file.filename or "").lower()
    if filename and not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded",
        ) from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV has no header row")

    normalized_headers = {
        (name or "").strip().lower(): name for name in reader.fieldnames
    }
    required = {"title", "body", "scripture_reference"}
    missing = required - set(normalized_headers)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
        )

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        row = {
            key: (raw_row.get(normalized_headers.get(key, key)) or "").strip()
            for key in NOTE_CSV_HEADERS
        }
        if not any(row.values()):
            continue
        rows.append(row)

    result = import_notes_from_rows(db, rows)
    return NoteImportResponse(
        added=result.added,
        skipped=result.skipped,
        errors=result.errors,
    )


@router.get("/matching-count", response_model=NoteMatchCountResponse)
def count_matching_notes_endpoint(
    title: str = "",
    body: str = "",
    db: Session = Depends(get_db),
) -> NoteMatchCountResponse:
    count = count_notes_by_title_and_body(db, title, body)
    return NoteMatchCountResponse(count=count)


@router.delete("/matching", response_model=NoteMatchDeleteResponse)
def delete_matching_notes_endpoint(
    payload: NoteMatchBody,
    db: Session = Depends(get_db),
) -> NoteMatchDeleteResponse:
    deleted = delete_notes_by_title_and_body(db, payload.title, payload.body)
    if not deleted:
        raise HTTPException(status_code=404, detail="No matching notes found")
    return NoteMatchDeleteResponse(deleted=deleted)


@router.patch("/{note_id}", response_model=NoteDetailResponse)
def update_note_endpoint(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
) -> NoteDetailResponse:
    try:
        note = update_note(
            db,
            note_id,
            title=payload.title,
            body=payload.body,
            reference=payload.reference,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return _to_detail_response(note)


@router.delete("/{note_id}", status_code=204)
def delete_note_by_id_endpoint(
    note_id: int,
    db: Session = Depends(get_db),
) -> None:
    if not delete_note_by_id(db, note_id):
        raise HTTPException(status_code=404, detail="Note not found")

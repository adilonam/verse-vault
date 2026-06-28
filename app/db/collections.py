from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.db.base import engine
from app.db.models.collections import Collection, CollectionNote, CollectionVerseRef
from app.db.models.notes import Note
from app.db.notes import upsert_note
from app.db.verse_refs import get_or_create_verse_ref, parse_reference_string

SAMPLE_COLLECTIONS: list[dict[str, object]] = [
    {
        "name": "Promises of God",
        "description": (
            "Verses affirming God's faithfulness and covenant promises throughout Scripture."
        ),
        "color": "gold",
        "verse_refs": ["Jeremiah 29:11", "Numbers 23:19", "Deuteronomy 7:9"],
        "created_at": datetime(2026, 6, 20),
        "updated_at": datetime(2026, 6, 20),
    },
    {
        "name": "Morning Meditations",
        "description": (
            "A curated set for quiet time and reflection at the start of each day."
        ),
        "color": "sage",
        "verse_refs": ["Psalms 5:3", "Psalms 143:8", "Lamentations 3:22"],
        "created_at": datetime(2026, 6, 18),
        "updated_at": datetime(2026, 6, 18),
    },
    {
        "name": "Faith & Trust",
        "description": "Scriptures on trusting God through trials and uncertainty.",
        "color": "rose",
        "verse_refs": ["Proverbs 3:5", "Isaiah 41:10", "Psalms 46:10"],
        "created_at": datetime(2026, 6, 15),
        "updated_at": datetime(2026, 6, 15),
    },
]

COLLECTION_COLORS = ("gold", "sage", "rose", "steel", "amber", "muted")


@dataclass(frozen=True)
class CollectionData:
    id: int
    name: str
    description: str
    color: str
    verse_count: int
    verse_refs: list[str]
    created_at: datetime


@dataclass(frozen=True)
class CollectionListItem:
    id: int
    name: str
    verse_count: int


@dataclass(frozen=True)
class CollectionVerseRefDetail:
    verse_ref_id: int
    reference: str
    book_id: int
    chapter: int
    verse: int


@dataclass(frozen=True)
class CollectionNoteDetail:
    id: int
    title: str
    body_preview: str
    scripture_reference: str
    book_id: int | None
    chapter: int | None
    verse: int | None
    created_at: datetime
    date_label: str


@dataclass(frozen=True)
class CollectionDetail:
    id: int
    name: str
    description: str
    color: str
    verse_count: int
    verse_refs: list[CollectionVerseRefDetail]
    notes: list[CollectionNoteDetail]


def _body_preview(body: str, limit: int = 200) -> str:
    if len(body) <= limit:
        return body
    return body[: limit - 3].rstrip() + "..."


def _verse_ref_display_strings(collection: Collection) -> list[str]:
    return [link.verse_ref.reference for link in collection.verse_refs]


def _to_collection_data(collection: Collection) -> CollectionData:
    return CollectionData(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        color=collection.color,
        verse_count=collection.verse_count,
        verse_refs=_verse_ref_display_strings(collection),
        created_at=collection.created_at,
    )


def _recalculate_verse_count(db: Session, collection_id: int) -> None:
    db.flush()
    count = db.scalar(
        select(func.count())
        .select_from(CollectionVerseRef)
        .where(CollectionVerseRef.collection_id == collection_id)
    ) or 0
    collection = db.get(Collection, collection_id)
    if collection is not None:
        collection.verse_count = count


def _migrate_collection_verse_refs(db: Session) -> None:
    table_exists = db.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='collection_verse_refs'"
        )
    ).first()
    if table_exists is None:
        return

    columns = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(collection_verse_refs)")).all()
    }
    if "reference" not in columns or "verse_ref_id" in columns:
        return

    rows = db.execute(
        text("SELECT id, collection_id, reference FROM collection_verse_refs")
    ).all()
    db.execute(text("DROP TABLE collection_verse_refs"))
    CollectionVerseRef.__table__.create(bind=engine)

    seen: set[tuple[int, int]] = set()
    for _row_id, collection_id, reference in rows:
        parsed = parse_reference_string(db, reference)
        if parsed is None:
            continue
        book_id, chapter, verse = parsed
        verse_ref = get_or_create_verse_ref(db, book_id, chapter, verse)
        key = (collection_id, verse_ref.id)
        if key in seen:
            continue
        seen.add(key)
        db.add(
            CollectionVerseRef(
                collection_id=collection_id,
                verse_ref_id=verse_ref.id,
            )
        )

    collection_ids = db.scalars(select(Collection.id)).all()
    for collection_id in collection_ids:
        _recalculate_verse_count(db, collection_id)


def _link_verse_ref_strings(
    db: Session,
    collection_id: int,
    references: list[str],
) -> int:
    linked = 0
    seen: set[int] = set()
    for reference in references:
        cleaned = reference.strip()
        if not cleaned:
            continue
        parsed = parse_reference_string(db, cleaned)
        if parsed is None:
            continue
        book_id, chapter, verse = parsed
        verse_ref = get_or_create_verse_ref(db, book_id, chapter, verse)
        if verse_ref.id in seen:
            continue
        seen.add(verse_ref.id)
        existing = db.scalar(
            select(CollectionVerseRef).where(
                CollectionVerseRef.collection_id == collection_id,
                CollectionVerseRef.verse_ref_id == verse_ref.id,
            )
        )
        if existing is not None:
            continue
        db.add(
            CollectionVerseRef(
                collection_id=collection_id,
                verse_ref_id=verse_ref.id,
            )
        )
        linked += 1
    return linked


def init_collections_tables() -> None:
    Collection.__table__.create(bind=engine, checkfirst=True)
    CollectionVerseRef.__table__.create(bind=engine, checkfirst=True)
    CollectionNote.__table__.create(bind=engine, checkfirst=True)

    with Session(engine) as db:
        _migrate_collection_verse_refs(db)

        collection_count = db.scalar(select(func.count()).select_from(Collection)) or 0
        if collection_count == 0:
            for item in SAMPLE_COLLECTIONS:
                refs = item["verse_refs"]  # type: ignore[assignment]
                collection = Collection(
                    name=str(item["name"]),
                    description=str(item["description"]),
                    color=str(item["color"]),
                    verse_count=0,
                    created_at=item["created_at"],  # type: ignore[arg-type]
                    updated_at=item["updated_at"],  # type: ignore[arg-type]
                )
                db.add(collection)
                db.flush()
                _link_verse_ref_strings(db, collection.id, list(refs))
                _recalculate_verse_count(db, collection.id)
        db.commit()


def get_collections(db: Session) -> list[CollectionData]:
    rows = db.scalars(
        select(Collection)
        .options(
            selectinload(Collection.verse_refs).selectinload(
                CollectionVerseRef.verse_ref
            )
        )
        .order_by(Collection.created_at.desc())
    ).all()
    return [_to_collection_data(row) for row in rows]


def get_collection_list(db: Session) -> list[CollectionListItem]:
    rows = db.scalars(select(Collection).order_by(Collection.name)).all()
    return [
        CollectionListItem(
            id=row.id,
            name=row.name,
            verse_count=row.verse_count,
        )
        for row in rows
    ]


def get_collection_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Collection)) or 0


def get_collection_detail(db: Session, collection_id: int) -> CollectionDetail | None:
    collection = db.scalar(
        select(Collection)
        .options(
            selectinload(Collection.verse_refs).selectinload(
                CollectionVerseRef.verse_ref
            ),
            selectinload(Collection.notes)
            .selectinload(CollectionNote.note)
            .selectinload(Note.verse_ref),
        )
        .where(Collection.id == collection_id)
    )
    if collection is None:
        return None

    verse_refs = [
        CollectionVerseRefDetail(
            verse_ref_id=link.verse_ref_id,
            reference=link.verse_ref.reference,
            book_id=link.verse_ref.book_id,
            chapter=link.verse_ref.chapter,
            verse=link.verse_ref.verse,
        )
        for link in collection.verse_refs
    ]

    notes = sorted(
        (
            CollectionNoteDetail(
                id=link.note.id,
                title=link.note.title,
                body_preview=_body_preview(link.note.body),
                scripture_reference=link.note.scripture_reference,
                book_id=link.note.verse_ref.book_id if link.note.verse_ref else None,
                chapter=link.note.verse_ref.chapter if link.note.verse_ref else None,
                verse=link.note.verse_ref.verse if link.note.verse_ref else None,
                created_at=link.note.created_at,
                date_label=link.note.created_at.strftime("%b %d, %Y"),
            )
            for link in collection.notes
        ),
        key=lambda note: note.created_at,
        reverse=True,
    )

    return CollectionDetail(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        color=collection.color,
        verse_count=collection.verse_count,
        verse_refs=verse_refs,
        notes=notes,
    )


def create_collection(
    db: Session,
    *,
    name: str,
    description: str,
    color: str,
    verse_refs: list[str],
) -> CollectionData:
    now = datetime.now()
    normalized_color = color if color in COLLECTION_COLORS else "gold"

    collection = Collection(
        name=name.strip(),
        description=description.strip(),
        color=normalized_color,
        verse_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(collection)
    db.flush()

    _link_verse_ref_strings(db, collection.id, verse_refs)
    _recalculate_verse_count(db, collection.id)

    db.commit()
    saved = db.scalar(
        select(Collection)
        .options(
            selectinload(Collection.verse_refs).selectinload(
                CollectionVerseRef.verse_ref
            )
        )
        .where(Collection.id == collection.id)
    )
    assert saved is not None
    return _to_collection_data(saved)


def add_note_to_collection(
    db: Session,
    *,
    book_id: int,
    chapter: int,
    verse: int,
    title: str,
    body: str,
    collection_id: int,
    book_name: str | None = None,
) -> Note:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise ValueError(f"Collection {collection_id} not found")

    note_data = upsert_note(
        db,
        title,
        body,
        book_id,
        chapter,
        verse,
        book_name=book_name,
    )
    note = db.get(Note, note_data.id)
    assert note is not None

    existing_note_link = db.scalar(
        select(CollectionNote).where(
            CollectionNote.collection_id == collection_id,
            CollectionNote.note_id == note.id,
        )
    )
    if existing_note_link is None:
        db.add(CollectionNote(collection_id=collection_id, note_id=note.id))

    verse_ref = get_or_create_verse_ref(
        db,
        book_id,
        chapter,
        verse,
        book_name=book_name,
    )
    existing_ref_link = db.scalar(
        select(CollectionVerseRef).where(
            CollectionVerseRef.collection_id == collection_id,
            CollectionVerseRef.verse_ref_id == verse_ref.id,
        )
    )
    if existing_ref_link is None:
        db.add(
            CollectionVerseRef(
                collection_id=collection_id,
                verse_ref_id=verse_ref.id,
            )
        )
        _recalculate_verse_count(db, collection_id)

    collection.updated_at = datetime.now()
    db.commit()
    db.refresh(note)
    return note


def update_collection(
    db: Session,
    collection_id: int,
    *,
    name: str,
    description: str,
    color: str,
) -> CollectionDetail | None:
    collection = db.get(Collection, collection_id)
    if collection is None:
        return None

    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValueError("Collection name is required")

    collection.name = cleaned_name
    collection.description = description.strip()
    collection.color = color if color in COLLECTION_COLORS else "gold"
    collection.updated_at = datetime.now()
    db.commit()
    return get_collection_detail(db, collection_id)


def add_verse_to_collection(
    db: Session,
    collection_id: int,
    *,
    book_id: int | None = None,
    chapter: int | None = None,
    verse: int | None = None,
    reference: str | None = None,
    book_name: str | None = None,
) -> CollectionVerseRefDetail | None:
    collection = db.get(Collection, collection_id)
    if collection is None:
        return None

    if reference is not None:
        parsed = parse_reference_string(db, reference)
        if parsed is None:
            raise ValueError(f"Invalid verse reference: {reference}")
        book_id, chapter, verse = parsed

    if book_id is None or chapter is None or verse is None:
        raise ValueError("book_id, chapter, and verse are required")

    verse_ref = get_or_create_verse_ref(
        db,
        book_id,
        chapter,
        verse,
        book_name=book_name,
    )
    existing = db.scalar(
        select(CollectionVerseRef).where(
            CollectionVerseRef.collection_id == collection_id,
            CollectionVerseRef.verse_ref_id == verse_ref.id,
        )
    )
    if existing is None:
        db.add(
            CollectionVerseRef(
                collection_id=collection_id,
                verse_ref_id=verse_ref.id,
            )
        )
        _recalculate_verse_count(db, collection_id)
        collection.updated_at = datetime.now()
        db.commit()

    return CollectionVerseRefDetail(
        verse_ref_id=verse_ref.id,
        reference=verse_ref.reference,
        book_id=verse_ref.book_id,
        chapter=verse_ref.chapter,
        verse=verse_ref.verse,
    )


def remove_verse_from_collection(
    db: Session,
    collection_id: int,
    verse_ref_id: int,
) -> bool:
    link = db.scalar(
        select(CollectionVerseRef).where(
            CollectionVerseRef.collection_id == collection_id,
            CollectionVerseRef.verse_ref_id == verse_ref_id,
        )
    )
    if link is None:
        return False

    db.delete(link)
    _recalculate_verse_count(db, collection_id)
    collection = db.get(Collection, collection_id)
    if collection is not None:
        collection.updated_at = datetime.now()
    db.commit()
    return True


def link_note_to_collection(
    db: Session,
    collection_id: int,
    note_id: int,
) -> CollectionNoteDetail | None:
    collection = db.get(Collection, collection_id)
    if collection is None:
        return None

    note = db.scalar(
        select(Note)
        .options(selectinload(Note.verse_ref))
        .where(Note.id == note_id)
    )
    if note is None:
        return None

    existing = db.scalar(
        select(CollectionNote).where(
            CollectionNote.collection_id == collection_id,
            CollectionNote.note_id == note_id,
        )
    )
    if existing is None:
        db.add(CollectionNote(collection_id=collection_id, note_id=note_id))
        collection.updated_at = datetime.now()
        db.commit()

    return CollectionNoteDetail(
        id=note.id,
        title=note.title,
        body_preview=_body_preview(note.body),
        scripture_reference=note.scripture_reference,
        book_id=note.verse_ref.book_id if note.verse_ref else None,
        chapter=note.verse_ref.chapter if note.verse_ref else None,
        verse=note.verse_ref.verse if note.verse_ref else None,
        created_at=note.created_at,
        date_label=note.created_at.strftime("%b %d, %Y"),
    )


def remove_note_from_collection(
    db: Session,
    collection_id: int,
    note_id: int,
) -> bool:
    link = db.scalar(
        select(CollectionNote).where(
            CollectionNote.collection_id == collection_id,
            CollectionNote.note_id == note_id,
        )
    )
    if link is None:
        return False

    db.delete(link)
    collection = db.get(Collection, collection_id)
    if collection is not None:
        collection.updated_at = datetime.now()
    db.commit()
    return True

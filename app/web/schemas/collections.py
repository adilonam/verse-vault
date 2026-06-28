from datetime import datetime

from pydantic import BaseModel, Field


class CollectionListItem(BaseModel):
    id: int
    name: str
    verse_count: int


class CollectionUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    color: str = "gold"


class CollectionVerseAdd(BaseModel):
    book_id: int | None = Field(default=None, ge=1, le=66)
    chapter: int | None = Field(default=None, ge=1)
    verse: int | None = Field(default=None, ge=1)
    reference: str | None = None


class CollectionVerseRefResponse(BaseModel):
    verse_ref_id: int
    reference: str
    book_id: int
    chapter: int
    verse: int


class CollectionNoteAdd(BaseModel):
    note_id: int | None = Field(default=None, ge=1)
    title: str = ""
    body: str = ""
    reference: str | None = None
    book_id: int | None = Field(default=None, ge=1, le=66)
    chapter: int | None = Field(default=None, ge=1)
    verse: int | None = Field(default=None, ge=1)


class CollectionNoteResponse(BaseModel):
    id: int
    title: str
    body_preview: str
    scripture_reference: str
    book_id: int | None
    chapter: int | None
    verse: int | None
    created_at: datetime
    date_label: str


class CollectionDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    color: str
    verse_count: int
    verse_refs: list[CollectionVerseRefResponse]
    notes: list[CollectionNoteResponse]

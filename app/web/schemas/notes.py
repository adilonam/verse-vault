from datetime import datetime

from pydantic import BaseModel, Field


class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    scripture_reference: str
    created_at: datetime
    updated_at: datetime


class NoteDetailResponse(NoteResponse):
    book_id: int | None = None
    chapter: int | None = None
    verse: int | None = None
    date_label: str = ""


class NoteUpdate(BaseModel):
    title: str = ""
    body: str = ""
    reference: str = ""


class NoteUpsert(BaseModel):
    title: str = ""
    body: str = ""
    book_id: int = Field(ge=1, le=66)
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)


class NoteAddToCollection(BaseModel):
    title: str = ""
    body: str = ""
    book_id: int = Field(ge=1, le=66)
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)
    collection_id: int = Field(ge=1)


class NoteMatchBody(BaseModel):
    title: str = ""
    body: str = ""


class NoteMatchCountResponse(BaseModel):
    count: int


class NoteMatchDeleteResponse(BaseModel):
    deleted: int


class NoteImportResponse(BaseModel):
    added: int
    skipped: int
    errors: int

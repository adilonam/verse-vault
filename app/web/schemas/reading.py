from pydantic import BaseModel, Field


class ReadingPositionUpdate(BaseModel):
    book_id: int = Field(ge=1, le=66)
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)


class ReadingPositionResponse(BaseModel):
    book_id: int
    chapter: int
    verse: int
    book_progress_percent: int

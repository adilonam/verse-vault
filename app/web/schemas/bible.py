from pydantic import BaseModel, Field


class VerseLookupResponse(BaseModel):
    text: str
    reference: str
    version: str
    book_id: int = Field(ge=1, le=66)
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)

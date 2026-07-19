from pydantic import BaseModel, Field


class BibleVersionOptionResponse(BaseModel):
    id: int
    abbreviation: str
    version: str


class AppSettingsResponse(BaseModel):
    bible_version_id: int
    versions: list[BibleVersionOptionResponse]


class BibleVersionUpdate(BaseModel):
    bible_version_id: int = Field(ge=1)


class BibleVersionUpdateResponse(BaseModel):
    bible_version_id: int

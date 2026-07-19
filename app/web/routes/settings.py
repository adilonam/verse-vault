from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.settings import (
    get_bible_version_id,
    list_bible_versions,
    set_bible_version_id,
)
from app.web.schemas.settings import (
    AppSettingsResponse,
    BibleVersionOptionResponse,
    BibleVersionUpdate,
    BibleVersionUpdateResponse,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings(db: Session = Depends(get_db)) -> AppSettingsResponse:
    versions = list_bible_versions(db)
    return AppSettingsResponse(
        bible_version_id=get_bible_version_id(db),
        versions=[
            BibleVersionOptionResponse(
                id=v.id,
                abbreviation=v.abbreviation,
                version=v.version,
            )
            for v in versions
        ],
    )


@router.post("/bible-version", response_model=BibleVersionUpdateResponse)
def update_bible_version(
    payload: BibleVersionUpdate,
    db: Session = Depends(get_db),
) -> BibleVersionUpdateResponse:
    try:
        set_bible_version_id(db, payload.bible_version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BibleVersionUpdateResponse(bible_version_id=payload.bible_version_id)

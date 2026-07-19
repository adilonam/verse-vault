from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import engine
from app.db.bible import get_bible_version
from app.db.models.bible import BibleVersionKey
from app.db.models.settings import DEFAULT_BIBLE_VERSION_ID, AppSettings


@dataclass(frozen=True)
class BibleVersionOption:
    id: int
    abbreviation: str
    version: str


def init_app_settings_table() -> None:
    AppSettings.__table__.create(bind=engine, checkfirst=True)

    with Session(engine) as db:
        row = db.get(AppSettings, 1)
        if row is None:
            db.add(
                AppSettings(id=1, bible_version_id=DEFAULT_BIBLE_VERSION_ID)
            )
            db.commit()


def get_bible_version_id(db: Session) -> int:
    row = db.get(AppSettings, 1)
    if row is None:
        return DEFAULT_BIBLE_VERSION_ID
    return row.bible_version_id


def get_active_bible_version(db: Session) -> BibleVersionKey:
    return get_bible_version(db, get_bible_version_id(db))


def list_bible_versions(db: Session) -> list[BibleVersionOption]:
    rows = db.scalars(
        select(BibleVersionKey).order_by(BibleVersionKey.id)
    ).all()
    return [
        BibleVersionOption(
            id=row.id,
            abbreviation=row.abbreviation,
            version=row.version,
        )
        for row in rows
    ]


def set_bible_version_id(db: Session, bible_version_id: int) -> None:
    get_bible_version(db, bible_version_id)
    row = db.get(AppSettings, 1)
    if row is None:
        db.add(AppSettings(id=1, bible_version_id=bible_version_id))
    else:
        row.bible_version_id = bible_version_id
    db.commit()

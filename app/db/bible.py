import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BibleVersion:
    id: int
    table: str
    abbreviation: str
    language: str
    version: str


def get_bible_version(db_path: Path, version_id: int) -> BibleVersion:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, "table", abbreviation, language, version
            FROM bible_version_key
            WHERE id = ?
            """,
            (version_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Bible version id {version_id} not found in bible_version_key")

    return BibleVersion(
        id=row[0],
        table=row[1],
        abbreviation=row[2],
        language=row[3],
        version=row[4],
    )

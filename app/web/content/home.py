from typing import TypedDict

from sqlalchemy.orm import Session

from app.db.bible import get_verse_of_day
from app.db.models.bible import BibleVersionKey


class NavItem(TypedDict):
    id: str
    title: str
    subtitle: str
    icon: str
    active: bool
    href: str


class Progress(TypedDict):
    label: str
    percent: int


class VerseOfDay(TypedDict):
    label: str
    text: str
    reference: str


class HomePage(TypedDict):
    progress: Progress
    time: str
    date: str
    nav_label: str
    nav_items: list[NavItem]
    verse_of_day: VerseOfDay


VERSE_OF_DAY_LABEL = "VERSE OF THE DAY"


def build_home_page(
    *,
    db: Session,
    bible_version: BibleVersionKey,
    continue_book: str,
    continue_chapter: int,
    continue_verse: int,
    progress_percent: int,
    note_count: int,
    collection_count: int,
) -> HomePage:
    text, reference = get_verse_of_day(db, bible_version.table)

    return {
        "progress": {
            "label": "BIBLE",
            "percent": progress_percent,
        },
        "time": "8:13 PM",
        "date": "Sunday, June 21, 2026",
        "nav_label": "NAVIGATE",
        "nav_items": [
            {
                "id": "continue",
                "title": "Continue",
                "subtitle": f"{continue_book} - verse {continue_verse}",
                "icon": "play",
                "active": True,
                "href": "/continue",
            },
            {
                "id": "bible",
                "title": "Bible",
                "subtitle": "Browse books",
                "icon": "book",
                "active": False,
                "href": "/bible",
            },
            {
                "id": "notes",
                "title": "Notes",
                "subtitle": f"{note_count} saved note{'s' if note_count != 1 else ''}",
                "icon": "notes",
                "active": False,
                "href": "/notes",
            },
            {
                "id": "collections",
                "title": "Collections",
                "subtitle": (
                    f"{collection_count} collection"
                    f"{'s' if collection_count != 1 else ''}"
                ),
                "icon": "collections",
                "active": False,
                "href": "/collections",
            },
        ],
        "verse_of_day": {
            "label": VERSE_OF_DAY_LABEL,
            "text": text,
            "reference": reference,
        },
    }

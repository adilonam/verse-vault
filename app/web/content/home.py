from typing import TypedDict

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
    version: str


class HomePage(TypedDict):
    progress: Progress
    time: str
    date: str
    nav_label: str
    nav_items: list[NavItem]
    verse_of_day: VerseOfDay


VERSE_OF_DAY: VerseOfDay = {
    "label": "VERSE OF THE DAY",
    "text": (
        "For I know the plans I have for you, declares the Lord, "
        "plans to prosper you and not to harm you, plans to give you "
        "hope and a future."
    ),
    "reference": "Jeremiah 29:11",
    "version": "",
}


def build_home_page(
    *,
    bible_version: BibleVersionKey,
    continue_book: str,
    continue_chapter: int,
    continue_verse: int,
    progress_percent: int,
) -> HomePage:
    return {
        "progress": {
            "label": "VERSES ANALYZED",
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
                "subtitle": bible_version.version,
                "icon": "book",
                "active": False,
                "href": "/bible",
            },
            {
                "id": "notes",
                "title": "Notes",
                "subtitle": "14 saved notes",
                "icon": "notes",
                "active": False,
                "href": "#",
            },
            {
                "id": "collections",
                "title": "Collections",
                "subtitle": "3 collections",
                "icon": "collections",
                "active": False,
                "href": "#",
            },
        ],
        "verse_of_day": {
            **VERSE_OF_DAY,
            "version": bible_version.abbreviation,
        },
    }

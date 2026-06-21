from typing import TypedDict


class NavItem(TypedDict):
    id: str
    title: str
    subtitle: str
    icon: str
    active: bool


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


HOME_PAGE: HomePage = {
    "progress": {
        "label": "VERSES ANALYZED",
        "percent": 68,
    },
    "time": "8:13 PM",
    "date": "Sunday, June 21, 2026",
    "nav_label": "NAVIGATE",
    "nav_items": [
        {
            "id": "continue",
            "title": "Continue",
            "subtitle": "Romans 8 - verse 28",
            "icon": "play",
            "active": True,
        },
        {
            "id": "bible",
            "title": "Bible",
            "subtitle": "New International Version",
            "icon": "book",
            "active": False,
        },
        {
            "id": "notes",
            "title": "Notes",
            "subtitle": "14 saved notes",
            "icon": "notes",
            "active": False,
        },
        {
            "id": "collections",
            "title": "Collections",
            "subtitle": "3 collections",
            "icon": "collections",
            "active": False,
        },
    ],
    "verse_of_day": {
        "label": "VERSE OF THE DAY",
        "text": (
            "For I know the plans I have for you, declares the Lord, "
            "plans to prosper you and not to harm you, plans to give you "
            "hope and a future."
        ),
        "reference": "Jeremiah 29:11",
        "version": "NIV",
    },
}

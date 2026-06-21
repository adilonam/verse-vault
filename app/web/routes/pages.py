from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.db.bible import get_bible_version
from app.web.content.home import HOME_PAGE

router = APIRouter()
templates = Jinja2Templates(directory=settings.templates_dir)


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request) -> HTMLResponse:
    try:
        bible_version = get_bible_version(
            settings.database_path,
            settings.bible_version_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    page = {
        **HOME_PAGE,
        "verse_of_day": {
            **HOME_PAGE["verse_of_day"],
            "version": bible_version.abbreviation,
        },
    }

    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"page": page, "bible_version": bible_version},
    )

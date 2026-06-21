from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.web.router import api_router


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name)
    application.mount(
        "/static",
        StaticFiles(directory=settings.static_dir),
        name="static",
    )
    application.include_router(api_router)
    return application


app = create_app()

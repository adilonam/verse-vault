from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.reading import init_reading_tables
from app.web.router import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_reading_tables()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.mount(
        "/static",
        StaticFiles(directory=settings.static_dir),
        name="static",
    )
    application.include_router(api_router)
    return application


app = create_app()

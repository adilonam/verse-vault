from fastapi import APIRouter

from app.web.routes import collections, notes, pages, reading

api_router = APIRouter()
api_router.include_router(pages.router)
api_router.include_router(reading.router)
api_router.include_router(notes.router)
api_router.include_router(collections.router)

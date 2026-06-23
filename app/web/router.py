from fastapi import APIRouter

from app.web.routes import pages, reading

api_router = APIRouter()
api_router.include_router(pages.router)
api_router.include_router(reading.router)

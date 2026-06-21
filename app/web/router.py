from fastapi import APIRouter

from app.web.routes import pages

api_router = APIRouter()
api_router.include_router(pages.router)

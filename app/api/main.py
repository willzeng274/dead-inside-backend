from fastapi import APIRouter

from app.api.routes import root, chat

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(chat.router)

from fastapi import APIRouter

from app.api.routes import root, chat, legacy_chat

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(chat.router)
api_router.include_router(legacy_chat.router)
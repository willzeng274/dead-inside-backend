from fastapi import APIRouter

from app.api.routes import test, private, root
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(test.router)
api_router.include_router(root.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

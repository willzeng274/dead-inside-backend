import os
from typing import Literal

from pydantic import (
    AnyUrl,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from openai import AsyncOpenAI
import redis.asyncio as redis

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    ENVIRONMENT: Literal["local", "production"] = "local"

    FRONTEND_HOST: str = "http://localhost:3000"

    BACKEND_CORS_ORIGINS: list[AnyUrl] | str = []

    REDIS_HOST: str = "redis-13867.c81.us-east-1-2.ec2.redns.redis-cloud.com"
    REDIS_PORT: int = 13867
    REDIS_USERNAME: str = "default"
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DECODE_RESPONSES: bool = True

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin.rstrip("/")) for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST.rstrip("/")
        ]

    LLM_MODEL_CHAT: str = "gpt-4o"
    LLM_MODEL_CHARACTER_GENERATION: str = "gpt-4o"


llm_client: AsyncOpenAI = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

settings = Settings()

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    username=settings.REDIS_USERNAME,
    password=settings.REDIS_PASSWORD,
    decode_responses=settings.REDIS_DECODE_RESPONSES,
)

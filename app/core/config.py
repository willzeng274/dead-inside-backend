import os
from typing import Literal

from pydantic import (
    AnyUrl,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from openai import AsyncOpenAI

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

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin.rstrip("/")) for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST.rstrip("/")
        ]

    SPEECH_TO_TEXT_MODEL: str = "gpt-4o-transcribe"
    # SPEECH_TO_TEXT_MODEL: str = "whisper-1"
    # SPEECH_TO_TEXT_MODEL: str = "gpt-4o-mini-transcribe"


llm_client: AsyncOpenAI = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

settings = Settings()

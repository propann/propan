"""Centralized configuration for Propan."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    ft_engine_profit_url: str = Field(
        default="http://ft_engine:8080/api/v1/profit",
        validation_alias="FT_ENGINE_PROFIT_URL",
    )
    hal_voice: str = Field(default="fr-FR-HenriNeural", validation_alias="HAL_VOICE")
    hal_speech_file: Path = Field(default=Path("speech.mp3"), validation_alias="HAL_SPEECH_FILE")
    hal_thought_interval: int = Field(default=30, validation_alias="HAL_THOUGHT_INTERVAL")
    hal_self_improve: bool = Field(default=False, validation_alias="HAL_SELF_IMPROVE")
    hal_self_improve_every: int = Field(default=5, validation_alias="HAL_SELF_IMPROVE_EVERY")
    hal_cycle: int = Field(default=1, validation_alias="HAL_CYCLE")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    python_executable: str = Field(default="python3", validation_alias="PYTHON_EXECUTABLE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()

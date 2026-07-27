"""
Application configuration.

All configuration values are loaded from environment variables (.env file).
Nothing is hardcoded.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Telegram ---
    BOT_TOKEN: str
    GROUP_ID: int  # yagona guruh - barcha murojaatlar shu yerga tushadi

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./ayolhub.db"

    # --- App ---
    APP_NAME: str = "AyolHub AI - Guliston"
    REGION_NAME: str = "Sirdaryo"
    DISTRICT_NAME: str = "Guliston"
    TRACKING_PREFIX: str = "GLS"  # e.g. GLS-2026-000001

    # --- AI (Google Gemini - bepul tarif) ---
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

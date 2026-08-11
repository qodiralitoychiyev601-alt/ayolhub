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

    # --- AI (Bytez orqali) ---
    # MUHIM: Google Gemini'ning ushbu loyihaga bog'langan hisobida "AQ."
    # formatidagi kalitlar standart REST API bilan ishlamasligi aniqlandi
    # (Google'ning o'zida davom etayotgan, hisobga xos muammo). Shu sababli
    # AI provayder sifatida Bytez (bytez.com) ishlatilmoqda — bitta API
    # kalit orqali ko'plab modellarga ulanish imkonini beradi.
    BYTEZ_API_KEY: str | None = None
    BYTEZ_MODEL: str = "Qwen/Qwen3-4B"

    # Eski Gemini sozlamalari (hozircha ishlatilmaydi, lekin kelajakda
    # provayder qaytarilsa deb saqlab turilgan — .env'da bo'lmasa ham xato
    # bermaydi):
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

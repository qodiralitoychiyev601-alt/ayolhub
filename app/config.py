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

    # --- AI (Groq orqali — permanent bepul tarif) ---
    # TARIX: Avval Google Gemini ishlatilgan edi, lekin ushbu loyihaga
    # bog'langan Google hisobida "AQ." formatidagi kalitlar standart REST
    # API bilan ishlamasligi aniqlandi (Google'ning o'zida davom etayotgan
    # muammo). Keyin Bytez sinovdan o'tkazildi (pullik, credit asosida).
    # Yakuniy yechim: Groq — butunlay bepul, doimiy tarif, OpenAI-mos
    # standart format, kreditkarta shart emas (console.groq.com/keys).
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Eski sozlamalar (hozircha ishlatilmaydi, lekin .env'da bo'lmasa ham
    # xato bermasligi uchun saqlab turilgan):
    BYTEZ_API_KEY: str | None = None
    BYTEZ_MODEL: str = "google/gemma-3-4b-it"
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

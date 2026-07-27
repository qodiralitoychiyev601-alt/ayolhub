"""
Entry point.

Usage:
    python run.py

This creates database tables if they don't exist yet (fine for the SQLite
pilot; once you move to Postgres, use Alembic migrations instead — see
README.md) and starts long-polling.
"""

import asyncio

import structlog

from app.bot import create_bot_and_dispatcher
from app.database.base import Base
from app.database.session import engine
from app.logging_config import configure_logging

logger = structlog.get_logger()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    configure_logging()
    await init_db()

    bot, dp = create_bot_and_dispatcher()

    logger.info("bot_starting")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

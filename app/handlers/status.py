"""Bot bootstrap: creates Bot/Dispatcher, registers middlewares and routers."""

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.handlers import additional_info, ai, appeal, placeholders, start, status
from app.middlewares.db_middleware import DatabaseMiddleware

logger = structlog.get_logger()


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # Routers — order matters: appeal FSM must be checked before generic
    # placeholder text handlers so state-bound messages are captured first.
    dp.include_router(start.router)
    dp.include_router(appeal.router)
    dp.include_router(status.router)
    dp.include_router(additional_info.router)
    dp.include_router(ai.router)
    dp.include_router(placeholders.router)

    return bot, dp

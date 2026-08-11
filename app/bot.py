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

    # Routers — order matters:
    # 1) start/appeal/status/additional_info/placeholders: aniq matnli
    #    menyu tugmalarini ushlaydi (ba'zilari holatdan qat'i nazar ishlaydi).
    # 2) ai.router ENG OXIRIDA turishi shart — chunki u AIChat.active holatida
    #    F.text bo'yicha "hammasini tutuvchi" (catch-all) handlerga ega.
    #    Agar u oldinroq tursa, foydalanuvchi AI suhbatida bo'lganda boshqa
    #    menyu tugmalarini bossa ham, matn AI'ga savol sifatida yuborilib,
    #    foydalanuvchi boshqa bo'limga chiqa olmay qolar edi.
    dp.include_router(start.router)
    dp.include_router(appeal.router)
    dp.include_router(status.router)
    dp.include_router(additional_info.router)
    dp.include_router(placeholders.router)
    dp.include_router(ai.router)

    return bot, dp

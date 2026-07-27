"""
Helper: run this, then send ANY message in your group (with the bot
already added to it, as admin). The chat_id will be printed in the
console — copy it into your .env file as GROUP_ID.

Usage:
    python get_chat_id.py
    (in Telegram, send a message in your group)
    -> Ctrl+C to stop once you have the id
"""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from app.config import get_settings

settings = get_settings()


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def echo_chat_id(message: Message) -> None:
        print(f"Chat nomi: {message.chat.title or message.chat.full_name}")
        print(f"Chat ID:   {message.chat.id}")
        print("-" * 40)

    print("Botga istalgan guruhda xabar yozing... (to'xtatish uchun Ctrl+C)")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

"""
Murojaatlar holatini tekshirish bo'limi.
"""

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="status")


@router.message(F.text == "📊 Murojaat holati")
async def check_status(message: Message) -> None:
    """Murojaat holatini ko'rsatuvchi xandler"""
    await message.answer(
        "📊 **Murojaatingiz holati:**\n\n"
        "Sizda hozircha ko'rib chiqilayotgan murojaatlar mavjud emas.",
        parse_mode="Markdown"
    )

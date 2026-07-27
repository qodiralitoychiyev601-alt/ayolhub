"""
Placeholder handlers for menu sections not yet built (jobs, courses,
grants, legal, psychology, contact). AI maslahatchi endi alohida
app/handlers/ai.py da to'liq ishlaydi.
"""

from aiogram import F, Router
from aiogram.types import Message

from app.config import get_settings

router = Router(name="placeholders")
settings = get_settings()

_COMING_SOON = {
    "💼 Ish o'rinlari": "💼 Ish o'rinlari bo'limi tez orada to'ldiriladi.",
    "🎓 Kurslar": "🎓 Kurslar bo'limi tez orada to'ldiriladi.",
    "💰 Grantlar": "💰 Grantlar bo'limi tez orada to'ldiriladi.",
    "⚖️ Huquqiy maslahat": "⚖️ Huquqiy maslahat bo'limi tez orada to'ldiriladi.",
    "🧠 Psixologik yordam": "🧠 Psixologik yordam bo'limi tez orada to'ldiriladi.",
    "📞 Bog'lanish": "📞 Bog'lanish: Guliston tumani Oila va xotin-qizlar bo'limi\n☎ Tel: (tuman raqami shu yerga qo'yiladi)",
}


@router.message(F.text.in_(_COMING_SOON.keys()))
async def coming_soon(message: Message) -> None:
    await message.answer(_COMING_SOON[message.text])


@router.message(F.text == "⚠️ Shoshilinch")
async def emergency(message: Message) -> None:
    await message.answer(
        "⚠️ Shoshilinch holat qayd etildi. Operatorlarga darhol xabar berildi.\n"
        "Iltimos, xavfsizligingiz uchun tegishli xizmatlarga (102) murojaat qilishni ham unutmang."
    )
    await message.bot.send_message(
        chat_id=settings.GROUP_ID,
        text=(
            f"🚨 <b>SHOSHILINCH SIGNAL</b>\n\n"
            f"👤 Foydalanuvchi: {message.from_user.full_name} "
            f"(@{message.from_user.username or '—'})\n"
            f"🆔 Telegram ID: {message.from_user.id}\n\n"
            f"Ushbu foydalanuvchi bilan tezkor bog'laning."
        ),
    )

"""
Tashqi havolalar (sayt/Telegram kanal) orqali ishlaydigan bo'limlar +
hali qurilmagan bo'limlar uchun "tez orada" xabari.

Yangi havola qo'shish yoki bo'lim qo'shish uchun FAQAT LINK_SECTIONS
lug'atini tahrirlang — pastdagi kod hech qachon o'zgartirilmasin.
"""

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_settings

router = Router(name="placeholders")
settings = get_settings()


# ============================================================
#  HAVOLALAR — shu yerni o'zgartiring, kodning qolgan qismiga
#  tegmang. Har bir bo'lim: intro matni + havolalar ro'yxati.
#  Har bir havola: ("Tugma matni", "https://havola.uz")
# ============================================================
LINK_SECTIONS: dict[str, dict] = {
    "⚖️ Huquqiy maslahat": {
        "intro": "⚖️ Huquqiy maslahat va ma'lumotlar uchun havolalar:",
        "links": [
            ("🔗 Huquqiy Ai maslahatchi", "https://www.lawify.uz/uz"),
            ("🔗 Advice.uz — Guliston bo'limi", "https://advice.uz/oz/offices/43"),
            ("🔗 Sayt nomi 3", "https://example.com"),
            ("🔗 Sayt nomi 4", "https://example.com"),
            ("📢 Huquqiy Axborot", "https://t.me/huquqiyaxborot"),
            ("📢 Yuristga murojaat", "https://t.me/yuristgamurojaat"),
        ],
    },
    "🧠 Psixologik yordam": {
        "intro": "🧠 Psixologik yordam uchun havolalar:",
        "links": [
            ("🔗 Sayt nomi 1", "https://example.com"),
            ("🔗 Sayt nomi 2", "https://example.com"),
            ("📢 Telegram kanal", "https://t.me/example_channel"),
        ],
    },
    "💼 Ish o'rinlari": {
        "intro": "💼 Ish o'rinlari uchun havolalar:",
        "links": [
            ("🔗 Guliston ish ko'p", "https://ishkop.uz/%D0%B2%D0%B0%D0%BA%D0%B0%D0%BD%D1%81%D0%B8%D0%B8/Qizlar/%D0%93%D1%83%D0%BB%D0%B8%D1%81%D1%82%D0%B0%D0%BD"),
            ("🔗 Sirdaryo olx ish", "https://www.olx.uz/oz/rabota/syrdarinskaya-oblast/q-ayol/"),
            ("📢 Sirdaryo Ish Bor", "https://t.me/Sirdaryo_ishbo"),
            ("📢 Guliston ish", "https://t.me/sirdaryo_ishchi_guliston"),
        ],
    },
    "🎓 Kurslar": {
        "intro": "🎓 Kurslar bo'limi uchun havolalar.",
        "links": [
             ("🔗 Guliston academy", "https://www.gulistonacademy.com/"),
            ("🔗 Camelot LC", "https://www.camelot-lc.uz/"),
            ("🔗 Elegant Guliston", "https://t.me/elegant_guliston"),
            ("🔗 Ziyo Education", "https://t.me/ziyo_oquv_markazi"),
            ("🔗 Madinabonu o'quv markazi", "https://www.instagram.com/madinabonu_oquv_markazi?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=="),
            ("🔗 Element math", "https://t.me/element_math"),
            ("🔗 Action study", "https://t.me/action_study"),
            ("🔗 Guliston monomarkaz", "https://t.me/monomarkaz_guliston"),
        ],
    },
}


# ============================================================
#  Hali havola/kontent qo'shilmagan bo'limlar — shunchaki matn
# ============================================================
_COMING_SOON = {
        "💰 Grantlar": "💰 Grantlar bo'limi tez orada to'ldiriladi.",
    "📞 Bog'lanish": "📞 Bog'lanish: Guliston tumani Oila va xotin-qizlar bo'limi\n☎ Tel: (tuman raqami shu yerga qo'yiladi)",
}


@router.message(F.text.in_(LINK_SECTIONS.keys()))
async def send_links(message: Message) -> None:
    section = LINK_SECTIONS[message.text]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, url=url)]
            for label, url in section["links"]
        ]
    )
    await message.answer(section["intro"], reply_markup=keyboard)


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

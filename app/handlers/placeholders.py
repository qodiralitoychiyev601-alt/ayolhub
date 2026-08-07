"""
Tashqi havolalar (sayt/Telegram kanal) va 16 ta mahalla bilan bog'lanish bo'limi.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_settings

router = Router(name="placeholders")
settings = get_settings()


# ============================================================
# 🔗 HAVOLALAR BO'LIMLARI
# ============================================================
LINK_SECTIONS: dict[str, dict] = {
    "⚖️ Huquqiy maslahat": {
        "intro": "⚖️ **Huquqiy maslahat va foydali manbalar:**\n\nQuyidagi tugmalar orqali rasmiy huquqiy portallar hamda mutaxassislarga murojaat qilishingiz mumkin:",
        "links": [
            ("🤖 Huquqiy AI maslahatchi", "https://www.lawify.uz/uz"),
            ("🏛️ Advice.uz — Guliston bo'limi", "https://advice.uz/oz/offices/43"),
            ("🔨 Huquqiy Portal", "https://huquqiyportal.uz/"),
            ("🛡️ Inson huquqlari portali", "http://insonhuquqlari.uz/"),
            ("📜 Huquqiy Axborot kanali", "https://t.me/huquqiyaxborot"),
            ("🧑‍⚖️ Yuristga bevosita murojaat", "https://t.me/yuristgamurojaat"),
        ],
    },
    "🧠 Psixologik yordam": {
        "intro": "🧠 **Psixologik ko'mak va maslahat:**\n\nRuhiy xotirjamlik va psixologik yordam olish uchun malakali mutaxassislar kanallari:",
        "links": [
            ("🌸 Psixologik yordam va tashxis", "https://t.me/psixologik_tashxis_echimbor"),
            ("🌺 Psixolog Abidjanova Parizoda", "https://t.me/abidjanova"),
            ("🌻 Psixolog Sitora Abdurahmonova", "https://t.me/sitorabonuabdurahmanova"),
        ],
    },
    "💼 Ish o'rinlari": {
        "intro": "💼 **Aholi bandligi va vakansiyalar:**\n\nBo'sh ish o'rinlari hamda xotin-qizlar uchun mos vakansiyalar bilan tanishing:",
        "links": [
            ("🏢 Guliston ish o'rinlari portali", "https://ishkop.uz/%D0%B2%D0%B0%D0%BA%D0%B0%D0%BD%D1%81%D0%B8%D0%B8/Qizlar/%D0%93%D1%83%D0%BB%D0%B8%D1%81%D1%82%D0%B0%D0%BD"),
            ("🔍 Sirdaryo OLX ish e'lonlari", "https://www.olx.uz/oz/rabota/syrdarinskaya-oblast/q-ayol/"),
            ("📢 Sirdaryo Ish Bor kanali", "https://t.me/Sirdaryo_ishbo"),
            ("📢 Guliston ishchi kanali", "https://t.me/sirdaryo_ishchi_guliston"),
        ],
    },
    "🎓 Kurslar": {
        "intro": "🎓 **O'quv markazlari va ta'lim kurslari:**\n\nBilim va kasb-hunar egallash uchun taklif etilayotgan o'quv markazlari:",
        "links": [
            ("🎓 Guliston Academy", "https://www.gulistonacademy.com/"),
            ("🏫 Camelot LC o'quv markazi", "https://www.camelot-lc.uz/"),
            ("✨ Elegant Guliston", "https://t.me/elegant_guliston"),
            ("📚 Ziyo Education", "https://t.me/ziyo_oquv_markazi"),
            ("📐 Madinabonu o'quv markazi", "https://www.instagram.com/madinabonu_oquv_markazi?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=="),
            ("🔬 Element Math", "https://t.me/element_math"),
            ("🎯 Action Study", "https://t.me/action_study"),
            ("💡 Guliston Monomarkaz", "https://t.me/monomarkaz_guliston"),
        ],
    },
    "💰 Grantlar": {
        "intro": "💰 **Grantlar, xalqaro dasturlar va stipendiyalar:**\n\nTa'lim va loyihalar uchun mo'ljallangan grant imkoniyatlari:",
        "links": [
            ("🎓 Grantlar.uz portali", "https://grantlar.uz/"),
            ("🌐 GrantGo xalqaro imkoniyatlar", "https://grantgo.uz/"),
        ],
    },
}

# ============================================================
# 🏡 16 TA MAHALLA VA FAOLLAR MA'LUMOTLARI
# ============================================================
MAHALLALAR: dict[str, dict] = {
    "m_1": {"name": "🌸 Beshbuloq MFY", "faol": "Maqsuda Usmonova", "phone": "+998 90 123 45 67"},
    "m_2": {"name": "🛠️ Tajribakor MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 99 315 85 34"},
    "m_3": {"name": "💧 Oqoltin MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 99 315 85 34"},
    "m_4": {"name": "⭐ Yulduz MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 68"},
    "m_5": {"name": "🏞️ Ulug'obod MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 70"},
    "m_6": {"name": "🌾 Dehqonobod MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 71"},
    "m_7": {"name": "☀️ Zarbdor MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 72"},
    "m_8": {"name": "🌿 Soyibobod MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 73"},
    "m_9": {"name": "🌊 Buloqboshi MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 74"},
    "m_10": {"name": "🕊️ Humo MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 75"},
    "m_11": {"name": "🌷 Navbahor MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 76"},
    "m_12": {"name": "🏡 Yangiobod MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 77"},
    "m_13": {"name": "🍎 Mevastor MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 78"},
    "m_14": {"name": "🚀 Istiqlol MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 79"},
    "m_15": {"name": "🏆 Guliston MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 80"},
    "m_16": {"name": "🌅 Oltinobod MFY", "faol": "Xotin-qizlar faoli", "phone": "+998 90 123 45 81"},
}


def make_mahalla_keyboard() -> InlineKeyboardMarkup:
    """16 ta mahallani 2 ustunli chiroyli tugmalar ko'rinishida chiqarish"""
    buttons = []
    keys = list(MAHALLALAR.keys())
    for i in range(0, len(keys), 2):
        row = [
            InlineKeyboardButton(text=MAHALLALAR[keys[i]]["name"], callback_data=f"mahalla:{keys[i]}")
        ]
        if i + 1 < len(keys):
            row.append(
                InlineKeyboardButton(text=MAHALLALAR[keys[i + 1]]["name"], callback_data=f"mahalla:{keys[i + 1]}")
            )
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================
# 📩 XANDLERLAR
# ============================================================

@router.message(F.text.in_(LINK_SECTIONS.keys()))
async def send_links(message: Message) -> None:
    """Tashqi havolalar bo'limi"""
    section = LINK_SECTIONS[message.text]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, url=url)]
            for label, url in section["links"]
        ]
    )
    await message.answer(section["intro"], reply_markup=keyboard, parse_mode="Markdown")


@router.message(F.text == "📞 Bog'lanish")
async def contact_section(message: Message) -> None:
    """Bog'lanish va mahalla tanlash bo'limi"""
    text = (
        "🏛️ **Guliston tumani Oila va xotin-qizlar bo'limi**\n\n"
        "☎️ **Ishonch telefoni:** `(786-32-23)`\n\n"
        "👇 **Mahalla xotin-qizlar faoli bilan bog'lanish uchun kerakli mahallani tanlang:**"
    )
    await message.answer(text, reply_markup=make_mahalla_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("mahalla:"))
async def mahalla_info_callback(callback: CallbackQuery) -> None:
    """Mahalla faoli haqida ma'lumot ko'rsatish"""
    m_key = callback.data.split(":")[1]
    info = MAHALLALAR.get(m_key)

    if info:
        text = (
            f"🏡 **{info['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Xotin-qizlar faoli:** {info['faol']}\n"
            f"📞 **Aloqa telefoni:** `{info['phone']}`\n\n"
            f"💡 *Raqam ustiga bossangiz, avtomatik nusxalanadi.*"
        )
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "⚠️ Shoshilinch")
async def emergency(message: Message) -> None:
    """Shoshilinch holat signali"""
    await message.answer(
        "⚠️ **Shoshilinch holat qayd etildi.** Operatorlarga darhol xabar berildi.\n\n"
        "🚨 Iltimos, xavfsizligingiz uchun tegishli xizmatlarga (**102** yoki **112**) ham murojaat qiling.",
        parse_mode="Markdown",
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
        parse_mode="HTML",
    )

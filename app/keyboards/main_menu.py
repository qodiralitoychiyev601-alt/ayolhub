"""Main reply keyboard — the bot's home menu."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🤖 AI maslahatchi")],
        [KeyboardButton(text="📝 Murojaat yuborish")],
        [KeyboardButton(text="📊 Murojaatim holati")],
        [KeyboardButton(text="💼 Ish o'rinlari"), KeyboardButton(text="🎓 Kurslar")],
        [KeyboardButton(text="💰 Grantlar")],
        [KeyboardButton(text="⚖️ Huquqiy maslahat"), KeyboardButton(text="🧠 Psixologik yordam")],
        [KeyboardButton(text="📞 Bog'lanish")],
        [KeyboardButton(text="⚠️ Shoshilinch")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_media_step_keyboard(has_media: bool = False) -> ReplyKeyboardMarkup:
    """has_media=True bo'lsa — foydalanuvchi allaqachon kamida 1 ta fayl
    biriktirgan, shuning uchun "✅ Tayyor" tugmasi ko'rsatiladi ("O'tkazib
    yuborish" endi mantiqsiz, chunki fayl allaqachon bor)."""
    if has_media:
        rows = [
            [KeyboardButton(text="✅ Tayyor")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ]
    else:
        rows = [
            [KeyboardButton(text="➡️ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def get_ai_chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Bosh menyuga qaytish")]],
        resize_keyboard=True,
    )

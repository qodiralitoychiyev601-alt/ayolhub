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


def get_media_step_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_ai_chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Bosh menyuga qaytish")]],
        resize_keyboard=True,
    )

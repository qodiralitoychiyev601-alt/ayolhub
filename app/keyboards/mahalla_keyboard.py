"""Inline keyboard for choosing a mahalla, built from the static constants list."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import MAHALLA_LIST


def get_mahalla_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"mahalla:{i}")]
        for i, name in enumerate(MAHALLA_LIST)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_status_keyboard(appeal_id: int) -> InlineKeyboardMarkup:
    """Buttons shown under an appeal card inside the group."""
    rows = [
        [
            InlineKeyboardButton(text="✅ Qabul qilindi", callback_data=f"status:{appeal_id}:accepted"),
            InlineKeyboardButton(text="🔄 Jarayonda", callback_data=f"status:{appeal_id}:in_progress"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ Ma'lumot kerak", callback_data=f"status:{appeal_id}:need_info"),
            InlineKeyboardButton(text="🏁 Bajarildi", callback_data=f"status:{appeal_id}:resolved"),
        ],
        [
            InlineKeyboardButton(text="🚫 Rad etildi", callback_data=f"status:{appeal_id}:rejected"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

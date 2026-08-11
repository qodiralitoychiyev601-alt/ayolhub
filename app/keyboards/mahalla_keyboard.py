"""Inline keyboard for choosing a mahalla, built from the static constants list."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import MAHALLA_LIST


def get_mahalla_keyboard() -> InlineKeyboardMarkup:
    # Prefiks "appeal_mahalla:" — bu murojaat (Appeal) FSM oqimiga tegishli
    # tanlov ekanini bildiradi va placeholders.py dagi "contact_mahalla:"
    # prefiksi bilan HECH QACHON to'qnashmaydi.
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"appeal_mahalla:{i}")]
        for i, name in enumerate(MAHALLA_LIST)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_status_keyboard(appeal_id: int) -> InlineKeyboardMarkup:
    """Buttons shown under an appeal card inside the group."""
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Qabul qilindi",
                callback_data=f"status:qabul:{appeal_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Jarayonda",
                callback_data=f"status:jarayon:{appeal_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ Ma'lumot kerak",
                callback_data=f"status:malumot:{appeal_id}"
            ),
            InlineKeyboardButton(
                text="🏁 Bajarildi",
                callback_data=f"status:bajarildi:{appeal_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🚫 Rad etildi",
                callback_data=f"status:rad:{appeal_id}"
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)

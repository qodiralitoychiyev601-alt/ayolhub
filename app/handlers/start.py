"""/start command and the "Home" entry point."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import get_main_menu

router = Router(name="start")

HOME_BUTTON_TEXT = "🏠 Bosh menyuga qaytish"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Assalomu alaykum, <b>AyolHub AI</b> botiga xush kelibsiz!\n\n"
        "Guliston tumani Oila va xotin-qizlar bo'limining rasmiy yordamchi boti.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == HOME_BUTTON_TEXT)
async def go_home(message: Message, state: FSMContext) -> None:
    """
    Works regardless of current FSM state (or missing state) — this is the
    universal "escape hatch" so the user is never stuck, even right after a
    redeploy resets in-memory conversation state.
    """
    await state.clear()
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_main_menu())

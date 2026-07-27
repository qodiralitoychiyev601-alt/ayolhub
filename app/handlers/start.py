"""/start command and the "Home" entry point."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import get_main_menu

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Assalomu alaykum, <b>AyolHub AI</b> botiga xush kelibsiz!\n\n"
        "Guliston tumani Oila va xotin-qizlar bo'limining rasmiy yordamchi boti.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=get_main_menu(),
    )

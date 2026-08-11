"""'🤖 AI maslahatchi' — foydalanuvchi bilan erkin suhbat rejimi."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import get_ai_chat_keyboard, get_main_menu
from app.services.ai_service import ask_ai
from app.states.appeal_states import AIChat

router = Router(name="ai")

EXIT_TEXT = "🏠 Bosh menyuga qaytish"


@router.message(F.text == "🤖 AI maslahatchi")
async def start_ai_chat(message: Message, state: FSMContext) -> None:
    await state.set_state(AIChat.active)
    await message.answer(
        "🤖 AI maslahatchi bilan suhbat boshlandi.\n\n"
        "Savolingizni yozing — huquqiy, psixologik, ish, grant yoki oilaviy "
        "mavzularda maslahat bera olaman.\n\n"
        "Chiqish uchun \"🏠 Bosh menyuga qaytish\" tugmasini bosing.",
        reply_markup=get_ai_chat_keyboard(),
    )


@router.message(AIChat.active, F.text == EXIT_TEXT)
async def exit_ai_chat(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_main_menu())


@router.message(AIChat.active, F.text)
async def handle_ai_message(message: Message) -> None:
    thinking = await message.answer("⏳ Javob tayyorlanmoqda...")
    reply_text = await ask_ai(message.text)
    await thinking.delete()
    await message.answer(reply_text, reply_markup=get_ai_chat_keyboard())


@router.message(AIChat.active)
async def handle_ai_non_text(message: Message) -> None:
    await message.answer(
        "Hozircha faqat matnli savollarga javob bera olaman. Iltimos, savolingizni yozing."
    )

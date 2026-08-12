"""'🤖 AI maslahatchi' — foydalanuvchi bilan erkin suhbat rejimi."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import get_ai_chat_keyboard, get_main_menu
from app.services.ai_service import (
    ask_ai,
    ask_ai_about_pdf,
    ask_ai_with_image,
    extract_pdf_text,
    transcribe_voice,
)
from app.states.appeal_states import AIChat

router = Router(name="ai")

EXIT_TEXT = "🏠 Bosh menyuga qaytish"
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB — Telegram bot API cheklovi bilan mos


@router.message(F.text == "🤖 AI maslahatchi")
async def start_ai_chat(message: Message, state: FSMContext) -> None:
    await state.set_state(AIChat.active)
    await message.answer(
        "🤖 AI maslahatchi bilan suhbat boshlandi.\n\n"
        "Menga quyidagi usullarda murojaat qilishingiz mumkin:\n"
        "✍️ Matn yozing\n"
        "🎙 Ovozli xabar yuboring\n"
        "📷 Rasm yuboring (hujjat, spravka, chek va h.k. bo'lishi mumkin)\n"
        "📄 PDF fayl yuboring\n\n"
        "Huquqiy, psixologik, ish, grant yoki oilaviy mavzularda maslahat "
        "bera olaman.\n\n"
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


@router.message(AIChat.active, F.voice)
async def handle_ai_voice(message: Message) -> None:
    """Ovozli xabarni Groq Whisper orqali matnga aylantirib, AI'ga yuboradi."""
    thinking = await message.answer("🎙 Ovozli xabar tinglanmoqda...")

    try:
        file_info = await message.bot.get_file(message.voice.file_id)
        buffer = await message.bot.download_file(file_info.file_path)
        audio_bytes = buffer.read()
    except Exception as exc:
        print(f"[ai] Ovozli xabarni yuklab olishda xatolik: {exc!r}")
        await thinking.delete()
        await message.answer("Kechirasiz, ovozli xabarni o'qishda xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    transcript = await transcribe_voice(audio_bytes, filename="voice.ogg")
    if not transcript:
        await thinking.delete()
        await message.answer(
            "Kechirasiz, ovozli xabaringizni tushunolmadim. Iltimos, yozib yuboring "
            "yoki aniqroq qilib qayta gapirib ko'ring."
        )
        return

    await thinking.edit_text(
        f"🎙 Siz aytdingiz: <i>{transcript}</i>\n\n⏳ Javob tayyorlanmoqda...",
        parse_mode="HTML",
    )
    reply_text = await ask_ai(transcript)
    await thinking.delete()
    await message.answer(reply_text, reply_markup=get_ai_chat_keyboard())


@router.message(AIChat.active, F.photo)
async def handle_ai_photo(message: Message) -> None:
    """Rasmni Groq vision modeliga yuborib, tahlil/javob oladi (hujjat,
    spravka, chek va h.k. ichidagi matnni ham o'qiy oladi)."""
    thinking = await message.answer("📷 Rasm tahlil qilinmoqda...")

    try:
        largest_photo = message.photo[-1]
        file_info = await message.bot.get_file(largest_photo.file_id)
        buffer = await message.bot.download_file(file_info.file_path)
        image_bytes = buffer.read()
    except Exception as exc:
        print(f"[ai] Rasmni yuklab olishda xatolik: {exc!r}")
        await thinking.delete()
        await message.answer("Kechirasiz, rasmni o'qishda xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    caption = message.caption or ""
    reply_text = await ask_ai_with_image(caption, image_bytes, mime_type="image/jpeg")
    await thinking.delete()
    await message.answer(reply_text, reply_markup=get_ai_chat_keyboard())


@router.message(AIChat.active, F.document)
async def handle_ai_document(message: Message) -> None:
    """PDF fayldan matnni ajratib, AI'ga yuboradi. Boshqa fayl turlari
    (rasm sifatida yuborilgan document'lar bundan mustasno) qo'llab-
    quvvatlanmaydi."""
    doc = message.document
    mime_type = doc.mime_type or ""

    # Rasm document sifatida yuborilgan bo'lsa ham (masalan "Compress: off"
    # bilan yuborilgan JPEG), vision oqimiga yo'naltiramiz.
    if mime_type.startswith("image/"):
        thinking = await message.answer("📷 Rasm tahlil qilinmoqda...")
        try:
            file_info = await message.bot.get_file(doc.file_id)
            buffer = await message.bot.download_file(file_info.file_path)
            image_bytes = buffer.read()
        except Exception as exc:
            print(f"[ai] Rasm-hujjatni yuklab olishda xatolik: {exc!r}")
            await thinking.delete()
            await message.answer("Kechirasiz, faylni o'qishda xatolik yuz berdi. Qayta urinib ko'ring.")
            return
        caption = message.caption or ""
        reply_text = await ask_ai_with_image(caption, image_bytes, mime_type=mime_type)
        await thinking.delete()
        await message.answer(reply_text, reply_markup=get_ai_chat_keyboard())
        return

    if mime_type != "application/pdf":
        await message.answer(
            "Hozircha faqat PDF va rasm fayllarini tahlil qila olaman. "
            "Boshqa fayl turlari qo'llab-quvvatlanmaydi."
        )
        return

    if doc.file_size and doc.file_size > MAX_FILE_SIZE_BYTES:
        await message.answer("Kechirasiz, fayl hajmi juda katta (20 MB dan oshmasligi kerak).")
        return

    thinking = await message.answer("📄 PDF fayl o'qilmoqda...")

    try:
        file_info = await message.bot.get_file(doc.file_id)
        buffer = await message.bot.download_file(file_info.file_path)
        pdf_bytes = buffer.read()
        pdf_text = extract_pdf_text(pdf_bytes)
    except Exception as exc:
        print(f"[ai] PDF o'qishda xatolik: {exc!r}")
        await thinking.delete()
        await message.answer("Kechirasiz, PDF faylni o'qishda xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    if not pdf_text:
        await thinking.delete()
        await message.answer(
            "Kechirasiz, bu PDF'dan matn topa olmadim (ehtimol, skanerlangan "
            "rasm ko'rinishida). Sahifasini rasm (foto) sifatida yuborib "
            "ko'ring — men rasmdagi matnni ham o'qiy olaman."
        )
        return

    await thinking.edit_text("📄 PDF o'qildi.\n\n⏳ Javob tayyorlanmoqda...")
    caption = message.caption or ""
    reply_text = await ask_ai_about_pdf(caption, pdf_text)
    await thinking.delete()
    await message.answer(reply_text, reply_markup=get_ai_chat_keyboard())


@router.message(AIChat.active)
async def handle_ai_non_text(message: Message) -> None:
    await message.answer(
        "Hozircha matn, ovozli xabar, rasm yoki PDF fayl orqali savol bera "
        "olasiz. Iltimos, shulardan birini yuboring."
    )

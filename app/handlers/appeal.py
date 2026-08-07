"""
'Murojaat yuborish' — 6-qadamli oqim (5 majburiy + 1 ixtiyoriy media).

Flow: full_name -> mahalla -> street_and_house -> phone_number ->
message_text -> media (ixtiyoriy) -> confirm -> DB ga saqlanadi ->
YAGONA guruhga (settings.GROUP_ID) yuboriladi (rasm/video/ovoz bilan birga,
agar biriktirilgan bo'lsa).
"""

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import MAHALLA_LIST
from app.database.models import AppealStatus, MediaType
from app.keyboards.mahalla_keyboard import get_mahalla_keyboard, get_status_keyboard
from app.keyboards.main_menu import (
    get_cancel_keyboard,
    get_main_menu,
    get_media_step_keyboard,
    get_phone_request_keyboard,
)
from app.services.appeal_service import AppealService, NewAppealInput
from app.states.appeal_states import AppealForm

router = Router(name="appeal")
settings = get_settings()

CANCEL_TEXT = "❌ Bekor qilish"
SKIP_TEXT = "➡️ O'tkazib yuborish"

STATUS_LABELS = {
    AppealStatus.NEW: "🆕 Yangi",
    AppealStatus.ACCEPTED: "✅ Qabul qilindi",
    AppealStatus.IN_PROGRESS: "🔄 Jarayonda",
    AppealStatus.NEED_INFO: "ℹ️ Qo'shimcha ma'lumot kerak",
    AppealStatus.RESOLVED: "🏁 Bajarildi",
    AppealStatus.REJECTED: "🚫 Rad etildi",
    AppealStatus.CLOSED: "🔒 Yopildi",
}

TYPE_LABELS = {
    "complaint": "Shikoyat",
    "application": "Ariza",
    "suggestion": "Taklif",
    "gratitude": "Minnatdorchilik",
    "emergency": "⚠️ SHOSHILINCH",
}


def _build_group_card(appeal) -> str:
    status_enum = AppealStatus(appeal.status) if isinstance(appeal.status, str) else appeal.status
    text = (
        f"<b>Yangi murojaat — {appeal.tracking_number}</b>\n\n"
        f"👤 <b>F.I.Sh:</b> {appeal.full_name}\n"
        f"🏘 <b>Mahalla:</b> {appeal.mahalla_name}\n"
        f"🏠 <b>Manzil:</b> {appeal.street_and_house}\n"
        f"📞 <b>Tel:</b> {appeal.phone_number}\n"
        f"📌 <b>Turi:</b> {TYPE_LABELS.get(appeal.appeal_type, appeal.appeal_type)}\n"
        f"📅 <b>Sana:</b> {appeal.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"💬 <b>Matn:</b>\n{appeal.message_text}\n\n"
        f"<b>Holat:</b> {STATUS_LABELS.get(status_enum, appeal.status)}"
    )
    return text


# ---------- Step 0: entry point ----------

@router.message(F.text == "📝 Murojaat yuborish")
async def start_appeal(message: Message, state: FSMContext) -> None:
    await state.set_state(AppealForm.full_name)
    await message.answer(
        "Murojaat yuborish uchun bir necha savolga javob bering.\n\n"
        "1️⃣ Ism va familiyangizni to'liq kiriting:",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(StateFilter(AppealForm), F.text == CANCEL_TEXT)
async def cancel_appeal(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Murojaat bekor qilindi.", reply_markup=get_main_menu())


# ---------- Step 1: full name ----------

@router.message(AppealForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, to'liq ism familyangizni kiriting.")
        return

    await state.update_data(full_name=message.text.strip())
    await state.set_state(AppealForm.mahalla)
    await message.answer(
        "2️⃣ Mahallangizni tanlang:",
        reply_markup=get_mahalla_keyboard(),
    )


# ---------- Step 2: mahalla (inline) ----------

@router.callback_query(AppealForm.mahalla, F.data.startswith("mahalla:"))
async def process_mahalla(callback: CallbackQuery, state: FSMContext) -> None:
    index = int(callback.data.split(":")[1])
    mahalla_name = MAHALLA_LIST[index]

    await state.update_data(mahalla_name=mahalla_name)
    await callback.message.edit_text(f"Mahalla tanlandi: <b>{mahalla_name}</b>", parse_mode="HTML")
    await state.set_state(AppealForm.street_and_house)
    await callback.message.answer(
        "3️⃣ Ko'cha nomi va uy raqamingizni kiriting:\n(masalan: Mustaqillik ko'chasi, 12-uy)",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


# ---------- Step 3: street and house ----------

@router.message(AppealForm.street_and_house)
async def process_address(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, ko'cha va uy raqamini kiriting.")
        return

    await state.update_data(street_and_house=message.text.strip())
    await state.set_state(AppealForm.phone_number)
    await message.answer(
        "4️⃣ Telefon raqamingizni yuboring (tugma orqali yoki qo'lda kiriting):",
        reply_markup=get_phone_request_keyboard(),
    )


# ---------- Step 4: phone number ----------

@router.message(AppealForm.phone_number, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone_number=message.contact.phone_number)
    await _ask_for_message(message, state)


@router.message(AppealForm.phone_number, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 9:
        await message.answer("Telefon raqami noto'g'ri. Qaytadan kiriting (masalan: +998901234567):")
        return

    await state.update_data(phone_number=phone)
    await _ask_for_message(message, state)


async def _ask_for_message(message: Message, state: FSMContext) -> None:
    await state.set_state(AppealForm.message_text)
    await message.answer(
        "5️⃣ Muammoingiz yoki taklifingizni batafsil yozing:",
        reply_markup=get_cancel_keyboard(),
    )


# ---------- Step 5: message text -> media step ----------

@router.message(AppealForm.message_text)
async def process_message_text(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("Iltimos, muammo yoki taklifingizni yozing.")
        return

    await state.update_data(message_text=message.text.strip())
    await state.set_state(AppealForm.media)
    await message.answer(
        "6️⃣ Agar rasm, video yoki ovozli xabar biriktirmoqchi bo'lsangiz, "
        "yuboring. Aks holda o'tkazib yuborishingiz mumkin.",
        reply_markup=get_media_step_keyboard(),
    )


# ---------- Step 6: media (optional) ----------

@router.message(AppealForm.media, F.text == SKIP_TEXT)
async def skip_media(message: Message, state: FSMContext) -> None:
    await state.update_data(media_type=None, media_file_id=None)
    await _show_confirmation(message, state)


@router.message(AppealForm.media, F.photo)
async def receive_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(
        media_type=MediaType.PHOTO.value, media_file_id=message.photo[-1].file_id
    )
    await _show_confirmation(message, state)


@router.message(AppealForm.media, F.video)
async def receive_video(message: Message, state: FSMContext) -> None:
    await state.update_data(
        media_type=MediaType.VIDEO.value, media_file_id=message.video.file_id
    )
    await _show_confirmation(message, state)


@router.message(AppealForm.media, F.voice)
async def receive_voice(message: Message, state: FSMContext) -> None:
    await state.update_data(
        media_type=MediaType.VOICE.value, media_file_id=message.voice.file_id
    )
    await _show_confirmation(message, state)


@router.message(AppealForm.media, F.document)
async def receive_document(message: Message, state: FSMContext) -> None:
    await state.update_data(
        media_type=MediaType.DOCUMENT.value, media_file_id=message.document.file_id
    )
    await _show_confirmation(message, state)


@router.message(AppealForm.media)
async def media_step_invalid(message: Message) -> None:
    await message.answer(
        "Iltimos, rasm, video, ovozli xabar yoki fayl yuboring, "
        "yoki \"➡️ O'tkazib yuborish\" tugmasini bosing."
    )


async def _show_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    media_note = ""
    if data.get("media_type"):
        media_labels = {
            "photo": "📷 Rasm biriktirildi",
            "video": "🎥 Video biriktirildi",
            "voice": "🎙 Ovozli xabar biriktirildi",
            "document": "📎 Fayl biriktirildi",
        }
        media_note = f"\n{media_labels.get(data['media_type'], '')}"

    summary = (
        "📋 <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🏘 {data['mahalla_name']}\n"
        f"🏠 {data['street_and_house']}\n"
        f"📞 {data['phone_number']}\n"
        f"💬 {data['message_text']}"
        f"{media_note}\n\n"
        "Hammasi to'g'rimi? Yuborish uchun \"✅ Tasdiqlash\" tugmasini bosing."
    )

    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )
    await state.set_state(AppealForm.confirm)
    await message.answer(summary, reply_markup=confirm_kb, parse_mode="HTML")


# ---------- Confirm -> save + send to group ----------

@router.message(AppealForm.confirm, F.text == "✅ Tasdiqlash")
async def confirm_appeal(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    service = AppealService(session)

    appeal = await service.submit_appeal(
        NewAppealInput(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=data["full_name"],
            mahalla_name=data["mahalla_name"],
            street_and_house=data["street_and_house"],
            phone_number=data["phone_number"],
            message_text=data["message_text"],
            media_type=data.get("media_type"),
            media_file_id=data.get("media_file_id"),
        )
    )

    await state.clear()
    await message.answer(
        f"✅ Murojaatingiz qabul qilindi!\n\n"
        f"Kuzatuv raqami: <b>{appeal.tracking_number}</b>\n"
        f"Holatini \"📊 Murojaatim holati\" bo'limidan kuzatib borishingiz mumkin.",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )

    card_text = _build_group_card(appeal)
    keyboard = get_status_keyboard(appeal.id)

    sent_message = await _send_card_to_group(message, card_text, keyboard, appeal)
    if sent_message:
        await service.appeal_repo.set_group_message_id(appeal.id, sent_message.message_id)
        await session.commit()


async def _send_card_to_group(message: Message, card_text: str, keyboard, appeal):
    bot = message.bot
    chat_id = settings.GROUP_ID

    if not appeal.media_type or not appeal.media_file_id:
        return await bot.send_message(chat_id=chat_id, text=card_text, reply_markup=keyboard, parse_mode="HTML")

    caption = card_text if len(card_text) <= 1024 else card_text[:1000] + "…"
    send_map = {
        MediaType.PHOTO.value: bot.send_photo,
        MediaType.VIDEO.value: bot.send_video,
        MediaType.VOICE.value: bot.send_voice,
        MediaType.DOCUMENT.value: bot.send_document,
    }
    file_kwarg = {
        MediaType.PHOTO.value: "photo",
        MediaType.VIDEO.value: "video",
        MediaType.VOICE.value: "voice",
        MediaType.DOCUMENT.value: "document",
    }
    sender = send_map[appeal.media_type]
    kwarg_name = file_kwarg[appeal.media_type]

    sent = await sender(
        chat_id=chat_id,
        **{kwarg_name: appeal.media_file_id},
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    if len(card_text) > 1024:
        await bot.send_message(chat_id=chat_id, text=card_text, parse_mode="HTML")

    return sent


# ---------- Guruhdagi tugmalar uchun Callback Handler ----------

@router.callback_query(F.data.startswith("status:") | F.data.startswith("appeal_status:"))
async def process_status_change(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Guruhdagi holat tugmalari bosilganda ma'lumotni yangilash"""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)
        return

    action = parts[1]
    try:
        appeal_id = int(parts[2])
    except ValueError:
        await callback.answer("ID formati xato!", show_alert=True)
        return

    action_map = {
        "qabul": AppealStatus.ACCEPTED,
        "jarayon": AppealStatus.IN_PROGRESS,
        "malumot": AppealStatus.NEED_INFO,
        "bajarildi": AppealStatus.RESOLVED,
        "rad": AppealStatus.REJECTED,
    }

    new_status = action_map.get(action)
    if not new_status:
        await callback.answer("Noma'lum holat!", show_alert=True)
        return

    service = AppealService(session)
    appeal = await service.appeal_repo.get_by_id(appeal_id)
    if not appeal:
        await callback.answer("Murojaat bazadan topilmadi!", show_alert=True)
        return

    # Statusni bazada yangilash
    await service.appeal_repo.update_status(appeal_id, new_status.value)
    await session.commit()

    status_label = STATUS_LABELS.get(new_status, new_status.value)
    await callback.answer(f"Holat o'zgartirildi: {status_label}")

    # Guruhdagi kartani yangilash
    appeal.status = new_status.value
    updated_card_text = _build_group_card(appeal)

    try:
        if callback.message.text:
            await callback.message.edit_text(
                text=updated_card_text,
                reply_markup=callback.message.reply_markup,
                parse_mode="HTML"
            )
        elif callback.message.caption:
            await callback.message.edit_caption(
                caption=updated_card_text[:1024],
                reply_markup=callback.message.reply_markup,
                parse_mode="HTML"
            )
    except Exception:
        pass

    # Foydalanuvchiga shaxsiy xat orqali xabar yuborish
    try:
        user_msg = (
            f"🔔 <b>Murojaatingiz holati o'zgardi!</b>\n\n"
            f"Kuzatuv raqami: <b>{appeal.tracking_number}</b>\n"
            f"Yangi holat: <b>{status_label}</b>"
        )
        await bot.send_message(chat_id=appeal.telegram_id, text=user_msg, parse_mode="HTML")
    except Exception:
        pass

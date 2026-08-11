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
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
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
from app.repositories.citizen_repository import CitizenRepository
from app.services.appeal_service import AppealService, NewAppealInput
from app.states.appeal_states import AppealForm

router = Router(name="appeal")
settings = get_settings()

CANCEL_TEXT = "❌ Bekor qilish"
SKIP_TEXT = "➡️ O'tkazib yuborish"
DONE_TEXT = "✅ Tayyor"
MAX_MEDIA_ITEMS = 5

MEDIA_ADDED_LABELS = {
    "photo": "📷 Rasm",
    "video": "🎥 Video",
    "voice": "🎙 Ovozli xabar",
    "document": "📎 Fayl",
}

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

@router.callback_query(AppealForm.mahalla, F.data.startswith("appeal_mahalla:"))
async def process_mahalla(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        index = int(callback.data.split(":")[1])
        mahalla_name = MAHALLA_LIST[index]
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri tanlov. Iltimos, ro'yxatdan qayta tanlang.", show_alert=True)
        return

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

    await state.update_data(message_text=message.text.strip(), media_items=[])
    await state.set_state(AppealForm.media)
    await message.answer(
        "6️⃣ Agar rasm, video, ovozli xabar yoki fayl biriktirmoqchi bo'lsangiz, "
        f"yuboring (bir nechtasini ketma-ket yuborishingiz mumkin, eng ko'pi bilan "
        f"{MAX_MEDIA_ITEMS} ta). Aks holda o'tkazib yuborishingiz mumkin.",
        reply_markup=get_media_step_keyboard(has_media=False),
    )


# ---------- Step 6: media (optional, bir nechta fayl) ----------

@router.message(AppealForm.media, F.text == SKIP_TEXT)
async def skip_media(message: Message, state: FSMContext) -> None:
    await _show_confirmation(message, state)


@router.message(AppealForm.media, F.text == DONE_TEXT)
async def finish_media(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("media_items"):
        await message.answer(
            "Hali hech qanday fayl biriktirmadingiz. Fayl yuboring yoki "
            "\"➡️ O'tkazib yuborish\" tugmasini bosing."
        )
        return
    await _show_confirmation(message, state)


async def _append_media(message: Message, state: FSMContext, media_type: str, file_id: str) -> None:
    data = await state.get_data()
    items: list[dict] = data.get("media_items") or []

    if len(items) >= MAX_MEDIA_ITEMS:
        await message.answer(
            f"Eng ko'pi bilan {MAX_MEDIA_ITEMS} ta fayl biriktirishingiz mumkin. "
            f"\"✅ Tayyor\" tugmasini bosing.",
            reply_markup=get_media_step_keyboard(has_media=True),
        )
        return

    items.append({"media_type": media_type, "media_file_id": file_id})
    await state.update_data(media_items=items)

    label = MEDIA_ADDED_LABELS.get(media_type, "Fayl")
    await message.answer(
        f"{label} qabul qilindi ({len(items)}/{MAX_MEDIA_ITEMS}).\n"
        f"Yana fayl biriktirishingiz mumkin yoki \"✅ Tayyor\" tugmasini bosing.",
        reply_markup=get_media_step_keyboard(has_media=True),
    )


@router.message(AppealForm.media, F.photo)
async def receive_photo(message: Message, state: FSMContext) -> None:
    await _append_media(message, state, MediaType.PHOTO.value, message.photo[-1].file_id)


@router.message(AppealForm.media, F.video)
async def receive_video(message: Message, state: FSMContext) -> None:
    await _append_media(message, state, MediaType.VIDEO.value, message.video.file_id)


@router.message(AppealForm.media, F.voice)
async def receive_voice(message: Message, state: FSMContext) -> None:
    await _append_media(message, state, MediaType.VOICE.value, message.voice.file_id)


@router.message(AppealForm.media, F.document)
async def receive_document(message: Message, state: FSMContext) -> None:
    await _append_media(message, state, MediaType.DOCUMENT.value, message.document.file_id)


@router.message(AppealForm.media)
async def media_step_invalid(message: Message) -> None:
    await message.answer(
        "Iltimos, rasm, video, ovozli xabar yoki fayl yuboring, "
        "\"✅ Tayyor\" yoki \"➡️ O'tkazib yuborish\" tugmasini bosing."
    )


async def _show_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    items: list[dict] = data.get("media_items") or []

    media_note = ""
    if items:
        counts: dict[str, int] = {}
        for item in items:
            counts[item["media_type"]] = counts.get(item["media_type"], 0) + 1
        parts = [f"{MEDIA_ADDED_LABELS.get(t, t)} x{c}" for t, c in counts.items()]
        media_note = f"\n📎 Biriktirilgan fayllar: {', '.join(parts)} (jami {len(items)} ta)"

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
            media_items=data.get("media_items") or [],
        )
    )
    # appeal.media_items shu obyekt yaratilgan sessiyada allaqachon xotirada
    # to'ldirilgan (repository.create() ichida .append() qilingan), shuning
    # uchun uni qayta so'rovsiz, xavfsiz o'qish mumkin.
    media_items = list(appeal.media_items)

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

    sent_message = await _send_card_to_group(message, card_text, keyboard, appeal, media_items)
    if sent_message:
        await service.appeal_repo.set_group_message_id(appeal.id, sent_message.message_id)
        await session.commit()


_SEND_MAP_NAMES = {
    MediaType.PHOTO.value: "send_photo",
    MediaType.VIDEO.value: "send_video",
    MediaType.VOICE.value: "send_voice",
    MediaType.DOCUMENT.value: "send_document",
}
_FILE_KWARG_NAMES = {
    MediaType.PHOTO.value: "photo",
    MediaType.VIDEO.value: "video",
    MediaType.VOICE.value: "voice",
    MediaType.DOCUMENT.value: "document",
}


async def _send_card_to_group(message: Message, card_text: str, keyboard, appeal, media_items: list):
    """Murojaat kartasini guruhga yuboradi. Agar bir nechta fayl biriktirilgan
    bo'lsa — BIRINCHISI asosiy karta (tugmalar bilan) sifatida, qolganlari esa
    alohida, kuzatuv raqamiga ishora qiluvchi xabarlar sifatida yuboriladi —
    shu bilan hech qanday fayl yo'qolib qolmaydi."""
    bot = message.bot
    chat_id = settings.GROUP_ID

    if not media_items:
        return await bot.send_message(chat_id=chat_id, text=card_text, reply_markup=keyboard, parse_mode="HTML")

    caption = card_text if len(card_text) <= 1024 else card_text[:1000] + "…"

    first = media_items[0]
    sender = getattr(bot, _SEND_MAP_NAMES[first.media_type])
    kwarg_name = _FILE_KWARG_NAMES[first.media_type]

    sent = await sender(
        chat_id=chat_id,
        **{kwarg_name: first.media_file_id},
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    if len(card_text) > 1024:
        await bot.send_message(chat_id=chat_id, text=card_text, parse_mode="HTML")

    # Qolgan fayllarni (2-, 3-, ...) navbat bilan yuboramiz. Bittasi
    # muvaffaqiyatsiz bo'lsa ham, qolganlari va asosiy karta baribir yetib boradi.
    total = len(media_items)
    for idx, item in enumerate(media_items[1:], start=2):
        try:
            extra_sender = getattr(bot, _SEND_MAP_NAMES[item.media_type])
            extra_kwarg = _FILE_KWARG_NAMES[item.media_type]
            await extra_sender(
                chat_id=chat_id,
                **{extra_kwarg: item.media_file_id},
                caption=f"📎 {appeal.tracking_number} — qo'shimcha fayl ({idx}/{total})",
            )
        except Exception as exc:
            print(f"[appeal] Qo'shimcha faylni yuborishda xatolik ({appeal.tracking_number}): {exc!r}")

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

    status_label = STATUS_LABELS.get(new_status, new_status.value)

    # Statusni bazada yangilash (tarixga operator ID'si bilan birga yoziladi).
    # AppealService.change_status o'zi ichida session.commit() ni bajaradi.
    appeal = await service.change_status(
        appeal_id=appeal_id,
        new_status=new_status,
        changed_by_telegram_id=callback.from_user.id,
        comment=f"Operator ({callback.from_user.full_name}) holatni '{status_label}' ga o'zgartirdi",
    )
    if appeal is None:
        await callback.answer("Murojaat bazadan topilmadi!", show_alert=True)
        return

    await callback.answer(f"Holat o'zgartirildi: {status_label}")

    # Guruhdagi kartani yangilash
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
    except Exception as exc:
        print(f"[appeal] Guruh kartasini yangilashda xatolik ({appeal.tracking_number}): {exc!r}")

    # Fuqaroga shaxsiy xabar yuborish.
    # MUHIM: Appeal modelida telegram_id maydoni YO'Q (faqat citizen_id FK bor) —
    # shuning uchun Citizen jadvalidan alohida so'rov orqali olamiz.
    citizen_repo = CitizenRepository(session)
    citizen = await citizen_repo.get_by_id(appeal.citizen_id)

    if citizen is None:
        print(f"[appeal] Citizen topilmadi (appeal={appeal.tracking_number}), xabar yuborilmadi.")
        return

    try:
        if new_status == AppealStatus.NEED_INFO:
            # "Ma'lumot kerak" bosilganda — fuqarodan aniq nima kerakligini
            # so'raymiz va "📎 Ma'lumot yuborish" tugmasi bilan to'g'ridan-to'g'ri
            # additional_info.py oqimiga yo'naltiramiz.
            user_msg = (
                f"ℹ️ <b>Murojaatingiz bo'yicha qo'shimcha ma'lumot kerak!</b>\n\n"
                f"Kuzatuv raqami: <b>{appeal.tracking_number}</b>\n\n"
                f"Iltimos, quyidagilardan birini yuboring:\n"
                f"• Pasport seriya va raqamingiz (matn)\n"
                f"• Pasport nusxasi (rasm)\n"
                f"• Yoki operator so'ragan boshqa hujjat/rasm\n\n"
                f"Pastdagi tugmani bosib yuborishingiz mumkin 👇"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📎 Ma'lumot yuborish", callback_data=f"addinfo:{appeal.id}"
                    )
                ]]
            )
            await bot.send_message(chat_id=citizen.telegram_id, text=user_msg, parse_mode="HTML", reply_markup=kb)
        else:
            user_msg = (
                f"🔔 <b>Murojaatingiz holati o'zgardi!</b>\n\n"
                f"Kuzatuv raqami: <b>{appeal.tracking_number}</b>\n"
                f"Yangi holat: <b>{status_label}</b>"
            )
            await bot.send_message(chat_id=citizen.telegram_id, text=user_msg, parse_mode="HTML")
    except Exception as exc:
        print(f"[appeal] Fuqaroga xabar yuborishda xatolik ({appeal.tracking_number}): {exc!r}")

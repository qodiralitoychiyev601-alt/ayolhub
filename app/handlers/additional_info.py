"""
'📎 Qo'shimcha ma'lumot yuborish' — operator "Qo'shimcha ma'lumot kerak"
tugmasini bosgach, fuqaro shu oqim orqali javob yozadi (matn, rasm, video,
ovozli xabar, fayl — barchasi qo'llab-quvvatlanadi). Javob guruhga, aynan
o'sha murojaat kartasiga REPLY tarzida yuboriladi, shu bilan operator
qaysi murojaatga tegishli ekanini darhol ko'radi.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import AppealStatus
from app.keyboards.main_menu import get_cancel_keyboard, get_main_menu
from app.repositories.appeal_repository import AppealRepository
from app.repositories.citizen_repository import CitizenRepository
from app.services.appeal_service import AppealService
from app.states.appeal_states import AdditionalInfo

router = Router(name="additional_info")
settings = get_settings()

CANCEL_TEXT = "❌ Bekor qilish"


@router.callback_query(F.data.startswith("addinfo:"))
async def start_additional_info(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    appeal_id = int(callback.data.split(":")[1])

    appeal_repo = AppealRepository(session)
    citizen_repo = CitizenRepository(session)
    appeal = await appeal_repo.get_by_id(appeal_id)

    if appeal is None:
        await callback.answer("Murojaat topilmadi.", show_alert=True)
        return

    citizen = await citizen_repo.get_by_id(appeal.citizen_id)
    if citizen is None or citizen.telegram_id != callback.from_user.id:
        await callback.answer("Bu murojaat sizga tegishli emas.", show_alert=True)
        return

    await state.set_state(AdditionalInfo.waiting)
    await state.update_data(appeal_id=appeal.id, tracking_number=appeal.tracking_number)

    await callback.answer()
    await callback.message.answer(
        f"📎 <b>{appeal.tracking_number}</b> murojaatingiz uchun qo'shimcha "
        f"ma'lumot yuboring.\n\n"
        f"Matn, rasm, video yoki ovozli xabar yuborishingiz mumkin.",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdditionalInfo.waiting, F.text == CANCEL_TEXT)
async def cancel_additional_info(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_menu())


async def _forward_to_group(message: Message, appeal, citizen_name: str) -> bool:
    """Sends the citizen's follow-up to the group, replying to the original
    appeal card when possible. Returns True on success."""
    bot = message.bot
    chat_id = settings.GROUP_ID
    reply_to = appeal.group_message_id or None

    header = f"📎 Qo'shimcha ma'lumot — {appeal.tracking_number} ({citizen_name})"

    try:
        if message.text:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{header}\n\n{message.text}",
                reply_to_message_id=reply_to,
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=chat_id,
                photo=message.photo[-1].file_id,
                caption=header,
                reply_to_message_id=reply_to,
            )
        elif message.video:
            await bot.send_video(
                chat_id=chat_id,
                video=message.video.file_id,
                caption=header,
                reply_to_message_id=reply_to,
            )
        elif message.voice:
            await bot.send_voice(
                chat_id=chat_id,
                voice=message.voice.file_id,
                caption=header,
                reply_to_message_id=reply_to,
            )
        elif message.video_note:
            # Round video messages have no caption support — send header separately.
            await bot.send_message(chat_id=chat_id, text=header, reply_to_message_id=reply_to)
            await bot.send_video_note(chat_id=chat_id, video_note=message.video_note.file_id)
        elif message.document:
            await bot.send_document(
                chat_id=chat_id,
                document=message.document.file_id,
                caption=header,
                reply_to_message_id=reply_to,
            )
        else:
            return False
    except Exception as exc:
        print(f"[additional_info] Guruhga yuborishda xatolik: {exc!r}")
        return False

    return True


@router.message(
    AdditionalInfo.waiting,
    F.text | F.photo | F.video | F.voice | F.video_note | F.document,
)
async def receive_additional_info(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    appeal_id = data.get("appeal_id")

    appeal_repo = AppealRepository(session)
    appeal = await appeal_repo.get_by_id(appeal_id) if appeal_id else None

    if appeal is None:
        await state.clear()
        await message.answer("Murojaat topilmadi. Bosh menyuga qaytdingiz.", reply_markup=get_main_menu())
        return

    sent = await _forward_to_group(message, appeal, message.from_user.full_name)

    if not sent:
        await message.answer(
            "Kechirasiz, bu turdagi xabarni yubora olmayman. "
            "Matn, rasm, video yoki ovozli xabar yuboring."
        )
        return

    # Fuqaro javob berganidan keyin murojaat holatini "Jarayonda" ga qaytaramiz —
    # operator endi qo'shimcha ma'lumotni ko'rib, davom ettiradi.
    service = AppealService(session)
    await service.change_status(
        appeal_id=appeal.id,
        new_status=AppealStatus.IN_PROGRESS,
        changed_by_telegram_id=message.from_user.id,
        comment="Fuqaro qo'shimcha ma'lumot yubordi",
    )

    await state.clear()
    await message.answer(
        "✅ Qo'shimcha ma'lumotingiz yuborildi. Rahmat!",
        reply_markup=get_main_menu(),
    )

"""
'Murojaatim holati' — citizen sees their own appeals.
Also handles the status-change buttons pressed by mahalla-group operators.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AppealStatus
from app.repositories.citizen_repository import CitizenRepository
from app.services.appeal_service import AppealService

router = Router(name="status")

STATUS_LABELS = {
    "new": "🆕 Yangi",
    "accepted": "✅ Qabul qilindi",
    "in_progress": "🔄 Jarayonda",
    "need_info": "ℹ️ Qo'shimcha ma'lumot kerak",
    "resolved": "🏁 Bajarildi",
    "rejected": "🚫 Rad etildi",
    "closed": "🔒 Yopildi",
}


@router.message(F.text == "📊 Murojaatim holati")
async def my_appeals(message: Message, session: AsyncSession) -> None:
    service = AppealService(session)
    appeals = await service.get_citizen_appeals(message.from_user.id)

    if not appeals:
        await message.answer("Sizda hozircha murojaatlar mavjud emas.")
        return

    lines = ["<b>📊 Sizning murojaatlaringiz:</b>\n"]
    for a in appeals[:20]:
        lines.append(
            f"• <b>{a.tracking_number}</b> — {STATUS_LABELS.get(a.status, a.status)}\n"
            f"  {a.created_at.strftime('%Y-%m-%d')} | {a.message_text[:50]}"
        )
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("status:"))
async def change_status(callback: CallbackQuery, session: AsyncSession) -> None:
    """Operator in a mahalla/admin group taps a status button on an appeal card."""
    _, appeal_id_str, new_status_value = callback.data.split(":")
    appeal_id = int(appeal_id_str)

    service = AppealService(session)
    appeal = await service.change_status(
        appeal_id=appeal_id,
        new_status=AppealStatus(new_status_value),
        changed_by_telegram_id=callback.from_user.id,
    )

    if appeal is None:
        await callback.answer("Murojaat topilmadi.", show_alert=True)
        return

    # Update the card text in place (both in the group and, if this is a
    # different message, leave the other one — each chat edits its own copy).
    label = STATUS_LABELS.get(new_status_value, new_status_value)
    old_text = callback.message.text or callback.message.html_text
    lines = old_text.split("\n")
    lines = [l for l in lines if not l.startswith("Holat:") and not l.startswith("<b>Holat:")]
    new_text = "\n".join(lines) + f"\n\n<b>Holat:</b> {label}"

    await callback.message.edit_text(new_text, reply_markup=callback.message.reply_markup)
    await callback.answer(f"Holat yangilandi: {label}")

    # Notify the citizen.
    citizen_repo = CitizenRepository(session)
    citizen = await citizen_repo.get_by_id(appeal.citizen_id)
    if citizen:
        try:
            await callback.bot.send_message(
                chat_id=citizen.telegram_id,
                text=f"📢 Murojaatingiz holati yangilandi!\n\n"
                     f"Kuzatuv raqami: {appeal.tracking_number}\n"
                     f"Yangi holat: {label}",
            )
        except Exception:
            pass  # citizen may have blocked the bot — do not crash the operator flow

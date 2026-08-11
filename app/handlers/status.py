"""
Murojaatlar holatini tekshirish bo'limi.

Fuqaro "📊 Murojaatim holati" tugmasini bosganda, uning Telegram ID'si
bo'yicha bazadan barcha murojaatlari (eng yangisidan boshlab) chiqariladi.
"""

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Appeal, AppealStatus
from app.services.appeal_service import AppealService

router = Router(name="status")

STATUS_LABELS = {
    AppealStatus.NEW: "🆕 Yangi",
    AppealStatus.ACCEPTED: "✅ Qabul qilindi",
    AppealStatus.IN_PROGRESS: "🔄 Jarayonda",
    AppealStatus.NEED_INFO: "ℹ️ Qo'shimcha ma'lumot kerak",
    AppealStatus.RESOLVED: "🏁 Bajarildi",
    AppealStatus.REJECTED: "🚫 Rad etildi",
    AppealStatus.CLOSED: "🔒 Yopildi",
}

MAX_SHOWN = 10  # bitta xabarda ko'rsatiladigan eng ko'p murojaatlar soni


def _status_label(appeal: Appeal) -> str:
    status = AppealStatus(appeal.status) if isinstance(appeal.status, str) else appeal.status
    return STATUS_LABELS.get(status, str(appeal.status))


def _format_appeal_line(appeal: Appeal) -> str:
    date_str = appeal.created_at.strftime("%Y-%m-%d %H:%M")
    return (
        f"🔹 <b>{appeal.tracking_number}</b>\n"
        f"   Holat: {_status_label(appeal)}\n"
        f"   Sana: {date_str}"
    )


@router.message(F.text.in_(["📊 Murojaatim holati", "📊 Murojaat holati"]))
async def check_status(message: Message, session: AsyncSession) -> None:
    """Fuqaroning barcha murojaatlarini holati bilan birga ko'rsatadi."""
    service = AppealService(session)
    appeals = await service.get_citizen_appeals(message.from_user.id)

    if not appeals:
        await message.answer(
            "📊 <b>Murojaatingiz holati:</b>\n\n"
            "Sizda hozircha yuborilgan murojaatlar mavjud emas.\n\n"
            "Murojaat yuborish uchun \"📝 Murojaat yuborish\" tugmasidan foydalaning."
        )
        return

    shown = appeals[:MAX_SHOWN]
    lines = [f"📊 <b>Sizning murojaatlaringiz ({len(appeals)} ta):</b>\n"]
    lines.extend(_format_appeal_line(a) for a in shown)

    remaining = len(appeals) - len(shown)
    if remaining > 0:
        lines.append(f"\n… va yana {remaining} ta murojaat.")

    await message.answer("\n\n".join(lines))

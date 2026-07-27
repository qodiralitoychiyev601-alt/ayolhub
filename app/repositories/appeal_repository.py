"""Repository for Appeal + its status history."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Appeal,
    AppealStatus,
    AppealStatusHistory,
    AppealType,
)


class AppealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Appeal.id)))
        return result.scalar_one()

    async def create(
        self,
        tracking_number: str,
        citizen_id: int,
        mahalla_name: str,
        full_name: str,
        street_and_house: str,
        phone_number: str,
        message_text: str,
        appeal_type: AppealType = AppealType.COMPLAINT,
        media_type: str | None = None,
        media_file_id: str | None = None,
    ) -> Appeal:
        appeal = Appeal(
            tracking_number=tracking_number,
            citizen_id=citizen_id,
            mahalla_name=mahalla_name,
            full_name=full_name,
            street_and_house=street_and_house,
            phone_number=phone_number,
            message_text=message_text,
            appeal_type=appeal_type,
            status=AppealStatus.NEW,
            media_type=media_type,
            media_file_id=media_file_id,
        )
        self.session.add(appeal)
        await self.session.flush()

        self.session.add(
            AppealStatusHistory(
                appeal_id=appeal.id,
                old_status=None,
                new_status=AppealStatus.NEW.value,
                changed_by_telegram_id=0,
                comment="Murojaat yaratildi",
            )
        )
        await self.session.flush()
        return appeal

    async def get_by_tracking_number(self, tracking_number: str) -> Appeal | None:
        result = await self.session.execute(
            select(Appeal).where(Appeal.tracking_number == tracking_number)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, appeal_id: int) -> Appeal | None:
        return await self.session.get(Appeal, appeal_id)

    async def get_by_citizen(self, citizen_id: int) -> list[Appeal]:
        result = await self.session.execute(
            select(Appeal)
            .where(Appeal.citizen_id == citizen_id)
            .order_by(Appeal.created_at.desc())
        )
        return list(result.scalars().all())

    async def set_group_message_id(self, appeal_id: int, message_id: int) -> None:
        appeal = await self.get_by_id(appeal_id)
        if appeal:
            appeal.group_message_id = message_id
            await self.session.flush()

    async def update_status(
        self,
        appeal_id: int,
        new_status: AppealStatus,
        changed_by_telegram_id: int,
        comment: str | None = None,
    ) -> Appeal | None:
        appeal = await self.get_by_id(appeal_id)
        if appeal is None:
            return None

        old_status = appeal.status
        appeal.status = new_status
        self.session.add(
            AppealStatusHistory(
                appeal_id=appeal.id,
                old_status=old_status,
                new_status=new_status.value,
                changed_by_telegram_id=changed_by_telegram_id,
                comment=comment,
            )
        )
        await self.session.flush()
        return appeal

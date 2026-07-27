"""
Business logic for appeals — independent of Telegram/aiogram.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import Appeal, AppealStatus, AppealType, Citizen
from app.repositories.appeal_repository import AppealRepository
from app.repositories.citizen_repository import CitizenRepository
from app.utils.tracking_number import generate_tracking_number

settings = get_settings()


@dataclass
class NewAppealInput:
    telegram_id: int
    username: str | None
    full_name: str
    mahalla_name: str
    street_and_house: str
    phone_number: str
    message_text: str
    appeal_type: AppealType = AppealType.COMPLAINT
    media_type: str | None = None
    media_file_id: str | None = None


class AppealService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appeal_repo = AppealRepository(session)
        self.citizen_repo = CitizenRepository(session)

    async def submit_appeal(self, data: NewAppealInput) -> Appeal:
        citizen: Citizen = await self.citizen_repo.create_or_update(
            telegram_id=data.telegram_id,
            username=data.username,
            full_name=data.full_name,
            phone_number=data.phone_number,
            mahalla_name=data.mahalla_name,
            street_and_house=data.street_and_house,
        )

        total = await self.appeal_repo.count_all()
        tracking_number = generate_tracking_number(settings.TRACKING_PREFIX, total + 1)

        appeal = await self.appeal_repo.create(
            tracking_number=tracking_number,
            citizen_id=citizen.id,
            mahalla_name=data.mahalla_name,
            full_name=data.full_name,
            street_and_house=data.street_and_house,
            phone_number=data.phone_number,
            message_text=data.message_text,
            appeal_type=data.appeal_type,
            media_type=data.media_type,
            media_file_id=data.media_file_id,
        )

        await self.session.commit()
        return appeal

    async def get_citizen_appeals(self, telegram_id: int) -> list[Appeal]:
        citizen = await self.citizen_repo.get_by_telegram_id(telegram_id)
        if citizen is None:
            return []
        return await self.appeal_repo.get_by_citizen(citizen.id)

    async def get_by_tracking_number(self, tracking_number: str) -> Appeal | None:
        return await self.appeal_repo.get_by_tracking_number(tracking_number)

    async def change_status(
        self,
        appeal_id: int,
        new_status: AppealStatus,
        changed_by_telegram_id: int,
        comment: str | None = None,
    ) -> Appeal | None:
        appeal = await self.appeal_repo.update_status(
            appeal_id, new_status, changed_by_telegram_id, comment
        )
        await self.session.commit()
        return appeal

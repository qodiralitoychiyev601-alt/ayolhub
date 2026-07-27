"""Repository for Citizen (Telegram users)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Citizen


class CitizenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, citizen_id: int) -> Citizen | None:
        return await self.session.get(Citizen, citizen_id)

    async def get_by_telegram_id(self, telegram_id: int) -> Citizen | None:
        result = await self.session.execute(
            select(Citizen).where(Citizen.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        telegram_id: int,
        username: str | None,
        full_name: str,
        phone_number: str,
        mahalla_name: str,
        street_and_house: str,
    ) -> Citizen:
        citizen = await self.get_by_telegram_id(telegram_id)
        if citizen is None:
            citizen = Citizen(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                phone_number=phone_number,
                mahalla_name=mahalla_name,
                street_and_house=street_and_house,
            )
            self.session.add(citizen)
        else:
            citizen.username = username
            citizen.full_name = full_name
            citizen.phone_number = phone_number
            citizen.mahalla_name = mahalla_name
            citizen.street_and_house = street_and_house

        await self.session.flush()
        return citizen

from sqlalchemy import select

from app.cities.models import City
from app.common.repository import BaseRepository


class CityRepository(BaseRepository):
    async def list_active_names(self) -> list[str]:
        q = (
            select(City.name)
            .where(City.is_active.is_(True))
            .order_by(City.name)
        )
        result = await self.session.execute(q)
        return [row[0] for row in result.all()]

    async def list_active(self) -> list[City]:
        q = (
            select(City)
            .where(City.is_active.is_(True))
            .order_by(City.name)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

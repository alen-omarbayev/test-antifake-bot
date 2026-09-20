from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.serial_number import SerialNumber


class SerialNumberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_serial(self, serial_number: str) -> SerialNumber | None:
        result = await self._session.execute(
            select(SerialNumber).where(SerialNumber.serial_number == serial_number)
        )
        return result.scalar_one_or_none()

    async def bulk_upsert(self, rows: Sequence[dict]) -> int:
        if not rows:
            return 0
        stmt = insert(SerialNumber).values(list(rows)).on_conflict_do_nothing(
            index_elements=["serial_number"]
        )
        result = await self._session.execute(stmt)
        return result.rowcount or 0

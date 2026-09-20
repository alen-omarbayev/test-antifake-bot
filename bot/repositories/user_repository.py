from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def upsert_on_activity(self, telegram_id: int, username: str | None) -> User:
        stmt = (
            insert(User)
            .values(telegram_id=telegram_id, username=username)
            .on_conflict_do_update(
                index_elements=[User.telegram_id],
                set_={"username": username, "last_active_at": func.now()},
            )
            .returning(User)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

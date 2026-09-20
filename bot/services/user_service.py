from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User
from bot.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def register_activity(self, telegram_id: int, username: str | None) -> User:
        return await self._repo.upsert_on_activity(telegram_id, username)

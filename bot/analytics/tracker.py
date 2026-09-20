from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.events import (
    EVENT_BOT_STARTED,
    EVENT_SERIAL_CHECK_FAILED,
    EVENT_SERIAL_CHECK_STARTED,
    EVENT_SERIAL_CHECK_SUCCESS,
)
from bot.repositories.analytics_event_repository import AnalyticsEventRepository


class AnalyticsTracker:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AnalyticsEventRepository(session)

    async def track_bot_started(self, user_id: int) -> None:
        await self._repo.log_event(user_id, EVENT_BOT_STARTED)

    async def track_serial_check_started(self, user_id: int) -> None:
        await self._repo.log_event(user_id, EVENT_SERIAL_CHECK_STARTED)

    async def track_serial_check_success(
        self, user_id: int, serial_number: str, batch_id: str | None
    ) -> None:
        await self._repo.log_event(
            user_id,
            EVENT_SERIAL_CHECK_SUCCESS,
            {"serial_number": serial_number, "batch_id": batch_id},
        )

    async def track_serial_check_failed(
        self, user_id: int, serial_number: str, reason: str
    ) -> None:
        await self._repo.log_event(
            user_id,
            EVENT_SERIAL_CHECK_FAILED,
            {"serial_number": serial_number, "reason": reason},
        )

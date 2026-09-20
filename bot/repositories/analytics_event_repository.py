from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.analytics_event import AnalyticsEvent


class AnalyticsEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_event(
        self, user_id: int, event_type: str, payload: dict | None = None
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(user_id=user_id, event_type=event_type, event_payload=payload)
        self._session.add(event)
        await self._session.flush()
        return event

from datetime import date, datetime
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.events import EVENT_SERIAL_CHECK_FAILED
from bot.models.analytics_event import AnalyticsEvent
from bot.models.user import User


class EventRow(NamedTuple):
    created_at: datetime
    telegram_id: int
    username: str | None
    event_type: str
    serial_number: str | None
    reason: str | None
    batch_id: str | None


class AnalyticsReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_users(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def count_new_users(self, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(User).where(User.first_seen_at >= since)
        )
        return result.scalar_one()

    async def count_events_by_type(self, since: datetime) -> dict[str, int]:
        result = await self._session.execute(
            select(AnalyticsEvent.event_type, func.count())
            .where(AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.event_type)
        )
        return {event_type: count for event_type, count in result.all()}

    async def count_failed_by_reason(self, since: datetime) -> dict[str, int]:
        failed = (
            select(AnalyticsEvent.event_payload["reason"].astext.label("reason"))
            .where(
                AnalyticsEvent.event_type == EVENT_SERIAL_CHECK_FAILED,
                AnalyticsEvent.created_at >= since,
            )
            .subquery()
        )
        result = await self._session.execute(
            select(failed.c.reason, func.count()).group_by(failed.c.reason)
        )
        return {reason or "unknown": count for reason, count in result.all()}

    async def daily_event_counts(self, since: datetime, tz: str) -> list[tuple[date, str, int]]:
        # Local day is computed in a subquery so GROUP BY references a plain column
        # instead of repeating the expression with a second tz bind parameter.
        events = (
            select(
                func.date(func.timezone(tz, AnalyticsEvent.created_at)).label("day"),
                AnalyticsEvent.event_type,
            )
            .where(AnalyticsEvent.created_at >= since)
            .subquery()
        )
        result = await self._session.execute(
            select(events.c.day, events.c.event_type, func.count())
            .group_by(events.c.day, events.c.event_type)
            .order_by(events.c.day)
        )
        return [(day, event_type, count) for day, event_type, count in result.all()]

    async def daily_new_users(self, since: datetime, tz: str) -> dict[date, int]:
        users = (
            select(func.date(func.timezone(tz, User.first_seen_at)).label("day"))
            .where(User.first_seen_at >= since)
            .subquery()
        )
        result = await self._session.execute(
            select(users.c.day, func.count()).group_by(users.c.day)
        )
        return {day: count for day, count in result.all()}

    async def list_events(self, since: datetime, limit: int) -> list[EventRow]:
        payload = AnalyticsEvent.event_payload
        result = await self._session.execute(
            select(
                AnalyticsEvent.created_at,
                User.telegram_id,
                User.username,
                AnalyticsEvent.event_type,
                payload["serial_number"].astext,
                payload["reason"].astext,
                payload["batch_id"].astext,
            )
            .join(User, User.id == AnalyticsEvent.user_id)
            .where(AnalyticsEvent.created_at >= since)
            .order_by(AnalyticsEvent.created_at, AnalyticsEvent.id)
            .limit(limit)
        )
        return [EventRow(*row) for row in result.all()]

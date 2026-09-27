from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.events import (
    EVENT_BOT_STARTED,
    EVENT_SERIAL_CHECK_FAILED,
    EVENT_SERIAL_CHECK_STARTED,
    EVENT_SERIAL_CHECK_SUCCESS,
)
from bot.repositories.analytics_report_repository import AnalyticsReportRepository

FAILED_REASON_LABELS = {"not_found": "не найден", "inactive": "неактивен"}


@dataclass
class DailyStats:
    day: date
    new_users: int = 0
    checks: int = 0
    success: int = 0
    failed: int = 0


@dataclass
class AnalyticsReport:
    days: int
    since: datetime
    timezone: str
    total_users: int
    new_users: int
    bot_started: int
    checks: int
    success: int
    failed: int
    failed_by_reason: dict[str, int] = field(default_factory=dict)
    daily: list[DailyStats] = field(default_factory=list)


def period_start(days: int, tz: str, now: datetime | None = None) -> datetime:
    """Local midnight of the first day of a period of `days` days ending today."""
    zone = ZoneInfo(tz)
    today = (now or datetime.now(zone)).astimezone(zone).date()
    return datetime.combine(today - timedelta(days=days - 1), time.min, tzinfo=zone)


class AnalyticsReportService:
    def __init__(self, session: AsyncSession, tz: str) -> None:
        self._repo = AnalyticsReportRepository(session)
        self._tz = tz

    async def build(self, days: int, now: datetime | None = None) -> AnalyticsReport:
        since = period_start(days, self._tz, now)

        by_type = await self._repo.count_events_by_type(since)
        daily = {
            since.date() + timedelta(days=offset): DailyStats(since.date() + timedelta(days=offset))
            for offset in range(days)
        }

        for day, count in (await self._repo.daily_new_users(since, self._tz)).items():
            if day in daily:
                daily[day].new_users = count

        for day, event_type, count in await self._repo.daily_event_counts(since, self._tz):
            stats = daily.get(day)
            if stats is None:
                continue
            if event_type == EVENT_SERIAL_CHECK_STARTED:
                stats.checks = count
            elif event_type == EVENT_SERIAL_CHECK_SUCCESS:
                stats.success = count
            elif event_type == EVENT_SERIAL_CHECK_FAILED:
                stats.failed = count

        return AnalyticsReport(
            days=days,
            since=since,
            timezone=self._tz,
            total_users=await self._repo.count_users(),
            new_users=await self._repo.count_new_users(since),
            bot_started=by_type.get(EVENT_BOT_STARTED, 0),
            checks=by_type.get(EVENT_SERIAL_CHECK_STARTED, 0),
            success=by_type.get(EVENT_SERIAL_CHECK_SUCCESS, 0),
            failed=by_type.get(EVENT_SERIAL_CHECK_FAILED, 0),
            failed_by_reason=await self._repo.count_failed_by_reason(since),
            daily=list(daily.values()),
        )


def format_report(report: AnalyticsReport) -> str:
    checks_line = f"Проверок: {report.checks} — ✅ {report.success} / ❌ {report.failed}"
    if report.failed_by_reason:
        reasons = ", ".join(
            f"{FAILED_REASON_LABELS.get(reason, reason)}: {count}"
            for reason, count in sorted(report.failed_by_reason.items())
        )
        checks_line += f" ({reasons})"

    lines = [
        f"📊 Отчёт за {report.days} дн. (с {report.since:%d.%m.%Y}, {report.timezone})",
        f"Пользователей всего: {report.total_users}, новых: {report.new_users}",
        f"Запусков /start: {report.bot_started}",
        checks_line,
        "",
        "По дням:",
    ]
    lines.extend(
        f"{stats.day:%d.%m} — новых {stats.new_users}, проверок {stats.checks} "
        f"(✅ {stats.success} / ❌ {stats.failed})"
        for stats in report.daily
    )
    return "\n".join(lines)

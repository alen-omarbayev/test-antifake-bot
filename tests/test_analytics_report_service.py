from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from bot.services.analytics_report_service import (
    AnalyticsReportService,
    format_report,
    period_start,
)

TZ = "Asia/Dushanbe"
# 20:00 UTC on Sep 26 is already 01:00 on Sep 27 in Dushanbe (UTC+5).
NOW = datetime(2026, 9, 26, 20, 0, tzinfo=timezone.utc)


def test_period_start_uses_local_day_boundary():
    since = period_start(3, TZ, now=NOW)

    assert since == datetime(2026, 9, 25, 0, 0, tzinfo=ZoneInfo(TZ))
    assert since.astimezone(timezone.utc) == datetime(2026, 9, 24, 19, 0, tzinfo=timezone.utc)


def test_period_start_single_day_is_today():
    assert period_start(1, TZ, now=NOW).date() == date(2026, 9, 27)


async def build_report():
    with patch("bot.services.analytics_report_service.AnalyticsReportRepository") as repo_cls:
        repo = repo_cls.return_value
        repo.count_users = AsyncMock(return_value=120)
        repo.count_new_users = AsyncMock(return_value=5)
        repo.count_events_by_type = AsyncMock(
            return_value={
                "bot_started": 7,
                "serial_check_started": 10,
                "serial_check_success": 6,
                "serial_check_failed": 4,
            }
        )
        repo.count_failed_by_reason = AsyncMock(return_value={"not_found": 3, "inactive": 1})
        repo.daily_new_users = AsyncMock(return_value={date(2026, 9, 25): 2})
        repo.daily_event_counts = AsyncMock(
            return_value=[
                (date(2026, 9, 25), "serial_check_started", 4),
                (date(2026, 9, 25), "serial_check_success", 3),
                (date(2026, 9, 25), "serial_check_failed", 1),
                (date(2026, 9, 27), "serial_check_started", 6),
                (date(2026, 9, 27), "bot_started", 7),
            ]
        )

        return await AnalyticsReportService(session=object(), tz=TZ).build(3, now=NOW)


async def test_build_aggregates_totals_and_fills_empty_days():
    report = await build_report()

    assert report.total_users == 120
    assert report.new_users == 5
    assert report.bot_started == 7
    assert (report.checks, report.success, report.failed) == (10, 6, 4)
    assert report.failed_by_reason == {"not_found": 3, "inactive": 1}

    assert [stats.day for stats in report.daily] == [
        date(2026, 9, 25),
        date(2026, 9, 26),
        date(2026, 9, 27),
    ]
    first, empty, last = report.daily
    assert (first.new_users, first.checks, first.success, first.failed) == (2, 4, 3, 1)
    assert (empty.new_users, empty.checks, empty.success, empty.failed) == (0, 0, 0, 0)
    assert last.checks == 6


async def test_format_report_contains_key_lines():
    text = format_report(await build_report())

    assert "Отчёт за 3 дн. (с 25.09.2026, Asia/Dushanbe)" in text
    assert "Пользователей всего: 120, новых: 5" in text
    assert "Проверок: 10 — ✅ 6 / ❌ 4 (неактивен: 1, не найден: 3)" in text
    assert "26.09 — новых 0, проверок 0 (✅ 0 / ❌ 0)" in text
    assert "<" not in text

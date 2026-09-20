from unittest.mock import AsyncMock, patch

from bot.analytics.events import (
    EVENT_BOT_STARTED,
    EVENT_SERIAL_CHECK_FAILED,
    EVENT_SERIAL_CHECK_STARTED,
    EVENT_SERIAL_CHECK_SUCCESS,
)
from bot.analytics.tracker import AnalyticsTracker


async def test_track_bot_started():
    with patch("bot.analytics.tracker.AnalyticsEventRepository") as repo_cls:
        repo_cls.return_value.log_event = AsyncMock()
        tracker = AnalyticsTracker(session=object())

        await tracker.track_bot_started(1)

    repo_cls.return_value.log_event.assert_awaited_once_with(1, EVENT_BOT_STARTED)


async def test_track_serial_check_started():
    with patch("bot.analytics.tracker.AnalyticsEventRepository") as repo_cls:
        repo_cls.return_value.log_event = AsyncMock()
        tracker = AnalyticsTracker(session=object())

        await tracker.track_serial_check_started(1)

    repo_cls.return_value.log_event.assert_awaited_once_with(1, EVENT_SERIAL_CHECK_STARTED)


async def test_track_serial_check_success():
    with patch("bot.analytics.tracker.AnalyticsEventRepository") as repo_cls:
        repo_cls.return_value.log_event = AsyncMock()
        tracker = AnalyticsTracker(session=object())

        await tracker.track_serial_check_success(1, "ABC123", "BATCH1")

    repo_cls.return_value.log_event.assert_awaited_once_with(
        1, EVENT_SERIAL_CHECK_SUCCESS, {"serial_number": "ABC123", "batch_id": "BATCH1"}
    )


async def test_track_serial_check_failed():
    with patch("bot.analytics.tracker.AnalyticsEventRepository") as repo_cls:
        repo_cls.return_value.log_event = AsyncMock()
        tracker = AnalyticsTracker(session=object())

        await tracker.track_serial_check_failed(1, "ABC123", "not_found")

    repo_cls.return_value.log_event.assert_awaited_once_with(
        1, EVENT_SERIAL_CHECK_FAILED, {"serial_number": "ABC123", "reason": "not_found"}
    )

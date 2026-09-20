from unittest.mock import AsyncMock, patch

from bot.models.serial_number import SerialNumber
from bot.models.user import User
from bot.services.serial_check_service import SerialCheckService


def make_user() -> User:
    return User(id=1, telegram_id=100, username="tester")


async def test_check_found_and_active():
    fake_serial = SerialNumber(
        id=1, serial_number="ABC123", is_active=True, batch_id="BATCH1"
    )
    with patch("bot.services.serial_check_service.SerialNumberRepository") as repo_cls, patch(
        "bot.services.serial_check_service.AnalyticsTracker"
    ) as tracker_cls:
        repo_cls.return_value.get_by_serial = AsyncMock(return_value=fake_serial)
        tracker = tracker_cls.return_value
        tracker.track_serial_check_success = AsyncMock()

        service = SerialCheckService(session=object())
        result = await service.check(make_user(), " abc123 ")

    assert result.found is True
    assert result.is_active is True
    assert result.normalized_serial == "ABC123"
    assert result.batch_id == "BATCH1"
    tracker.track_serial_check_success.assert_awaited_once_with(1, "ABC123", "BATCH1")


async def test_check_found_but_inactive():
    fake_serial = SerialNumber(
        id=1, serial_number="ABC123", is_active=False, batch_id="BATCH1"
    )
    with patch("bot.services.serial_check_service.SerialNumberRepository") as repo_cls, patch(
        "bot.services.serial_check_service.AnalyticsTracker"
    ) as tracker_cls:
        repo_cls.return_value.get_by_serial = AsyncMock(return_value=fake_serial)
        tracker = tracker_cls.return_value
        tracker.track_serial_check_failed = AsyncMock()

        service = SerialCheckService(session=object())
        result = await service.check(make_user(), "ABC123")

    assert result.found is False
    assert result.is_active is False
    tracker.track_serial_check_failed.assert_awaited_once_with(1, "ABC123", "inactive")


async def test_check_not_found():
    with patch("bot.services.serial_check_service.SerialNumberRepository") as repo_cls, patch(
        "bot.services.serial_check_service.AnalyticsTracker"
    ) as tracker_cls:
        repo_cls.return_value.get_by_serial = AsyncMock(return_value=None)
        tracker = tracker_cls.return_value
        tracker.track_serial_check_failed = AsyncMock()

        service = SerialCheckService(session=object())
        result = await service.check(make_user(), "unknown")

    assert result.found is False
    assert result.is_active is None
    tracker.track_serial_check_failed.assert_awaited_once_with(1, "UNKNOWN", "not_found")

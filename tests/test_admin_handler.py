from unittest.mock import MagicMock, patch

import pytest

from bot.config.settings import Settings
from bot.handlers.admin import DEFAULT_STATS_DAYS, is_admin, parse_stats_days


def fake_settings(admin_ids: set[int]) -> Settings:
    return Settings(bot_token="t", database_url="db", admin_ids=frozenset(admin_ids))


def test_is_admin_true_for_listed_user(make_message):
    with patch("bot.handlers.admin.get_settings", return_value=fake_settings({123})):
        assert is_admin(make_message(user_id=123)) is True


def test_is_admin_false_for_other_user(make_message):
    with patch("bot.handlers.admin.get_settings", return_value=fake_settings({123})):
        assert is_admin(make_message(user_id=456)) is False


def test_is_admin_false_without_sender():
    message = MagicMock()
    message.from_user = None
    with patch("bot.handlers.admin.get_settings", return_value=fake_settings({123})):
        assert is_admin(message) is False


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (None, DEFAULT_STATS_DAYS),
        ("  ", DEFAULT_STATS_DAYS),
        ("30", 30),
        (" 1 ", 1),
        ("0", None),
        ("91", None),
        ("abc", None),
    ],
)
def test_parse_stats_days(args, expected):
    assert parse_stats_days(args) == expected

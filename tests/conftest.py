from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.methods import SendMessage, TelegramMethod


class RecordingBot(Bot):
    """Bot that records outgoing API calls instead of sending them to Telegram."""

    def __init__(self) -> None:
        super().__init__(token="42:TEST")
        self.calls: list[TelegramMethod] = []

    async def __call__(self, method, request_timeout=None):
        self.calls.append(method)
        return True

    @property
    def replies(self) -> list[str]:
        return [call.text for call in self.calls if isinstance(call, SendMessage)]


@pytest.fixture
def bot():
    return RecordingBot()


@pytest.fixture
def make_message():
    def _make(text: str = "", user_id: int = 123, username: str | None = "tester"):
        message = MagicMock()
        message.text = text
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.username = username
        message.answer = AsyncMock()
        return message

    return _make

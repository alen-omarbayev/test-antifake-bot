from unittest.mock import AsyncMock, MagicMock

import pytest


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

from datetime import datetime
from itertools import count
from unittest.mock import MagicMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Chat, Message, PhotoSize, Update, User

from bot.config.settings import Settings
from bot.handlers import get_routers
from bot.handlers.admin import STATS_USAGE_TEXT, admin_router
from bot.handlers.fallback import TEXT_ONLY_TEXT, UNKNOWN_COMMAND_TEXT, fallback_router

ADMIN_ID = 123
USER_ID = 456


@pytest.fixture(scope="module")
def dp():
    # Routers are module-level singletons and can be attached to only one parent,
    # so the whole module shares one Dispatcher. Order matches get_routers().
    dispatcher = Dispatcher()
    dispatcher.include_routers(admin_router, fallback_router)
    return dispatcher


@pytest.fixture(autouse=True)
def admin_settings():
    settings = Settings(bot_token="t", database_url="db", admin_ids=frozenset({ADMIN_ID}))
    with patch("bot.handlers.admin.get_settings", return_value=settings):
        yield


@pytest.fixture
def send(dp, bot):
    message_ids = count(1)

    async def _send(text: str | None = None, photo: list[PhotoSize] | None = None, user_id=USER_ID):
        message = Message(
            message_id=next(message_ids),
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=User(id=user_id, is_bot=False, first_name="Tester"),
            text=text,
            photo=photo,
        )
        bot.calls.clear()
        await dp.feed_update(
            bot, Update(update_id=message.message_id, message=message), session=MagicMock()
        )
        return bot.replies

    return _send


def test_fallback_router_is_last():
    assert get_routers()[-1] is fallback_router


@pytest.mark.parametrize("command", ["/stats", "/stats_export", "/import", "/done", "/help"])
async def test_unknown_or_forbidden_command_gets_hint(send, command):
    assert await send(command) == [UNKNOWN_COMMAND_TEXT]


async def test_admin_command_is_handled_by_admin_router(send):
    assert await send("/stats abc", user_id=ADMIN_ID) == [STATS_USAGE_TEXT]


async def test_non_text_message_gets_hint(send):
    photo = [PhotoSize(file_id="p1", file_unique_id="u1", width=10, height=10)]

    assert await send(photo=photo) == [TEXT_ONLY_TEXT]

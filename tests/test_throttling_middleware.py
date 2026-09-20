import time
from unittest.mock import AsyncMock

from bot.middlewares.throttling import ThrottlingMiddleware


async def test_second_call_within_cooldown_is_blocked(make_message, monkeypatch):
    middleware = ThrottlingMiddleware(cooldown_seconds=3.0)
    handler = AsyncMock(return_value="ok")
    message = make_message(user_id=1)

    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    result1 = await middleware(handler, message, {})
    assert result1 == "ok"
    handler.assert_awaited_once()

    now[0] += 1.0
    result2 = await middleware(handler, message, {})

    assert result2 is None
    handler.assert_awaited_once()
    message.answer.assert_awaited_once()


async def test_call_after_cooldown_passes_through(make_message, monkeypatch):
    middleware = ThrottlingMiddleware(cooldown_seconds=3.0)
    handler = AsyncMock(return_value="ok")
    message = make_message(user_id=2)

    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    await middleware(handler, message, {})
    now[0] += 5.0
    result = await middleware(handler, message, {})

    assert result == "ok"
    assert handler.await_count == 2

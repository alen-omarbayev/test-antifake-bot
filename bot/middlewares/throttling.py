import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, cooldown_seconds: float = 3.0) -> None:
        self._cooldown = cooldown_seconds
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        now = time.monotonic()

        if user_id is not None:
            last = self._last_call.get(user_id)
            if last is not None and now - last < self._cooldown:
                await event.answer("Слишком часто. Подождите немного и попробуйте снова.")
                return None
            self._last_call[user_id] = now

        return await handler(event, data)

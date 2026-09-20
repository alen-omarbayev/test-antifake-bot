import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config.settings import get_settings
from bot.db.engine import dispose_engine, get_sessionmaker
from bot.handlers import get_routers
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.user_activity import UserActivityMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    sessionmaker = get_sessionmaker()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.update.outer_middleware(DbSessionMiddleware(sessionmaker))
    dp.message.middleware(UserActivityMiddleware())
    dp.callback_query.middleware(UserActivityMiddleware())

    for router in get_routers():
        dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())

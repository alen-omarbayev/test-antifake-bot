from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.tracker import AnalyticsTracker
from bot.keyboards.main_menu import CHECK_SERIAL_CALLBACK, check_failed_keyboard
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.models.user import User
from bot.services.serial_check_service import SerialCheckResult, SerialCheckService
from bot.texts import TEXTS, lang_of, t

serial_router = Router(name="serial_check")
serial_router.message.middleware(ThrottlingMiddleware(cooldown_seconds=3.0))


def format_result(result: SerialCheckResult, lang: str) -> str:
    texts = TEXTS[lang]
    if result.found:
        return texts["check_success"]
    return texts["check_failed"] + "\n\n" + texts["service_center"]


@serial_router.callback_query(F.data == CHECK_SERIAL_CALLBACK)
async def on_check_serial_pressed(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(t(user, "check_instructions"))


@serial_router.message(F.text & ~F.text.startswith("/"))
async def on_serial_text(message: Message, session: AsyncSession, user: User) -> None:
    await AnalyticsTracker(session).track_serial_check_started(user.id)
    result = await SerialCheckService(session).check(user, message.text)
    lang = lang_of(user)
    reply_markup = None if result.found else check_failed_keyboard(lang)
    await message.answer(format_result(result, lang), reply_markup=reply_markup)

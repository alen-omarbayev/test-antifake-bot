from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.tracker import AnalyticsTracker
from bot.keyboards.main_menu import CHECK_SERIAL_CALLBACK
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.models.user import User
from bot.services.serial_check_service import SerialCheckResult, SerialCheckService

serial_router = Router(name="serial_check")
serial_router.message.middleware(ThrottlingMiddleware(cooldown_seconds=3.0))


def format_result(result: SerialCheckResult) -> str:
    if result.found:
        return f"✅ Серийный номер {result.normalized_serial} найден. Товар подлинный."
    return f"❌ Серийный номер {result.normalized_serial} не найден в базе."


@serial_router.callback_query(F.data == CHECK_SERIAL_CALLBACK)
async def on_check_serial_pressed(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Отправьте серийный номер сообщением.")


@serial_router.message(F.text & ~F.text.startswith("/"))
async def on_serial_text(message: Message, session: AsyncSession, user: User) -> None:
    await AnalyticsTracker(session).track_serial_check_started(user.id)
    result = await SerialCheckService(session).check(user, message.text)
    await message.answer(format_result(result))

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.tracker import AnalyticsTracker
from bot.keyboards.main_menu import main_menu_keyboard
from bot.models.user import User

start_router = Router(name="start")

GREETING_TEXT = (
    "Привет! Я помогу проверить подлинность серийного номера товара LG.\n\n"
    "Нажмите кнопку ниже или просто отправьте серийный номер сообщением."
)


@start_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, user: User) -> None:
    await AnalyticsTracker(session).track_bot_started(user.id)
    await message.answer(GREETING_TEXT, reply_markup=main_menu_keyboard())

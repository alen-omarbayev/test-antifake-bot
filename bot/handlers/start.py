from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.tracker import AnalyticsTracker
from bot.keyboards.main_menu import (
    LANG_CALLBACK_PREFIX,
    MAIN_MENU_CALLBACK,
    language_keyboard,
    main_menu_keyboard,
)
from bot.models.user import User
from bot.services.user_service import UserService
from bot.texts import CHOOSE_LANGUAGE_TEXT, LANGUAGES, lang_of, t

start_router = Router(name="start")


@start_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, user: User) -> None:
    await AnalyticsTracker(session).track_bot_started(user.id)
    await message.answer(CHOOSE_LANGUAGE_TEXT, reply_markup=language_keyboard())


@start_router.callback_query(F.data.startswith(LANG_CALLBACK_PREFIX))
async def on_language_chosen(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await callback.answer()
    lang = callback.data.removeprefix(LANG_CALLBACK_PREFIX)
    if lang not in LANGUAGES or callback.message is None:
        return
    await UserService(session).set_language(user, lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(t(user, "greeting"))
    await callback.message.answer(t(user, "choose_section"), reply_markup=main_menu_keyboard(lang))


@start_router.callback_query(F.data == MAIN_MENU_CALLBACK)
async def on_main_menu(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            t(user, "choose_section"), reply_markup=main_menu_keyboard(lang_of(user))
        )

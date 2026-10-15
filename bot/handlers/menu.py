from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.main_menu import (
    CITY_CALLBACK_PREFIX,
    SERVICE_CALLBACK,
    SITE_CALLBACK,
    STORES_CALLBACK,
    cities_keyboard,
)
from bot.models.user import User
from bot.stores import STORES, format_stores
from bot.texts import lang_of, t

menu_router = Router(name="menu")


@menu_router.callback_query(F.data == STORES_CALLBACK)
async def on_stores(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_reply_markup(reply_markup=cities_keyboard(lang_of(user)))


@menu_router.callback_query(F.data.startswith(CITY_CALLBACK_PREFIX))
async def on_city(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    city = callback.data.removeprefix(CITY_CALLBACK_PREFIX)
    if city in STORES and callback.message is not None:
        await callback.message.answer(format_stores(city, lang_of(user)))


@menu_router.callback_query(F.data == SITE_CALLBACK)
async def on_site(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(t(user, "site"))


@menu_router.callback_query(F.data == SERVICE_CALLBACK)
async def on_service(callback: CallbackQuery, user: User) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(t(user, "service_center"))

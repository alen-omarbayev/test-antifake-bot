from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.stores import CITY_DUSHANBE, CITY_KHUJAND
from bot.texts import LANGUAGE_BUTTONS, TEXTS

LANG_CALLBACK_PREFIX = "lang:"
CHECK_SERIAL_CALLBACK = "menu:check"
STORES_CALLBACK = "menu:stores"
SITE_CALLBACK = "menu:site"
SERVICE_CALLBACK = "menu:service"
MAIN_MENU_CALLBACK = "menu:main"
CITY_CALLBACK_PREFIX = "stores:"


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lang, label in LANGUAGE_BUTTONS.items():
        builder.button(text=label, callback_data=LANG_CALLBACK_PREFIX + lang)
    return builder.as_markup()


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    texts = TEXTS[lang]
    builder = InlineKeyboardBuilder()
    builder.button(text=texts["btn_check"], callback_data=CHECK_SERIAL_CALLBACK)
    builder.button(text=texts["btn_stores"], callback_data=STORES_CALLBACK)
    builder.button(text=texts["btn_site"], callback_data=SITE_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()


def cities_keyboard(lang: str) -> InlineKeyboardMarkup:
    texts = TEXTS[lang]
    builder = InlineKeyboardBuilder()
    builder.button(text=texts["btn_dushanbe"], callback_data=CITY_CALLBACK_PREFIX + CITY_DUSHANBE)
    builder.button(text=texts["btn_khujand"], callback_data=CITY_CALLBACK_PREFIX + CITY_KHUJAND)
    return builder.as_markup()


def check_failed_keyboard(lang: str) -> InlineKeyboardMarkup:
    texts = TEXTS[lang]
    builder = InlineKeyboardBuilder()
    builder.button(text=texts["btn_check_again"], callback_data=CHECK_SERIAL_CALLBACK)
    builder.button(text=texts["btn_service"], callback_data=SERVICE_CALLBACK)
    builder.button(text=texts["btn_main_menu"], callback_data=MAIN_MENU_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()

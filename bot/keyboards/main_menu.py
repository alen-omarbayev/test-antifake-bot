from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

CHECK_SERIAL_CALLBACK = "check_serial"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔎 Проверить серийный номер", callback_data=CHECK_SERIAL_CALLBACK)
    return builder.as_markup()

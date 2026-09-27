from aiogram import Router

from bot.handlers.admin import admin_router
from bot.handlers.serial_check import serial_router
from bot.handlers.serial_import import import_router
from bot.handlers.start import start_router


def get_routers() -> list[Router]:
    # import_router must precede serial_router: in import mode text is serials to load, not to check.
    return [start_router, admin_router, import_router, serial_router]

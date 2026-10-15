from aiogram import Router

from bot.handlers.admin import admin_router
from bot.handlers.fallback import fallback_router
from bot.handlers.menu import menu_router
from bot.handlers.serial_check import serial_router
from bot.handlers.serial_import import import_router
from bot.handlers.start import start_router


def get_routers() -> list[Router]:
    # import_router must precede serial_router: in import mode text is serials to load, not to check.
    # fallback_router must be last: it answers every message the other routers did not handle.
    return [start_router, menu_router, admin_router, import_router, serial_router, fallback_router]

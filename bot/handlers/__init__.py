from aiogram import Router

from bot.handlers.serial_check import serial_router
from bot.handlers.start import start_router


def get_routers() -> list[Router]:
    return [start_router, serial_router]

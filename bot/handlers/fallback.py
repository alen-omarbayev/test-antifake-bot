from aiogram import F, Router
from aiogram.types import Message

fallback_router = Router(name="fallback")

# One reply for every unknown command, so non-admins cannot tell that admin commands exist.
UNKNOWN_COMMAND_TEXT = (
    "Неизвестная команда. Отправьте серийный номер сообщением или нажмите /start."
)
TEXT_ONLY_TEXT = "Отправьте серийный номер текстом."


@fallback_router.message(F.text.startswith("/"))
async def on_unknown_command(message: Message) -> None:
    await message.answer(UNKNOWN_COMMAND_TEXT)


@fallback_router.message()
async def on_other_message(message: Message) -> None:
    await message.answer(TEXT_ONLY_TEXT)

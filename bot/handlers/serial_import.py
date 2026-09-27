import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import get_settings
from bot.handlers.admin import is_admin
from bot.services.serial_import_service import (
    ParsedSerials,
    SerialImportService,
    format_import_result,
    make_batch_id,
    parse_text,
    parse_xlsx,
)

logger = logging.getLogger(__name__)

import_router = Router(name="serial_import")
import_router.message.filter(is_admin)

# Bot API refuses getFile for files larger than 20 MB.
MAX_FILE_SIZE = 20 * 1024 * 1024


class ImportStates(StatesGroup):
    waiting = State()


def instructions_text(batch_id: str) -> str:
    return (
        f"📥 Загрузка серийных номеров (партия {batch_id})\n\n"
        "Отправьте номера одним из способов:\n"
        "• Сообщением — по одному в строке (можно через запятую или пробел). "
        "В одно сообщение помещается примерно 300 номеров, можно отправить несколько.\n"
        "• Файлом Excel (.xlsx) — номера в первой колонке или в колонке с заголовком "
        "serial_number (по желанию ещё batch_id). Файл до 20 МБ.\n\n"
        "Регистр и пробелы не важны, повторы и уже загруженные номера пропускаются.\n"
        "/done — завершить, /cancel — выйти."
    )


@import_router.message(Command("import"))
async def cmd_import(message: Message, state: FSMContext) -> None:
    batch_id = make_batch_id(get_settings().report_timezone)
    await state.set_state(ImportStates.waiting)
    await state.set_data({"batch_id": batch_id, "inserted": 0, "existing": 0})
    await message.answer(instructions_text(batch_id))


@import_router.message(ImportStates.waiting, Command("done"))
async def cmd_done(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await message.answer(
        f"Загрузка завершена (партия {data['batch_id']}).\n"
        f"Всего добавлено новых: {data['inserted']}, уже были в базе: {data['existing']}."
    )


@import_router.message(ImportStates.waiting, Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Режим загрузки закрыт. Уже загруженные номера остались в базе.")


async def _import_and_report(
    message: Message, state: FSMContext, session: AsyncSession, parsed: ParsedSerials
) -> None:
    if not parsed.rows and not parsed.invalid:
        await message.answer("Не нашёл ни одного номера. Проверьте формат и отправьте ещё раз.")
        return

    result = await SerialImportService(session).import_rows(parsed.rows)
    data = await state.get_data()
    await state.update_data(
        inserted=data["inserted"] + result.inserted,
        existing=data["existing"] + result.existing,
    )
    await message.answer(format_import_result(parsed, result))


@import_router.message(ImportStates.waiting, F.text & ~F.text.startswith("/"))
async def on_import_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await _import_and_report(message, state, session, parse_text(message.text, data["batch_id"]))


@import_router.message(ImportStates.waiting, F.document)
async def on_import_document(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    document = message.document
    if not (document.file_name or "").lower().endswith(".xlsx"):
        await message.answer("Поддерживаются только файлы Excel .xlsx.")
        return
    if document.file_size is not None and document.file_size > MAX_FILE_SIZE:
        await message.answer(
            "Файл больше 20 МБ — Telegram не даст боту его скачать. Разбейте на части."
        )
        return

    await message.answer("⏳ Обрабатываю файл…")
    content = await bot.download(document)
    data = await state.get_data()
    try:
        parsed = await asyncio.to_thread(parse_xlsx, content.read(), data["batch_id"])
    except Exception:
        logger.exception("Failed to parse uploaded xlsx %s", document.file_name)
        await message.answer("Не удалось прочитать файл. Убедитесь, что это корректный .xlsx.")
        return
    await _import_and_report(message, state, session, parsed)


@import_router.message(ImportStates.waiting)
async def on_import_other(message: Message) -> None:
    await message.answer("Отправьте номера текстом или файлом .xlsx. /done — завершить.")

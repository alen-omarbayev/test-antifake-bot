from datetime import datetime
from io import BytesIO
from itertools import count
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot, Dispatcher
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.types import Chat, Document, Message, Update, User
from openpyxl import Workbook

from bot.config.settings import Settings
from bot.handlers.serial_import import MAX_FILE_SIZE, import_router
from bot.services.serial_import_service import ImportResult

BATCH_ID = "tg-20261009-1200"
NON_ADMIN_ID = 999

# FSM state is keyed by chat + user, so a fresh user per test gives a clean state
# while all tests share one Dispatcher.
_user_ids = count(1000)


class RecordingBot(Bot):
    """Bot that records outgoing API calls instead of sending them to Telegram."""

    def __init__(self) -> None:
        super().__init__(token="42:TEST")
        self.calls: list[TelegramMethod] = []

    async def __call__(self, method, request_timeout=None):
        self.calls.append(method)
        return True

    @property
    def replies(self) -> list[str]:
        return [call.text for call in self.calls if isinstance(call, SendMessage)]


def make_xlsx(rows: list[list]) -> bytes:
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def user_id() -> int:
    return next(_user_ids)


@pytest.fixture
def importer(user_id):
    """Fake SerialImportService: serials starting with "OLD" count as already in the DB."""
    calls: list[list[dict]] = []

    async def import_rows(rows):
        calls.append(rows)
        existing = sum(row["serial_number"].startswith("OLD") for row in rows)
        return ImportResult(inserted=len(rows) - existing, existing=existing)

    service = MagicMock()
    service.import_rows = AsyncMock(side_effect=import_rows)
    settings = Settings(bot_token="t", database_url="db", admin_ids=frozenset({user_id}))
    with (
        patch("bot.handlers.admin.get_settings", return_value=settings),
        patch("bot.handlers.serial_import.get_settings", return_value=settings),
        patch("bot.handlers.serial_import.make_batch_id", return_value=BATCH_ID),
        patch("bot.handlers.serial_import.SerialImportService", return_value=service),
    ):
        yield calls


@pytest.fixture
def bot():
    return RecordingBot()


@pytest.fixture(scope="module")
def dp():
    # import_router is a module-level singleton and can be attached to only one parent,
    # so the whole module shares one Dispatcher.
    dispatcher = Dispatcher()
    dispatcher.include_router(import_router)
    return dispatcher


@pytest.fixture
def send(dp, bot, user_id):
    update_ids = count(1)

    async def _send(
        text: str | None = None, document: Document | None = None, sender_id: int | None = None
    ):
        sender_id = sender_id or user_id
        message = Message(
            message_id=next(update_ids),
            date=datetime.now(),
            chat=Chat(id=sender_id, type="private"),
            from_user=User(id=sender_id, is_bot=False, first_name="Tester"),
            text=text,
            document=document,
        )
        bot.calls.clear()
        handled = await dp.feed_update(
            bot, Update(update_id=message.message_id, message=message), session=MagicMock()
        )
        return bot.replies, handled

    return _send


def xlsx_document(name="serials.xlsx", size=1024) -> Document:
    return Document(file_id="f1", file_unique_id="u1", file_name=name, file_size=size)


async def test_non_admin_is_ignored(send, importer):
    replies, handled = await send("/import", sender_id=NON_ADMIN_ID)

    assert replies == []
    assert handled is not True


async def test_text_outside_import_mode_is_not_handled(send, importer):
    replies, _ = await send("ABC1 ABC2")

    assert replies == []
    assert importer == []


async def test_import_shows_instructions_with_batch_id(send, importer):
    replies, _ = await send("/import")

    assert len(replies) == 1
    assert BATCH_ID in replies[0]


async def test_text_is_imported_and_totals_accumulate(send, importer):
    await send("/import")

    replies, _ = await send("abc1, abc2\nOLD1 abc1")
    assert importer[0] == [
        {"serial_number": "ABC1", "batch_id": BATCH_ID},
        {"serial_number": "ABC2", "batch_id": BATCH_ID},
        {"serial_number": "OLD1", "batch_id": BATCH_ID},
    ]
    assert "Добавлено новых: 2, уже были в базе: 1, повторов: 1" in replies[0]

    await send("abc3")
    replies, _ = await send("/done")
    assert f"партия {BATCH_ID}" in replies[0]
    assert "Всего добавлено новых: 3, уже были в базе: 1" in replies[0]


async def test_done_leaves_import_mode(send, importer):
    await send("/import")
    await send("/done")

    replies, _ = await send("ABC1")

    assert replies == []
    assert importer == []


async def test_cancel_leaves_import_mode(send, importer):
    await send("/import")

    replies, _ = await send("/cancel")
    assert "Режим загрузки закрыт" in replies[0]

    replies, _ = await send("ABC1")
    assert replies == []
    assert importer == []


async def test_text_without_serials_is_not_imported(send, importer):
    await send("/import")

    replies, _ = await send(" ,; ")

    assert "Не нашёл ни одного номера" in replies[0]
    assert importer == []


async def test_unknown_command_in_import_mode_gets_hint(send, importer):
    await send("/import")

    replies, _ = await send("/stats")

    assert "Отправьте номера текстом или файлом .xlsx" in replies[0]
    assert importer == []


async def test_xlsx_document_is_imported(send, importer, bot):
    await send("/import")
    bot.download = AsyncMock(
        return_value=BytesIO(make_xlsx([["serial_number", "batch_id"], ["x1", "b-7"], ["x2", None]]))
    )

    replies, _ = await send(document=xlsx_document())

    assert replies[0] == "⏳ Обрабатываю файл…"
    assert importer[0] == [
        {"serial_number": "X1", "batch_id": "b-7"},
        {"serial_number": "X2", "batch_id": BATCH_ID},
    ]
    assert "Добавлено новых: 2" in replies[1]


async def test_non_xlsx_document_is_rejected(send, importer, bot):
    await send("/import")
    bot.download = AsyncMock()

    replies, _ = await send(document=xlsx_document(name="serials.csv"))

    assert replies == ["Поддерживаются только файлы Excel .xlsx."]
    bot.download.assert_not_called()


async def test_too_large_document_is_rejected(send, importer, bot):
    await send("/import")
    bot.download = AsyncMock()

    replies, _ = await send(document=xlsx_document(size=MAX_FILE_SIZE + 1))

    assert "больше 20 МБ" in replies[0]
    bot.download.assert_not_called()


async def test_broken_xlsx_reports_error(send, importer, bot):
    await send("/import")
    bot.download = AsyncMock(return_value=BytesIO(b"not an xlsx"))

    replies, _ = await send(document=xlsx_document())

    assert "Не удалось прочитать файл" in replies[-1]
    assert importer == []

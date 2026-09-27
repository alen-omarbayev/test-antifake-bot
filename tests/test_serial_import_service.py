from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, patch

from openpyxl import Workbook

from bot.services.serial_import_service import (
    CHUNK_SIZE,
    ImportResult,
    ParsedSerials,
    SerialImportService,
    format_import_result,
    make_batch_id,
    parse_text,
    parse_xlsx,
)


def make_xlsx(rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_parse_text_splits_normalizes_and_dedupes():
    parsed = parse_text(" abc1\nABC2, abc3;abc1  abc4\n\n", "tg-1")

    assert [row["serial_number"] for row in parsed.rows] == ["ABC1", "ABC2", "ABC3", "ABC4"]
    assert all(row["batch_id"] == "tg-1" for row in parsed.rows)
    assert parsed.duplicates == 1
    assert parsed.invalid == []


def test_parse_text_rejects_too_long_serial():
    parsed = parse_text("ok1 " + "x" * 65, None)

    assert [row["serial_number"] for row in parsed.rows] == ["OK1"]
    assert parsed.invalid == ["X" * 65]


def test_parse_xlsx_with_header_uses_file_batch_id():
    data = make_xlsx(
        [
            ["Batch_ID", "Serial_Number"],
            ["lot-1", "abc1"],
            [None, "abc2"],
            [None, None],
            ["lot-2", "abc1"],
        ]
    )

    parsed = parse_xlsx(data, "tg-1")

    assert parsed.rows == [
        {"serial_number": "ABC1", "batch_id": "lot-1"},
        {"serial_number": "ABC2", "batch_id": "tg-1"},
    ]
    assert parsed.duplicates == 1


def test_parse_xlsx_without_header_reads_first_column():
    data = make_xlsx([["abc1", "ignored"], [123456], [123456.0], ["abc2"]])

    parsed = parse_xlsx(data, "tg-1")

    assert [row["serial_number"] for row in parsed.rows] == ["ABC1", "123456", "ABC2"]
    assert parsed.duplicates == 1


def test_parse_xlsx_empty_sheet():
    assert parse_xlsx(make_xlsx([]), "tg-1").rows == []


async def test_import_rows_chunks_and_counts():
    rows = [{"serial_number": f"S{i}", "batch_id": None} for i in range(CHUNK_SIZE + 5)]
    with patch("bot.services.serial_import_service.SerialNumberRepository") as repo_cls:
        repo_cls.return_value.bulk_upsert = AsyncMock(side_effect=[CHUNK_SIZE - 10, 5])

        result = await SerialImportService(session=object()).import_rows(rows)

    chunks = [call.args[0] for call in repo_cls.return_value.bulk_upsert.await_args_list]
    assert [len(chunk) for chunk in chunks] == [CHUNK_SIZE, 5]
    assert result == ImportResult(inserted=CHUNK_SIZE - 5, existing=10)


async def test_import_rows_empty_does_not_touch_db():
    with patch("bot.services.serial_import_service.SerialNumberRepository") as repo_cls:
        repo_cls.return_value.bulk_upsert = AsyncMock()

        result = await SerialImportService(session=object()).import_rows([])

    repo_cls.return_value.bulk_upsert.assert_not_awaited()
    assert result == ImportResult(inserted=0, existing=0)


def test_make_batch_id_uses_local_time():
    now = datetime(2026, 9, 28, 20, 30, tzinfo=timezone.utc)

    assert make_batch_id("Asia/Dushanbe", now=now) == "tg-20260929-0130"


def test_format_import_result_escapes_invalid_examples():
    parsed = ParsedSerials(duplicates=2, invalid=["<B>" + "X" * 70])

    text = format_import_result(parsed, ImportResult(inserted=10, existing=3))

    assert "Добавлено новых: 10, уже были в базе: 3, повторов: 2, некорректных: 1" in text
    assert "&lt;B&gt;" in text
    assert "<B>" not in text

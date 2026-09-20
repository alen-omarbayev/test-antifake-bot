import pytest

from scripts.import_serials import read_rows


def test_read_rows_normalizes_and_strips(tmp_path):
    csv_path = tmp_path / "serials.csv"
    csv_path.write_text(
        "serial_number,batch_id\n abc123 ,batch1\ndef456,\n", encoding="utf-8"
    )

    rows = read_rows(csv_path)

    assert rows == [
        {"serial_number": "ABC123", "batch_id": "batch1"},
        {"serial_number": "DEF456", "batch_id": None},
    ]


def test_read_rows_missing_serial_number_column(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("foo,bar\n1,2\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        read_rows(csv_path)


def test_read_rows_skips_blank_serial(tmp_path):
    csv_path = tmp_path / "serials.csv"
    csv_path.write_text("serial_number,batch_id\n,batch1\nABC,batch2\n", encoding="utf-8")

    rows = read_rows(csv_path)

    assert rows == [{"serial_number": "ABC", "batch_id": "batch2"}]

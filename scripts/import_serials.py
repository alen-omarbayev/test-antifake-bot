import argparse
import asyncio
import csv
from collections.abc import Sequence
from pathlib import Path

from bot.db.engine import get_sessionmaker
from bot.services.normalization import normalize_serial
from bot.services.serial_import_service import SerialImportService


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk import serial numbers from a CSV file.")
    parser.add_argument("csv_path", type=Path, help="Path to CSV with a serial_number column")
    return parser.parse_args(argv)


def read_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "serial_number" not in reader.fieldnames:
            raise SystemExit("CSV must contain a 'serial_number' column.")

        rows: list[dict] = []
        for raw_row in reader:
            serial = (raw_row.get("serial_number") or "").strip()
            if not serial:
                continue
            batch_id = (raw_row.get("batch_id") or "").strip() or None
            rows.append({"serial_number": normalize_serial(serial), "batch_id": batch_id})
        return rows


async def import_serials(csv_path: Path) -> None:
    rows = read_rows(csv_path)

    async with get_sessionmaker()() as session:
        result = await SerialImportService(session).import_rows(rows)
        await session.commit()

    print(
        f"Processed {len(rows)} rows, inserted {result.inserted} new, "
        f"{result.existing} already existed."
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(import_serials(args.csv_path))


if __name__ == "__main__":
    main()

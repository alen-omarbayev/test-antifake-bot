import argparse
import asyncio
import csv
from collections.abc import Sequence
from pathlib import Path

from bot.db.engine import get_sessionmaker
from bot.repositories.serial_number_repository import SerialNumberRepository
from bot.services.normalization import normalize_serial

CHUNK_SIZE = 1000


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


def _chunks(rows: list[dict], size: int) -> list[list[dict]]:
    return [rows[i : i + size] for i in range(0, len(rows), size)]


async def import_serials(csv_path: Path) -> None:
    rows = read_rows(csv_path)
    inserted = 0

    async with get_sessionmaker()() as session:
        repo = SerialNumberRepository(session)
        for chunk in _chunks(rows, CHUNK_SIZE):
            inserted += await repo.bulk_upsert(chunk)
        await session.commit()

    print(
        f"Processed {len(rows)} rows, inserted {inserted} new, "
        f"{len(rows) - inserted} already existed."
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(import_serials(args.csv_path))


if __name__ == "__main__":
    main()

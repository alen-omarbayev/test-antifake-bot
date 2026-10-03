import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path

from bot.config.settings import get_settings
from bot.db.engine import dispose_engine, get_sessionmaker
from bot.services.analytics_export_service import AnalyticsExportService, render_xlsx
from bot.services.analytics_report_service import AnalyticsReportService, format_report

DEFAULT_DAYS = 7
MAX_DAYS = 365


def _days(value: str) -> int:
    days = int(value)
    if not 1 <= days <= MAX_DAYS:
        raise argparse.ArgumentTypeError(f"must be between 1 and {MAX_DAYS}")
    return days


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print bot analytics report.")
    parser.add_argument(
        "--days", type=_days, default=DEFAULT_DAYS, help=f"Period length (default {DEFAULT_DAYS})"
    )
    parser.add_argument("--xlsx", type=Path, help="Also save the report as an Excel file")
    return parser.parse_args(argv)


async def run(days: int, xlsx_path: Path | None = None) -> None:
    tz = get_settings().report_timezone
    export = None
    try:
        async with get_sessionmaker()() as session:
            if xlsx_path is None:
                report = await AnalyticsReportService(session, tz).build(days)
            else:
                export = await AnalyticsExportService(session, tz).build(days)
                report = export.report
    finally:
        await dispose_engine()
    print(format_report(report))
    if export is not None:
        xlsx_path.write_bytes(render_xlsx(export))
        print(f"\nExcel saved to {xlsx_path} ({len(export.events)} events)")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(run(args.days, args.xlsx))


if __name__ == "__main__":
    main()

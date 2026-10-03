import asyncio

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import get_settings
from bot.services.analytics_export_service import (
    AnalyticsExportService,
    export_filename,
    render_xlsx,
)
from bot.services.analytics_report_service import AnalyticsReportService, format_report

admin_router = Router(name="admin")

DEFAULT_STATS_DAYS = 7
MAX_STATS_DAYS = 90
STATS_USAGE_TEXT = (
    f"Использование: /stats [дни] или /stats_export [дни], от 1 до {MAX_STATS_DAYS}. "
    f"По умолчанию {DEFAULT_STATS_DAYS}."
)


def is_admin(message: Message) -> bool:
    # Read settings at call time so importing handlers does not require a configured .env.
    return message.from_user is not None and message.from_user.id in get_settings().admin_ids


def parse_stats_days(args: str | None) -> int | None:
    if not args or not args.strip():
        return DEFAULT_STATS_DAYS
    try:
        days = int(args.strip())
    except ValueError:
        return None
    return days if 1 <= days <= MAX_STATS_DAYS else None


@admin_router.message(Command("stats"), is_admin)
async def cmd_stats(message: Message, command: CommandObject, session: AsyncSession) -> None:
    days = parse_stats_days(command.args)
    if days is None:
        await message.answer(STATS_USAGE_TEXT)
        return

    report = await AnalyticsReportService(session, get_settings().report_timezone).build(days)
    await message.answer(format_report(report))


@admin_router.message(Command("stats_export"), is_admin)
async def cmd_stats_export(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    days = parse_stats_days(command.args)
    if days is None:
        await message.answer(STATS_USAGE_TEXT)
        return

    await message.answer("⏳ Готовлю файл…")
    export = await AnalyticsExportService(session, get_settings().report_timezone).build(days)
    content = await asyncio.to_thread(render_xlsx, export)
    caption = f"📊 Отчёт за {days} дн., событий: {len(export.events)}"
    if export.truncated:
        caption += " (обрезано, см. лист «Сводка»)"
    await message.answer_document(
        BufferedInputFile(content, filename=export_filename(export.report)), caption=caption
    )

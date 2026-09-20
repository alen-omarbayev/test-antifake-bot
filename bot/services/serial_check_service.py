from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.analytics.tracker import AnalyticsTracker
from bot.models.user import User
from bot.repositories.serial_number_repository import SerialNumberRepository
from bot.services.normalization import normalize_serial


@dataclass(frozen=True)
class SerialCheckResult:
    found: bool
    is_active: bool | None
    normalized_serial: str
    batch_id: str | None


class SerialCheckService:
    def __init__(self, session: AsyncSession) -> None:
        self._serials = SerialNumberRepository(session)
        self._analytics = AnalyticsTracker(session)

    async def check(self, user: User, raw_serial: str) -> SerialCheckResult:
        normalized = normalize_serial(raw_serial)
        row = await self._serials.get_by_serial(normalized)

        if row is None:
            await self._analytics.track_serial_check_failed(user.id, normalized, "not_found")
            return SerialCheckResult(
                found=False, is_active=None, normalized_serial=normalized, batch_id=None
            )

        if not row.is_active:
            await self._analytics.track_serial_check_failed(user.id, normalized, "inactive")
            return SerialCheckResult(
                found=False,
                is_active=False,
                normalized_serial=normalized,
                batch_id=row.batch_id,
            )

        await self._analytics.track_serial_check_success(user.id, normalized, row.batch_id)
        return SerialCheckResult(
            found=True, is_active=True, normalized_serial=normalized, batch_id=row.batch_id
        )

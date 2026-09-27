import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

DEFAULT_REPORT_TIMEZONE = "Asia/Dushanbe"


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    admin_ids: frozenset[int] = frozenset()
    report_timezone: str = DEFAULT_REPORT_TIMEZONE


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set. Check your .env file.")
    return value


def _parse_admin_ids(raw: str | None) -> frozenset[int]:
    if not raw:
        return frozenset()
    try:
        return frozenset(int(part) for part in raw.split(",") if part.strip())
    except ValueError:
        raise RuntimeError(
            f"ADMIN_IDS must be a comma-separated list of Telegram user ids, got {raw!r}."
        ) from None


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        bot_token=_require_env("BOT_TOKEN"),
        database_url=_require_env("DATABASE_URL"),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
        report_timezone=os.getenv("REPORT_TIMEZONE") or DEFAULT_REPORT_TIMEZONE,
    )

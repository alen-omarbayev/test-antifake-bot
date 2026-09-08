import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set. Check your .env file.")
    return value


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        bot_token=_require_env("BOT_TOKEN"),
        database_url=_require_env("DATABASE_URL"),
    )

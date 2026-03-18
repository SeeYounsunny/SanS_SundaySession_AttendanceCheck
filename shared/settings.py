from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str

    field_bot_token: str | None = None
    admin_bot_token: str | None = None

    admin_user_ids: set[int] = frozenset()


def _parse_admin_user_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        field_bot_token=os.environ.get("FIELD_BOT_TOKEN"),
        admin_bot_token=os.environ.get("ADMIN_BOT_TOKEN"),
        admin_user_ids=_parse_admin_user_ids(os.environ.get("ADMIN_USER_IDS")),
    )


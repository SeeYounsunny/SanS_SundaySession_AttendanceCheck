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


def _normalize_database_url(url: str) -> str:
    """Use postgresql+psycopg:// (psycopg3) so SQLAlchemy doesn't load psycopg2."""
    # Force psycopg (v3) driver; we install psycopg[binary], not psycopg2
    if "psycopg2" in url:
        url = url.replace("postgresql+psycopg2", "postgresql+psycopg", 1)
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if "sslmode=" not in url:
        url += "&sslmode=require" if "?" in url else "?sslmode=require"
    return url


def get_settings() -> Settings:
    raw = os.environ.get("DATABASE_URL") or ""
    if not raw:
        raise RuntimeError("DATABASE_URL is not set")
    return Settings(
        database_url=_normalize_database_url(raw),
        field_bot_token=os.environ.get("FIELD_BOT_TOKEN"),
        admin_bot_token=os.environ.get("ADMIN_BOT_TOKEN"),
        admin_user_ids=_parse_admin_user_ids(os.environ.get("ADMIN_USER_IDS")),
    )


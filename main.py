from __future__ import annotations

import os


def main() -> None:
    """
    Railway/Railpack fallback entrypoint.

    Railpack may auto-run `main.py` at repo root when no framework is detected.
    We dispatch to the correct bot by environment variable.
    """
    role = (os.environ.get("BOT_ROLE") or "").strip().lower()

    if role in {"field", "field_bot", "field-bot"}:
        from field_bot.main import main as run

        run()
        return

    if role in {"admin", "admin_bot", "admin-bot"}:
        from admin_bot.main import main as run

        run()
        return

    raise SystemExit(
        "BOT_ROLE env var is required. Set BOT_ROLE=field or BOT_ROLE=admin for each Railway service."
    )


if __name__ == "__main__":
    main()


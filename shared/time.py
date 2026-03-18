from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


KST = timezone(timedelta(hours=9))

# Session policy (KST)
# - Opens: Sunday 20:50
# - Check-in allowed: Sunday 21:00–23:00
SESSION_OPEN_AT = time(20, 50)
SESSION_CHECKIN_START = time(21, 0)
SESSION_CHECKIN_END = time(23, 0)


def now_kst() -> datetime:
    return datetime.now(tz=KST)


def week_start_date_kst(d: date) -> date:
    """
    Week key: Monday-based week start in KST.
    """
    return d - timedelta(days=d.weekday())


def current_week_start_kst() -> date:
    return week_start_date_kst(now_kst().date())


def most_recent_sunday_kst(d: date) -> date:
    # weekday(): Mon=0 ... Sun=6
    days_since_sunday = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sunday)


def current_session_date_kst(now: datetime | None = None) -> date:
    """
    Returns the most recent Sunday date in KST.
    (The session happens every Sunday night, so the session key is that Sunday date.)
    """
    n = now or now_kst()
    return most_recent_sunday_kst(n.date())


def checkin_allowed_kst(now: datetime | None = None) -> tuple[bool, str, date]:
    """
    Returns: (allowed, message, session_date)
    - allowed: True only on Sunday between 21:00 (inclusive) and 23:00 (exclusive)
    - message: user-facing reason when not allowed
    - session_date: the Sunday date used for uniqueness/stat keys
    """
    n = now or now_kst()
    session_date = most_recent_sunday_kst(n.date())

    if n.weekday() != 6:
        return (
            False,
            "출석은 매주 일요일 정규세션(21:00–23:00, KST)에만 가능해요.",
            session_date,
        )

    t = n.timetz().replace(tzinfo=None)
    if t < SESSION_OPEN_AT:
        return (
            False,
            "아직 세션이 열리지 않았어요. 세션은 20:50(KST)에 열리고, 출석은 21:00부터 가능해요.",
            session_date,
        )
    if t < SESSION_CHECKIN_START:
        return (
            False,
            "세션은 열려있어요(20:50). 출석은 21:00부터 가능해요.",
            session_date,
        )
    if t >= SESSION_CHECKIN_END:
        return (
            False,
            "출석 가능 시간이 끝났어요. 출석은 21:00–23:00(KST) 사이만 가능해요.",
            session_date,
        )

    return True, "OK", session_date


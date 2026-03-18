from __future__ import annotations

from datetime import date

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from shared.models import Checkin, GroupChat
from shared.time import now_kst


def upsert_group_pending(session: Session, chat_id: int, title: str | None) -> GroupChat:
    existing = session.execute(select(GroupChat).where(GroupChat.chat_id == chat_id)).scalar_one_or_none()
    ts = now_kst()
    if existing:
        existing.title = title
        existing.updated_at = ts
        return existing

    group = GroupChat(
        chat_id=chat_id,
        title=title,
        is_enabled=False,
        enabled_at=None,
        created_at=ts,
        updated_at=ts,
    )
    session.add(group)
    return group


def enable_group(session: Session, chat_id: int) -> bool:
    ts = now_kst()
    res = session.execute(
        update(GroupChat)
        .where(GroupChat.chat_id == chat_id)
        .values(is_enabled=True, enabled_at=ts, updated_at=ts)
    )
    return res.rowcount > 0


def list_groups(session: Session) -> list[GroupChat]:
    return list(session.execute(select(GroupChat).order_by(GroupChat.created_at.desc())).scalars().all())


def get_group(session: Session, chat_id: int) -> GroupChat | None:
    return session.execute(select(GroupChat).where(GroupChat.chat_id == chat_id)).scalar_one_or_none()


def create_checkin(
    session: Session,
    chat_id: int,
    week_date: date,
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> Checkin:
    ts = now_kst()
    checkin = Checkin(
        chat_id=chat_id,
        week_date=week_date,
        user_id=user_id,
        user_username=username,
        user_first_name=first_name,
        user_last_name=last_name,
        created_at=ts,
    )
    session.add(checkin)
    return checkin


def count_checkins_by_week(session: Session) -> list[tuple[int, date, int]]:
    """
    Returns rows: (chat_id, week_date, count)
    """
    stmt: Select = (
        select(Checkin.chat_id, Checkin.week_date, func.count().label("cnt"))
        .group_by(Checkin.chat_id, Checkin.week_date)
        .order_by(Checkin.week_date.desc())
    )
    rows = session.execute(stmt).all()
    return [(int(r[0]), r[1], int(r[2])) for r in rows]


def count_checkins_for_group_week(session: Session, chat_id: int, week_date: date) -> int:
    stmt = select(func.count()).select_from(Checkin).where(Checkin.chat_id == chat_id, Checkin.week_date == week_date)
    return int(session.execute(stmt).scalar_one())


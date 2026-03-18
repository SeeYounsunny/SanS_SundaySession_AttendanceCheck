from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class GroupChat(Base):
    __tablename__ = "group_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    checkins: Mapped[list["Checkin"]] = relationship(back_populates="group")


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("group_chats.chat_id", ondelete="CASCADE"), nullable=False)
    week_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    group: Mapped[GroupChat] = relationship(back_populates="checkins", primaryjoin="Checkin.chat_id==GroupChat.chat_id")

    __table_args__ = (
        UniqueConstraint("chat_id", "week_date", "user_id", name="uq_checkins_chat_week_user"),
        Index("ix_checkins_chat_week", "chat_id", "week_date"),
    )


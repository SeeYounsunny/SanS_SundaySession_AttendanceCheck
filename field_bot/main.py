from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ChatMemberHandler, CommandHandler, ContextTypes
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

from shared.db import create_db_engine, make_session_factory, session_scope
from shared.queries import create_checkin, get_group, upsert_group_pending
from shared.settings import get_settings
from shared.time import checkin_allowed_kst


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("field_bot")


def _is_group_chat(update: Update) -> bool:
    chat = update.effective_chat
    if not chat:
        return False
    return chat.type in ("group", "supergroup")


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    session_factory = context.application.bot_data["session_factory"]

    with session_scope(session_factory) as session:
        upsert_group_pending(session, chat_id=chat.id, title=chat.title)


async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_group_chat(update):
        await update.effective_message.reply_text("이 명령은 조 단체방에서만 사용할 수 있어요.")
        return

    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    allowed, msg, session_date = checkin_allowed_kst()
    if not allowed:
        await update.effective_message.reply_text(msg)
        return

    session_factory = context.application.bot_data["session_factory"]
    week_date = session_date

    with session_scope(session_factory) as session:
        group = get_group(session, chat_id=chat.id)
        if not group:
            upsert_group_pending(session, chat_id=chat.id, title=chat.title)
            await update.effective_message.reply_text("그룹이 아직 등록되지 않았어요. 운영자가 enable 하면 출석이 가능해요.")
            return

        if not group.is_enabled:
            await update.effective_message.reply_text("이 그룹은 아직 운영자가 enable 하지 않았어요. 운영봇에서 enable 후 다시 시도해 주세요.")
            return

        try:
            create_checkin(
                session,
                chat_id=chat.id,
                week_date=week_date,
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            # Trigger unique constraint (chat_id, week_date, user_id) early
            session.flush()
        except IntegrityError:
            session.rollback()
            # unique(chat_id, week_date, user_id)
            await update.effective_message.reply_text(f"이미 이번 세션 출석이 기록되어 있어요. (세션 날짜: {week_date})")
            return

    await update.effective_message.reply_text(f"출석 완료. (세션 날짜: {week_date})")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "현장봇 명령\n"
        "- /checkin : 이번 주 출석 기록\n"
    )


def main() -> None:
    load_dotenv()
    settings = get_settings()
    if not settings.field_bot_token:
        raise RuntimeError("FIELD_BOT_TOKEN is required")

    engine = create_db_engine()
    session_factory = make_session_factory(engine)

    app = Application.builder().token(settings.field_bot_token).build()
    app.bot_data["engine"] = engine
    app.bot_data["session_factory"] = session_factory

    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("checkin", cmd_checkin))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))

    logger.info("field bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


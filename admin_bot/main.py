from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from dotenv import load_dotenv

from shared.db import create_db_engine, make_session_factory, session_scope
from shared.queries import count_checkins_by_week, count_checkins_for_group_week, enable_group, get_group, list_groups
from shared.settings import get_settings
from shared.time import current_session_date_kst


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("admin_bot")


def _is_admin(update: Update) -> bool:
    settings = get_settings()
    user = update.effective_user
    if not user:
        return False
    return (not settings.admin_user_ids) or (user.id in settings.admin_user_ids)


async def _reject_if_not_admin(update: Update) -> bool:
    if _is_admin(update):
        return False
    await update.effective_message.reply_text("권한이 없어요.")
    return True


def _groups_keyboard(groups) -> InlineKeyboardMarkup:
    rows = []
    for g in groups:
        label = f"{'✅' if g.is_enabled else '🕗'} {g.title or '(no title)'}"
        rows.append(
            [
                InlineKeyboardButton(label, callback_data=f"group:{g.chat_id}"),
                InlineKeyboardButton("enable", callback_data=f"enable:{g.chat_id}"),
            ]
        )
    return InlineKeyboardMarkup(rows or [[InlineKeyboardButton("없음", callback_data="noop")]])


async def cmd_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return

    session_factory = context.application.bot_data["session_factory"]
    with session_scope(session_factory) as session:
        groups = list_groups(session)

    await update.effective_message.reply_text(
        "그룹 목록 (🕗 pending / ✅ enabled)\n"
        "버튼으로 enable 하거나, `/enable <chat_id>`를 사용할 수 있어요.",
        reply_markup=_groups_keyboard(groups),
    )


async def cmd_enable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return

    if not context.args:
        await update.effective_message.reply_text("사용법: /enable <chat_id>")
        return

    chat_id = int(context.args[0])
    session_factory = context.application.bot_data["session_factory"]
    with session_scope(session_factory) as session:
        ok = enable_group(session, chat_id=chat_id)
    await update.effective_message.reply_text("enable 완료" if ok else "해당 chat_id 그룹을 찾지 못했어요.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return

    session_factory = context.application.bot_data["session_factory"]
    session_date = current_session_date_kst()

    with session_scope(session_factory) as session:
        groups = {g.chat_id: g for g in list_groups(session)}
        weekly = []
        for chat_id, g in groups.items():
            cnt = count_checkins_for_group_week(session, chat_id=chat_id, week_date=session_date)
            weekly.append((g, cnt))

        all_rows = count_checkins_by_week(session)

    lines = [f"정규세션 통계 (세션 날짜: {session_date})"]
    for g, cnt in sorted(weekly, key=lambda x: (x[0].is_enabled is False, -(x[1]))):
        status = "✅" if g.is_enabled else "🕗"
        lines.append(f"- {status} {g.title or '(no title)'} ({g.chat_id}): {cnt}")

    lines.append("")
    lines.append("전체(그룹/주차별) 카운트(최근순)")
    for chat_id, week_date, cnt in all_rows[:20]:
        title = groups.get(chat_id).title if chat_id in groups else None
        lines.append(f"- {title or '(unknown)'} ({chat_id}) / {week_date}: {cnt}")

    await update.effective_message.reply_text("\n".join(lines))


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    q = update.callback_query
    await q.answer()

    if await _reject_if_not_admin(update):
        return

    data = q.data or ""
    session_factory = context.application.bot_data["session_factory"]

    if data.startswith("enable:"):
        chat_id = int(data.split(":", 1)[1])
        with session_scope(session_factory) as session:
            ok = enable_group(session, chat_id=chat_id)
        await q.edit_message_text("enable 완료" if ok else "실패: 그룹을 찾지 못했어요.")
        return

    if data.startswith("group:"):
        chat_id = int(data.split(":", 1)[1])
        with session_scope(session_factory) as session:
            g = get_group(session, chat_id=chat_id)
        if not g:
            await q.edit_message_text("그룹을 찾지 못했어요.")
            return
        await q.edit_message_text(
            f"그룹 상세\n"
            f"- title: {g.title}\n"
            f"- chat_id: {g.chat_id}\n"
            f"- enabled: {g.is_enabled}\n"
        )
        return

    # noop or unknown
    return


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    await update.effective_message.reply_text(
        "운영봇 명령\n"
        "- /groups : 그룹 목록 + enable 버튼\n"
        "- /enable <chat_id> : 그룹 enable\n"
        "- /stats : 주간/전체 통계\n"
    )


def main() -> None:
    load_dotenv()
    settings = get_settings()
    if not settings.admin_bot_token:
        raise RuntimeError("ADMIN_BOT_TOKEN is required")

    engine = create_db_engine()
    session_factory = make_session_factory(engine)

    app = Application.builder().token(settings.admin_bot_token).build()
    app.bot_data["engine"] = engine
    app.bot_data["session_factory"] = session_factory

    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("groups", cmd_groups))
    app.add_handler(CommandHandler("enable", cmd_enable))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("admin bot started")
    app.run_polling()


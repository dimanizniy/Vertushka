from telegram import Update
from telegram.ext import ContextTypes
from core.database import set_setting, get_setting, get_station_by_number, get_all_registered_user_tgids, get_all_groups_stats, manual_pay_group, get_station_by_number
from core.database import get_free_stations_with_location
from telegram.constants import ParseMode
from core.utils.permissions import require_role

@require_role("admin")
async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("org_registration_open", "true")
    await update.message.reply_text("Registration for organizers is now open!")

@require_role("admin")
async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("org_registration_open", "false")
    await update.message.reply_text("Registration for organizers is now closed.")

# Begin quest, acces to stations is allowed
@require_role("admin")
async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("quest_started", "true")
    set_setting("quest_ended", "false")
    tgs = get_all_registered_user_tgids()
    text = f"Quest has begun! Type /free to see the list of available stations and take the first one."
    sent = 0
    for tg in set(tgs):
        try:
            await context.bot.send_message(chat_id=tg, text=text)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"Quest started. Notifications sent to registered users ({sent}).")

@require_role("admin")
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("quest_ended", "true")
    await update.message.reply_text("Quest ended. Taking new stations is no longer allowed.")

@require_role("admin")
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Using: /pay <group_number> <N>")
        return
    group = args[0]
    try:
        n = float(args[1])
    except ValueError:
        await update.message.reply_text("N must be a number (can be fractional).")
        return
    res = manual_pay_group(group, n)
    if not res["ok"]:
        await update.message.reply_text(f"Error: {res['error']}")
        return
    await update.message.reply_text(f"Manual payment of {n} points to group {group} completed.")

@require_role("admin")
async def mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Type /mailing <text> to send a message to all registered users.")
        return
    tgs = get_all_registered_user_tgids()
    sent = 0
    for tg in set(tgs):
        try:
            await context.bot.send_message(chat_id=tg, text=text)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"Mailing completed. Sent to: {sent}")

@require_role("admin")
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_all_groups_stats()
    if not rows:
        await update.message.reply_text("There are no registered groups yet.")
        return
    lines = []
    pos = 1
    for r in rows:
        score = float(r["score"] or 0)
        lines.append(f"{pos}. Group {r['group_number']} — {score:.2f}")
        pos += 1
    await update.message.reply_text("\n".join(lines))

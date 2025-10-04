import re
from telegram import Update
from telegram.ext import ContextTypes
from core.database import register_curator, get_group_score_and_history_by_tg, take_station
from core.utils.decorators import role_required
from telegram import Update
from telegram.ext import ContextTypes
from core.utils.permissions import require_role

GROUP_RE = re.compile(r"^1\d{2}$")  # format 1XX

async def reg_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Please specify your group number in format 1XX: /reg_user 123")
        return
    group_number = args[0].strip()
    if not GROUP_RE.match(group_number):
        await update.message.reply_text("Invalid group number format. Expected format is 1XX (e.g. 101).")
        return

    res = register_curator(tg_id, group_number)
    if not res["ok"]:
        await update.message.reply_text(f"Registration error: {res['error']}")
        return
    await update.message.reply_text(f"You are registered as curator of group {group_number}.")

@require_role("curator", "admin")
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_group_score_and_history_by_tg(update.effective_user.id)
    if not data:
        await update.message.reply_text("You are not registered as a curator or an error occurred.")
        return
    g = data["group"]
    hist = data["history"]
    out = [f"Group: {g['group_number']}\nCurrent score: {float(g['score']):.2f}", "\nScore history:"]
    if not hist:
        out.append("— no scores yet.")
    else:
        for r in hist:
            station = r["station_number"] if r["station_number"] else "—"
            points = float(r["points"])
            bonus = float(r["bonus"] or 0)
            out.append(f"{r['timestamp']:%Y-%m-%d %H:%M} — {points} (+{bonus}) — station {station}")
    await update.message.reply_text("\n".join(out))

@require_role("curator", "admin")
async def take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Please specify the station number: /take 3")
        return
    try:
        n = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid station number.")
        return
    res = take_station(tg_id, n)
    if not res["ok"]:
        await update.message.reply_text(f"Failed to take the station: {res['error']}")
        return
    await update.message.reply_text(f"You have successfully taken station {n}")
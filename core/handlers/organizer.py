from telegram import Update
from telegram.ext import ContextTypes
from core.database import register_organizer, get_organizer_station_by_tg, reward_current_group_by_organizer, release_station_by_number, get_station_by_number, get_user_by_tg
from core.utils.decorators import role_required
from core.utils.keyboards import station_free_button
from telegram import Update
from telegram.ext import ContextTypes
from core.utils.permissions import require_role
from core.database import get_connection

async def reg_org(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please specify your station number: /reg_org 3")
        return
    try:
        n = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid station number.")
        return
    res = register_organizer(update.effective_user.id, n)
    if not res["ok"]:
        await update.message.reply_text(f"Registration error: {res['error']}")
        return
    await update.message.reply_text(f"You are registered as organizer of station {n}.")

@require_role("organizer", "admin")
async def station(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = get_organizer_station_by_tg(update.effective_user.id)
    if not st:
        await update.message.reply_text("You are not registered as organizer or station not found.")
        return

    status = "free" if st["is_free"] else "occupied"

    # instead of ID, get group_number from groups table
    group_text = "No group is currently present"
    if st["current_group"]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT group_number FROM groups WHERE id=%s;", (st["current_group"],))
        g = cur.fetchone()
        cur.close()
        conn.close()
        if g:
            group_text = f"Group: {g['group_number']}"
    print(f'st={st}')
    text = (
        f"Number: {st['number']}\n"
        f"Name: {st['name']}\n"
        f"Location: {st['location']}\n"
        f"Status: {status}\n"
        f"{group_text}"
    )

    # "Station free" button
    kb = station_free_button(st["number"])
    await update.message.reply_text(text, reply_markup=kb)

@require_role("organizer", "admin")
async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please specify an integer number of points (1..10): /reward 5")
        return
    try:
        n = int(args[0])
    except ValueError:
        await update.message.reply_text("A whole number is required.")
        return
    if not (1 <= n <= 10):
        await update.message.reply_text("Points must be between 1 and 10.")
        return
    res = reward_current_group_by_organizer(update.effective_user.id, n, 0)
    if not res["ok"]:
        await update.message.reply_text(f"Error: {res['error']}")
        return
    await update.message.reply_text(f"{n} points have been awarded to the current group (id={res['group_id']}).")

@require_role("organizer", "admin")
async def reward_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please specify a bonus (0.0..1.0): /reward_bonus 0.5")
        return
    try:
        v = float(args[0])
    except ValueError:
        await update.message.reply_text("Invalid number format.")
        return
    if not (0.0 <= v <= 1.0):
        await update.message.reply_text("Bonus must be between 0.0 and 1.0.")
        return
    res = reward_current_group_by_organizer(update.effective_user.id, 0, v)
    if not res["ok"]:
        await update.message.reply_text(f"Error: {res['error']}")
        return
    await update.message.reply_text(f"Bonus {v} has been awarded to the current group (id={res['group_id']}).")

@require_role("organizer", "admin")
async def station_free_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /station_free <N> command in case the button does not work
    args = context.args
    if not args:
        await update.message.reply_text("Please specify the station number: /station_free 3")
        return
    try:
        n = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid station number.")
        return
    # check that this is your station
    st = get_organizer_station_by_tg(update.effective_user.id)
    if not st or st["number"] != n:
        await update.message.reply_text("You are not the organizer of this station.")
        return
    release_station_by_number(n)
    await update.message.reply_text(f"Station {n} has been marked as free.")

from telegram import Update
from telegram.ext import ContextTypes
from core.database import get_free_stations_with_location, get_user_role, get_setting
from core.utils.keyboards import station_free_button, free_stations_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_user_role(user.id)
    if role == "curator":
        text = f"Hello, {user.first_name} — you are registered as a curator. Use /help."
    elif role == "organizer":
        text = f"Hello, {user.first_name} — you are registered as an organizer. Use /help."
    elif role == "admin":
        text = f"Hello, {user.first_name} — you are registered as the main organizer. Use /help."
    else:
        text = f"Hello, {user.first_name}! You are not registered. To register, use /reg_user or /reg_org (if registration is open)."

    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_user_role(user.id)
    base = [
        "/start — greeting",
        "/help — help",
        "/free — list of free stations"
    ]
    if role == "curator":
        base += [
            "/reg_user <group_number_in_format_1XX> — register as curator",
            "/info — information about your group",
            "/take <N> — take station №N"
        ]
    if role == "organizer":
        base += [
            "/reg_org <N> — register as organizer of station N",
            "/station — information about your station",
            "/station_free <N> - release station N (if you are the organizer of this station)",
            "/reward <N> — give N main points (1..10)",
            "/reward_bonus <X.Y> — give bonus (0.0..1.0)",
            "Button 'Station free' — mark the station as free"
        ]
    if role == "admin":
        base += [
            "/open — open organizer registration",
            "/close — close organizer registration",
            "/begin — start the quest (send first station)",
            "/end — finish the quest (stations cannot be taken)",
            "/pay <group_number> <N> — manually give N points",
            "/mailing <text> — send a message to everyone",
            "/stats — full statistics by groups"
        ]
    await update.message.reply_text("\n".join(base))

async def free_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    free = get_free_stations_with_location()
    if not free:
        await update.message.reply_text("No free stations available.")
        return
    kb = free_stations_keyboard(free)
    await update.message.reply_text("Free stations:", reply_markup=kb)

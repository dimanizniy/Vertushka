from telegram import Update
from telegram.ext import ContextTypes
from core.database import take_station, get_station_by_number, release_station_by_number, get_user_role
from core.utils.keyboards import free_stations_keyboard
import logging

logger = logging.getLogger(__name__)

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "cancel":
        await query.edit_message_text("Operation cancelled.")
        return

    if data.startswith("take:"):
        # Curator took the station via button
        number = int(data.split(":", 1)[1])
        tg_id = query.from_user.id
        res = take_station(tg_id, number)
        if not res["ok"]:
            await query.edit_message_text(f"Failed to take the station: {res['error']}")
            return
        station = get_station_by_number(number)
        await query.edit_message_text(f"You have successfully taken station {number}.\nName: {station['name']}\nLocation: {station['location']}")
        return

    if data.startswith("free_station:"):
        number = int(data.split(":", 1)[1])
        # Check that the request is made by the organizer of this station
        tg_id = query.from_user.id
        role = get_user_role(tg_id)
        if role != "organizer":
            await query.edit_message_text("Only the organizer can mark the station as free.")
            return
        # снимем отметку
        release_station_by_number(number)
        await query.edit_message_text(f"Station {number} marked as free.")
        return

    # Unrecognized action
    await query.edit_message_text("Unrecognized action.")

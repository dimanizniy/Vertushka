from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def free_stations_keyboard(stations):
    """
    stations: [(number, location), (number, location), ...]
    callback_data: take:<number>
    """
    buttons = []
    for number, location in stations:
        buttons.append([
            InlineKeyboardButton(
                text=f"Take {number} ({location})",
                callback_data=f"take:{number}"
            )
        ])
    # Add a cancel button
    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)

def station_free_button(number):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Station is free", callback_data=f"free_station:{number}")]])

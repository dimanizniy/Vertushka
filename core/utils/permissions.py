from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from core.database import get_user_by_tg, get_user_role   # путь поправь под свой проект
from functools import wraps
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def require_role(*roles):
    """
    Decorator to restrict command access by roles.
    Example: @require_role("admin", "curator")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            tg_id = update.effective_user.id
            role = get_user_role(tg_id)

            if role not in roles:
                await update.message.reply_text("⛔ You do not have permission for this command.")
                return

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

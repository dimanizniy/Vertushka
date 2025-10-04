from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from core.models import SessionLocal
from core.models.user import User

def role_required(required_role):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            session = SessionLocal()
            tg_id = update.effective_user.id
            user = session.query(User).filter_by(tg_id=tg_id).first()
            session.close()

            if not user or user.role != required_role:
                await update.message.reply_text("⛔ You do not have permission for this command.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

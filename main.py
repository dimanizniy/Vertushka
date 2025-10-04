import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from core.config import TOKEN
from core.database import wait_for_db, init_db
from core.handlers.common import start, help_command, free_cmd
from core.handlers.curator import reg_user, info, take
from core.handlers.organizer import reg_org, station, reward, reward_bonus, station_free_cmd
from core.handlers.admin import open_cmd, close_cmd, begin, end, pay, mailing, stats
from core.handlers.callbacks import callback_router
from core.handlers import common, curator, organizer, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_handlers(app):
    # General
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("free", free_cmd))

    # Curator
    app.add_handler(CommandHandler("reg_user", reg_user))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("take", take))

    # Organizer
    app.add_handler(CommandHandler("reg_org", reg_org))
    app.add_handler(CommandHandler("station", station))
    app.add_handler(CommandHandler("reward", reward))
    app.add_handler(CommandHandler("reward_bonus", reward_bonus))
    app.add_handler(CommandHandler("station_free", station_free_cmd))

    # Admin
    app.add_handler(CommandHandler("open", open_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("begin", begin))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("mailing", mailing))
    app.add_handler(CommandHandler("stats", stats))

    # Callback (inline buttons)
    app.add_handler(CallbackQueryHandler(callback_router))

    app.add_handler(CommandHandler("start", common.start))

def main():
    logger.info("Waiting Postgres...")
    wait_for_db()
    logger.info("Database initialization (if needed)...")
    init_db()

    app = Application.builder().token(TOKEN).build()
    register_handlers(app)
    logger.info("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()

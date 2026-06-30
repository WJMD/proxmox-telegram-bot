import logging
import sys
import signal

from telegram import Update
from telegram.ext import Application

from core.logger import setup_logging
from config import TELEGRAM, SETTINGS
from handlers.routers import HANDLERS
from services.alerts import AlertManager
from proxmox.client import close_connection
from language.loader import load_translations


def signal_handler(signum, frame):
    logger.info("Received signal to shut down...")
    close_connection()
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

setup_logging()
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    logger.info("Starting background services...")
    alert_manager = AlertManager(application)
    application.bot_data["alert_manager"] = alert_manager
    await alert_manager.start()


async def post_shutdown(application: Application):
    logger.info("Stopping background services...")
    alert_manager = application.bot_data.get("alert_manager")
    if alert_manager:
        await alert_manager.stop()


def main():
    logger.info("Building application...")
    logger.debug(f"Python version: {sys.version}")

    try:
        application = (
            Application.builder()
            .token(TELEGRAM.bot_token)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )

        application.bot_data["whitelist"] = TELEGRAM.whitelist

        for handler in HANDLERS:
            application.add_handler(handler)

        logger.info("Bot started! Waiting for updates...")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Critical error starting bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process stopped by user.")
import asyncio
import logging
from textwrap import dedent

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core.auth import require_auth
from system.sensors import get_status
from language.loader import load_translations
from config import SETTINGS

# Initialize translation dictionary based on configuration settings
_t = load_translations(getattr(SETTINGS, "language", "en"))
logger = logging.getLogger(__name__)


@require_auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start and /help command sequence, returning a localized description."""
    try:
        # We look up the help text structure dynamically from our language pack.
        # If it doesn't exist, we fall back to the default English structure below.
        default_help = dedent(
            """\
            Hi! This is a bot for managing <b>Proxmox VE</b>.

            <b>Commands:</b>
            /status - Host status
            /vm - List VMs
            /lxc - List LXC containers
            /console &lt;cmd&gt; - Execute command
            """
        )
        help_text = _t.get("help_text", default_help)
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Error occurred while executing start menu sequence:")
        await update.message.reply_text(
            "❌ " + _t.get("generic_error", "An unexpected error occurred. Please check server logs.")
        )


@require_auth
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command sequence, returning hardware and local sensor metrics."""
    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, get_status)

        title = _t.get("status_title", "📊 Host Status:")
        await update.message.reply_text(
            f"<b>{title}</b>\n{info}", 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.exception("Error occurred while retrieving host status statistics:")
        if update.message:
           await update.message.reply_text(_t.get("generic_error", "An unexpected error occurred. Please check server logs."))
        else:
            # handle case where there is no message (e.g., callback query)
            pass
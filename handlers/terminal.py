import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from proxmox.vms import execute_vm_command
from proxmox.lxcs import execute_lxc_command
from core.auth import require_auth  # если у тебя есть декоратор

from language.loader import load_translations
from config import SETTINGS

_t = load_translations(getattr(SETTINGS, "language", "en"))

logger = logging.getLogger(__name__)


@require_auth
async def handle_terminal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    console_state = context.user_data.get("active_console")

    if not console_state:
        return

    text = update.message.text.strip()

    if text.lower() == "exit":
        del context.user_data["active_console"]
        await update.message.reply_text(
            "🔌 Выход из терминала. Обычный режим бота восстановлен."
        )
        return

    res_type = console_state["type"]
    vmid = console_state["id"]
    node = console_state["node"]

    await update.message.reply_chat_action("typing")

    try:
        if res_type == "vm":
            result = await asyncio.to_thread(execute_vm_command, vmid, node, text)
        else:
            result = await asyncio.to_thread(execute_lxc_command, vmid, node, text)

        if len(result) > 4000:
            result = result[:4000] + "\n... [ВЫВОД ОБРЕЗАН]"

        await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Console error: {e}")
        await update.message.reply_text(f"❌ Системная ошибка: {e}")

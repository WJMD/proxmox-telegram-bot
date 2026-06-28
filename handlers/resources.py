import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.auth import require_auth
from proxmox.vms import get_vm_list, vm_action
from proxmox.lxcs import get_lxc_list, lxc_action
from proxmox.utils import format_uptime
from language.loader import load_translations
from config import SETTINGS

_t = load_translations(getattr(SETTINGS, "language", "en"))
logger = logging.getLogger(__name__)


@require_auth
async def vm_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /vm command."""
    if not update.message:
        return

    try:
        loop = asyncio.get_running_loop()
        vms = await loop.run_in_executor(None, get_vm_list)

        if not vms:
            await update.message.reply_text(_t.get("status_vm_not_found", "No VMs found."))
            return

        lines = ["<b>🖥️ Virtual Machines</b>"]
        for vm in vms:
            status_icon = "🟢" if vm["status"] == "running" else "🔴"
            uptime = format_uptime(vm["uptime"])
            lines.append(
                f"{status_icon} <b>{vm['name']}</b> (ID: {vm['id']})\n"
                f"   Status: {vm['status']} | Uptime: {uptime}\n"
                f"   CPU: {vm['cpu_usage_percent']}% | RAM: {vm['mem_used_mb']}MB/{vm['mem_total_mb']}MB ({vm['mem_usage_percent']}%)\n"
                f"   Disk: {vm['disk_used_gb']}GB / {vm['disk_total_gb']}GB"
            )
        await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in vm_list_cmd: {e}", exc_info=True)
        await update.message.reply_text(f"❌ {_t.get('generic_error', 'An error occurred: {e}')}".format(e=e))


@require_auth
async def lxc_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /lxc command."""
    if not update.message:
        return

    try:
        loop = asyncio.get_running_loop()
        lxcs = await loop.run_in_executor(None, get_lxc_list)

        if not lxcs:
            await update.message.reply_text(_t.get("status_lxc_not_found", "No LXC containers found."))
            return

        lines = ["<b>📦 LXC Containers</b>"]
        for ct in lxcs:
            status_icon = "🟢" if ct["status"] == "running" else "🔴"
            uptime = format_uptime(ct["uptime"])
            lines.append(
                f"{status_icon} <b>{ct['name']}</b> (ID: {ct['id']})\n"
                f"   Status: {ct['status']} | Uptime: {uptime}\n"
                f"   CPU: {ct['cpu_usage_percent']}% | RAM: {ct['mem_used_mb']}MB/{ct['mem_total_mb']}MB ({ct['mem_usage_percent']}%)\n"
                f"   Disk: {ct['disk_used_gb']}GB / {ct['disk_total_gb']}GB"
            )
        await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in lxc_list_cmd: {e}", exc_info=True)
        await update.message.reply_text(f"❌ {_t.get('generic_error', 'An error occurred: {e}')}".format(e=e))


# ======================================================================
# Callback handlers for inline buttons (actions on VMs and LXC)
# ======================================================================

async def vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for VM actions (start/stop/reboot)."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    try:
        data = query.data.split("_")
        if len(data) < 3:
            await query.edit_message_text("❌ Invalid action.")
            return

        action = data[1]
        vmid = int(data[2])
        node = data[3] if len(data) > 3 else None

        result = vm_action(vmid, action, node)
        await query.edit_message_text(
            f"✅ VM {vmid}: {result}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in vm_callback: {e}", exc_info=True)
        await query.edit_message_text(f"❌ {_t.get('generic_error', 'An error occurred: {e}')}".format(e=e))


async def lxc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for LXC actions (start/stop/reboot)."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    try:
        data = query.data.split("_")
        if len(data) < 3:
            await query.edit_message_text("❌ Invalid action.")
            return

        action = data[1]
        vmid = int(data[2])
        node = data[3] if len(data) > 3 else None

        result = lxc_action(vmid, action, node)
        await query.edit_message_text(
            f"✅ LXC {vmid}: {result}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in lxc_callback: {e}", exc_info=True)
        await query.edit_message_text(f"❌ {_t.get('generic_error', 'An error occurred: {e}')}".format(e=e))



# ----------------------------------------------------------------------
# Async wrappers for the synchronous functions (since they do IO)
# ----------------------------------------------------------------------

async def get_vm_list_async():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_vm_list)

async def get_lxc_list_async():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_lxc_list)
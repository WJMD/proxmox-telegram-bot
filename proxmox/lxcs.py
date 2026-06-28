import logging
import time
import subprocess
from typing import Dict, Any
from typing import Optional

from proxmox.client import get_proxmox_api, retry_proxmox_call
from proxmox.utils import find_node_by_vmid, parse_lxc_status
from config import PROXMOX
from language.loader import load_translations
from config import SETTINGS

logger = logging.getLogger(__name__)
_t = load_translations(getattr(SETTINGS, "language", "en"))


@retry_proxmox_call(max_retries=3)
def get_lxc_list() -> list:
    proxmox = get_proxmox_api(PROXMOX)
    lxcs = []
    try:
        for node in proxmox.nodes.get():
            node_name = node["node"]
            for ct in proxmox.nodes(node_name).lxc.get():
                vmid = int(ct["vmid"])
                try:
                    # ✅ CORRECCIÓN: usar .current() en lugar de .current.get()
                    status = proxmox.nodes(node_name).lxc(vmid).status.current()
                    metrics = parse_lxc_status(status)
                    lxcs.append({
                        "id": vmid,
                        "name": ct.get("name", f"LXC{vmid}"),
                        "status": ct.get("status", "unknown"),
                        "node": node_name,
                        **metrics
                    })
                except Exception as e:
                    logger.error(_t.get("lxc_error_metrics", "[LXC {vmid}] Error retrieving node metrics: {e}").format(vmid=vmid, e=e))
    except Exception as e:
        logger.error(_t.get("lxc_error_list", "Error fetching LXC container list: {e}").format(e=e))
    return lxcs


def lxc_action(vmid: int, action: str, node: Optional[str] = None) -> str:
    proxmox = get_proxmox_api(PROXMOX)

    if node is None:
        node = find_node_by_vmid(proxmox, vmid, "lxc")

    if not node:
        raise ValueError(_t.get("lxc_not_found", "LXC Container with ID {vmid} was not found on any cluster node.").format(vmid=vmid))

    try:
        if action == "start":
            proxmox.nodes(node).lxc(vmid).status.start.post() # type: ignore
            return _t.get("lxc_started", "Started")

        elif action == "stop":
            try:
                proxmox.nodes(node).lxc(vmid).status.shutdown.post(timeout=20) # type: ignore
                return _t.get("lxc_stopping", "Stopping...")
            except Exception as e:
                logger.warning(f"Graceful shutdown for LXC {vmid} failed ({e}). Enforcing hard stop.")
                proxmox.nodes(node).lxc(vmid).status.stop.post() # type: ignore
                return _t.get("lxc_force_stopped", "Force Stopped")

        elif action == "reboot":
            try:
                proxmox.nodes(node).lxc(vmid).status.reboot.post(timeout=20)  # type: ignore
                return _t.get("lxc_rebooting", "Rebooting...")
            except Exception as e:
                logger.warning(f"Graceful reboot for LXC {vmid} failed ({e}). Forcing sequential restart.")
                proxmox.nodes(node).lxc(vmid).status.stop.post() # type: ignore
                for _ in range(10):
                    # ✅ CORRECCIÓN: .current() en lugar de .current.get()
                    curr_status = proxmox.nodes(node).lxc(vmid).status.current().get("status")
                    if curr_status == "stopped":
                        break
                    time.sleep(1)
                proxmox.nodes(node).lxc(vmid).status.start.post() # type: ignore
                return _t.get("lxc_force_restarted", "Force Restarted")

        else:
            raise ValueError(_t.get("lxc_unknown_action", "Unknown action request parameters: {action}").format(action=action))

    except Exception as e:
        raise Exception(_t.get("lxc_action_failed", "Action '{action}' failed on LXC {vmid}: {e}").format(action=action, vmid=vmid, e=e))


def execute_lxc_command(vmid: int, node: str, command: str) -> str:
    logger.debug(_t.get("lxc_command_executing", "Executing command on LXC {vmid}: {command}").format(vmid=vmid, command=command))
    try:
        cmd = ["pct", "exec", str(vmid), "--", "bash", "-c", command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)

        out = result.stdout.strip()
        err = result.stderr.strip()

        if result.returncode != 0:
            logger.warning(_t.get("lxc_command_failed", "Command on LXC {vmid} failed with code {code}. stderr: {err}").format(vmid=vmid, code=result.returncode, err=err))
            return _t.get("lxc_command_error", "❌ Command failed (code {code}): {output}").format(code=result.returncode, output=err or out)

        if not out and not err:
            return _t.get("lxc_command_success", "✅ Command executed successfully (no output)")

        return out if out else err

    except subprocess.TimeoutExpired:
        logger.error(_t.get("lxc_command_timeout", "⏳ Timeout (30s)"))
        return _t.get("lxc_command_timeout", "⏳ Timeout (30s)")
    except Exception as e:
        logger.error(f"Error executing command on LXC {vmid}: {e}", exc_info=True)
        return _t.get("lxc_command_exception", "❌ Error: {e}").format(e=e)
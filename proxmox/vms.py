import re
import logging
import time
from typing import Dict, Any

from proxmox.client import get_proxmox_api, retry_proxmox_call
from proxmox.utils import find_node_by_vmid, parse_vm_status
from config import PROXMOX
from language.loader import load_translations
from config import SETTINGS

logger = logging.getLogger(__name__)
_t = load_translations(getattr(SETTINGS, "language", "en"))


@retry_proxmox_call(max_retries=3)
def get_vm_list() -> list:
    proxmox = get_proxmox_api(PROXMOX)
    vms = []
    try:
        for node in proxmox.nodes.get():
            node_name = node["node"]
            for vm in proxmox.nodes(node_name).qemu.get():
                if vm.get("template") == 1:
                    continue

                vmid = int(vm["vmid"])
                try:
                    status = proxmox.nodes(node_name).qemu(vmid).status.current.get()
                    config = proxmox.nodes(node_name).qemu(vmid).config()
                    metrics = parse_vm_status(status, config)
                    vms.append({
                        "id": vmid,
                        "name": vm.get("name", f"VM{vmid}"),
                        "status": vm.get("status", "unknown"),
                        "node": node_name,
                        **metrics
                    })
                except Exception as e:
                    logger.error(_t.get("vm_error_metrics", "[VM {vmid}] Error retrieving hardware infrastructure logs: {e}").format(vmid=vmid, e=e))
                    vms.append({
                        "id": vmid,
                        "name": "Error",
                        "status": "error",
                        "node": node_name,
                        "uptime": 0,
                        "cpu_usage_percent": 0,
                        "mem_used_mb": 0,
                        "mem_total_mb": 0,
                        "mem_usage_percent": 0,
                        "disk_used_gb": 0.0,
                        "disk_total_gb": 0.0,
                    })
    except Exception as e:
        logger.error(_t.get("vm_error_list", "Error fetching Virtual Machine inventory: {e}").format(e=e))
    return vms


def vm_action(vmid: int, action: str, node: str = None) -> str:
    proxmox = get_proxmox_api(PROXMOX)

    if node is None:
        node = find_node_by_vmid(proxmox, vmid, "qemu")

    if not node:
        raise ValueError(_t.get("vm_not_found", "Virtual Machine with ID {vmid} was not found on any cluster node.").format(vmid=vmid))

    try:
        if action == "start":
            proxmox.nodes(node).qemu(vmid).status.start.post()
            return _t.get("vm_started", "Started")

        elif action == "stop":
            try:
                proxmox.nodes(node).qemu(vmid).status.shutdown.post(timeout=30)
                return _t.get("vm_stopping", "Stopping...")
            except Exception as e:
                logger.warning(f"Graceful ACPI shutdown for VM {vmid} failed ({e}). Enforcing hard stop.")
                proxmox.nodes(node).qemu(vmid).status.stop.post()
                return _t.get("vm_force_stopped", "Force Stopped")

        elif action == "reboot":
            try:
                proxmox.nodes(node).qemu(vmid).status.reboot.post(timeout=30)
                return _t.get("vm_rebooting", "Rebooting...")
            except Exception as e:
                logger.warning(f"Graceful reboot for VM {vmid} failed ({e}). Executing hardware reset.")
                proxmox.nodes(node).qemu(vmid).status.reset.post()
                return _t.get("vm_force_reseted", "Force Reseted")

        else:
            raise ValueError(_t.get("vm_unknown_action", "Unknown action request parameters: {action}").format(action=action))

    except Exception as e:
        raise Exception(_t.get("vm_action_failed", "Action '{action}' failed on VM {vmid}: {e}").format(action=action, vmid=vmid, e=e))


def execute_vm_command(vmid: int, node: str, command: str) -> str:
    proxmox = get_proxmox_api(PROXMOX)
    logger.debug(_t.get("vm_command_executing", "Executing command on VM {vmid}: {command}").format(vmid=vmid, command=command))
    try:
        res = proxmox.nodes(node).qemu(vmid).agent.exec.post(command=["bash", "-c", command])
        pid = res.get("pid")
        if not pid:
            return _t.get("vm_no_pid", "❌ Could not get PID from guest agent")

        for _ in range(15):
            status = proxmox.nodes(node).qemu(vmid).agent("exec-status").get(pid=pid)
            if status.get("exited") == 1:
                out = status.get("out-data", "")
                err = status.get("err-data", "")
                exitcode = status.get("exitcode")
                if exitcode is not None and exitcode != 0:
                    logger.warning(_t.get("vm_command_failed", "Command on VM {vmid} terminated with code {code}: {output}").format(vmid=vmid, code=exitcode, output=err or out))
                    return _t.get("vm_command_failed", "❌ Command failed (code {code}): {output}").format(code=exitcode, output=err or out)
                return out if out else (err if err else _t.get("vm_command_success", "✅ Command executed successfully"))
            time.sleep(1)

        logger.warning(_t.get("vm_command_timeout", "⏳ Timeout waiting for agent response"))
        return _t.get("vm_command_timeout", "⏳ Timeout waiting for agent response")

    except Exception as e:
        error_msg = str(e).lower()
        if "agent" in error_msg or "qemu-guest-agent is not running" in error_msg:
            logger.error(_t.get("vm_command_agent_unavailable", "❌ Error: QEMU Guest Agent not installed or not running"))
            return _t.get("vm_command_agent_unavailable", "❌ Error: QEMU Guest Agent not installed or not running")
        logger.error(f"Error executing command on VM {vmid}: {e}", exc_info=True)
        return _t.get("vm_command_exception", "❌ Command execution failure: {e}").format(e=e)
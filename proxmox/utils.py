import logging
from typing import Optional, Dict, Any
from language.loader import load_translations
from config import SETTINGS

_t = load_translations(getattr(SETTINGS, "language", "en"))

logger = logging.getLogger(__name__)

# --- Funciones auxiliares existentes ---

def _human_gb(bytes_val: Optional[int]) -> float:
    return round(bytes_val / (1024 ** 3), 1) if bytes_val else 0.0

def format_uptime(seconds: int) -> str:
    if not seconds:
        return "—"
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"

def human_size(bytes_val: int, unit: str = "GB") -> float:
    units = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}
    return round(bytes_val / units.get(unit.upper(), 1024 ** 3), 1)

def find_node_by_vmid(proxmox, vmid: int, resource_type: str = "qemu"):
    try:
        for node in proxmox.nodes.get():
            node_name = node["node"]
            resources = (
                proxmox.nodes(node_name).qemu.get()
                if resource_type == "qemu"
                else proxmox.nodes(node_name).lxc.get()
            )
            for res in resources:
                if int(res["vmid"]) == int(vmid):
                    return node_name
        raise ValueError(f"Target resource ID {vmid} could not be located in the cluster metadata")
    except Exception as e:
        logger.error(f"Cluster search sequence error: {e}")
        raise Exception(f"Cluster search sequence error: {e}")

# --- Nuevas funciones de parseo ---

def parse_lxc_status(status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts metrics from an LXC container status.
    Returns a dict with: uptime, cpu_usage_percent, mem_used_mb, mem_total_mb,
    mem_usage_percent, disk_used_gb, disk_total_gb.
    """
    uptime = int(status.get("uptime", 0))
    cpu = round(float(status.get("cpu", 0)) * 100, 1)
    mem_used = int(status.get("mem", 0)) // 1024 // 1024
    mem_total = int(status.get("maxmem", 1)) // 1024 // 1024
    mem_pct = round(mem_used / mem_total * 100, 1) if mem_total else 0

    used_gb = total_gb = 0.0
    if "rootfs" in status:
        used_gb += _human_gb(status["rootfs"].get("used", 0))
        total_gb += _human_gb(status["rootfs"].get("total", 0)) or _human_gb(status["rootfs"].get("max", 0))

    for key, val in status.items():
        if key.startswith("mp") or key.startswith("mountpoint"):
            if isinstance(val, dict):
                used_gb += _human_gb(val.get("used", 0))
                total_gb += _human_gb(val.get("total", 0)) or _human_gb(val.get("max", 0))

    return {
        "uptime": uptime,
        "cpu_usage_percent": cpu,
        "mem_used_mb": mem_used,
        "mem_total_mb": mem_total,
        "mem_usage_percent": mem_pct,
        "disk_used_gb": round(used_gb, 1),
        "disk_total_gb": round(total_gb, 1) if total_gb > 0 else 0.0,
    }

def parse_vm_status(status: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extracts metrics from a VM status.
    Optionally accepts the VM configuration to calculate total disk size
    if not available in the status.
    """
    uptime = int(status.get("uptime", 0))
    cpu = round(float(status.get("cpu", 0)) * 100, 1)
    mem_used = int(status.get("mem", 0)) // 1024 // 1024
    mem_total = int(status.get("maxmem", 1)) // 1024 // 1024
    mem_pct = round(mem_used / mem_total * 100, 1) if mem_total else 0

    used_gb = _human_gb(status.get("disk", 0))
    total_gb = _human_gb(status.get("maxdisk", 0))

    # Fallback: calculate from config if maxdisk is missing
    if total_gb == 0 and config:
        import re
        for val in config.values():
            if isinstance(val, str):
                m = re.search(r"size=(\d+)([GM]?)B?", val, re.I)
                if m:
                    size = int(m.group(1))
                    unit = m.group(2).upper()
                    if not unit or unit == "G":
                        total_gb += size
                    elif unit == "M":
                        total_gb += size / 1024

    return {
        "uptime": uptime,
        "cpu_usage_percent": cpu,
        "mem_used_mb": mem_used,
        "mem_total_mb": mem_total,
        "mem_usage_percent": mem_pct,
        "disk_used_gb": used_gb if used_gb > 0 else 0.0,
        "disk_total_gb": round(total_gb, 1),
    }
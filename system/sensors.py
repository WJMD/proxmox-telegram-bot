import psutil
import logging
from typing import List, Dict, Any, Optional

from language.loader import load_translations
from config import SETTINGS

_t = load_translations(getattr(SETTINGS, "language", "en"))
logger = logging.getLogger(__name__)


def get_temperatures() -> List[Dict[str, Any]]:
    """
    Returns a list of temperature readings from available sensors.
    Each entry: {"sensor": name, "temp": current_temp, "high": high_temp, "critical": critical_temp}
    """
    temps = []
    try:
        if hasattr(psutil, "sensors_temperatures"):
            sensors = psutil.sensors_temperatures()
            if sensors:
                for name, entries in sensors.items():
                    for entry in entries:
                        temps.append({
                            "sensor": name,
                            "temp": entry.current,
                            "high": entry.high if hasattr(entry, "high") else None,
                            "critical": entry.critical if hasattr(entry, "critical") else None,
                        })
    except Exception as e:
        logger.error(f"Error reading temperatures: {e}")
    return temps


def get_battery_status() -> Dict[str, Any]:
    """
    Returns battery status information.
    Returns: {
        "has_battery": bool,
        "percent": int,
        "is_charging": bool,
        "time_left": int (seconds),
        "status": str (charging, discharging, full, etc.)
    }
    """
    result = {
        "has_battery": False,
        "percent": 0,
        "is_charging": False,
        "time_left": 0,
        "status": "unknown"
    }

    if not hasattr(psutil, "sensors_battery"):
        return result

    battery = psutil.sensors_battery()
    if battery is None:
        return result

    result["has_battery"] = True
    result["percent"] = battery.percent
    result["is_charging"] = battery.power_plugged
    result["time_left"] = battery.secsleft if battery.secsleft != -1 else 0

    if battery.power_plugged:
        if battery.percent == 100:
            result["status"] = "full"
        else:
            result["status"] = "charging"
    else:
        if battery.secsleft == 0:
            result["status"] = "empty"
        else:
            result["status"] = "discharging"

    return result


def get_status() -> str:
    """Returns a formatted status string with system metrics."""
    try:
        # 1. Uptime
        uptime_seconds = psutil.boot_time()
        uptime_str = format_uptime(uptime_seconds)

        # 2. CPU
        cpu_pct = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()

        # 3. Memory
        mem = psutil.virtual_memory()
        mem_used_gb = mem.used / (1024**3)
        mem_total_gb = mem.total / (1024**3)
        mem_pct = mem.percent

        # 4. Disks
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "name": part.device,
                    "mount": part.mountpoint,
                    "used_gb": usage.used / (1024**3),
                    "total_gb": usage.total / (1024**3),
                    "pct": usage.percent,
                })
            except PermissionError:
                continue

        # 5. Temperatures
        temps = get_temperatures()

        # 6. Battery status
        battery = get_battery_status()

        # ---------- Build output using translations ----------
        lines = []
        lines.append(f"<b>{_t.get('status_title', '📊 Host Status:')}</b>")

        # Uptime
        lines.append(f"{_t.get('status_uptime', '⏰ Uptime:')} {uptime_str}")

        # CPU
        cpu1, cpu5, cpu15 = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
        lines.append(
            _t.get('status_cpu', '⚡ CPU Load: 1m: {cpu1} ({pct1}%), 5m: {cpu5} ({pct5}%), 15m: {cpu15} ({pct15}%)')
            .format(cpu1=f"{cpu1:.2f}", pct1=f"{cpu_pct:.1f}",
                    cpu5=f"{cpu5:.2f}", pct5=f"{cpu_pct:.1f}",
                    cpu15=f"{cpu15:.2f}", pct15=f"{cpu_pct:.1f}")
        )

        # RAM
        lines.append(
            _t.get('status_ram', '💻 RAM: {used}GB / {total}GB ({pct}%)')
            .format(used=f"{mem_used_gb:.1f}", total=f"{mem_total_gb:.1f}", pct=f"{mem_pct:.1f}")
        )

        # Disks
        if disks:
            lines.append(_t.get('status_disks', '💽 Disks:'))
            for d in disks:
                lines.append(
                    _t.get('status_disk', '🖥️ {name}: {pct}% ({used}GB / {total}GB)')
                    .format(name=d["name"], pct=f"{d['pct']:.1f}",
                            used=f"{d['used_gb']:.1f}", total=f"{d['total_gb']:.1f}")
                )

        # Battery (solo si tiene batería)
        if battery["has_battery"]:
            battery_icon = "🔋" if battery["is_charging"] else "🪫"
            status_text = battery["status"].capitalize()
            lines.append(
                f"{battery_icon} <b>Battery:</b> {battery['percent']}% ({status_text})"
            )
            if battery["time_left"] > 0 and not battery["is_charging"]:
                hours = battery["time_left"] // 3600
                minutes = (battery["time_left"] % 3600) // 60
                lines.append(f"   ⏱️ Time remaining: {hours}h {minutes}m")

        # Temperatures
        if temps:
            lines.append(_t.get('status_temperatures', '🌡️ Temperatures:'))
            for t in temps:
                lines.append(f"   {t['sensor']}: {t['temp']:.1f}°C")
        else:
            lines.append(_t.get('status_no_temp', '🌡️ Temperature reading not supported on your OS.'))

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error generating status: {e}", exc_info=True)
        return _t.get('status_error', '❌ An error occurred while retrieving host status.')


def format_uptime(seconds: float) -> str:
    """Converts seconds to a human-readable uptime string."""
    seconds = int(seconds)
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"
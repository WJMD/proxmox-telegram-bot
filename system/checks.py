import psutil
import logging
from config import ALERTS
from system.sensors import get_temperatures

from language.loader import load_translations
from config import SETTINGS

_t = load_translations(getattr(SETTINGS, "language", "en"))
logger = logging.getLogger(__name__)


def check_cpu_temp():
    try:
        temps = get_temperatures()
        if not temps:
            return False, 0

        # Buscar sensor de CPU
        cpu_temp = None
        for t in temps:
            if "cpu" in t["sensor"].lower() or "core" in t["sensor"].lower():
                if cpu_temp is None or t["temp"] > cpu_temp:
                    cpu_temp = t["temp"]

        # Si no encontró sensor de CPU, usar el más alto
        if cpu_temp is None:
            cpu_temp = max([t["temp"] for t in temps])

        return cpu_temp > ALERTS.cpu_temp_threshold, round(cpu_temp, 1)

    except Exception as e:
        logger.error(f"❌ Error checking temperature: {e}")
        return False, 0


def check_cpu_usage():
    try:
        usage = psutil.cpu_percent(interval=None)
        return usage > ALERTS.cpu_usage_threshold, round(usage, 1)
    except Exception as e:
        logger.error(f"❌ Error checking CPU: {e}")
        return False, 0


def check_ram_usage():
    try:
        ram = psutil.virtual_memory()
        return ram.percent > ALERTS.ram_usage_threshold, round(ram.percent, 1)
    except Exception as e:
        logger.error(f"❌ Error checking RAM: {e}")
        return False, 0
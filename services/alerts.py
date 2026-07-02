import asyncio
import logging
import time
import json
import os
import subprocess
from datetime import datetime

from telegram.ext import Application

from system.checks import check_cpu_temp, check_cpu_usage, check_ram_usage
from system.sensors import get_battery_status
from language.loader import load_translations
from config import TELEGRAM, ALERTS, SETTINGS

# ===== Translation loading =====
CURRENT_LANGUAGE = getattr(SETTINGS, "language", "en")

def load_translations(lang):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "..", "language", f"{lang}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        fallback_path = os.path.join(base_path, "..", "language", "en.json")
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️ No language dictionary files found in 'language/' directory.")
            return {}

_t = load_translations(CURRENT_LANGUAGE)
logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, application: Application):
        self.app = application
        self.running = False
        self.task = None

        # Battery state tracking variables
        self.last_power_plugged = None
        self.last_battery_percent = None
        self.battery_60_alerted = False          # Prevents spam of the 60% alert
        self.last_unplugged_reminder = 0         # Timestamp of the last reminder sent
        self.reminder_interval = 300             # 5 minutes in seconds

    async def start(self):
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info(_t.get("monitoring_started", "🚨 Monitoring system started!"))

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(_t.get("monitoring_stopped", "Monitoring system stopped"))

    async def _monitor_loop(self):
        error_sleep = 60
        while self.running:
            try:
                await self._check_alerts()
                await asyncio.sleep(ALERTS.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(_t.get("error_monitoring", "❌ Monitoring error: {e}").format(e=e))
                await asyncio.sleep(error_sleep)

    async def _run_check(self, check_func):
        """Runs a synchronous hardware check inside a thread executor to avoid blocking the bot."""
        return await asyncio.to_thread(check_func)

    # ===== Helper: Save event to system event log =====
    def add_system_event(self, message: str):
        """Saves a message to the system event log file using system-event-manager.sh."""
        try:
            clean_message = message.replace('\n', ' ').replace('"', '\\"')
            subprocess.run(
                ["/usr/local/bin/system-event-manager.sh", "add", clean_message],
                check=False,
                timeout=5,
                capture_output=True
            )
        except Exception as e:
            logger.warning(f"Failed to add system event: {e}")

    # ===== Helper: Send alert (with fallback to event log on network failure) =====
    async def _send_alert(self, text: str):
        try:
            for chat_id in TELEGRAM.whitelist:
                await self.app.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            logger.info(_t.get("alert_sent_log").format(text=text))
        except Exception as e:
            error_str = str(e).lower()
            # If it's a network error, save to the event file
            if any(keyword in error_str for keyword in ("network", "connect", "dns", "timeout")):
                logger.warning(f"Network error saving alert to event file: {e}")
                clean_text = text.replace('<b>', '').replace('</b>', '') \
                                 .replace('<i>', '').replace('</i>', '')
                self.add_system_event(clean_text)
            else:
                logger.error(_t.get("error_send_alert").format(e=e))

    # ===== Main alert checking loop =====
    async def _check_alerts(self):
        # 1. CPU Temperature Check
        try:
            alert, value = await self._run_check(check_cpu_temp)
            if alert:
                msg = _t.get("alert_overheat").format(value=value, threshold=ALERTS.cpu_temp_threshold)
                await self._send_alert(msg)
            else:
                logger.debug(_t.get("log_temp_ok").format(value=value))
        except Exception as e:
            logger.error(_t.get("error_temp_check").format(e=e))

        # 2. CPU Usage Check
        try:
            alert, value = await self._run_check(check_cpu_usage)
            if alert:
                msg = _t.get("alert_cpu_high").format(value=value, threshold=ALERTS.cpu_usage_threshold)
                await self._send_alert(msg)
        except Exception as e:
            logger.error(_t.get("error_cpu_check").format(e=e))

        # 3. RAM Usage Check
        try:
            alert, value = await self._run_check(check_ram_usage)
            if alert:
                msg = _t.get("alert_ram_high").format(value=value, threshold=ALERTS.ram_usage_threshold)
                await self._send_alert(msg)
        except Exception as e:
            logger.error(_t.get("error_ram_check").format(e=e))

        # ---- Battery status monitoring ----
        try:
            battery = await asyncio.to_thread(get_battery_status)
            if not battery["has_battery"]:
                return

            percent = battery["percent"]
            is_plugged = battery["is_charging"] or battery["status"] == "full"

            # Initialize previous state on first run
            if self.last_power_plugged is None:
                self.last_power_plugged = is_plugged
                self.last_battery_percent = percent
                return

            # --- Detect power state change (plugged ↔ unplugged) ---
            if self.last_power_plugged and not is_plugged:
                msg = _t.get("alert_power_unplugged", "🔋 Power disconnected! Running on battery: {percent}%").format(percent=round(percent))
                await self._send_alert(msg)
                self.battery_60_alerted = False
                self.last_unplugged_reminder = time.time()   # Reset reminder timer

            elif not self.last_power_plugged and is_plugged:
                msg = _t.get("alert_power_restored", "🔌 Power restored! Charging: {percent}%").format(percent=round(percent))
                await self._send_alert(msg)
                self.battery_60_alerted = False
                self.last_unplugged_reminder = 0

            # --- 60% battery warning (only if unplugged) ---
            if not is_plugged and percent <= 60 and not self.battery_60_alerted:
                msg = _t.get("alert_battery_60_warning", "⚠️ Battery at {percent}% - Discharging.\nThe system will shut down when battery reaches 50%.").format(percent=round(percent))
                await self._send_alert(msg)
                self.battery_60_alerted = True
                self.last_unplugged_reminder = time.time()   # Reset reminder timer after warning

            # --- Periodic reminder every 5 minutes (only if unplugged) ---
            if not is_plugged and self.last_unplugged_reminder > 0:
                elapsed = time.time() - self.last_unplugged_reminder
                if elapsed >= self.reminder_interval:
                    msg = _t.get("alert_power_reminder", "🔋 Reminder: Still running on battery ({percent}%). Please connect to power to avoid shutdown.").format(percent=round(percent))
                    await self._send_alert(msg)
                    self.last_unplugged_reminder = time.time()  # Update timestamp

            # --- Update previous state ---
            self.last_power_plugged = is_plugged
            self.last_battery_percent = percent

        except Exception as e:
            logger.error(f"❌ Error checking battery status: {e}")
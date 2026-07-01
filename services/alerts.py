import asyncio
import logging
from telegram.ext import Application
from system.checks import check_cpu_temp, check_cpu_usage, check_ram_usage
from config import TELEGRAM, ALERTS, SETTINGS
import json
import os
from language.loader import load_translations
from system.sensors import get_battery_status


# Initialize the global translation dictionary
# --- Carga de traducciones ---
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
         # Variables to store the previous battery state
        self.last_power_plugged = None
        self.last_battery_percent = None
        self.battery_60_alerted = False  # to prevent spam

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
            
        # ---- News alerts of Battery ----
        try:
            battery = await asyncio.to_thread(get_battery_status)
            if battery["has_battery"]:
                percent = battery["percent"]
                is_plugged = battery["is_charging"] or battery["status"] == "full"

                # Initial status: save the initial state without sending an alert.
                if self.last_power_plugged is None:
                    self.last_power_plugged = is_plugged
                    self.last_battery_percent = percent
                    return

                # Change from plugged to unplugged
                if self.last_power_plugged and not is_plugged:
                    msg = _t.get("alert_power_unplugged", "🔋 Power disconnected! Running on battery: {percent}%").format(percent=round(percent))
                    await self._send_alert(msg)
                    self.battery_60_alerted = False  # Reset flag for the 60% alert

                # Change from unplugged to plugged
                elif not self.last_power_plugged and is_plugged:
                    msg = _t.get("alert_power_restored", "🔌 Power restored! Charging: {percent}%").format(percent=round(percent))
                    await self._send_alert(msg)

                # If it's unplugged and the battery is low at 60%, alert (only once)
                if not is_plugged and percent <= 60 and not self.battery_60_alerted:
                    msg = _t.get("alert_battery_60_warning", "⚠️ Battery at {percent}% - Discharging.\nThe system will shut down when battery reaches 50%.").format(percent=round(percent))
                    await self._send_alert(msg)
                    self.battery_60_alerted = True

                # If the battery goes above 60% (for example, if it's plugged in again), reset the flag
                if is_plugged and percent > 60:
                    self.battery_60_alerted = False

                # Update the previous state
                self.last_power_plugged = is_plugged
                self.last_battery_percent = percent

        except Exception as e:
            logger.error(f"❌ Error checking battery status: {e}")

    async def _send_alert(self, text: str):
        try:
            for chat_id in TELEGRAM.whitelist:
                await self.app.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            logger.info(_t.get("alert_sent_log").format(text=text))
        except Exception as e:
            logger.error(_t.get("error_send_alert").format(e=e))


    async def _send_alert(self, text: str):
        try:
            for chat_id in TELEGRAM.whitelist:
                await self.app.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            logger.info(_t.get("alert_sent_log").format(text=text))
        except Exception as e:
            logger.error(_t.get("error_send_alert").format(e=e))
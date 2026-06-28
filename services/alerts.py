import asyncio
import logging
from telegram.ext import Application
from system.checks import check_cpu_temp, check_cpu_usage, check_ram_usage
from config import TELEGRAM, ALERTS, SETTINGS
import json
import os
from language.loader import load_translations


# Initialize the global translation dictionary
CURRENT_LANGUAGE = getattr(SETTINGS, "language", "en")
_t = load_translations(CURRENT_LANGUAGE)

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, application: Application):
        self.app = application
        self.running = False
        self.task = None

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

    async def _send_alert(self, text: str):
        try:
            for chat_id in TELEGRAM.whitelist:
                await self.app.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            logger.info(_t.get("alert_sent_log").format(text=text))
        except Exception as e:
            logger.error(_t.get("error_send_alert").format(e=e))
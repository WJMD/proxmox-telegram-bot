import asyncio
import logging
from telegram.ext import Application
from system.checks import check_cpu_temp, check_cpu_usage, check_ram_usage
from config import TELEGRAM, ALERTS, SETTINGS
import json
import os

# 1. Leemos el idioma configurado en tu config.py
CURRENT_LANGUAGE = getattr(SETTINGS, "language", "en")

def load_translations(lang):
    # Esto te ubica en 'proxmox-telegram-bot/services'
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Con '..' subimos a la raíz y entramos a tu carpeta 'language'
    file_path = os.path.join(base_path, "..", "language", f"{lang}.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback: Si el idioma no existe, busca el inglés en la raíz
        fallback_path = os.path.join(base_path, "..", "language", "en.json")
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️ No se encontraron los archivos JSON en la carpeta 'language'.")
            return {}

# Inicializamos las traducciones globales
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
        logger.info(_t["monitoring_started"])

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(_t["monitoring_stopped"])

    async def _monitor_loop(self):
        error_sleep = 60

        while self.running:
            try:
                await self._check_alerts()
                await asyncio.sleep(ALERTS.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(_t["error_monitoring"].format(e=e))
                await asyncio.sleep(error_sleep)

    async def _run_check(self, check_func):
        """Запускает синхронную проверку в потоке, чтобы не блокировать бота"""
        return await asyncio.to_thread(check_func)

    async def _check_alerts(self):
        # 1. Verificación de Temperatura
        try:
            alert, value = await self._run_check(check_cpu_temp)
            if alert:
                msg = _t["alert_overheat"].format(value=value, threshold=ALERTS.cpu_temp_threshold)
                await self._send_alert(msg)
            else:
                logger.debug(_t["log_temp_ok"].format(value=value))
        except Exception as e:
            logger.error(_t["error_temp_check"].format(e=e))

        # 2. Verificación de uso de CPU
        try:
            alert, value = await self._run_check(check_cpu_usage)
            if alert:
                msg = _t["alert_cpu_high"].format(value=value, threshold=ALERTS.cpu_usage_threshold)
                await self._send_alert(msg)
        except Exception as e:
            logger.error(_t["error_cpu_check"].format(e=e))

        # 3. Verificación de uso de RAM
        try:
            alert, value = await self._run_check(check_ram_usage)
            if alert:
                msg = _t["alert_ram_high"].format(value=value, threshold=ALERTS.ram_usage_threshold)
                await self._send_alert(msg)
        except Exception as e:
            logger.error(_t["error_ram_check"].format(e=e))

    async def _send_alert(self, text: str):
        try:
            for chat_id in TELEGRAM.whitelist:
                await self.app.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            logger.info(_t["alert_sent_log"].format(text=text))
        except Exception as e:
            logger.error(_t["error_send_alert"].format(e=e))

import os
import logging
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Locate and load the .env file from the project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_env(key: str, required: bool = False, default: str = "") -> str:
    """Retrieves a string value from the environment variables.
    If required=True and the key is missing, raises a ValueError."""
    value = os.getenv(key, default).strip()
    if required and not value:
        raise ValueError(
            f"Critical Error: Missing required environment variable '{key}' in .env"
        )
    return value


def get_env_int(key: str, default: int) -> int:
    """Safely converts an environment variable to an integer.
    Returns the default value if conversion fails or if the key is missing."""
    value = os.getenv(key)
    if not value:
        return default
    try:
        return int(value.strip())
    except ValueError:
        logging.warning(
            f"Variable '{key}' has an invalid integer value '{value}'. Falling back to default: {default}"
        )
        return default


def get_whitelist(key: str) -> tuple[int, ...]:
    """Safely parses a comma-separated list of User IDs,
    skipping any individual elements that fail integer conversion."""
    raw_value = os.getenv(key, "")
    whitelist = []
    for uid in raw_value.split(","):
        uid = uid.strip()
        if uid:
            try:
                whitelist.append(int(uid))
            except ValueError:
                logging.warning(f"Skipped invalid ID in {key}: '{uid}'")
    return tuple(whitelist)


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    whitelist: tuple[int, ...]


@dataclass(frozen=True)
class ProxmoxConfig:
    host: str
    user: str
    token_name: str
    token_value: str
    port: int


@dataclass(frozen=True)
class AlertsConfig:
    cpu_temp_threshold: int
    cpu_usage_threshold: int
    ram_usage_threshold: int
    check_interval: int


@dataclass(frozen=True)
class SettingsConfig:
    language: str


# --- System Configurations Initialization ---

TELEGRAM = TelegramConfig(
    bot_token=get_env("BOT_TOKEN", required=True), whitelist=get_whitelist("WHITELIST")
)

_proxmox_host = get_env("HOST") or get_env("PROXMOX_HOST", default="localhost")
_proxmox_user = get_env("USER") or get_env("PROXMOX_USER", required=True)

# Append default authentication realm if missing
if "@" not in _proxmox_user:
    _proxmox_user = f"{_proxmox_user}@pam"

PROXMOX = ProxmoxConfig(
    host=_proxmox_host,
    user=_proxmox_user,
    token_name=get_env("PROXMOX_TOKEN_NAME", required=True),
    token_value=get_env("PROXMOX_TOKEN_VALUE", required=True),
    port=get_env_int("PROXMOX_PORT", 8006),
)

ALERTS = AlertsConfig(
    cpu_temp_threshold=get_env_int("CPU_TEMP_THRESHOLD", 75),
    cpu_usage_threshold=get_env_int("CPU_USAGE_THRESHOLD", 80),
    ram_usage_threshold=get_env_int("RAM_USAGE_THRESHOLD", 80),
    check_interval=get_env_int("CHECK_INTERVAL", 300),
)

# Global application settings (Default user-facing language: "es")
SETTINGS = SettingsConfig(
    language=get_env("LANGUAGE", default="es")
)
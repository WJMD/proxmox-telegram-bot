**🤖 Proxmox VE Telegram Bot**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/telegram--bot-v22.8-2CA5E0.svg?logo=telegram)](https://python-telegram-bot.org)
[![Proxmox VE](https://img.shields.io/badge/Proxmox-8.x%2B-EC6601.svg?logo=proxmox)](https://proxmox.com)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-2.1-blue.svg)](https://github.com/WJMD/proxmox-telegram-bot)

> **A secure and modern Telegram bot to monitor and manage your Proxmox VE homelab.** > Everything you need: host status, VM/LXC lists, secure console, and automatic alerts — all from your chat.

---

## 👥 Credits & Attribution

This project is an updated and enhanced fork of the original work developed by **Sliva**.  
* **Original Creator:** Sliva  
* **Original Repository:** [sliva-dev/proxmox-telegram-bot](https://github.com/sliva-dev/proxmox-telegram-bot)

### 🚀 Improvements in this Fork:
* **Full Internationalization (i18n):** Dynamic language support using JSON dictionaries (`language/` directory) for English, Spanish, and Russian.
* **Codebase Refactoring:** Clean English code, logs, and comments following best practices.
* **Modern Dependencies:** Updated to `python-telegram-bot v22.8`, `proxmoxer v2.3.0`, and `psutil v7.2.2` for 2026 compatibility.
* **Systemd Service:** Easy autostart and management with `systemctl`.
* **Better Metrics:** Correct parsing of LXC and VM disk usage directly from Proxmox API.
* **Improved Security:** Enhanced console blacklist and whitelist protection.

---

## ✨ Features

| Category | Functionality | Description |
| :--- | :--- | :--- |
| **📊 Monitoring** | Host Status (`/status`) | Uptime, CPU load, RAM usage, disks, temperature, and battery |
| | VM/LXC Lists (`/vm`, `/lxc`) | Detailed real-time metrics for each resource |
| **⚡ Management** | VM/LXC Control | Start / Stop / Reboot with confirmation (via inline buttons) |
| | Cluster Support | Automatic node lookup by VMID |
| **🔧 Utilities** | Secure Console (`/console`) | 30s timeout, command blacklist, output truncation |
| | Automatic Alerts | Overheating, high CPU, and high RAM usage monitoring |
| **🔒 Security** | Whitelist Access | Only authorized Telegram IDs allowed |
| | Unauthorized Attempt Alerts | Admins receive instant notifications of suspicious activity |
| | Console Blacklist | Blocks dangerous commands (`rm -rf /`, `mkfs`, `shutdown`, etc.) |
| | Execution Timeout | Enforced 30-second limit per console command |
| **🌐 Language** | Multi-language | English, Spanish, Russian (easily extendable) |

---

## 🚀 Quick Start

### Prerequisites

- Proxmox VE 8.x or later
- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))

### Installation

```bash
cd /opt
git clone [https://github.com/WJMD/proxmox-telegram-bot.git](https://github.com/WJMD/proxmox-telegram-bot.git)
cd proxmox-telegram-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### Configuration

Create a `.env` file in the root directory:

```env
# Telegram
BOT_TOKEN=your_bot_token_from_BotFather
WHITELIST=your_telegram_id

# Proxmox (API Token is highly recommended!)
HOST=your_proxmox_ip
PROXMOX_USER=BotTelegram@pve
PROXMOX_TOKEN_NAME=BotTelegram@pve!bottelegram
PROXMOX_TOKEN_VALUE=your_token_value
PROXMOX_PORT=8006
VERIFY_SSL=False
LANGUAGE=en

# Alert & Application Settings
CPU_TEMP_THRESHOLD=80
CPU_USAGE_THRESHOLD=70
RAM_USAGE_THRESHOLD=70
CHECK_INTERVAL=30

```

> 💡 **How to create an API token in Proxmox VE:** > Go to `Datacenter → Permissions → API Tokens → Add`.
> **Important:** Disable **Privilege Separation** and assign the token the `Administrator` role (or a custom role with `VM.Audit`, `LXC.Audit`, `Sys.Audit`, and `VM.PowerMgmt` permissions) on the `/` path with **Propagate** enabled.

### Test Manually

```bash
python main.py

```

If everything works, you'll see the bot online in your Telegram chat.

---

## 🔄 Autostart via systemd

To run the bot as a background service that starts automatically on boot:

1. **Copy the service file** (already included in `system/`):

```bash
cp system/proxmox-telegram-bot.service /etc/systemd/system/

```

2. **Reload systemd and enable the service**:

```bash
systemctl daemon-reload
systemctl enable --now proxmox-telegram-bot.service

```

3. **Check status and logs**:

```bash
systemctl status proxmox-telegram-bot.service
journalctl -u proxmox-telegram-bot.service -f

```

### Service Management Commands

| Command | Action |
| --- | --- |
| `systemctl start proxmox-telegram-bot.service` | Start the bot |
| `systemctl stop proxmox-telegram-bot.service` | Stop the bot |
| `systemctl restart proxmox-telegram-bot.service` | Restart the bot |
| `systemctl status proxmox-telegram-bot.service` | Check status |
| `journalctl -u proxmox-telegram-bot.service -f` | Follow logs |

---

## 🎯 Bot Commands

| Command | Description |
| --- | --- |
| `/start` | Show the help menu with all available commands |
| `/status` | Display host status (uptime, CPU, RAM, disks, temperature, battery) |
| `/vm` | List all Virtual Machines with detailed metrics (CPU, RAM, disk) |
| `/lxc` | List all LXC Containers with detailed metrics (CPU, RAM, disk) |
| `/console <cmd>` | Execute a command on the host (e.g., `/console ls -la`) |

> ⚠️ **Console restrictions:** > The bot blocks dangerous commands like `rm -rf /`, `mkfs`, `fdisk`, `dd`, `shutdown`, `reboot`, fork bombs, and other destructive operations. Commands are limited to 30 seconds and output is truncated to 4000 characters.

---

## 🛡️ Security

### Multi-level Protection:

* ✅ **Whitelist Authorization** — Only explicitly authorized Telegram IDs can interact with the bot.
* ✅ **Intrusion Attempt Alerts** — Instant administrative notifications when unauthorized users attempt actions.
* ✅ **Secured Console** — Strict shell command blacklist protecting your infrastructure against:
* `rm -rf /`, `mkfs`, `fdisk`, `dd of=/dev/`, `wipefs`
* `shutdown`, `reboot`, `halt`, `poweroff`
* Fork bombs and dangerous logical syntax constructions


* ✅ **Execution Timeouts** — Enforced 30-second maximum timeout per console command to prevent terminal hangs.
* ✅ **Output Truncation** — Smart truncation at 4000 characters to strictly respect Telegram's message payload limits.

---

## 📁 Project Structure

```text
proxmox-telegram-bot/
├── main.py                               # Bot startup script
├── config.py                             # Configuration loader from .env
├── requirements.txt                      # Project dependencies
├── .env                                  # Environment variables (git-ignored)
├── README.md                             # Project documentation
├── install.sh                            # Automated installation script
│
├── core/                                 # Core bot modules
│   ├── __init__.py
│   ├── auth.py                           # Whitelist validation + security alerts
│   └── logger.py                         # Logging configurations
│
├── handlers/                             # Bot command handlers
│   ├── __init__.py
│   ├── common.py                         # General commands (/start, /help, /status)
│   ├── console.py                        # Server console emulator
│   ├── resources.py                      # Unified resource handler
│   └── routers.py                        # Command routing logic
│
├── language/                             # Localization dictionaries (JSON)
│   ├── en.json                           # English
│   ├── es.json                           # Spanish
│   └── ru.json                           # Russian
│
├── proxmox/                              # Proxmox API integration
│   ├── __init__.py
│   ├── client.py                         # API client (requests-based)
│   ├── vms.py                            # Virtual Machine operations
│   ├── lxcs.py                           # LXC Container operations
│   └── utils.py                          # Helper utilities
│
├── services/                             # Additional internal services
│   ├── __init__.py
│   └── alerts.py                         # Monitoring loop and alert system
│
└── system/                               # System level utilities
    ├── __init__.py
    ├── checks.py                         # System metrics (CPU, RAM, temperature)
    ├── sensors.py                        # Hardware sensors and battery
    └── proxmox-telegram-bot.service      # systemd service file

```

---

## 📝 License

**MIT License** — Full usage freedom with liability disclaimer.

```text
MIT License © 2025-2026 Sliva (Original)
Enhanced and maintained by Wander J. (2026)

```

---

### ⭐ If you found this project useful, give it a star!

### 🐛 Found a bug? — [Open an Issue](https://github.com/WJMD/proxmox-telegram-bot/issues)

### 💡 Want to help? — Pull Requests are welcome!

**Original Author:** [Sliva](https://github.com/sliva-dev)

**Maintained and Enhanced by:** [Wander J.](https://github.com/WJMD)

**Version:** 2.1 — June 2026

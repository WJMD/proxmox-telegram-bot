**🤖 Proxmox VE Telegram Bot**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/telegram--bot-v22.8-2CA5E0.svg?logo=telegram)](https://python-telegram-bot.org)
[![Proxmox VE](https://img.shields.io/badge/Proxmox-8.x%2B-EC6601.svg?logo=proxmox)](https://proxmox.com)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-2.0-blue.svg)](https://github.com/wandel-dr/proxmox-telegram-bot)

> **The most advanced and secure Telegram bot for Proxmox VE management in 2026**
> Everything a system administrator needs: monitoring, alerts, VM/LXC management, and a secure shell—directly in your chat.

---

## 👥 Credits & Attribution

This project is an updated and enhanced fork of the original work developed by **Sliva**. 
* **Original Creator:** Sliva 
* **Original Repository:** [sliva-dev/proxmox-telegram-bot](https://github.com/sliva-dev/proxmox-telegram-bot)

### 🚀 Improvements in this Fork:
* **Full Internationalization (i18n):** Implemented a dynamic language architecture using separate JSON dictionaries (`language/` directory) supporting English, Spanish, and Russian.
* **Codebase Refactoring:** Standardized all internal variables, system logs, comments, and exceptions to professional English following clean code best practices.
* **Infrastructure Upgrades:** Updated critical core dependencies (`python-telegram-bot v22.8`, `proxmoxer v2.3.0`, and `psutil v7.2.2`) to ensure full stability with 2026 systems and modern Proxmox VE APIs.

---

## ✨ Features

| Category | Functionality | Description |
| :--- | :--- | :--- |
| **📊 Monitoring** | Host Status (`/status`) | Uptime, CPU load, RAM usage, storage, and temperatures |
| | VM/LXC Lists (`/vm`, `/lxc`) | Button-based management, real-time metrics |
| **⚡ Management** | VM/LXC Control | Start / Stop / Reboot with confirmation prompts |
| | Cluster Support | Automatic node lookup by VMID |
| **🔧 Utilities** | Secure Console (`/console`) | 30s timeout, command blacklist, output truncation |
| | Automatic Alerts | Overheating, high CPU, and high RAM usage monitoring |
| **🔐 Security** | Whitelist Access | Only authorized Telegram IDs allowed |
| | Access Attempt Alerts | Administrators receive instant notifications of unauthorized actions |

---

## 🚀 Quick Start

### Installation

```bash
cd /opt
git clone [https://github.com/wandel-dr/proxmox-telegram-bot.git](https://github.com/wandel-dr/proxmox-telegram-bot.git)
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
PROXMOX_TOKEN_NAME=telegram-bot@pve!
PROXMOX_TOKEN_VALUE=your_token_value
PROXMOX_PORT=8006

# Alert & Application Settings
LANGUAGE=es
CPU_TEMP_THRESHOLD=80
CPU_USAGE_THRESHOLD=70
RAM_USAGE_THRESHOLD=70
CHECK_INTERVAL=30

```

> 💡 **How to create an API token in Proxmox VE:** > Go to `Datacenter → Permissions → API Tokens → Add`.
> Required Permissions: `/`

### Execution

```bash
python main.py

```

---

## 🎯 Bot Commands

| Command | Description |
| --- | --- |
| `/start` | Welcome message and command list |
| `/status` | Complete host summary status |
| `/vm` | List of all Virtual Machines |
| `/lxc` | List of all LXC Containers |
| `/console <cmd>` | Execute a terminal command (`ls`, `mkdir`, etc.) |

---

## 🔧 Autostart via systemd

Create the service file `/etc/systemd/system/proxmox-bot.service`:

```ini
[Unit]
Description=Proxmox VE Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/proxmox-telegram-bot
ExecStart=/opt/proxmox-telegram-bot/venv/bin/python /opt/proxmox-telegram-bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

Enable and start the background service:

```bash
systemctl daemon-reload
systemctl enable --now proxmox-bot.service

```

---

## 🛡️ Security

### Multi-level Protection:

* ✅ **Whitelist Authorization** — Only explicitly authorized Telegram IDs can interact with the bot.
* ✅ **Intrusion Attempt Alerts** — Instant administrative notifications when unauthorized users attempt actions.
* ✅ **Secured Console** — Strict shell command blacklist protecting your infrastructure against:
* `rm -rf /`, `mkfs`, `fdisk`, `dd of=/dev/`, `wipefs`
* `shutdown`, `reboot`, `halt`, `poweroff`
* Fork bombs and dangerous logical syntax constructions.


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
│   ├── en.json
│   ├── es.json
│   └── ru.json
│
├── proxmox/                              # Proxmox API integration
│   ├── __init__.py
│   ├── client.py                         # API client instance
│   ├── vms.py                            # Virtual Machine operations
│   ├── lxcs.py                           # LXC Container operations
│   └── utils.py                          # Proxmox helper utilities
│
├── services/                             # Additional internal services
│   ├── __init__.py
│   └── alerts.py                         # Monitoring loop and alert system
│
└── system/                               # System level utilities
    ├── __init__.py
    ├── checks.py                         # System metrics (disk, RAM, system load)
    └── sensors.py                        # Thermal monitoring and hardware sensors

```

---

## 📸 Demo

### 🖥️ Bot Interface in Action

---

## 📄 License

**MIT License** — Full usage freedom with liability disclaimer.

```text
MIT License © 2025-2026 Sliva

```

---

### ⭐ If you found this project useful, give it a star!

### 🐛 Found a bug? — Open an Issue

### 💡 Want to help? — Pull Requests are welcome!

**Original Author:** [Sliva]((https://www.google.com/search?q=https://github.com/sliva-dev))

**Maintained and Enhanced by:** [Wander J.](https://www.google.com/search?q=https://github.com/WJMD)

**Version:** 2.1 (June 2026)


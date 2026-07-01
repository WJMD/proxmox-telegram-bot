# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.18.1] - 2026-07-01

###🧹 Refactoring & Chores
- **Git**: Added `test/` directory to `.gitignore` to prevent test suites from being tracked by @WJMD

---


## [2.18.0] - 2026-07-01

### Added
- **Event System**: Implemented a summary-based event system for internet outages
  - New `system-event-manager.sh` to store and send event summaries when internet is restored
  - New `internet-monitor.sh` to detect and log internet connectivity changes
  - Event file limited to 10 entries to prevent abuse and maintain security
  - Users receive a single summary message with all events that occurred during the outage
- **System Integration**: Modified `battery-monitor.sh` to use the event manager for shutdown notifications
- **System Integration**: Modified `notify_startup.sh` to log system startup events via the event manager
- **Installation**: Updated `install.sh` to deploy new scripts and configure cron for internet monitoring

### Changed
- None

### Fixed
- None

### Security
- **Queue Prevention**: Replaced persistent message queue with a limited event file to avoid potential exploitation

---

## [2.17.0] - 2026-07-01

### Added
- **i18n**: Complete internationalization system with support for English, Spanish, and Russian by @WJMD
- **Alerts**: New automatic battery monitoring system
  - Connect/disconnect notifications
  - 60% warning with 50% shutdown notice
  - Imminent shutdown notification
- **System**: Added `battery-monitor.sh` and `notify_startup.sh` bash scripts with systemd services
- **Installation**: Automated `install.sh` script for dependencies, cron, and services setup

### Changed
- **Dependencies**: Replaced `proxmoxer` library with custom `requests` implementation for better token control
- **UI/UX**: Improved host status formatting (RAM visual bar, cleaner uptime format)
- **Logs**: Standardized all internal backend logs to English

### Fixed
- **Auth**: Fixed Proxmox API token authentication by injecting `PVEAPIToken` into headers
- **Core**: Resolved `get_battery_status` import failure in `services/alerts.py`
- **i18n**: Added fallbacks to `_t.get()` to prevent crashes on missing translation keys
- **API**: Fixed `.current.get()` syntax errors in `vms.py` and `lxcs.py`
- **UI**: Fixed battery alert percentage displaying decimals instead of integers

### Removed
- **Security**: Temporarily disabled `/console` command pending security sandbox improvements

---

## [2.0.0] - 2026-06-28

### Added
- Fork from original Sliva repository
- Initial environment setup (virtualenv, dependencies, `.env`)
- Internationalization (i18n) with JSON files for English, Spanish, and Russian
- Automatic alerts for CPU, RAM, and temperature
- Basic commands: `/status`, `/vm`, `/lxc`, `/start`, `/help`
- Systemd service for the bot (`proxmox-telegram-bot.service`)
- Whitelist system for authorized users

### Changed
- Rewrote authentication layer (from `proxmoxer` to `requests`)
- Improved error handling and logging

### Fixed
- Authentication errors with Proxmox API token
- Syntax errors in Proxmox API interaction

---

## [1.0.0] - 2026-05-xx

### Added
- Base functionality from original Sliva bot
- Basic commands to list VMs and LXCs
- Basic token-based authenticationo).
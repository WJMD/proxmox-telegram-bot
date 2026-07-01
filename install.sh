#!/bin/bash

# colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No color

echo -e "${GREEN}=== Proxmox Telegram Bot - Installer ===${NC}"

# 1. Verify that it is running as root.
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo).${NC}"
    exit 1
fi

# 2. Verify that Python 3 is installed.
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is not installed. Please install it first.${NC}"
    exit 1
fi

# ===== INSTALL SYSTEM DEPENDENCIES =====
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y upower curl

# 3. Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# 5. Create example .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating example .env file...${NC}"
    cat > .env << EOF
# Telegram
BOT_TOKEN=TU_TOKEN_HERE
WHITELIST=TU_ID_HERE

# Proxmox
HOST=IP_PROXMOX
PROXMOX_USER=User for bot. EXAMPLE: BotTelegram@pve
PROXMOX_TOKEN_NAME=TOKEN NAME for bot. EXAMPLE: BotTelegram@pve!bottelegram
PROXMOX_TOKEN_VALUE=TU_TOKEN_SECRET_HERE
PROXMOX_PORT=8006
VERIFY_SSL=False
#Change language (en, es, fr, de, etc.)
LANGUAGE=en

# Alerts
CPU_TEMP_THRESHOLD=80
CPU_USAGE_THRESHOLD=70
RAM_USAGE_THRESHOLD=70
CHECK_INTERVAL=30
EOF
    echo -e "${YELLOW}⚠️  Edit the .env file with your credentials before starting the bot.${NC}"
fi

# ===== INSTALL SYSTEM SCRIPTS =====
echo -e "${YELLOW}Installing system scripts...${NC}"

# Copy scripts to the /usr/local/bin directory
cp system/battery-monitor.sh /usr/local/bin/
cp system/notify_startup.sh /usr/local/bin/

# Make them executable
chmod +x /usr/local/bin/battery-monitor.sh
chmod +x /usr/local/bin/notify_startup.sh

# ===== Configure systemd services =====
echo -e "${YELLOW}Configuring systemd services...${NC}"

# Startup notification service
cp system/notify-startup.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable notify-startup.service

# Battery monitoring service (alternative to cron)
# cp system/battery-monitor.service /etc/systemd/system/
# systemctl enable battery-monitor.service

# ===== Configure Cron for the battery monitor =====
echo -e "${YELLOW}Configuring cron job for battery monitoring...${NC}"
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/battery-monitor.sh") | crontab -

# ===== COPY THE BOT SERVICE =====
echo -e "${YELLOW}Installing bot systemd service...${NC}"
cp system/proxmox-telegram-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable proxmox-telegram-bot.service

# ===== INSTALL INTERNET MONITORING SCRIPTS =====
echo -e "${YELLOW}Installing internet monitoring scripts...${NC}"
cp system/internet-monitor.sh /usr/local/bin/
cp system/system-event-manager.sh /usr/local/bin/
chmod +x /usr/local/bin/internet-monitor.sh
chmod +x /usr/local/bin/system-event-manager.sh

# ===== Configure Cron for Internet Monitor =====
echo -e "${YELLOW}Configuring cron job for internet monitoring...${NC}"
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/internet-monitor.sh") | crontab -

# 7. Final message
echo -e "${GREEN}✅ Installation completed.${NC}"
echo -e "${YELLOW}To start the bot:${NC}"
echo "  systemctl start proxmox-telegram-bot.service"
echo -e "${YELLOW}To view logs:${NC}"
echo "  journalctl -u proxmox-telegram-bot.service -f"
echo -e "${YELLOW}To edit the .env file:${NC}"
echo "  nano .env"
echo -e "${YELLOW}Note: You can also start the notification service with:${NC}"
echo "  systemctl start notify-startup.service"
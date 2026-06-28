#!/bin/bash

# colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No color

echo -e "${GREEN}=== Proxmox Telegram Bot - Installer ===${NC}"

# 1. Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo).${NC}"
    exit 1
fi

# 2. Verify that Python 3 is installed.
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is not installed. Please install it first.${NC}"
    exit 1
fi

# 3. Create virtual environment
echo -e "${YELLOW} Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
echo -e "${YELLOW} Installing dependencies...${NC}"
pip install -r requirements.txt

# 5. Create example .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW} Creating example .env file...${NC}"
    cat > .env << EOF
# Telegram
BOT_TOKEN=TU_TOKEN_HERE
WHITELIST=TU_ID_HERE

# Proxmox
HOST=IP PROXMOX
PROXMOX_USER= User for bot. EXAMPLE: BotTelegram@pve
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

# 6. Copy the systemd service
echo -e "${YELLOW} Installing service systemd...${NC}"
cp system/proxmox-telegram-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable proxmox-telegram-bot.service

# 7. Final message
echo -e "${GREEN}✅ Installation completed.${NC}"
echo -e "${YELLOW}To start the bot:${NC}"
echo "  systemctl start proxmox-telegram-bot.service"
echo -e "${YELLOW}To view logs:${NC}"
echo "  journalctl -u proxmox-telegram-bot.service -f"
echo -e "${YELLOW}To edit the .env file:${NC}"
echo "  nano .env"
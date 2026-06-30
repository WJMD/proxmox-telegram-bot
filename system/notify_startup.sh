#!/bin/bash

# Bot token and chat ID (you can read them from the bot's .env file)
BOT_TOKEN=$(grep BOT_TOKEN /opt/proxmox-telegram-bot/.env | cut -d= -f2 | tr -d ' ')
CHAT_ID=$(grep WHITELIST /opt/proxmox-telegram-bot/.env | cut -d= -f2 | cut -d, -f1 | tr -d ' ')

MESSAGE="🚀 <b>System started!</b>\nProxmox server is now online."

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
     -d chat_id="$CHAT_ID" \
     -d text="$MESSAGE" \
     -d parse_mode="HTML" > /dev/null 2>&1
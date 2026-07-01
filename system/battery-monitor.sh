#!/bin/bash

# =====Get bot credentials from the .env file =====
BOT_TOKEN=$(grep BOT_TOKEN /opt/proxmox-telegram-bot/.env | cut -d= -f2 | tr -d ' ')
CHAT_ID=$(grep WHITELIST /opt/proxmox-telegram-bot/.env | cut -d= -f2 | cut -d, -f1 | tr -d ' ')

# ===== EXECUTION LOG =====
echo "$(date): Executing battery monitor" >> /var/log/battery-monitor.log

# Battery threshold to initiate shutdown (50%)
THRESHOLD=50

# Obtain the battery device
BATTERY_PATH=$(upower -e | grep BAT | head -1)

if [ -z "$BATTERY_PATH" ]; then
    echo "Battery not found"
    exit 1
fi

# Obtain the battery percentage
PERCENTAGE=$(upower -i "$BATTERY_PATH" | grep percentage | awk '{print $2}' | sed 's/%//')

# Obtain the battery state
STATE=$(upower -i "$BATTERY_PATH" | grep state | awk '{print $2}')

# If it's discharging and the percentage is below the threshold, initiate shutdown
if [ "$STATE" == "discharging" ] && [ "$PERCENTAGE" -le "$THRESHOLD" ]; then
    /usr/local/bin/system-event-manager.sh add "⚠️ System shutting down! Battery at ${PERCENTAGE}%."
    sleep 60

   # Check out and shut down
    logger "Battery at ${PERCENTAGE}%. Initiating system shutdown..."
    /sbin/shutdown -h now
fi
 
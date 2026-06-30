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
    # ===== SEND SHUTDOWN NOTIFICATION =====
    MESSAGE="⚠️ <b>System shutting down!</b>\nBattery at ${PERCENTAGE}%. Shutting down in 30 seconds..."
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
         -d chat_id="$CHAT_ID" \
         -d text="$MESSAGE" \
         -d parse_mode="HTML" > /dev/null 2>&1

    # Wait 30 seconds for the message to be delivered
    sleep 30

    # Check out and shut down
    logger "Battery at ${PERCENTAGE}%. Initiating system shutdown..."
    /sbin/shutdown -h now
fi
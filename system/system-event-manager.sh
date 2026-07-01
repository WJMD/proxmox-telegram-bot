#!/bin/bash

EVENT_FILE="/var/tmp/system_events.log"
MAX_EVENTS=50
BOT_TOKEN=$(grep BOT_TOKEN /opt/proxmox-telegram-bot/.env | cut -d= -f2 | tr -d ' ')
CHAT_ID=$(grep WHITELIST /opt/proxmox-telegram-bot/.env | cut -d= -f2 | cut -d, -f1 | tr -d ' ')

# Función para agregar evento
add_event() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $msg" >> "$EVENT_FILE"
    # Mantener solo las últimas MAX_EVENTS líneas
    if [ -f "$EVENT_FILE" ]; then
        local lines=$(wc -l < "$EVENT_FILE")
        if [ "$lines" -gt "$MAX_EVENTS" ]; then
            tail -n "$MAX_EVENTS" "$EVENT_FILE" > "$EVENT_FILE.tmp"
            mv "$EVENT_FILE.tmp" "$EVENT_FILE"
        fi
    fi
}

# Función para enviar resumen y vaciar archivo
send_summary() {
    if [ ! -f "$EVENT_FILE" ] || [ ! -s "$EVENT_FILE" ]; then
        return 0
    fi
    # Verificar conectividad a Internet
    if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        return 1
    fi
    # Construir mensaje resumen
    local summary="📋 <b>System Event Summary (Internet was down)</b>\n"
    local count=0
    while IFS= read -r line; do
        count=$((count+1))
        summary="${summary}${count}. ${line}\n"
    done < "$EVENT_FILE"
    # Enviar resumen
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
         -d chat_id="$CHAT_ID" \
         -d text="$summary" \
         -d parse_mode="HTML" > /dev/null 2>&1
    # Vaciar archivo
    > "$EVENT_FILE"
}

# Modo de uso
if [ "$1" == "add" ] && [ -n "$2" ]; then
    add_event "$2"
    exit 0
fi

if [ $# -eq 0 ]; then
    send_summary
    exit 0
fi

echo "Usage: $0 [add <message>]  OR  $0  (to send summary)"
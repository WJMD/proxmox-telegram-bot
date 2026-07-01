#!/bin/bash

STATE_FILE="/var/tmp/internet_state"

# Verificar conectividad
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    CURRENT_STATE="online"
else
    CURRENT_STATE="offline"
fi

# Leer estado anterior
if [ -f "$STATE_FILE" ]; then
    OLD_STATE=$(cat "$STATE_FILE")
else
    OLD_STATE="unknown"
fi

# Si cambió el estado
if [ "$CURRENT_STATE" != "$OLD_STATE" ]; then
    if [ "$CURRENT_STATE" == "offline" ]; then
        /usr/local/bin/system-event-manager.sh add "🌐 Internet connection lost"
    elif [ "$CURRENT_STATE" == "online" ] && [ "$OLD_STATE" == "offline" ]; then
        /usr/local/bin/system-event-manager.sh add "🌐 Internet connection restored"
        # Intentar enviar resumen inmediatamente
        /usr/local/bin/system-event-manager.sh
    fi
    echo "$CURRENT_STATE" > "$STATE_FILE"
fi
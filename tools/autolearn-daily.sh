#!/bin/bash
# autolearn-daily.sh - Daily autonomous learning trigger
# Place this in /etc/cron.daily/ or run via OpenClaw scheduler

export TZ=America/St_Johns
LOG_FILE="/config/clawd/logs/autolearn_cron.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting daily autolearn..." >> "$LOG_FILE"

cd /config/clawd || exit 1

# Run the autolearn tool
/usr/local/bin/autolearn >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Autolearn completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Autolearn failed with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"

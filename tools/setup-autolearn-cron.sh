#!/bin/bash
# setup-autolearn-cron.sh - Setup cron job for autonomous learning
# Run this script to enable daily autonomous learning

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAWD_DIR="/config/clawd"
LOG_DIR="$CLAWD_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "🧠 Setting up Autolearn Cron Job"
echo "================================"
echo ""

# Check if we're in a container without crontab
if ! command -v crontab >/dev/null 2>&1; then
    echo "⚠️  crontab not available in this environment"
    echo ""
    echo "Alternative setup methods:"
    echo ""
    echo "1. Home Assistant Automation:"
    echo "   Add to configuration.yaml:"
    echo "   shell_command:"
    echo "     claw_autolearn: 'cd $CLAWD_DIR && python3 tools/claw_autolearn.py >> $LOG_DIR/autolearn_cron.log 2>&1'"
    echo ""
    echo "   automation:"
    echo "     - alias: 'Claw Daily Autolearn'"
    echo "       trigger:"
    echo "         platform: time"
    echo "         at: '09:00:00'"
    echo "       action:"
    echo "         service: shell_command.claw_autolearn"
    echo ""
    echo "2. Systemd Timer (Linux systems):"
    echo "   sudo cp $SCRIPT_DIR/autolearn-daily.service /etc/systemd/system/"
    echo "   sudo cp $SCRIPT_DIR/autolearn-daily.timer /etc/systemd/system/"
    echo "   sudo systemctl enable --now autolearn-daily.timer"
    echo ""
    echo "3. Manual cron on host:"
    echo "   Add to host crontab:"
    echo "   0 9 * * * docker exec <container> /usr/local/bin/autolearn"
    echo ""
    echo "4. OpenClaw Scheduler:"
    echo "   Use the automation config in: $CLAWD_DIR/data/autolearn_automation.json"
    exit 0
fi

# Setup crontab
echo "✓ crontab is available"
echo ""

# Create the cron job
CRON_JOB="0 9 * * * TZ=America/St_Johns cd $CLAWD_DIR \u0026\u0026 /usr/local/bin/autolearn \u003e\u003e $LOG_DIR/autolearn_cron.log 2\u003e\u00261 # Claw Autolearn"

# Check if already exists
if crontab -l 2>/dev/null | grep -q "Claw Autolearn"; then
    echo "ℹ️  Cron job already exists. Updating..."
    (crontab -l 2>/dev/null | grep -v "Claw Autolearn"; echo "$CRON_JOB") | crontab -
else
    echo "📝 Adding new cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
fi

echo ""
echo "✅ Cron job installed!"
echo ""
echo "Current crontab:"
crontab -l | grep "Claw Autolearn" | sed 's/^/  /'
echo ""
echo "📋 Next steps:"
echo "  • Learning runs daily at 9:00 AM NT"
echo "  • Logs: $LOG_DIR/autolearn_cron.log"
echo "  • Run manually: autolearn"
echo "  • View status: autolearn --status"

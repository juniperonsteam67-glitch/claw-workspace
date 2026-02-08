#!/bin/bash
# Network Monitor Check - Standalone Version
# Reads JSON config, logs to memory

CONFIG_FILE="/config/clawd/network-monitor.json"
MEMORY_DIR="/config/clawd/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
TODAY=$(date "+%Y-%m-%d")
LOG_FILE="$MEMORY_DIR/network-monitor-$TODAY.log"

mkdir -p "$MEMORY_DIR"

echo "" >> "$LOG_FILE"
echo "## Network Monitor Check - $TIMESTAMP" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Use Python to extract service data, then check with bash
python3 << 'PYEOF'
import json
import socket
import sys

with open("/config/clawd/network-monitor.json") as f:
    config = json.load(f)

down_required = []

for svc in config.get("services", []):
    name = svc["name"]
    host = svc["host"]
    port = svc["port"]
    optional = svc.get("optional", True)
    
    # Check TCP connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        is_up = (result == 0)
    except Exception:
        is_up = False
    
    status = "UP" if is_up else "DOWN"
    opt_str = " (optional)" if optional else " **REQUIRED**"
    icon = "✅" if is_up else "❌"
    
    print(f"{icon} {name}: {status}{opt_str}")
    
    if not is_up and not optional:
        down_required.append(name)

print(f"\nDOWN_REQUIRED_COUNT: {len(down_required)}")
if down_required:
    print(f"ALERT_SERVICES: {', '.join(down_required)}")
    sys.exit(2)
else:
    sys.exit(0)
PYEOF

EXIT_CODE=$?

# Also append raw output to log
echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE

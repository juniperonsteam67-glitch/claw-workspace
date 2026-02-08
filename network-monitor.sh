#!/usr/bin/env bash
# Network Monitor - checks critical services
# Logs to memory, returns exit code 2 if non-optional services are down

MEMORY_DIR="/config/clawd/memory"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')
LOG_FILE="$MEMORY_DIR/network-monitor-$TODAY.log"

# Ensure memory dir exists
mkdir -p "$MEMORY_DIR"

# Check TCP port using bash built-in
check_tcp() {
    local host=$1
    local port=$2
    timeout 5 bash -c "> /dev/tcp/$host/$port" 2>/dev/null
}

# Check HTTP service
check_http() {
    local host=$1
    local port=$2
    local expected="${3:-}"
    local url="http://$host:$port"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
    
    if [ -z "$expected" ]; then
        [ "$code" = "200" ]
    else
        [ "$code" = "$expected" ]
    fi
}

# Track results
SERVICES_UP=()
SERVICES_DOWN=()
down_required=()

# Log header to file
echo "" >> "$LOG_FILE"
echo "## Network Monitor Check - $TIMESTAMP" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Check service and log result
check_and_log() {
    local name=$1
    local check_type=$2
    local host=$3
    local port=$4
    local expected=$5
    local optional=$6
    
    if [ "$check_type" = "http" ]; then
        if check_http "$host" "$port" "$expected"; then
            STATUS="UP"
        else
            STATUS="DOWN"
        fi
    else
        if check_tcp "$host" "$port"; then
            STATUS="UP"
        else
            STATUS="DOWN"
        fi
    fi
    
    # Log to file
    if [ "$STATUS" = "UP" ]; then
        icon="✅"
    else
        icon="❌"
    fi
    
    if [ "$optional" = "true" ]; then
        opt_tag=" (optional)"
    else
        opt_tag=" **REQUIRED**"
    fi
    
    echo "$icon $name: $STATUS$opt_tag" >> "$LOG_FILE"
    
    # Track for alerting
    if [ "$STATUS" = "DOWN" ] && [ "$optional" = "false" ]; then
        down_required+=("$name")
    fi
    
    echo "$name: $STATUS"
}

# Run checks - Non-optional services
check_and_log "Home Assistant" "http" "localhost" "8123" "200" "false"
check_and_log "OpenClaw Gateway" "http" "localhost" "9000" "" "false"
check_and_log "External Internet" "tcp" "1.1.1.1" "443" "" "false"

# Run checks - Optional services  
check_and_log "Frigate NVR" "http" "localhost" "8080" "" "true"
check_and_log "MQTT Broker" "tcp" "localhost" "1883" "" "true"
check_and_log "SSH Server" "tcp" "localhost" "22" "" "true"

echo "" >> "$LOG_FILE"

# Summary output
echo "TIMESTAMP: $TIMESTAMP"
echo "DOWN_COUNT: ${#down_required[@]}"

if [ ${#down_required[@]} -gt 0 ]; then
    echo "ALERT_SERVICES: ${down_required[*]}"
    exit 2
fi

exit 0

#!/bin/bash
# Fix timezone in all Python files
# Run this first: export TZ=America/St_Johns

cd /config/clawd/tools

for f in *.py; do
    # Check if already has TZ fix
    if grep -q "TZ.*America/St_Johns" "$f" 2>/dev/null; then
        continue
    fi
    
    # Create temp file with TZ fix at top
    cat > /tmp/tz_fix.py << 'EOF'
import os
os.environ['TZ'] = 'America/St_Johns'
import time
time.tzset()

EOF
    
    # Append rest of file (skip any existing imports at top)
    tail -n +1 "$f" >> /tmp/tz_fix.py
    
    # Replace original
    mv /tmp/tz_fix.py "$f"
    chmod +x "$f"
done

echo "Timezone fix applied to all tools"
echo "Current NST time: $(TZ=America/St_Johns date '+%H:%M:%S')"

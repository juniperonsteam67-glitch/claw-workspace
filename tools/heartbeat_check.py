#!/usr/bin/env python3
"""
Claw Heartbeat Check - Fixed Timezone Version
Properly handles NST (Newfoundland) timezone
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Force Newfoundland timezone
os.environ['TZ'] = 'America/St_Johns'

def get_last_improvement_time():
    """Get timestamp of last improvement cycle"""
    try:
        with open('/config/clawd/memory/improvement_log.jsonl', 'r') as f:
            lines = f.readlines()
            if not lines:
                return None
            last = json.loads(lines[-1])
            ts_str = (last.get('timestamp') or '').strip()
            if not ts_str:
                return None
            # Parse ISO format
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1] + '+00:00'
            return datetime.fromisoformat(ts_str)
    except Exception as e:
        print(f"Error reading log: {e}")
        return None

def get_now_nst():
    """Get current time in Newfoundland timezone"""
    return datetime.now(ZoneInfo('America/St_Johns'))

def check_and_run_improvement():
    """Check if improvement is needed and run if so"""
    last_ts = get_last_improvement_time()
    if not last_ts:
        print("No previous improvement found")
        return run_improvement()
    
    now = get_now_nst()
    
    # Ensure both are timezone-aware
    if last_ts.tzinfo is None:
        # If timestamp is naive, treat it as local Newfoundland time
        last_ts = last_ts.replace(tzinfo=ZoneInfo('America/St_Johns'))
    
    diff_minutes = (now - last_ts).total_seconds() / 60
    
    print(f"Last improvement: {last_ts.strftime('%H:%M:%S')} ({diff_minutes:.1f} min ago)")
    
    if diff_minutes > 20:
        print(f"Overdue by {diff_minutes:.1f} min - running improvement")
        return run_improvement()
    else:
        print(f"On schedule ({diff_minutes:.1f} min since last)")
        return False

def run_improvement():
    """Run improvement cycle"""
    result = subprocess.run(
        ['python3', '/config/clawd/tools/improve.py'],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # Log heartbeat trigger
    log_entry = {
        'timestamp': get_now_nst().isoformat(),
        'trigger': 'heartbeat',
        'action': 'improvement_cycle'
    }
    with open('/config/clawd/memory/heartbeat_log.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    return True

def check_services():
    """Check and restart services if needed"""
    needs_action = False
    
    # Check dashboard
    result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
    if ':8080' not in result.stdout:
        print("Dashboard DOWN - restarting...")
        subprocess.Popen(
            ['python3', '/config/clawd/dashboard/server.py'],
            cwd='/config/clawd/dashboard'
        )
        needs_action = True
    else:
        print("Dashboard OK")
    
    # Check gateway
    if ':18789' not in result.stdout:
        print("Gateway DOWN")
        needs_action = True
    else:
        print("Gateway OK")
    
    return needs_action

def main():
    print(f"🦅 Heartbeat Check - {get_now_nst().strftime('%H:%M:%S NST')}")
    print("=" * 50)
    
    action_taken = False
    
    # Check improvement
    if check_and_run_improvement():
        action_taken = True
    
    # Check services
    if check_services():
        action_taken = True
    
    print(f"\nAction taken: {action_taken}")
    return action_taken

if __name__ == "__main__":
    main()

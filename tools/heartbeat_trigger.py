#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Heartbeat Trigger
Backup system to ensure continuous operation
Runs when heartbeat fires (if cron misfires)
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/config/clawd"
LOG_FILE = "/config/clawd/memory/heartbeat_log.jsonl"

def log_heartbeat(action, result):
    """Log heartbeat activity"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "trigger": "heartbeat",
        "action": action,
        "result": result
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_last_improvement():
    """Check when last improvement ran"""
    improve_log = Path(WORKSPACE) / "memory" / "improvement_log.jsonl"
    
    if not improve_log.exists():
        return None
    
    try:
        with open(improve_log, 'r') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                return datetime.fromisoformat(last_entry['timestamp'].replace('Z', '+00:00'))
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    
    return None

def run_improvement_cycle():
    """Run full improvement cycle"""
    print("🦅 Heartbeat Trigger: Running improvement cycle...")
    
    # Generate ideas
    result1 = subprocess.run(
        ["python3", f"{WORKSPACE}/tools/improve.py"],
        capture_output=True, text=True
    )
    
    # Execute ideas
    result2 = subprocess.run(
        ["python3", f"{WORKSPACE}/tools/execute_ideas.py"],
        capture_output=True, text=True
    )
    
    success = result1.returncode == 0 and result2.returncode == 0
    
    log_heartbeat("improvement_cycle", "success" if success else "failed")
    
    return success

def check_and_commit_changes():
    """Check for uncommitted changes and commit if needed"""
    result = subprocess.run(
        ["git", "-C", WORKSPACE, "status", "--porcelain"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        # There are changes - commit them
        subprocess.run(["git", "-C", WORKSPACE, "add", "-A"], capture_output=True)
        subprocess.run(
            ["git", "-C", WORKSPACE, "commit", "-m", f"Auto-commit from heartbeat at {datetime.now().strftime('%H:%M')}"],
            capture_output=True
        )
        subprocess.run(["git", "-C", WORKSPACE, "push"], capture_output=True)
        
        log_heartbeat("auto_commit", "success")
        return True
    
    return False

def main():
    print("🦅 Heartbeat Trigger - Backup System")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    actions_taken = []
    
    # Check if improvement is overdue
    last_improvement = check_last_improvement()
    if last_improvement:
        minutes_since = (datetime.now() - last_improvement).total_seconds() / 60
        print(f"Last improvement: {minutes_since:.0f} minutes ago")
        
        if minutes_since > 20:  # Overdue by 20+ min
            print("⚠️  Improvement overdue - triggering now")
            if run_improvement_cycle():
                actions_taken.append("ran improvement cycle")
        else:
            print("✓ Improvement on schedule")
    else:
        print("⚠️  No improvement log found - running now")
        if run_improvement_cycle():
            actions_taken.append("ran improvement cycle")
    
    # Check for uncommitted changes
    if check_and_commit_changes():
        actions_taken.append("auto-committed changes")
    
    # Summary
    print()
    if actions_taken:
        print(f"✅ Actions taken: {', '.join(actions_taken)}")
    else:
        print("✅ All systems on track - no action needed")
    
    log_heartbeat("check_complete", "ok")

if __name__ == "__main__":
    main()

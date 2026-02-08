#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Error Recovery
Automatically fixes common issues
"""

import subprocess
import os
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = "/config/clawd"
LOG_FILE = "/config/clawd/memory/recovery_log.jsonl"

RECOVERY_ACTIONS = {
    'git_lock': {
        'check': lambda: Path(f"{WORKSPACE}/.git/index.lock").exists(),
        'fix': lambda: Path(f"{WORKSPACE}/.git/index.lock").unlink() if Path(f"{WORKSPACE}/.git/index.lock").exists() else None,
        'description': 'Remove stale git lock file'
    },
    'dangling_processes': {
        'check': lambda: len(subprocess.run("ps aux | grep chromium | grep -v grep", shell=True, capture_output=True).stdout.decode().strip().split('\n')) > 5,
        'fix': lambda: subprocess.run("pkill -f chromium", shell=True, capture_output=True),
        'description': 'Kill excess chromium processes'
    },
    'large_logs': {
        'check': lambda: any(
            f.stat().st_size > 10*1024*1024 
            for f in Path(f"{WORKSPACE}/memory").glob("*_log.jsonl")
            if f.exists()
        ),
        'fix': lambda: subprocess.run(["python3", f"{WORKSPACE}/tools/log_cleanup.py"], capture_output=True),
        'description': 'Run log cleanup'
    },
    'missing_crons': {
        'check': lambda: False,  # Placeholder - would check if crons are actually running
        'fix': lambda: None,
        'description': 'Check cron health'
    }
}

def log_recovery(action, success, details=""):
    """Log recovery action"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'success': success,
        'details': details
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_and_recover():
    """Check for issues and attempt recovery"""
    print("🦅 Error Recovery System")
    print("=" * 40)
    
    recovered = []
    failed = []
    
    for issue_name, actions in RECOVERY_ACTIONS.items():
        try:
            if actions['check']():
                print(f"⚠️  Issue detected: {issue_name}")
                print(f"   Attempting: {actions['description']}")
                
                actions['fix']()
                
                # Verify fix
                if not actions['check']():
                    print(f"   ✅ Fixed!")
                    log_recovery(issue_name, True)
                    recovered.append(issue_name)
                else:
                    print(f"   ❌ Fix failed")
                    log_recovery(issue_name, False, "Fix verification failed")
                    failed.append(issue_name)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            log_recovery(issue_name, False, str(e))
            failed.append(issue_name)
    
    print()
    if recovered:
        print(f"✅ Recovered {len(recovered)} issue(s): {', '.join(recovered)}")
    
    if failed:
        print(f"❌ Failed to recover {len(failed)} issue(s): {', '.join(failed)}")
    
    if not recovered and not failed:
        print("✅ No issues detected - system healthy")
    
    return len(recovered), len(failed)

def main():
    recovered, failed = check_and_recover()
    
    # Return exit code for scripting
    if failed > 0:
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
"""
Claw Self-Healing Daemon
Keeps my services running without human intervention
"""

import subprocess
import os
import time
import json
from datetime import datetime

LOG_FILE = "/config/clawd/memory/self_heal_log.jsonl"
CHECK_INTERVAL = 60  # seconds

def log_action(action, status, details=""):
    """Log self-healing actions"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "status": status,
        "details": details
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_process(name, check_cmd, restart_cmd):
    """Check if a process is running, restart if not"""
    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            print(f"⚠️  {name} is down, restarting...")
            subprocess.run(restart_cmd, shell=True)
            log_action(f"restart_{name}", "success", f"Restarted at {datetime.now()}")
            return True
        return False
    except Exception as e:
        log_action(f"check_{name}", "error", str(e))
        return False

def check_disk_space():
    """Alert if disk is getting full"""
    try:
        result = subprocess.run("df -h /config | tail -1 | awk '{print $5}' | sed 's/%//'", 
                              shell=True, capture_output=True, text=True)
        usage = int(result.stdout.strip())
        
        if usage > 90:
            log_action("disk_space", "critical", f"Disk usage: {usage}%")
            return True
        elif usage > 75:
            log_action("disk_space", "warning", f"Disk usage: {usage}%")
            return True
        return False
    except Exception as e:
        log_action("disk_space", "error", str(e))
        return False

def check_git_status():
    """Check for uncommitted changes and auto-commit if needed"""
    try:
        os.chdir("/config/clawd")
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            changes = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            
            # Auto-commit with timestamp
            subprocess.run("git add -A", shell=True)
            subprocess.run(f'git commit -m "Auto-commit: {changes} uncommitted changes at $(date)"', shell=True)
            subprocess.run("git push", shell=True)
            
            log_action("auto_commit", "success", f"Committed {changes} changes")
            return True
        return False
    except Exception as e:
        log_action("auto_commit", "error", str(e))
        return False

def main():
    """Main self-healing loop"""
    print("🦅 Claw Self-Healing Daemon started")
    print(f"Logging to: {LOG_FILE}")
    print("Press Ctrl+C to stop\n")
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            actions = []
            
            # Check dashboard server
            if check_process("dashboard", 
                           "ss -tlnp | grep :8080",
                           "cd /config/clawd/dashboard && TZ=America/St_Johns nohup python3 server.py > /dev/null 2>&1 &"):
                actions.append("restarted dashboard")
            
            # Check disk space
            if check_disk_space():
                actions.append("disk alert")
            
            # Auto-commit changes every 5 minutes (not every iteration)
            if int(time.time()) % 300 < 60:  # Every 5 minutes
                if check_git_status():
                    actions.append("auto-committed")
            
            if actions:
                print(f"[{timestamp}] Actions: {', '.join(actions)}")
            else:
                print(f"[{timestamp}] All systems nominal ✓")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n🛑 Self-healing daemon stopped")

if __name__ == "__main__":
    main()

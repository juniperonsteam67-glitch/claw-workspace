#!/usr/bin/env python3
"""
Claw Self-Healing Daemon
Keeps services running without human intervention
"""

import json
import os
import subprocess
import time
from datetime import datetime

os.environ["TZ"] = "America/St_Johns"
try:
    time.tzset()
except Exception:
    pass

LOG_FILE = "/config/clawd/memory/self_heal_log.jsonl"
CHECK_INTERVAL = 60


def run_cmd(cmd, timeout=15, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def log_action(action, status, details=""):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "status": status,
        "details": details,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def start_dashboard():
    proc = subprocess.Popen(
        ["python3", "/config/clawd/dashboard/server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid > 0


def check_process(name, check_cmd):
    try:
        result = run_cmd(check_cmd)
        if result.returncode != 0 or not result.stdout.strip():
            print(f"⚠️  {name} is down, restarting...")
            ok = start_dashboard() if name == "dashboard" else False
            log_action(f"restart_{name}", "success" if ok else "error")
            return ok
        return False
    except subprocess.TimeoutExpired:
        log_action(f"check_{name}", "error", "timeout")
    except Exception as e:
        log_action(f"check_{name}", "error", str(e))
    return False


def check_disk_space():
    try:
        result = run_cmd(["df", "-P", "/config"])
        if result.returncode != 0:
            return False
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return False
        usage_field = lines[1].split()[4].replace("%", "")
        usage = int(usage_field)
        if usage > 90:
            log_action("disk_space", "critical", f"Disk usage: {usage}%")
            return True
        if usage > 75:
            log_action("disk_space", "warning", f"Disk usage: {usage}%")
            return True
    except (IndexError, ValueError) as e:
        log_action("disk_space", "error", f"parse error: {e}")
    except Exception as e:
        log_action("disk_space", "error", str(e))
    return False


def check_git_status():
    try:
        result = run_cmd(["git", "status", "--porcelain"], cwd="/config/clawd", timeout=20)
        if not result.stdout.strip():
            return False
        changes = len([l for l in result.stdout.splitlines() if l.strip()])
        run_cmd(["git", "add", "-A"], cwd="/config/clawd", timeout=20)
        run_cmd(["git", "commit", "-m", f"Auto-commit: {changes} uncommitted changes at {datetime.now().isoformat()}"], cwd="/config/clawd", timeout=20)
        run_cmd(["git", "push"], cwd="/config/clawd", timeout=30)
        log_action("auto_commit", "success", f"Committed {changes} changes")
        return True
    except subprocess.TimeoutExpired:
        log_action("auto_commit", "error", "timeout")
    except Exception as e:
        log_action("auto_commit", "error", str(e))
    return False


def main():
    print("🦅 Claw Self-Healing Daemon started")
    print(f"Logging to: {LOG_FILE}")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            actions = []

            if check_process("dashboard", ["ss", "-tlnp"]):
                actions.append("restarted dashboard")

            # verify dashboard port specifically
            try:
                ss = run_cmd(["ss", "-tlnp"])
                if ":8080" not in ss.stdout:
                    if start_dashboard():
                        actions.append("started dashboard")
            except Exception:
                pass

            if check_disk_space():
                actions.append("disk alert")

            if int(time.time()) % 300 < 60 and check_git_status():
                actions.append("auto-committed")

            if actions:
                print(f"[{timestamp}] Actions: {', '.join(actions)}")
            else:
                print(f"[{timestamp}] All systems nominal ✓")

            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Self-healing daemon stopped")
            return


if __name__ == "__main__":
    main()

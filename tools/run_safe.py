#!/usr/bin/env python3
"""Run commands with retry + logging (no shell=True)."""

import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime

os.environ["TZ"] = "America/St_Johns"
try:
    time.tzset()
except Exception:
    pass

LOG_FILE = "/config/clawd/memory/operation_log.jsonl"


def log_operation(cmd, status, output="", error=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": cmd,
        "status": status,
        "output": (output or "")[:500],
        "error": (error or "")[:500],
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_with_retry(cmd, max_retries=3, retry_delay=5):
    parts = shlex.split(cmd)
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(parts, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                log_operation(cmd, "success", result.stdout)
                return True, result.stdout
            err = f"Exit code {result.returncode}: {result.stderr}"
            if attempt < max_retries:
                log_operation(cmd, f"retry_{attempt}", error=err)
                time.sleep(retry_delay)
            else:
                log_operation(cmd, "failed", error=err)
                return False, result.stderr
        except subprocess.TimeoutExpired:
            err = "Command timed out after 5 minutes"
            log_operation(cmd, f"timeout_attempt_{attempt}", error=err)
            if attempt >= max_retries:
                return False, err
            time.sleep(retry_delay)
        except Exception as e:
            log_operation(cmd, f"exception_attempt_{attempt}", error=str(e))
            if attempt >= max_retries:
                return False, str(e)
            time.sleep(retry_delay)
    return False, "Max retries exceeded"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run_safe.py 'your command here'")
        sys.exit(1)

    command = sys.argv[1]
    print(f"🦅 Running with retry protection: {command}")
    success, output = run_with_retry(command)
    if success:
        print("✓ Success")
        print(output if output else "(no output)")
        sys.exit(0)
    print("❌ Failed after retries")
    print(output)
    sys.exit(1)


if __name__ == "__main__":
    main()

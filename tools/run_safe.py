#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw's "Keep Working" Toolkit
Wraps any command with logging, retry logic, and error recovery
"""

import subprocess
import sys
import time
import json
from datetime import datetime
import os

LOG_FILE = "/config/clawd/memory/operation_log.jsonl"

def log_operation(cmd, status, output="", error=""):
    """Log any operation"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": cmd,
        "status": status,
        "output": output[:500] if output else "",  # Truncate long output
        "error": error[:500] if error else ""
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def run_with_retry(cmd, max_retries=3, retry_delay=5):
    """Run a command with automatic retry on failure"""
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                log_operation(cmd, "success", result.stdout)
                return True, result.stdout
            else:
                error_msg = f"Exit code {result.returncode}: {result.stderr}"
                if attempt < max_retries:
                    log_operation(cmd, f"retry_{attempt}", error=error_msg)
                    time.sleep(retry_delay)
                else:
                    log_operation(cmd, "failed", error=error_msg)
                    return False, result.stderr
                    
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out after 5 minutes"
            log_operation(cmd, f"timeout_attempt_{attempt}", error=error_msg)
            if attempt >= max_retries:
                return False, error_msg
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
        print("Example: python3 run_safe.py 'curl https://api.example.com/data'")
        sys.exit(1)
    
    command = sys.argv[1]
    print(f"🦅 Running with retry protection: {command}")
    
    success, output = run_with_retry(command)
    
    if success:
        print("✓ Success")
        print(output if output else "(no output)")
        sys.exit(0)
    else:
        print("❌ Failed after retries")
        print(output)
        sys.exit(1)

if __name__ == "__main__":
    main()

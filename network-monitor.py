#!/usr/bin/env python3
"""Simple network monitor - checks configured services and logs status."""
import yaml
import subprocess
import datetime
import os
import sys
from pathlib import Path

CONFIG_PATH = Path("/config/clawd/network-monitor.yaml")
MEMORY_DIR = Path("/config/clawd/memory")

def check_tcp(host, port):
    """Check if a TCP port is open."""
    result = subprocess.run(
        ["nc", "-z", "-w", "5", host, str(port)],
        capture_output=True
    )
    return result.returncode == 0

def check_http(host, port, expected_code=None):
    """Check HTTP service."""
    url = f"http://{host}:{port}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "--connect-timeout", "5", url],
            capture_output=True, text=True, timeout=10
        )
        code = int(result.stdout.strip())
        if expected_code:
            return code == expected_code
        return 200 <= code < 500  # Any 2xx-4xx is "up"
    except (ValueError, subprocess.TimeoutExpired):
        return False

def check_service(service):
    """Check a single service."""
    svc_type = service.get("type", "tcp")
    host = service["host"]
    port = service["port"]
    
    if svc_type == "http":
        return check_http(host, port, service.get("expected_code"))
    else:
        return check_tcp(host, port)

def main():
    # Load config
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    
    services = config.get("services", [])
    
    # Run checks
    results = []
    down_required = []
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for svc in services:
        name = svc["name"]
        is_up = check_service(svc)
        is_optional = svc.get("optional", True)
        
        results.append({
            "name": name,
            "status": "UP" if is_up else "DOWN",
            "optional": is_optional
        })
        
        if not is_up and not is_optional:
            down_required.append(name)
    
    # Log to memory file
    MEMORY_DIR.mkdir(exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_path = MEMORY_DIR / f"network-monitor-{today}.log"
    
    with open(log_path, "a") as f:
        f.write(f"\n## Network Monitor Check - {timestamp}\n\n")
        for r in results:
            opt_tag = " (optional)" if r["optional"] else " **REQUIRED**"
            icon = "✅" if r["status"] == "UP" else "❌"
            f.write(f"{icon} {r['name']}: {r['status']}{opt_tag}\n")
        f.write("\n")
    
    # Output results for parsing
    print(f"TIMESTAMP: {timestamp}")
    print(f"DOWN_COUNT: {len(down_required)}")
    for r in results:
        print(f"{r['name']}: {r['status']}")
    
    if down_required:
        print(f"ALERT_SERVICES: {','.join(down_required)}")
        sys.exit(2)  # Exit code 2 = alert needed
    
    sys.exit(0)  # Exit code 0 = all good

if __name__ == "__main__":
    main()

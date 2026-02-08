#!/usr/bin/env python3
"""Network monitor - checks service status and logs results."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

def check_service(url, timeout=5):
    """Check if a service is responding."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        status_code = result.stdout.strip()
        return status_code == "200" or status_code.startswith("2")
    except Exception as e:
        return False

def main():
    # Load services config
    services_path = Path("/config/clawd/memory/network-services.json")
    if not services_path.exists():
        print("No services configured", file=sys.stderr)
        sys.exit(1)
    
    with open(services_path) as f:
        config = json.load(f)
    
    services = config.get("services", [])
    
    # Check each service
    results = []
    failed_non_optional = []
    
    for svc in services:
        name = svc["name"]
        url = svc["url"]
        optional = svc.get("optional", False)
        
        is_up = check_service(url)
        status = "UP" if is_up else "DOWN"
        
        results.append({
            "name": name,
            "url": url,
            "status": status,
            "optional": optional,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        if not is_up and not optional:
            failed_non_optional.append(name)
    
    # Log to memory file
    log_path = Path("/config/clawd/memory/network-monitor-log.jsonl")
    for r in results:
        with open(log_path, "a") as f:
            f.write(json.dumps(r) + "\n")
    
    # Output results as JSON for parsing
    output = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "services": results,
        "failed_non_optional": failed_non_optional,
        "all_ok": len(failed_non_optional) == 0
    }
    print(json.dumps(output))
    
    # Exit with error if non-optional services failed
    sys.exit(0 if output["all_ok"] else 1)

if __name__ == "__main__":
    main()

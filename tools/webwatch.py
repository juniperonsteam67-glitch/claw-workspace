#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw's Web Watch - Autonomous website monitoring
Watches websites for changes and logs them
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime
from urllib.parse import urlparse

WATCH_DIR = "/config/clawd/data/webwatch"
LOG_FILE = "/config/clawd/memory/webwatch_log.jsonl"

def ensure_dirs():
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def get_site_hash(url, retries=3):
    """Fetch site and return content hash with retry logic"""
    import time
    
    for attempt in range(retries):
        try:
            # Use curl to fetch with timeout
            result = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "30", "--retry", "2", url],
                capture_output=True,
                text=True,
                timeout=35
            )
            
            if result.returncode == 0 and result.stdout:
                # Hash the content (normalized - remove dynamic stuff)
                content = result.stdout
                # Simple normalization
                content = ' '.join(content.split())  # Normalize whitespace
                return hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Log failed attempt
            log_event("fetch_attempt", "retry", f"Attempt {attempt + 1}/{retries} failed for {url}")
            
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except subprocess.TimeoutExpired:
            log_event("fetch_attempt", "timeout", f"Attempt {attempt + 1}/{retries} timed out for {url}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            log_event("fetch_attempt", "error", f"Attempt {attempt + 1}/{retries} error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    
    return None

def check_site(url, name=None):
    """Check a single site for changes"""
    ensure_dirs()
    
    name = name or urlparse(url).netloc.replace(".", "_")
    state_file = os.path.join(WATCH_DIR, f"{name}.json")
    
    current_hash = get_site_hash(url)
    if not current_hash:
        return {"error": "Failed to fetch", "url": url}
    
    # Load previous state
    prev_state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            prev_state = json.load(f)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "name": name,
        "hash": current_hash,
        "changed": False
    }
    
    # Check for changes
    if prev_state.get("hash"):
        if prev_state["hash"] != current_hash:
            result["changed"] = True
            result["previous_check"] = prev_state.get("timestamp")
    
    # Save current state
    with open(state_file, 'w') as f:
        json.dump(result, f)
    
    # Log if changed
    if result["changed"]:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    return result

def list_watched_sites():
    """List all sites being watched"""
    ensure_dirs()
    sites = []
    for f in os.listdir(WATCH_DIR):
        if f.endswith('.json'):
            with open(os.path.join(WATCH_DIR, f), 'r') as fp:
                data = json.load(fp)
                sites.append({
                    "name": data.get("name"),
                    "url": data.get("url"),
                    "last_check": data.get("timestamp"),
                    "hash": data.get("hash")
                })
    return sites

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🦅 Claw's Web Watch")
        print("===================")
        print("")
        print("Usage:")
        print(f"  {sys.argv[0]} check <url> [name]  - Check a site")
        print(f"  {sys.argv[0]} list              - List watched sites")
        print("")
        print("Examples:")
        print(f"  {sys.argv[0]} check https://example.com")
        print(f"  {sys.argv[0]} check https://news.ycombinator.com hn")
        print("")
        
        # Show currently watched sites
        sites = list_watched_sites()
        if sites:
            print("Currently watching:")
            for s in sites:
                print(f"  • {s['name']}: {s['url']}")
                print(f"    Last check: {s['last_check']}")
        else:
            print("No sites being watched yet.")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "check" and len(sys.argv) >= 3:
        url = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"🔍 Checking {url}...")
        result = check_site(url, name)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        elif result.get("changed"):
            print(f"🚨 CHANGE DETECTED!")
            print(f"   URL: {result['url']}")
            print(f"   Time: {result['timestamp']}")
            print(f"   Previous: {result.get('previous_check', 'unknown')}")
        else:
            print(f"✓ No changes (hash: {result['hash']})")
            if result.get("previous_check"):
                print(f"  Last change: {result['previous_check']}")
    
    elif cmd == "list":
        sites = list_watched_sites()
        if sites:
            print(f"📡 Watching {len(sites)} site(s):")
            for s in sites:
                print(f"\n  {s['name']}")
                print(f"    URL: {s['url']}")
                print(f"    Last check: {s['last_check']}")
                print(f"    Hash: {s['hash'][:8]}...")
        else:
            print("No sites being watched.")
    
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()

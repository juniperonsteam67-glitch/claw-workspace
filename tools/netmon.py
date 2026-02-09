#!/usr/bin/env python3
import os
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Network Monitor
Monitors my services and alerts if anything fails
"""

import socket
import subprocess
import json
import time
from datetime import datetime

LOG_FILE = "/config/clawd/memory/network_monitor_log.jsonl"
CONFIG_FILE = "/config/clawd/data/network_monitor_config.json"

DEFAULT_SERVICES = [
    {"name": "Dashboard", "host": "127.0.0.1", "port": 8080, "type": "http"},
    {"name": "OpenClaw Gateway", "host": "127.0.0.1", "port": 18789, "type": "tcp"},
    {"name": "Chromium Debug", "host": "127.0.0.1", "port": 9222, "type": "tcp", "optional": True},
    {"name": "Self-Heal Daemon", "check": ["pgrep", "-f", "self_heal_daemon.py"], "type": "process"},
]

def log_event(event_type, service, status, details=""):
    """Log monitoring events"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "service": service,
        "status": status,
        "details": details
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_tcp_port(host, port):
    """Check if a TCP port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_http_service(host, port, path="/"):
    """Check if HTTP service responds"""
    try:
        import urllib.request
        url = f"http://{host}:{port}{path}"
        response = urllib.request.urlopen(url, timeout=5)
        return response.status == 200
    except:
        return False

def check_process(cmd):
    """Check if a process is running"""
    try:
        if isinstance(cmd, str):
            parts = cmd.split()
        else:
            parts = cmd
        result = subprocess.run(parts, capture_output=True, text=True, timeout=8)
        return result.returncode == 0 and bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

def check_service(service):
    """Check a single service"""
    service_type = service.get("type", "tcp")
    name = service.get("name", "unknown")
    
    if service_type == "tcp":
        host = service.get("host", "127.0.0.1")
        port = service.get("port", 80)
        return check_tcp_port(host, port)
    
    elif service_type == "http":
        host = service.get("host", "127.0.0.1")
        port = service.get("port", 80)
        path = service.get("path", "/")
        return check_http_service(host, port, path)
    
    elif service_type == "process":
        cmd = service.get("check", "")
        return check_process(cmd) if cmd else False
    
    return False

def run_monitor():
    """Run one monitoring pass"""
    services = DEFAULT_SERVICES
    
    # Load custom config if exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            custom = json.load(f)
            services = custom.get("services", services)
    
    results = []
    status_changed = False
    
    print(f"🔍 Network Monitor Check - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    for service in services:
        name = service.get("name", "unknown")
        is_optional = service.get("optional", False)
        
        is_up = check_service(service)
        status = "UP" if is_up else "DOWN"
        
        # Check previous status
        prev_status = None
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    entry = json.loads(line)
                    if entry.get("service") == name and entry.get("type") == "status":
                        prev_status = entry.get("status")
                        break
        except:
            pass
        
        # Log status
        log_event("status", name, status)
        
        # Display
        icon = "✅" if is_up else "⚠️ " if is_optional else "❌"
        optional_tag = " (optional)" if is_optional else ""
        print(f"{icon} {name}{optional_tag}: {status}")
        
        # Alert on status change
        if prev_status and prev_status != status:
            status_changed = True
            event_type = "recovered" if is_up else "failed"
            log_event(event_type, name, status, f"Changed from {prev_status}")
            
            if is_up:
                print(f"   🎉 {name} has recovered!")
            else:
                print(f"   🚨 {name} went down!")
                if not is_optional:
                    print(f"   → Attempting auto-restart...")
                    # Try to restart if we have a restart command
                    restart_cmd = service.get("restart")
                    if restart_cmd:
                        try:
                            cmd = restart_cmd if isinstance(restart_cmd, list) else restart_cmd.split()
                            subprocess.run(cmd, timeout=10, capture_output=True)
                            log_event("restart_attempt", name, "attempted")
                        except Exception as e:
                            log_event("restart_attempt", name, "error", str(e))
        
        results.append({
            "name": name,
            "status": status,
            "changed": prev_status != status if prev_status else False
        })
    
    print("=" * 50)
    
    # Summary
    up_count = sum(1 for r in results if r["status"] == "UP")
    total = len(results)
    print(f"Summary: {up_count}/{total} services up")
    
    if status_changed:
        print("⚠️  Status changes detected — check logs")
    else:
        print("✓ All stable")
    
    return results

def show_status():
    """Show current status of all services"""
    print("🦅 Claw Network Monitor - Current Status")
    print("=" * 50)
    
    for service in DEFAULT_SERVICES:
        name = service.get("name")
        is_up = check_service(service)
        is_optional = service.get("optional", False)
        
        icon = "🟢" if is_up else "🟡" if is_optional else "🔴"
        optional = " (optional)" if is_optional else ""
        status = "UP" if is_up else "DOWN"
        
        print(f"{icon} {name}{optional}: {status}")

def show_history(service_name=None, limit=20):
    """Show recent monitoring history"""
    print(f"🦅 Network Monitor History (last {limit} events)")
    print("=" * 50)
    
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            
        entries = [json.loads(l) for l in lines]
        
        if service_name:
            entries = [e for e in entries if e.get("service") == service_name]
        
        for entry in entries[-limit:]:
            ts = entry.get("timestamp", "?")[11:19]  # Just time
            event_type = entry.get("type", "?")
            service = entry.get("service", "?")
            status = entry.get("status", "?")
            print(f"{ts} | {event_type:12s} | {service:20s} | {status}")
            
    except FileNotFoundError:
        print("No history yet. Run a check first.")

def main():
    import sys
    
    if len(sys.argv) < 2:
        # Run monitor check
        run_monitor()
    
    elif sys.argv[1] == "status":
        show_status()
    
    elif sys.argv[1] == "history":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        show_history(service)
    
    elif sys.argv[1] == "loop":
        # Continuous monitoring mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                run_monitor()
                print(f"\nSleeping {interval}s...\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
    
    else:
        print("Usage:")
        print(f"  {sys.argv[0]}           # Run single check")
        print(f"  {sys.argv[0]} status    # Show current status")
        print(f"  {sys.argv[0]} history   # Show history [service]")
        print(f"  {sys.argv[0]} loop [s]  # Continuous monitoring")

if __name__ == "__main__":
    import os
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    main()

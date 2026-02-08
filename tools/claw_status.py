#!/usr/bin/env python3
"""
Claw Status - Unified status command
Shows everything at a glance
"""

import subprocess
import json
import os
from datetime import datetime

WORKSPACE = "/config/clawd"

def section(title):
    print(f"\n{'='*50}")
    print(f"🦅 {title}")
    print('='*50)

def run_cmd(cmd, default="unknown"):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else default
    except:
        return default

def main():
    print("🦅 CLAW STATUS - Everything at a glance")
    print("="*50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} NST")
    
    # System Info
    section("SYSTEM")
    print(f"  Hostname: {run_cmd('hostname')}")
    print(f"  Uptime: {run_cmd('uptime -p', 'unknown')}")
    print(f"  Timezone: America/St_Johns (NST, UTC-3:30)")
    
    # Git Status
    section("GIT REPOSITORY")
    commits = run_cmd(f"git -C {WORKSPACE} rev-list --count HEAD", "0")
    print(f"  Total commits: {commits}")
    last_commit = run_cmd(f"git -C {WORKSPACE} log -1 --format='%h - %s'")
    print(f"  Last commit: {last_commit}")
    branch = run_cmd(f"git -C {WORKSPACE} branch --show-current")
    print(f"  Branch: {branch}")
    
    # File Stats
    section("FILES")
    py_files = run_cmd(f"find {WORKSPACE} -name '*.py' | wc -l", "0")
    print(f"  Python files: {py_files}")
    total_files = run_cmd(f"find {WORKSPACE} -type f | wc -l", "0")
    print(f"  Total files: {total_files}")
    
    # Services
    section("SERVICES")
    dashboard = "🟢 UP" if run_cmd("ss -tlnp | grep :8080") else "🔴 DOWN"
    gateway = "🟢 UP" if run_cmd("ss -tlnp | grep :18789") else "🔴 DOWN"
    print(f"  Dashboard: {dashboard}")
    print(f"  OpenClaw Gateway: {gateway}")
    
    # Cron Jobs
    section("CRON JOBS")
    try:
        result = subprocess.run(["openclaw", "cron", "list"], capture_output=True, text=True)
        lines = [l for l in result.stdout.split('\n') if l.strip()]
        print(f"  Active jobs: {len([l for l in lines if 'id:' in l])}")
        for line in lines:
            if 'name:' in line:
                print(f"    • {line.split('name:')[1].strip()}")
    except:
        print("  Unable to fetch cron jobs")
    
    # Health Summary
    section("HEALTH SUMMARY")
    disk = run_cmd("df -h /config | tail -1 | awk '{print $5}'", "?")
    print(f"  Disk usage: {disk}")
    memory = run_cmd("free -h | grep Mem | awk '{print $3 \"/\" $2}'", "?")
    print(f"  Memory used: {memory}")
    
    # Recent Activity
    section("RECENT ACTIVITY")
    recent_commits = run_cmd(f"git -C {WORKSPACE} log --oneline -5 | head -5")
    if recent_commits:
        for line in recent_commits.split('\n'):
            print(f"  {line}")
    
    print("\n" + "="*50)
    print("For detailed info, use specific tools:")
    print("  python3 tools/netmon.py status")
    print("  python3 tools/self_reflect.py")
    print("  python3 tools/startup_briefing.py")

if __name__ == "__main__":
    main()

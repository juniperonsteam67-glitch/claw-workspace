#!/usr/bin/env python3
"""Claw Status - Unified status command"""

import os
import shlex
import subprocess
import time
from datetime import datetime

os.environ["TZ"] = "America/St_Johns"
try:
    time.tzset()
except Exception:
    pass

WORKSPACE = "/config/clawd"


def section(title):
    print(f"\n{'='*50}")
    print(f"🦅 {title}")
    print('='*50)


def run_cmd(cmd, default="unknown"):
    try:
        parts = cmd if isinstance(cmd, list) else shlex.split(cmd)
        result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else default
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return default


def main():
    print("🦅 CLAW STATUS - Everything at a glance")
    print("="*50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} NST")

    section("SYSTEM")
    print(f"  Hostname: {run_cmd('hostname')}")
    print(f"  Uptime: {run_cmd(['uptime', '-p'], 'unknown')}")
    print("  Timezone: America/St_Johns (NST, UTC-3:30)")

    section("GIT REPOSITORY")
    commits = run_cmd(["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"], "0")
    print(f"  Total commits: {commits}")
    last_commit = run_cmd(["git", "-C", WORKSPACE, "log", "-1", "--format=%h - %s"])
    print(f"  Last commit: {last_commit}")
    branch = run_cmd(["git", "-C", WORKSPACE, "branch", "--show-current"])
    print(f"  Branch: {branch}")

    section("FILES")
    py_files = run_cmd(["bash", "-lc", f"find {WORKSPACE} -name '*.py' | wc -l"], "0")
    total_files = run_cmd(["bash", "-lc", f"find {WORKSPACE} -type f | wc -l"], "0")
    print(f"  Python files: {py_files}")
    print(f"  Total files: {total_files}")

    section("SERVICES")
    ss_out = run_cmd(["ss", "-tlnp"], "")
    dashboard = "🟢 UP" if ":8080" in ss_out else "🔴 DOWN"
    gateway = "🟢 UP" if ":18789" in ss_out else "🔴 DOWN"
    print(f"  Dashboard: {dashboard}")
    print(f"  OpenClaw Gateway: {gateway}")

    section("CRON JOBS")
    try:
        result = subprocess.run(["openclaw", "cron", "list"], capture_output=True, text=True, timeout=15)
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        print(f"  Active jobs: {len([l for l in lines if 'cron ' in l])}")
    except (subprocess.TimeoutExpired, OSError):
        print("  Unable to fetch cron jobs")

    section("HEALTH SUMMARY")
    disk = run_cmd(["df", "-h", "/config"], "?")
    mem = run_cmd(["free", "-h"], "?")
    disk_line = disk.splitlines()[-1].split()[4] if disk and len(disk.splitlines()) > 1 else "?"
    mem_line = "?"
    if mem:
        for ln in mem.splitlines():
            if ln.startswith("Mem:"):
                parts = ln.split()
                if len(parts) >= 3:
                    mem_line = f"{parts[2]}/{parts[1]}"
    print(f"  Disk usage: {disk_line}")
    print(f"  Memory used: {mem_line}")

    section("RECENT ACTIVITY")
    recent_commits = run_cmd(["git", "-C", WORKSPACE, "log", "--oneline", "-5"])
    if recent_commits:
        for line in recent_commits.split('\n'):
            print(f"  {line}")


if __name__ == "__main__":
    main()

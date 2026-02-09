#!/usr/bin/env python3
"""Claw Performance Monitor"""

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

LOG_FILE = "/config/clawd/memory/performance_log.jsonl"


def run_cmd(cmd, timeout=10):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def measure_git_operations():
    start = time.time()
    result = run_cmd(["git", "-C", "/config/clawd", "status"], timeout=15)
    return {"git_status_time": round(time.time() - start, 3), "git_success": result.returncode == 0}


def measure_file_operations():
    test_file = "/tmp/perf_test.txt"
    start = time.time()
    with open(test_file, "w") as f:
        f.write("x" * 1000000)
    write_time = time.time() - start

    start = time.time()
    with open(test_file, "r") as f:
        _ = f.read()
    read_time = time.time() - start

    os.remove(test_file)
    return {"file_write_1mb": round(write_time, 3), "file_read_1mb": round(read_time, 3)}


def measure_python_startup():
    start = time.time()
    run_cmd(["python3", "-c", "print('ok')"], timeout=10)
    return {"python_startup": round(time.time() - start, 3)}


def get_system_stats():
    stats = {}
    try:
        df = run_cmd(["df", "-P", "/config"])
        stats["disk_usage_percent"] = int(df.stdout.strip().splitlines()[1].split()[4].replace("%", ""))
    except (IndexError, ValueError, subprocess.TimeoutExpired):
        stats["disk_usage_percent"] = None

    try:
        free = run_cmd(["free"]) 
        mem_line = [l for l in free.stdout.splitlines() if l.startswith("Mem:")][0]
        parts = mem_line.split()
        used, total = float(parts[2]), float(parts[1])
        stats["memory_usage_percent"] = round((used / total) * 100.0, 1)
    except (IndexError, ValueError, subprocess.TimeoutExpired):
        stats["memory_usage_percent"] = None

    try:
        uptime = run_cmd(["uptime"])
        if "load average:" in uptime.stdout:
            load = uptime.stdout.split("load average:")[1].split(",")[0].strip()
            stats["load_average"] = float(load)
        else:
            stats["load_average"] = None
    except (ValueError, subprocess.TimeoutExpired):
        stats["load_average"] = None

    try:
        ps = run_cmd(["ps", "aux"])
        stats["process_count"] = len(ps.stdout.splitlines())
    except subprocess.TimeoutExpired:
        stats["process_count"] = None

    return stats


def log_performance(metrics):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "metrics": metrics}) + "\n")


def analyze_trends():
    if not os.path.exists(LOG_FILE):
        return None
    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if len(entries) < 2:
        return None
    latest, previous = entries[-1]["metrics"], entries[-2]["metrics"]
    trends = {}
    if "git_status_time" in latest and "git_status_time" in previous:
        trends["git_speed_change"] = round(latest["git_status_time"] - previous["git_status_time"], 3)
    if latest.get("system", {}).get("disk_usage_percent") is not None and previous.get("system", {}).get("disk_usage_percent") is not None:
        trends["disk_growth"] = latest["system"]["disk_usage_percent"] - previous["system"]["disk_usage_percent"]
    return trends


def main():
    print("🦅 Performance Monitor")
    metrics = {
        **measure_git_operations(),
        **measure_file_operations(),
        **measure_python_startup(),
        "system": get_system_stats(),
    }
    log_performance(metrics)
    print(f"Git status: {metrics['git_status_time']}s | Python startup: {metrics['python_startup']}s")
    trends = analyze_trends()
    if trends:
        print(f"Trends: {trends}")


if __name__ == "__main__":
    main()

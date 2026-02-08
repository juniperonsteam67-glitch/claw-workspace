#!/usr/bin/env python3
"""
Claw Self-Monitor
Track my own resource usage and health
"""

import os
import os
os.environ['TZ'] = 'America/St_Johns'
import time
time.tzset()
import subprocess
import json
from datetime import datetime

WORKSPACE = "/config/clawd"

WORKSPACE = "/config/clawd"

WORKSPACE = "/config/clawd"
CONFIG_DIR = "/config/.openclaw"
LOG_FILE = os.path.join(WORKSPACE, "memory", "health_log.jsonl")

def get_disk_usage():
    """Check disk usage of workspace"""
    try:
        result = subprocess.run(
            ["du", "-sh", WORKSPACE],
            capture_output=True, text=True
        )
        return result.stdout.split()[0] if result.stdout else "unknown"
    except:
        return "unknown"

def get_memory_usage():
    """Get system memory info"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_total = None
        mem_available = None
        
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1]) / 1024 / 1024  # GB
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1]) / 1024 / 1024  # GB
        
        if mem_total and mem_available:
            used = mem_total - mem_available
            percent = (used / mem_total) * 100
            return {
                "total_gb": round(mem_total, 2),
                "available_gb": round(mem_available, 2),
                "used_gb": round(used, 2),
                "percent_used": round(percent, 1)
            }
        return {"error": "Could not parse meminfo"}
    except Exception as e:
        return {"error": str(e)}

def get_openclaw_stats():
    """Get OpenClaw session info"""
    try:
        result = subprocess.run(
            ["openclaw", "status"],
            capture_output=True, text=True
        )
        # Parse the output for key stats
        output = result.stdout
        
        stats = {}
        if "sessions" in output.lower():
            # Extract sessions count
            for line in output.split('\n'):
                if 'sessions' in line.lower() and any(c.isdigit() for c in line):
                    stats['raw_line'] = line.strip()
        
        return stats if stats else {"status": "running"}
    except Exception as e:
        return {"error": str(e)}

def count_files():
    """Count various file types in workspace"""
    stats = {
        "total_files": 0,
        "by_extension": {}
    }
    
    try:
        for root, dirs, files in os.walk(WORKSPACE):
            # Skip .git and node_modules
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                stats["total_files"] += 1
                ext = os.path.splitext(file)[1] or "no_extension"
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
    except Exception as e:
        stats["error"] = str(e)
    
    return stats

def check_alerts(health_data):
    """Check for concerning conditions"""
    alerts = []
    
    # Memory check
    mem = health_data.get("memory", {})
    if isinstance(mem, dict) and "percent_used" in mem:
        if mem["percent_used"] > 90:
            alerts.append(f"🚨 HIGH MEMORY USAGE: {mem['percent_used']}%")
        elif mem["percent_used"] > 75:
            alerts.append(f"⚠️  Elevated memory usage: {mem['percent_used']}%")
    
    # File count check (arbitrary threshold)
    files = health_data.get("files", {})
    if isinstance(files, dict) and files.get("total_files", 0) > 10000:
        alerts.append(f"⚠️  Large file count: {files['total_files']} files")
    
    return alerts

def log_health(health_data):
    """Log health data to file"""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(health_data) + '\n')
    except Exception as e:
        print(f"Warning: Could not log health data: {e}")

def generate_report():
    """Generate a health report"""
    now = datetime.now()
    
    health = {
        "timestamp": now.isoformat(),
        "disk_usage": get_disk_usage(),
        "memory": get_memory_usage(),
        "openclaw": get_openclaw_stats(),
        "files": count_files()
    }
    
    # Log for history
    log_health(health)
    
    # Generate report
    report = []
    report.append("=" * 50)
    report.append("🏥 CLAW SELF-HEALTH CHECK")
    report.append("=" * 50)
    report.append(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Memory
    mem = health["memory"]
    if isinstance(mem, dict) and "error" not in mem:
        report.append("🧠 SYSTEM MEMORY")
        report.append(f"  Total: {mem['total_gb']} GB")
        report.append(f"  Used: {mem['used_gb']} GB ({mem['percent_used']}%)")
        report.append(f"  Available: {mem['available_gb']} GB")
        report.append("")
    
    # Disk
    report.append("💾 WORKSPACE DISK USAGE")
    report.append(f"  {health['disk_usage']}")
    report.append("")
    
    # Files
    files = health["files"]
    if "error" not in files:
        report.append("📁 FILE STATISTICS")
        report.append(f"  Total files: {files['total_files']}")
        if files.get("by_extension"):
            report.append("  Top file types:")
            sorted_exts = sorted(files["by_extension"].items(), key=lambda x: x[1], reverse=True)[:5]
            for ext, count in sorted_exts:
                report.append(f"    {ext}: {count}")
        report.append("")
    
    # Alerts
    alerts = check_alerts(health)
    if alerts:
        report.append("🚨 ALERTS")
        for alert in alerts:
            report.append(f"  {alert}")
        report.append("")
    else:
        report.append("✅ All systems nominal")
        report.append("")
    
    report.append("=" * 50)
    
    return '\n'.join(report), health

if __name__ == "__main__":
    report, health = generate_report()
    print(report)
    
    # Return exit code based on alerts
    alerts = check_alerts(health)
    exit(1 if alerts else 0)

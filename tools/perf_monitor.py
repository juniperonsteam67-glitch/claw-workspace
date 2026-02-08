#!/usr/bin/env python3
"""
Claw Performance Monitor
Tracks performance metrics over time
"""

import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

LOG_FILE = "/config/clawd/memory/performance_log.jsonl"

def measure_git_operations():
    """Measure git operation speed"""
    start = time.time()
    result = subprocess.run(
        ["git", "-C", "/config/clawd", "status"],
        capture_output=True
    )
    git_time = time.time() - start
    
    return {
        'git_status_time': round(git_time, 3),
        'git_success': result.returncode == 0
    }

def measure_file_operations():
    """Measure file system performance"""
    test_file = "/tmp/perf_test.txt"
    
    # Write test
    start = time.time()
    with open(test_file, 'w') as f:
        f.write("x" * 1000000)  # 1MB
    write_time = time.time() - start
    
    # Read test
    start = time.time()
    with open(test_file, 'r') as f:
        _ = f.read()
    read_time = time.time() - start
    
    # Cleanup
    os.remove(test_file)
    
    return {
        'file_write_1mb': round(write_time, 3),
        'file_read_1mb': round(read_time, 3)
    }

def measure_python_startup():
    """Measure Python startup time"""
    start = time.time()
    result = subprocess.run(
        ["python3", "-c", "print('ok')"],
        capture_output=True
    )
    py_time = time.time() - start
    
    return {
        'python_startup': round(py_time, 3)
    }

def get_system_stats():
    """Get system statistics"""
    stats = {}
    
    # Disk usage
    try:
        result = subprocess.run(
            "df -h /config | tail -1 | awk '{print $5}' | sed 's/%//'",
            shell=True, capture_output=True, text=True
        )
        stats['disk_usage_percent'] = int(result.stdout.strip())
    except:
        stats['disk_usage_percent'] = None
    
    # Memory info
    try:
        result = subprocess.run(
            "free | grep Mem | awk '{print $3/$2 * 100.0}'",
            shell=True, capture_output=True, text=True
        )
        stats['memory_usage_percent'] = round(float(result.stdout.strip()), 1)
    except:
        stats['memory_usage_percent'] = None
    
    # Load average
    try:
        result = subprocess.run(
            "uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//'",
            shell=True, capture_output=True, text=True
        )
        stats['load_average'] = float(result.stdout.strip())
    except:
        stats['load_average'] = None
    
    # Process count
    try:
        result = subprocess.run(
            "ps aux | wc -l",
            shell=True, capture_output=True, text=True
        )
        stats['process_count'] = int(result.stdout.strip())
    except:
        stats['process_count'] = None
    
    return stats

def log_performance(metrics):
    """Log performance metrics"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def analyze_trends():
    """Analyze performance trends"""
    if not os.path.exists(LOG_FILE):
        return None
    
    entries = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except:
                pass
    
    if len(entries) < 2:
        return None
    
    # Get latest and previous
    latest = entries[-1]['metrics']
    previous = entries[-2]['metrics']
    
    trends = {}
    
    # Compare git performance
    if 'git_status_time' in latest and 'git_status_time' in previous:
        change = latest['git_status_time'] - previous['git_status_time']
        trends['git_speed_change'] = round(change, 3)
    
    # Compare disk usage
    if 'system' in latest and 'system' in previous:
        if latest['system'].get('disk_usage_percent') and previous['system'].get('disk_usage_percent'):
            disk_change = latest['system']['disk_usage_percent'] - previous['system']['disk_usage_percent']
            trends['disk_growth'] = disk_change
    
    return trends

def main():
    print("🦅 Performance Monitor")
    print("=" * 40)
    
    # Collect metrics
    print("📊 Collecting metrics...")
    
    git_metrics = measure_git_operations()
    file_metrics = measure_file_operations()
    py_metrics = measure_python_startup()
    system_stats = get_system_stats()
    
    metrics = {
        **git_metrics,
        **file_metrics,
        **py_metrics,
        'system': system_stats
    }
    
    # Log
    log_performance(metrics)
    
    # Display
    print(f"\n⚡ Performance Metrics:")
    print(f"  Git status: {metrics['git_status_time']}s")
    print(f"  File write 1MB: {metrics['file_write_1mb']}s")
    print(f"  File read 1MB: {metrics['file_read_1mb']}s")
    print(f"  Python startup: {metrics['python_startup']}s")
    print(f"\n💻 System:")
    print(f"  Disk: {metrics['system']['disk_usage_percent']}%")
    print(f"  Memory: {metrics['system']['memory_usage_percent']}%")
    print(f"  Load: {metrics['system']['load_average']}")
    print(f"  Processes: {metrics['system']['process_count']}")
    
    # Trends
    trends = analyze_trends()
    if trends:
        print(f"\n📈 Trends (vs last check):")
        if 'git_speed_change' in trends:
            direction = "slower" if trends['git_speed_change'] > 0 else "faster"
            print(f"  Git: {abs(trends['git_speed_change'])}s {direction}")
        if 'disk_growth' in trends:
            print(f"  Disk: +{trends['disk_growth']}% growth")
    
    print(f"\n✅ Performance logged")

if __name__ == "__main__":
    main()

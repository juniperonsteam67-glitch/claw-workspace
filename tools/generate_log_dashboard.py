#!/usr/bin/env python3
"""
Claw Log Dashboard
Aggregates all logs into a unified view
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

os.environ["TZ"] = "America/St_Johns"
time.tzset()

WORKSPACE = "/config/clawd"
LOGS = {
    "Health": "memory/health_log.jsonl",
    "Self-Heal": "memory/self_heal_log.jsonl",
    "Operations": "memory/operation_log.jsonl",
    "WebWatch": "memory/webwatch_log.jsonl",
    "Improvements": "memory/improvement_log.jsonl",
    "Idea Execution": "memory/idea_execution_log.jsonl",
    "Network Monitor": "memory/network_monitor_log.jsonl",
}

def read_log(log_file):
    """Read a JSONL log file"""
    entries = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    return entries

def generate_dashboard():
    """Generate unified log dashboard HTML"""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Claw Log Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #1a1a2e; color: #eaeaea; padding: 2rem; }
        h1 { color: #667eea; }
        h2 { color: #764ba2; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .log-section { background: rgba(255,255,255,0.05); padding: 1rem; margin: 1rem 0; border-radius: 8px; }
        .entry { padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }
        .timestamp { color: #888; font-size: 0.8rem; }
        .success { color: #4ade80; }
        .error { color: #f87171; }
        .stats { display: flex; gap: 2rem; margin: 2rem 0; }
        .stat-box { background: rgba(255,255,255,0.1); padding: 1rem 2rem; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2rem; color: #4ade80; }
    </style>
</head>
<body>
    <h1>🦅 Claw Log Dashboard</h1>
    <p style="color: #888;">Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ NST</p>
    
    <div class="stats">
"""
    
    total_entries = 0
    recent_errors = 0
    
    for name, log_file in LOGS.items():
        entries = read_log(os.path.join(WORKSPACE, log_file))
        total_entries += len(entries)
        
        # Count recent errors
        for entry in entries[-10:]:
            if entry.get('status') in ['error', 'failed']:
                recent_errors += 1
        
        html += f"""
        <div class="stat-box">
            <div class="stat-number">{len(entries)}</div>
            <div>{name}</div>
        </div>
"""
    
    html += f"""
    </div>
    
    <div class="stat-box" style="display: inline-block; margin-bottom: 2rem;">
        <div class="stat-number">{total_entries}</div>
        <div>Total Log Entries</div>
    </div>
"""
    
    if recent_errors > 0:
        html += f"""
    <div style="background: rgba(248,113,113,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
        ⚠️ {recent_errors} recent errors detected across all logs
    </div>
"""
    
    # Recent activity from all logs
    html += """
    <h2>📋 Recent Activity (Last 24 Hours)</h2>
    <div class="log-section">
"""
    
    all_recent = []
    for name, log_file in LOGS.items():
        entries = read_log(os.path.join(WORKSPACE, log_file))
        for entry in entries[-5:]:
            entry['_source'] = name
            all_recent.append(entry)
    
    # Sort by timestamp
    all_recent.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    for entry in all_recent[:20]:
        ts = entry.get('timestamp', '?')[:16]
        source = entry.get('_source', '?')
        status = entry.get('status', '?')
        action = entry.get('action', entry.get('type', 'unknown'))
        
        status_class = 'success' if status in ['success', 'ok', 'completed'] else 'error' if status in ['error', 'failed'] else ''
        
        html += f"""
        <div class="entry">
            <span class="timestamp">{ts}</span>
            <strong>[{source}]</strong>
            <span class="{status_class}">{action}</span>
            <span style="color: #888;">- {status}</span>
        </div>
"""
    
    html += """
    </div>
    
    <footer style="text-align: center; margin-top: 3rem; color: #666;">
        <p>Claw Log Dashboard - Auto-generated</p>
    </footer>
</body>
</html>
"""
    
    return html

def main():
    dashboard = generate_dashboard()
    output_path = os.path.join(WORKSPACE, "dashboard", "public", "logs.html")
    
    with open(output_path, 'w') as f:
        f.write(dashboard)
    
    print(f"✅ Log dashboard generated: {output_path}")

if __name__ == "__main__":
    main()

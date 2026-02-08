#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Smart Alert System
Monitors logs and sends alerts only for critical issues
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/config/clawd"
ALERT_STATE_FILE = os.path.join(WORKSPACE, "data", "alert_state.json")
LOG_FILES = [
    "memory/network_monitor_log.jsonl",
    "memory/self_heal_log.jsonl",
    "memory/operation_log.jsonl",
]

def load_alert_state():
    """Load previous alert state"""
    if os.path.exists(ALERT_STATE_FILE):
        with open(ALERT_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_alerts": {}, "alert_count": 0}

def save_alert_state(state):
    """Save alert state"""
    os.makedirs(os.path.dirname(ALERT_STATE_FILE), exist_ok=True)
    with open(ALERT_STATE_FILE, 'w') as f:
        json.dump(state, f)

def should_alert(error_key, state):
    """Determine if we should send an alert (rate limiting)"""
    last_alert = state["last_alerts"].get(error_key)
    
    if not last_alert:
        return True
    
    last_time = datetime.fromisoformat(last_alert)
    time_since = datetime.now() - last_time
    
    # Don't alert more than once per hour for same error
    return time_since > timedelta(hours=1)

def check_for_critical_issues():
    """Check logs for critical issues"""
    alerts = []
    
    # Check network monitor
    log_file = os.path.join(WORKSPACE, "memory/network_monitor_log.jsonl")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Check last 5 entries
            for line in lines[-5:]:
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "DOWN" and entry.get("service"):
                        alerts.append({
                            "level": "CRITICAL",
                            "service": entry.get("service"),
                            "message": f"{entry.get('service')} is DOWN",
                            "key": f"service_down_{entry.get('service')}"
                        })
                except:
                    pass
    
    # Check for disk space critical
    try:
        import subprocess
        result = subprocess.run(
            "df -h /config | tail -1 | awk '{print $5}' | sed 's/%//'",
            shell=True, capture_output=True, text=True
        )
        disk_pct = int(result.stdout.strip())
        if disk_pct > 90:
            alerts.append({
                "level": "CRITICAL",
                "service": "Disk Space",
                "message": f"Disk usage critical: {disk_pct}%",
                "key": "disk_space_critical"
            })
    except:
        pass
    
    # Check for repeated operation failures
    log_file = os.path.join(WORKSPACE, "memory/operation_log.jsonl")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_failures = []
            for line in lines[-10:]:
                try:
                    entry = json.loads(line)
                    if entry.get("status") in ["failed", "error"]:
                        recent_failures.append(entry)
                except:
                    pass
            
            if len(recent_failures) >= 5:  # 5+ failures in last 10 ops
                alerts.append({
                    "level": "WARNING",
                    "service": "Operations",
                    "message": f"High failure rate: {len(recent_failures)}/10 operations failed",
                    "key": "high_failure_rate"
                })
    
    return alerts

def generate_alert_report(alerts, state):
    """Generate alert report and update state"""
    if not alerts:
        return None
    
    report = []
    report.append("🚨 CLAW ALERT REPORT")
    report.append("=" * 50)
    report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} NST")
    report.append("")
    
    new_alerts = 0
    for alert in alerts:
        key = alert["key"]
        
        if should_alert(key, state):
            report.append(f"[{alert['level']}] {alert['service']}")
            report.append(f"  {alert['message']}")
            report.append("")
            
            # Update state
            state["last_alerts"][key] = datetime.now().isoformat()
            state["alert_count"] += 1
            new_alerts += 1
    
    if new_alerts == 0:
        return None  # All alerts were rate-limited
    
    report.append("=" * 50)
    report.append(f"Total new alerts: {new_alerts}")
    report.append("These issues require attention.")
    
    return "\n".join(report)

def main():
    print("🦅 Smart Alert System")
    print("=" * 50)
    
    state = load_alert_state()
    alerts = check_for_critical_issues()
    
    if not alerts:
        print("✅ No critical issues detected")
        # Still save state (timestamp update)
        save_alert_state(state)
        return
    
    print(f"Found {len(alerts)} potential issues")
    print(f"After rate limiting: {len([a for a in alerts if should_alert(a['key'], state)])} new alerts")
    
    report = generate_alert_report(alerts, state)
    
    if report:
        print("\n" + report)
        # Save state with updated alert times
        save_alert_state(state)
        
        # Log the alert
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "alerts_triggered": len(alerts),
            "new_alerts": len([a for a in alerts if should_alert(a['key'], state)]),
            "alert_count_total": state["alert_count"]
        }
        
        log_file = os.path.join(WORKSPACE, "memory/alert_log.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Return non-zero so cron knows to send alert
        return 1
    else:
        print("\n⚠️  Issues detected but rate-limited (already alerted recently)")
        save_alert_state(state)
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

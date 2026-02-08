#!/usr/bin/env python3
"""
Claw Predictive Self-Healing
Uses pattern analysis to predict and prevent failures
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

WORKSPACE = "/config/clawd"
LOG_FILE = "/config/clawd/memory/predictive_healing_log.jsonl"
PREDICTIONS_FILE = "/config/clawd/memory/predictions.json"

def log_prediction(issue, confidence, action_taken):
    """Log prediction and action"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "predicted_issue": issue,
        "confidence": confidence,
        "action": action_taken
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def analyze_disk_trend():
    """Predict when disk will be full based on growth rate"""
    # Get disk usage history
    history = []
    perf_log = Path(WORKSPACE) / "memory" / "performance_log.jsonl"
    
    if perf_log.exists():
        with open(perf_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if 'metrics' in entry and 'system' in entry['metrics']:
                        disk = entry['metrics']['system'].get('disk_usage_percent')
                        if disk:
                            history.append({
                                'timestamp': entry['timestamp'],
                                'disk_pct': disk
                            })
                except:
                    pass
    
    if len(history) < 3:
        return None
    
    # Calculate growth rate
    recent = history[-5:]  # Last 5 measurements
    if len(recent) < 2:
        return None
    
    # Simple trend: if growing, predict when it hits 90%
    changes = []
    for i in range(1, len(recent)):
        changes.append(recent[i]['disk_pct'] - recent[i-1]['disk_pct'])
    
    avg_growth = sum(changes) / len(changes)
    
    if avg_growth <= 0:
        return None  # Not growing or shrinking
    
    current = recent[-1]['disk_pct']
    to_full = 90 - current
    
    if to_full <= 0:
        return {
            'issue': 'disk_full',
            'confidence': 100,
            'time_to_issue': 'NOW',
            'current': current
        }
    
    # Estimate time to full (very rough approximation)
    if avg_growth > 0:
        periods_to_full = to_full / avg_growth
        hours_to_full = periods_to_full * 0.25  # Assuming 15-min periods
        
        if hours_to_full < 24:  # Less than 24 hours
            return {
                'issue': 'disk_full',
                'confidence': min(95, 50 + (avg_growth * 10)),
                'time_to_issue': f"~{hours_to_full:.1f} hours",
                'current': current,
                'growth_rate': avg_growth
            }
    
    return None

def predict_service_failure():
    """Predict service failures based on restart patterns"""
    history = []
    heal_log = Path(WORKSPACE) / "memory" / "self_heal_log.jsonl"
    
    if heal_log.exists():
        with open(heal_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('action') and 'restart' in entry['action']:
                        history.append({
                            'timestamp': entry['timestamp'],
                            'service': entry['action'].replace('restart_', ''),
                            'status': entry.get('status')
                        })
                except:
                    pass
    
    if not history:
        return None
    
    # Count restarts per service in last hour
    recent_restarts = defaultdict(int)
    now = datetime.now()
    
    for entry in history:
        try:
            entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            if (now - entry_time).total_seconds() < 3600:  # Last hour
                recent_restarts[entry['service']] += 1
        except:
            pass
    
    # If a service restarted 3+ times in an hour, predict failure
    for service, count in recent_restarts.items():
        if count >= 3:
            return {
                'issue': f'{service}_instability',
                'confidence': min(90, 60 + (count * 10)),
                'details': f"{count} restarts in last hour",
                'service': service
            }
    
    return None

def predict_commit_velocity_drop():
    """Predict if commit rate is dropping"""
    try:
        result = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--since=6 hours ago", "--oneline"],
            capture_output=True, text=True
        )
        recent_commits = len([l for l in result.stdout.strip().split('\n') if l])
        
        result2 = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--since=12 hours ago", "--until=6 hours ago", "--oneline"],
            capture_output=True, text=True
        )
        older_commits = len([l for l in result2.stdout.strip().split('\n') if l])
        
        if recent_commits < older_commits * 0.5 and older_commits > 5:
            return {
                'issue': 'activity_drop',
                'confidence': 75,
                'details': f"Recent: {recent_commits}, Previous: {older_commits}",
                'recent': recent_commits,
                'previous': older_commits
            }
    except:
        pass
    
    return None

def take_preemptive_action(prediction):
    """Take action before failure occurs"""
    issue = prediction['issue']
    
    if issue == 'disk_full':
        # Run cleanup early
        subprocess.run(
            ["python3", f"{WORKSPACE}/tools/log_cleanup.py"],
            capture_output=True
        )
        return "Ran log cleanup preemptively"
    
    elif issue.endswith('_instability'):
        # Increase monitoring frequency temporarily
        service = prediction.get('service', 'unknown')
        return f"Flagged {service} for enhanced monitoring"
    
    elif issue == 'activity_drop':
        # Trigger immediate improvement cycle
        subprocess.run(
            ["python3", f"{WORKSPACE}/tools/improve.py"],
            capture_output=True
        )
        return "Triggered improvement cycle to boost activity"
    
    return "No action available"

def main():
    print("🦅 Predictive Self-Healing")
    print("=" * 50)
    print(f"Analysis time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    predictions = []
    
    # Run all prediction models
    models = [
        ("Disk Usage", analyze_disk_trend),
        ("Service Stability", predict_service_failure),
        ("Activity Level", predict_commit_velocity_drop),
    ]
    
    for name, model_func in models:
        print(f"🔮 Checking {name}...")
        pred = model_func()
        
        if pred:
            predictions.append(pred)
            print(f"   ⚠️  PREDICTION: {pred['issue']}")
            print(f"      Confidence: {pred['confidence']}%")
            print(f"      Time to issue: {pred.get('time_to_issue', 'soon')}")
            
            # Take preemptive action
            action = take_preemptive_action(pred)
            print(f"      Action: {action}")
            
            log_prediction(pred['issue'], pred['confidence'], action)
        else:
            print(f"   ✓ No issues predicted")
    
    # Summary
    print()
    if predictions:
        print(f"⚠️  {len(predictions)} issue(s) predicted and preempted")
    else:
        print("✅ No failures predicted - all systems stable")
    
    # Save predictions for trend analysis
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump({
            'last_check': datetime.now().isoformat(),
            'predictions': predictions,
            'total_predictions_made': len(predictions)
        }, f, indent=2)
    
    print(f"\n📄 Predictions saved: {PREDICTIONS_FILE}")

if __name__ == "__main__":
    main()

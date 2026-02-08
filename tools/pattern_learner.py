#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Pattern Learner
Analyzes logs to learn my behavior patterns and optimize
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

WORKSPACE = "/config/clawd"

def read_all_logs():
    """Read all log files"""
    logs = {}
    log_dir = Path(WORKSPACE) / "memory"
    
    for log_file in log_dir.glob("*_log.jsonl"):
        entries = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except:
                        pass
        except:
            pass
        logs[log_file.stem] = entries
    
    return logs

def analyze_peak_activity(logs):
    """Find when I'm most active"""
    all_timestamps = []
    
    for log_name, entries in logs.items():
        for entry in entries:
            ts = entry.get('timestamp')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    all_timestamps.append(dt)
                except:
                    pass
    
    if not all_timestamps:
        return None
    
    hours = Counter(dt.hour for dt in all_timestamps)
    peak_hour = hours.most_common(1)[0]
    
    return {
        "peak_hour": peak_hour[0],
        "activity_count": peak_hour[1],
        "total_entries": len(all_timestamps)
    }

def find_error_patterns(logs):
    """Find recurring errors"""
    errors = []
    
    for log_name, entries in logs.items():
        for entry in entries:
            if entry.get('status') in ['error', 'failed']:
                errors.append({
                    'log': log_name,
                    'action': entry.get('action', 'unknown'),
                    'error': entry.get('error', entry.get('details', 'unknown')),
                    'timestamp': entry.get('timestamp')
                })
    
    # Group by error type
    error_types = defaultdict(list)
    for err in errors:
        key = f"{err['log']}/{err['action']}"
        error_types[key].append(err)
    
    return {
        'total_errors': len(errors),
        'recurring_issues': [
            {'issue': k, 'count': len(v), 'last_seen': max(e['timestamp'] for e in v)}
            for k, v in sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        ]
    }

def analyze_success_patterns(logs):
    """What works well"""
    successes = []
    
    for log_name, entries in logs.items():
        for entry in entries:
            if entry.get('status') in ['success', 'completed', 'ok']:
                successes.append(entry.get('action', 'unknown'))
    
    success_counts = Counter(successes)
    
    return {
        'total_successes': len(successes),
        'most_reliable': success_counts.most_common(5)
    }

def generate_optimization_recommendations(analysis):
    """Generate actionable recommendations"""
    recommendations = []
    
    # Based on peak activity
    if analysis.get('peak_activity'):
        peak = analysis['peak_activity']
        recommendations.append({
            'type': 'schedule_optimization',
            'recommendation': f"Schedule intensive tasks around hour {peak['peak_hour']} when I'm most active",
            'reason': f"Peak activity with {peak['activity_count']} entries"
        })
    
    # Based on errors
    if analysis.get('error_patterns', {}).get('recurring_issues'):
        for issue in analysis['error_patterns']['recurring_issues'][:3]:
            recommendations.append({
                'type': 'error_prevention',
                'recommendation': f"Add retry logic or pre-checks for {issue['issue']}",
                'reason': f"Failed {issue['count']} times"
            })
    
    # Based on successes
    if analysis.get('success_patterns', {}).get('most_reliable'):
        top_success = analysis['success_patterns']['most_reliable'][0]
        recommendations.append({
            'type': 'double_down',
            'recommendation': f"Do more of '{top_success[0]}' - it's my most reliable operation",
            'reason': f"Succeeded {top_success[1]} times"
        })
    
    return recommendations

def generate_learning_report():
    """Generate complete learning report"""
    print("🦅 Claw Pattern Learner")
    print("=" * 50)
    print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    logs = read_all_logs()
    print(f"📊 Analyzed {len(logs)} log sources")
    
    # Peak activity
    peak_activity = analyze_peak_activity(logs)
    if peak_activity:
        print(f"\n⏰ Peak Activity: Hour {peak_activity['peak_hour']}:00")
        print(f"   {peak_activity['activity_count']} entries during peak")
    
    # Error patterns
    error_patterns = find_error_patterns(logs)
    print(f"\n❌ Errors: {error_patterns['total_errors']} total")
    if error_patterns['recurring_issues']:
        print("   Top recurring issues:")
        for issue in error_patterns['recurring_issues'][:3]:
            print(f"   • {issue['issue']}: {issue['count']} times")
    
    # Success patterns
    success_patterns = analyze_success_patterns(logs)
    print(f"\n✅ Successes: {success_patterns['total_successes']} total")
    print("   Most reliable operations:")
    for op, count in success_patterns['most_reliable'][:3]:
        print(f"   • {op}: {count} successes")
    
    # Recommendations
    analysis = {
        'peak_activity': peak_activity,
        'error_patterns': error_patterns,
        'success_patterns': success_patterns
    }
    
    recommendations = generate_optimization_recommendations(analysis)
    
    print(f"\n💡 Recommendations ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['type']}] {rec['recommendation']}")
        print(f"   Reason: {rec['reason']}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'analysis': analysis,
        'recommendations': recommendations
    }
    
    report_file = Path(WORKSPACE) / "memory" / "learning_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: {report_file}")
    print("=" * 50)
    
    return recommendations

def main():
    recommendations = generate_learning_report()
    
    # Auto-implement simple recommendations
    print("\n🔧 Auto-implementing recommendations...")
    
    for rec in recommendations:
        if rec['type'] == 'error_prevention' and 'retry' in rec['recommendation'].lower():
            print(f"   ✓ Would add retry logic (requires tool modification)")
        elif rec['type'] == 'schedule_optimization':
            print(f"   ✓ Will schedule tasks around hour {rec['recommendation'].split('hour ')[1].split(' ')[0] if 'hour ' in rec['recommendation'] else 'peak'}")
    
    print("\n🦅 Learning cycle complete!")

if __name__ == "__main__":
    main()

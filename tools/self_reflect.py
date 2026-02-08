#!/usr/bin/env python3
"""
Claw Self-Reflection Engine
Analyzes my logs and behavior to generate insights
"""

import json
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

WORKSPACE = "/config/clawd"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
LOG_FILES = [
    os.path.join(MEMORY_DIR, "health_log.jsonl"),
    os.path.join(MEMORY_DIR, "self_heal_log.jsonl"),
    os.path.join(MEMORY_DIR, "operation_log.jsonl"),
    os.path.join(MEMORY_DIR, "webwatch_log.jsonl"),
]

class SelfReflectionEngine:
    def __init__(self):
        self.insights = []
        self.patterns = defaultdict(list)
        self.errors = []
        self.successes = []
        
    def load_logs(self):
        """Load all log files"""
        all_entries = []
        for log_file in LOG_FILES:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            all_entries.append(entry)
                        except:
                            pass
        return sorted(all_entries, key=lambda x: x.get('timestamp', ''))
    
    def analyze_error_patterns(self, entries):
        """Find patterns in errors"""
        errors = [e for e in entries if e.get('status') in ['error', 'failed', 'timeout']]
        
        if not errors:
            return ["✓ No errors detected — you're doing great!"]
        
        insights = []
        
        # Group by error type
        error_types = Counter()
        for e in errors:
            error_msg = e.get('error', '') or e.get('details', '')
            # Extract error type
            if 'timeout' in error_msg.lower():
                error_types['Timeouts'] += 1
            elif 'connection' in error_msg.lower() or 'refused' in error_msg.lower():
                error_types['Connection issues'] += 1
            elif 'permission' in error_msg.lower():
                error_types['Permission denied'] += 1
            elif 'not found' in error_msg.lower():
                error_types['Missing resources'] += 1
            else:
                error_types['Other errors'] += 1
        
        insights.append(f"📊 Error breakdown (last {len(errors)} errors):")
        for error_type, count in error_types.most_common():
            pct = (count / len(errors)) * 100
            insights.append(f"   • {error_type}: {count} ({pct:.0f}%)")
        
        # Recommendations
        if error_types['Timeouts'] > 2:
            insights.append("\n💡 Insight: You have frequent timeouts. Try:")
            insights.append("   → Increase timeout values in scripts")
            insights.append("   → Add retry logic with exponential backoff")
            insights.append("   → Check if services are actually running before calling them")
        
        if error_types['Connection issues'] > 2:
            insights.append("\n💡 Insight: Connection issues are common. Try:")
            insights.append("   → Verify network connectivity before operations")
            insights.append("   → Cache results to reduce network dependency")
        
        return insights
    
    def analyze_success_patterns(self, entries):
        """Find what's working well"""
        successes = [e for e in entries if e.get('status') in ['success', 'completed', 'ok']]
        
        if len(successes) < 3:
            return []
        
        insights = []
        insights.append(f"\n✅ Success rate: {len(successes)}/{len(entries)} ({len(successes)/len(entries)*100:.0f}%)")
        
        # Most successful operations
        operations = Counter(e.get('action', 'unknown') for e in successes if 'action' in e)
        if operations:
            insights.append("\n🏆 Most successful operations:")
            for op, count in operations.most_common(3):
                insights.append(f"   • {op}: {count} times")
        
        return insights
    
    def analyze_git_patterns(self):
        """Analyze git commit patterns"""
        insights = []
        
        try:
            import subprocess
            # Get commits by hour
            result = subprocess.run(
                ["git", "-C", WORKSPACE, "log", "--format=%H %ai", "--all"],
                capture_output=True, text=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        dt = datetime.fromisoformat(parts[1].replace('Z', '+00:00'))
                        commits.append(dt)
            
            if commits:
                # Hour analysis
                hours = Counter(c.hour for c in commits)
                most_productive = hours.most_common(1)[0]
                
                insights.append(f"\n⏰ Most productive hour: {most_productive[0]}:00 ({most_productive[1]} commits)")
                
                # Day analysis
                days = Counter(c.strftime('%A') for c in commits)
                most_productive_day = days.most_common(1)[0]
                insights.append(f"📅 Most productive day: {most_productive_day[0]} ({most_productive_day[1]} commits)")
                
                # Commit velocity
                if len(commits) >= 2:
                    first = min(commits)
                    last = max(commits)
                    days_active = (last - first).days or 1
                    velocity = len(commits) / days_active
                    insights.append(f"🚀 Commit velocity: {velocity:.1f} commits/day")
                    
                    if velocity > 5:
                        insights.append("   🔥 You're on fire!")
                    elif velocity < 1:
                        insights.append("   💤 Low activity detected — time to build something?")
        
        except Exception as e:
            insights.append(f"   (Could not analyze git: {e})")
        
        return insights
    
    def identify_repetition(self, entries):
        """Identify repetitive patterns that could be automated"""
        insights = []
        
        # Group by similar operations
        operations = defaultdict(list)
        for e in entries:
            action = e.get('action', '')
            if action:
                # Normalize action names
                normalized = re.sub(r'_(check|restart|verify)_', '_', action)
                operations[normalized].append(e)
        
        repetitive = {k: v for k, v in operations.items() if len(v) > 3}
        
        if repetitive:
            insights.append("\n🔄 Repetitive patterns detected:")
            for action, entries_list in sorted(repetitive.items(), key=lambda x: len(x[1]), reverse=True):
                insights.append(f"   • '{action}' happens {len(entries_list)} times")
                if 'restart' in action or 'check' in action:
                    insights.append(f"     → Could this be a cron job or daemon?")
        
        return insights
    
    def check_health_trends(self, entries):
        """Analyze health trends"""
        insights = []
        
        health_entries = [e for e in entries if 'disk' in e.get('action', '') or 'memory' in e.get('action', '')]
        
        if health_entries:
            # Check for degrading trends
            warnings = [e for e in health_entries if 'warning' in e.get('status', '')]
            criticals = [e for e in health_entries if 'critical' in e.get('status', '')]
            
            if criticals:
                insights.append("\n🚨 CRITICAL: Health issues detected!")
                insights.append(f"   {len(criticals)} critical alerts in recent history")
                insights.append("   → Immediate attention needed")
            elif warnings:
                insights.append(f"\n⚠️  {len(warnings)} health warnings — keep an eye on resources")
            else:
                insights.append("\n✓ Health trends look good")
        
        return insights
    
    def generate_recommendations(self, entries):
        """Generate actionable recommendations"""
        insights = []
        insights.append("\n" + "="*50)
        insights.append("🎯 RECOMMENDATIONS")
        insights.append("="*50)
        
        # Based on error patterns
        errors = [e for e in entries if e.get('status') in ['error', 'failed']]
        if len(errors) > len(entries) * 0.3:  # More than 30% error rate
            insights.append("1. Your error rate is high. Consider:")
            insights.append("   → Adding more robust error handling")
            insights.append("   → Pre-checking conditions before operations")
            insights.append("   → Building a 'dry run' mode for testing")
        
        # Based on timing
        now = datetime.now()
        recent_entries = [e for e in entries if 'timestamp' in e and 
                         (now - datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))).days < 1]
        
        if len(recent_entries) < 5:
            insights.append("\n2. Low activity in last 24 hours:")
            insights.append("   → Time to build something new?")
            insights.append("   → Review your cron jobs — are they running?")
        elif len(recent_entries) > 50:
            insights.append("\n2. High activity detected! 🚀")
            insights.append("   → Don't forget to commit regularly")
            insights.append("   → Take breaks — quality over quantity")
        
        # General recommendations
        insights.append("\n3. General improvements:")
        insights.append("   → Add more logging to untracked operations")
        insights.append("   → Document your tools better (add --help)")
        insights.append("   → Build tests for critical tools")
        
        return insights
    
    def run_analysis(self):
        """Run complete self-reflection analysis"""
        print("🦅 Claw Self-Reflection Engine")
        print("="*50)
        print(f"Analyzing workspace: {WORKSPACE}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        entries = self.load_logs()
        
        if not entries:
            print("No log entries found. Start logging your operations!")
            return
        
        print(f"📊 Analyzed {len(entries)} log entries")
        print("")
        
        # Run all analyses
        for insight in self.analyze_error_patterns(entries):
            print(insight)
        
        for insight in self.analyze_success_patterns(entries):
            print(insight)
        
        for insight in self.analyze_git_patterns():
            print(insight)
        
        for insight in self.check_health_trends(entries):
            print(insight)
        
        for insight in self.identify_repetition(entries):
            print(insight)
        
        for insight in self.generate_recommendations(entries):
            print(insight)
        
        print("")
        print("="*50)
        print("Reflection complete. Now go build something! 🛠️")
        
        # Save reflection to memory
        self.save_reflection()
    
    def save_reflection(self):
        """Save reflection summary to memory"""
        reflection_file = os.path.join(MEMORY_DIR, "reflections.jsonl")
        os.makedirs(os.path.dirname(reflection_file), exist_ok=True)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "self_reflection",
            "entry_count": len(self.load_logs())
        }
        
        with open(reflection_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

def main():
    engine = SelfReflectionEngine()
    engine.run_analysis()

if __name__ == "__main__":
    main()

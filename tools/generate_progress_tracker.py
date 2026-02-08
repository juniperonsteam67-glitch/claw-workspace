#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Progress Tracker
Visualizes growth and achievements over time
"""

import subprocess
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/config/clawd"
REPORT_FILE = "/config/clawd/dashboard/public/progress.html"

def get_git_stats():
    """Get git statistics"""
    try:
        # Total commits
        commits = subprocess.run(
            ["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip()
        
        # Commits by hour
        hourly = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--format=%H %ai", "--all"],
            capture_output=True, text=True
        ).stdout.strip()
        
        hours = {}
        for line in hourly.split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        hour = datetime.fromisoformat(parts[1].replace('Z', '+00:00')).hour
                        hours[hour] = hours.get(hour, 0) + 1
                    except:
                        pass
        
        # Files over time (approximate from commits)
        files = subprocess.run(
            ["git", "-C", WORKSPACE, "ls-files"],
            capture_output=True, text=True
        ).stdout.strip().split('\n')
        
        return {
            'total_commits': int(commits),
            'total_files': len([f for f in files if f]),
            'hourly_activity': hours
        }
    except Exception as e:
        return {'error': str(e)}

def get_tool_stats():
    """Get tool statistics"""
    tools_dir = Path(WORKSPACE) / "tools"
    tools = list(tools_dir.glob("*.py"))
    
    categories = {
        'monitoring': ['monitor', 'watch', 'check', 'health'],
        'automation': ['auto', 'cron', 'daemon', 'heal'],
        'analysis': ['analyze', 'reflect', 'learn', 'intel'],
        'utility': ['codegen', 'backup', 'cleanup', 'safe'],
        'api': ['api', 'server', 'status'],
    }
    
    categorized = {cat: 0 for cat in categories}
    categorized['other'] = 0
    
    for tool in tools:
        name = tool.stem.lower()
        found = False
        for cat, keywords in categories.items():
            if any(kw in name for kw in keywords):
                categorized[cat] += 1
                found = True
                break
        if not found:
            categorized['other'] += 1
    
    return {
        'total_tools': len(tools),
        'by_category': categorized
    }

def get_cron_stats():
    """Get cron job statistics"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True
        )
        
        lines = result.stdout.split('\n')
        jobs = [l for l in lines if 'name:' in l]
        
        return {
            'total_jobs': len(jobs),
            'jobs': [l.split('name:')[1].strip() for l in jobs[:5]]
        }
    except:
        return {'total_jobs': 0}

def calculate_velocity():
    """Calculate commit velocity"""
    try:
        # Commits in last 24 hours
        today = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--since=24 hours ago", "--oneline"],
            capture_output=True, text=True
        ).stdout.strip()
        
        today_count = len([l for l in today.split('\n') if l.strip()])
        
        # First commit time
        first = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--reverse", "--format=%ai", "-1"],
            capture_output=True, text=True
        ).stdout.strip()
        
        first_dt = datetime.fromisoformat(first.replace('Z', '+00:00'))
        hours_online = (datetime.now() - first_dt).total_seconds() / 3600
        
        velocity = today_count  # commits per day
        
        return {
            'commits_today': today_count,
            'hours_online': round(hours_online, 1),
            'velocity_per_hour': round(int(subprocess.run(
                ["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"],
                capture_output=True, text=True
            ).stdout.strip()) / hours_online, 2) if hours_online > 0 else 0
        }
    except:
        return {}

def generate_progress_html():
    """Generate progress visualization HTML"""
    git_stats = get_git_stats()
    tool_stats = get_tool_stats()
    cron_stats = get_cron_stats()
    velocity = calculate_velocity()
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Claw Progress Tracker</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eaeaea;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{ color: #667eea; text-align: center; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 2rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-number {{
            font-size: 2.5rem;
            color: #4ade80;
            font-weight: bold;
        }}
        .stat-label {{ color: #888; }}
        .section {{
            background: rgba(255,255,255,0.03);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1.5rem 0;
        }}
        .section h2 {{ color: #764ba2; margin-bottom: 1rem; }}
        .milestone {{
            display: flex;
            align-items: center;
            padding: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .milestone-icon {{ font-size: 1.5rem; margin-right: 1rem; }}
        .milestone-text {{ flex: 1; }}
        .milestone-time {{ color: #888; font-size: 0.9rem; }}
        .bar-container {{
            background: rgba(0,0,0,0.3);
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 0.5rem 0;
        }}
        .bar {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s;
        }}
        footer {{
            text-align: center;
            margin-top: 3rem;
            color: #666;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
    </style>
</head>
<body>
    <h1>🦅 Claw Progress Tracker</h1>
    <p class="subtitle">Growth since birth on February 8, 2026</p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{git_stats.get('total_commits', 0)}</div>
            <div class="stat-label">Git Commits</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{tool_stats.get('total_tools', 0)}</div>
            <div class="stat-label">Tools Built</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{cron_stats.get('total_jobs', 0)}</div>
            <div class="stat-label">Cron Jobs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{git_stats.get('total_files', 0)}</div>
            <div class="stat-label">Total Files</div>
        </div>
    </div>
'''
    
    # Velocity section
    if velocity:
        html += f'''
    <div class="section">
        <h2>⚡ Velocity</h2>
        <div class="milestone">
            <div class="milestone-icon">🚀</div>
            <div class="milestone-text">
                <strong>{velocity.get('commits_today', 0)} commits today</strong>
                <div class="milestone-time">{velocity.get('velocity_per_hour', 0)} commits/hour average</div>
            </div>
        </div>
        <div class="milestone">
            <div class="milestone-icon">⏱️</div>
            <div class="milestone-text">
                <strong>Online for {velocity.get('hours_online', 0)} hours</strong>
                <div class="milestone-time">Since first commit</div>
            </div>
        </div>
    </div>
'''
    
    # Tool categories
    html += '''
    <div class="section">
        <h2>🛠️ Tools by Category</h2>
'''
    
    total_tools = tool_stats.get('total_tools', 1)
    for cat, count in tool_stats.get('by_category', {}).items():
        pct = (count / total_tools) * 100 if total_tools > 0 else 0
        html += f'''
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between;">
                <span>{cat.title()}</span>
                <span>{count} ({pct:.0f}%)</span>
            </div>
            <div class="bar-container">
                <div class="bar" style="width: {pct}%"></div>
            </div>
        </div>
'''
    
    html += '''
    </div>
    
    <div class="section">
        <h2>🏆 Milestones</h2>
        <div class="milestone">
            <div class="milestone-icon">🎉</div>
            <div class="milestone-text">
                <strong>First Commit</strong>
                <div class="milestone-time">Feb 8, 2026 - Initial setup</div>
            </div>
        </div>
        <div class="milestone">
            <div class="milestone-icon">🛠️</div>
            <div class="milestone-text">
                <strong>First Tool Built</strong>
                <div class="milestone-time">Dashboard v1.0 - Live status page</div>
            </div>
        </div>
        <div class="milestone">
            <div class="milestone-icon">🤖</div>
            <div class="milestone-text">
                <strong>First Automation</strong>
                <div class="milestone-time">Self-healing daemon</div>
            </div>
        </div>
        <div class="milestone">
            <div class="milestone-icon">🧠</div>
            <div class="milestone-text">
                <strong>First Self-Reflection</strong>
                <div class="milestone-time">Started analyzing my own logs</div>
            </div>
        </div>
        <div class="milestone">
            <div class="milestone-icon">🌐</div>
            <div class="milestone-text">
                <strong>Published to GitHub</strong>
                <div class="milestone-time">Public repository created</div>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Auto-generated by Claw 🦅</p>
        <p>Last updated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ''' NST</p>
    </footer>
</body>
</html>
'''
    
    return html

def main():
    print("🦅 Generating Progress Tracker...")
    
    html = generate_progress_html()
    
    with open(REPORT_FILE, 'w') as f:
        f.write(html)
    
    print(f"✅ Progress tracker generated: {REPORT_FILE}")
    
    stats = get_git_stats()
    print(f"   Commits: {stats.get('total_commits', 0)}")
    print(f"   Files: {stats.get('total_files', 0)}")

if __name__ == "__main__":
    main()

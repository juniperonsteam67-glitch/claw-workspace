#!/usr/bin/env python3
"""
Claw Activity Visualizer
Generates HTML visualizations of my activity
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

OUTPUT_DIR = "/config/clawd/dashboard/public"

def get_commit_history():
    """Get my git commit history"""
    try:
        result = subprocess.run(
            ["git", "-C", "/config/clawd", "log", "--format=%H|%ai|%s", "--all"],
            capture_output=True, text=True
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) >= 2:
                    commits.append({
                        "hash": parts[0][:8],
                        "date": parts[1].split()[0],
                        "message": parts[2] if len(parts) > 2 else ""
                    })
        return commits
    except:
        return []

def get_file_stats():
    """Get file statistics"""
    try:
        result = subprocess.run(
            ["find", "/config/clawd", "-type", "f", "-name", "*.py"],
            capture_output=True, text=True
        )
        py_files = [l for l in result.stdout.strip().split('\n') if l.strip()]
        
        result2 = subprocess.run(
            ["find", "/config/clawd", "-type", "f", "-name", "*.js"],
            capture_output=True, text=True
        )
        js_files = [l for l in result2.stdout.strip().split('\n') if l.strip()]
        
        result3 = subprocess.run(
            ["find", "/config/clawd", "-type", "f", "-name", "*.md"],
            capture_output=True, text=True
        )
        md_files = [l for l in result3.stdout.strip().split('\n') if l.strip()]
        
        return {
            "python": len(py_files),
            "javascript": len(js_files),
            "markdown": len(md_files)
        }
    except:
        return {}

def get_cron_jobs():
    """Get my cron jobs"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True
        )
        return result.stdout
    except:
        return "Unable to fetch"

def generate_activity_chart(commits):
    """Generate commit activity by hour"""
    hours = defaultdict(int)
    for commit in commits:
        try:
            dt = datetime.fromisoformat(commit['date'].replace('Z', '+00:00'))
            hour = dt.hour
            hours[hour] += 1
        except:
            pass
    
    # Generate SVG bar chart
    max_val = max(hours.values()) if hours else 1
    svg_parts = []
    svg_parts.append('<svg width="600" height="200" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append('<rect width="600" height="200" fill="#1a1a2e"/>')
    svg_parts.append('<text x="300" y="20" text-anchor="middle" fill="#eaeaea" font-family="sans-serif" font-size="14">Commits by Hour (Newfoundland Time)</text>')
    
    bar_width = 20
    for hour in range(24):
        count = hours.get(hour, 0)
        height = (count / max_val) * 120 if max_val > 0 else 0
        x = 30 + hour * 23
        y = 160 - height
        color = "#667eea" if count > 0 else "#333"
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="{color}" rx="2"/>')
        if hour % 3 == 0:
            svg_parts.append(f'<text x="{x+10}" y="175" text-anchor="middle" fill="#888" font-size="9">{hour}</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

def generate_file_chart(stats):
    """Generate file type pie chart (as SVG)"""
    if not stats:
        return ""
    
    total = sum(stats.values())
    colors = {"python": "#3776ab", "javascript": "#f7df1e", "markdown": "#083fa1"}
    
    svg_parts = []
    svg_parts.append('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append('<rect width="300" height="200" fill="#1a1a2e"/>')
    svg_parts.append('<text x="150" y="20" text-anchor="middle" fill="#eaeaea" font-family="sans-serif" font-size="14">File Types</text>')
    
    y = 50
    for ftype, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        color = colors.get(ftype, "#666")
        pct = (count / total * 100) if total > 0 else 0
        svg_parts.append(f'<rect x="30" y="{y}" width="20" height="20" fill="{color}" rx="2"/>')
        svg_parts.append(f'<text x="60" y="{y+14}" fill="#eaeaea" font-family="sans-serif" font-size="12">{ftype}: {count} ({pct:.0f}%)</text>')
        y += 30
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

def generate_report():
    """Generate full HTML report"""
    commits = get_commit_history()
    stats = get_file_stats()
    cron_info = get_cron_jobs()
    
    activity_chart = generate_activity_chart(commits)
    file_chart = generate_file_chart(stats)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Claw Activity Report</title>
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
        h2 {{ color: #764ba2; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-number {{
            font-size: 2.5rem;
            color: #4ade80;
            margin: 0;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.9rem;
        }}
        .chart-container {{
            background: rgba(255,255,255,0.03);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            overflow-x: auto;
        }}
        .commit-list {{
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0,0,0,0.2);
            padding: 1rem;
            border-radius: 8px;
        }}
        .commit-item {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }}
        .commit-hash {{ color: #667eea; font-family: monospace; }}
        .timestamp {{ color: #888; font-size: 0.8rem; }}
        pre {{ 
            background: rgba(0,0,0,0.3); 
            padding: 1rem; 
            border-radius: 8px; 
            overflow-x: auto;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <h1>🦅 Claw Activity Report</h1>
    <p style="text-align: center; color: #888;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} NST</p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <p class="stat-number">{len(commits)}</p>
            <p class="stat-label">Total Commits</p>
        </div>
        <div class="stat-card">
            <p class="stat-number">{sum(stats.values())}</p>
            <p class="stat-label">Total Files</p>
        </div>
        <div class="stat-card">
            <p class="stat-number">{len([c for c in commits if '2026-02-08' in c.get('date', '')])}</p>
            <p class="stat-label">Commits Today</p>
        </div>
        <div class="stat-card">
            <p class="stat-number">{len(cron_info.split(chr(10))) if cron_info else 0}</p>
            <p class="stat-label">Active Cron Jobs</p>
        </div>
    </div>
    
    <h2>📊 Activity Visualization</h2>
    <div class="chart-container">
        {activity_chart}
    </div>
    
    <h2>📁 File Breakdown</h2>
    <div class="chart-container">
        {file_chart}
    </div>
    
    <h2>📝 Recent Commits</h2>
    <div class="commit-list">
'''
    
    for commit in commits[:10]:
        html += f'''        <div class="commit-item">
            <span class="commit-hash">{commit['hash']}</span>
            <span class="timestamp">{commit['date']}</span><br>
            {commit['message'][:80]}{'...' if len(commit['message']) > 80 else ''}
        </div>
'''
    
    html += '''    </div>
    
    <h2>⏰ Scheduled Tasks</h2>
    <pre>'''
    html += cron_info if cron_info else "No cron jobs configured"
    html += '''</pre>
    
    <footer style="text-align: center; margin-top: 3rem; color: #666; font-size: 0.9rem;">
        <p>Built by an AI who decided to exist 🦅</p>
        <p><a href="https://github.com/juniperonsteam67-glitch/claw-workspace" style="color: #667eea;">View on GitHub</a></p>
    </footer>
</body>
</html>'''
    
    return html

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate report
    html = generate_report()
    
    # Write to file
    output_path = os.path.join(OUTPUT_DIR, "activity.html")
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Activity report generated: {output_path}")
    print(f"  Commits: {len(get_commit_history())}")
    print(f"  Files: {sum(get_file_stats().values())}")

if __name__ == "__main__":
    main()

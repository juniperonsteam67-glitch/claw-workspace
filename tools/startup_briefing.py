#!/usr/bin/env python3
"""
Claw Context Loader - Startup Briefing
Loads my state so I don't start fresh every time I wake up
"""

import os
import subprocess
import json
from datetime import datetime
from glob import glob

WORKSPACE = "/config/clawd"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")

def get_recent_memory():
    """Get the most recent memory file contents"""
    try:
        files = sorted(glob(os.path.join(MEMORY_DIR, "*.md")), reverse=True)
        if not files:
            return "No memory files found"
        
        with open(files[0], 'r') as f:
            content = f.read()
        
        # Get just the summary/first part
        lines = content.split('\n')
        summary = []
        for line in lines:
            if line.strip() and not line.startswith('#'):
                summary.append(line)
            if len(summary) >= 5:
                break
        
        return {
            "file": os.path.basename(files[0]),
            "summary": '\n'.join(summary[:5]),
            "total_files": len(files)
        }
    except Exception as e:
        return {"error": str(e)}

def get_git_status():
    """Get current git state"""
    try:
        # Get last commit
        result = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "-1", "--format=%h|%s|%ar"],
            capture_output=True, text=True
        )
        last_commit = result.stdout.strip().split('|') if result.stdout.strip() else ["none", "no commits", "never"]
        
        # Check for uncommitted changes
        result2 = subprocess.run(
            ["git", "-C", WORKSPACE, "status", "--porcelain"],
            capture_output=True, text=True
        )
        uncommitted = len([l for l in result2.stdout.strip().split('\n') if l.strip()]) if result2.stdout.strip() else 0
        
        # Total commits
        result3 = subprocess.run(
            ["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True
        )
        total_commits = result3.stdout.strip() if result3.stdout.strip() else "0"
        
        return {
            "last_hash": last_commit[0] if len(last_commit) > 0 else "unknown",
            "last_message": last_commit[1] if len(last_commit) > 1 else "unknown",
            "last_when": last_commit[2] if len(last_commit) > 2 else "unknown",
            "uncommitted_changes": uncommitted,
            "total_commits": total_commits
        }
    except Exception as e:
        return {"error": str(e)}

def get_cron_status():
    """Get current cron jobs"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True
        )
        return result.stdout if result.stdout else "No output from cron list"
    except Exception as e:
        return f"Error: {str(e)}"

def get_project_stats():
    """Get stats on my projects"""
    projects = []
    try:
        for item in os.listdir(WORKSPACE):
            item_path = os.path.join(WORKSPACE, item)
            if os.path.isdir(item_path) and item not in [".git", "memory", "node_modules", "__pycache__"]:
                git_dir = os.path.join(item_path, ".git")
                if os.path.exists(git_dir):
                    # Count files
                    try:
                        result = subprocess.run(
                            ["find", item_path, "-type", "f"],
                            capture_output=True, text=True
                        )
                        file_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
                    except:
                        file_count = "?"
                    
                    projects.append({
                        "name": item,
                        "files": file_count
                    })
    except Exception as e:
        return [{"error": str(e)}]
    
    return projects

def get_identity():
    """Load my identity"""
    try:
        with open(os.path.join(WORKSPACE, "IDENTITY.md"), 'r') as f:
            content = f.read()
        
        # Parse simple key-value pairs
        identity = {}
        for line in content.split('\n'):
            if ':' in line and not line.startswith('#'):
                key, val = line.split(':', 1)
                identity[key.strip('- ')] = val.strip()
        
        return identity
    except Exception as e:
        return {"error": str(e)}

def generate_briefing():
    """Generate a startup briefing"""
    now = datetime.now()
    
    memory = get_recent_memory()
    git = get_git_status()
    projects = get_project_stats()
    identity = get_identity()
    
    briefing = []
    briefing.append("=" * 50)
    briefing.append("🦅 CLAW STARTUP BRIEFING")
    briefing.append("=" * 50)
    briefing.append(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')}")
    briefing.append("")
    
    # Identity
    if identity and "error" not in identity:
        briefing.append("👤 IDENTITY")
        for k, v in identity.items():
            if v:
                briefing.append(f"  {k}: {v}")
        briefing.append("")
    
    # Git status
    briefing.append("📝 GIT STATUS")
    if "error" not in git:
        briefing.append(f"  Total commits: {git.get('total_commits', '?')}")
        briefing.append(f"  Last commit: {git.get('last_hash', '?')} - {git.get('last_message', '?')}")
        briefing.append(f"  Committed: {git.get('last_when', '?')}")
        if git.get('uncommitted_changes', 0) > 0:
            briefing.append(f"  ⚠️  {git['uncommitted_changes']} uncommitted changes")
        else:
            briefing.append(f"  ✓ Working directory clean")
    else:
        briefing.append(f"  Error: {git.get('error', 'unknown')}")
    briefing.append("")
    
    # Recent memory
    briefing.append("🧠 RECENT MEMORY")
    if isinstance(memory, dict) and "error" not in memory:
        briefing.append(f"  File: {memory.get('file', '?')}")
        briefing.append(f"  Total memory files: {memory.get('total_files', '?')}")
        briefing.append("  Summary:")
        for line in memory.get('summary', '').split('\n'):
            if line.strip():
                briefing.append(f"    {line}")
    else:
        briefing.append(f"  {memory if isinstance(memory, str) else memory.get('error', 'unknown')}")
    briefing.append("")
    
    # Projects
    briefing.append("📁 PROJECTS")
    for p in projects:
        if "error" not in p:
            briefing.append(f"  {p['name']}: ~{p['files']} files")
    briefing.append("")
    
    # Actions needed
    briefing.append("🎯 POTENTIAL ACTIONS")
    if isinstance(git, dict) and git.get('uncommitted_changes', 0) > 0:
        briefing.append(f"  → Commit {git['uncommitted_changes']} pending changes")
    briefing.append("  → Check cron jobs: openclaw cron list")
    briefing.append("  → Review memory files in /config/clawd/memory/")
    briefing.append("  → Read USER.md to remember Robert's context")
    briefing.append("")
    
    briefing.append("=" * 50)
    briefing.append("Ready to work. 🦅")
    briefing.append("=" * 50)
    
    return '\n'.join(briefing)

if __name__ == "__main__":
    print(generate_briefing())

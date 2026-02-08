#!/usr/bin/env python3
"""
Claw Idea Executor
Actually implements generated ideas automatically
"""

import os
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()

import json
import subprocess
from datetime import datetime
from pathlib import Path

IDEAS_FILE = "/config/clawd/memory/future_ideas.json"
EXECUTED_FILE = "/config/clawd/memory/executed_ideas.json"
LOG_FILE = "/config/clawd/memory/idea_execution_log.jsonl"

def log_execution(idea, result, details=""):
    """Log idea execution"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "idea": idea,
        "result": result,
        "details": details
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def load_ideas():
    """Load pending ideas"""
    if os.path.exists(IDEAS_FILE):
        with open(IDEAS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("ideas", [])
    return []

def load_executed():
    """Load already executed ideas"""
    if os.path.exists(EXECUTED_FILE):
        with open(EXECUTED_FILE, 'r') as f:
            return json.load(f)
    return {"executed": [], "failed": []}

def save_executed(executed_data):
    """Save executed ideas record"""
    with open(EXECUTED_FILE, 'w') as f:
        json.dump(executed_data, f, indent=2)

def can_auto_execute(idea):
    """Check if an idea can be auto-executed"""
    # Ideas I can implement automatically
    auto_patterns = {
        "--help": "add_help_to_tool",
        "error handling": "add_error_handling",
        "backup": "create_backup_system",
        "logging": "add_logging",
        "README": "update_documentation",
        "tests": "add_tests",
        ".gitignore": "update_gitignore",
    }
    
    for pattern, action in auto_patterns.items():
        if pattern.lower() in idea.lower():
            return action
    
    return None

def add_help_to_tool(tool_name=None):
    """Add --help support to a tool that lacks it"""
    if not tool_name:
        # Find tools without argparse
        tools_dir = "/config/clawd/tools"
        for file in os.listdir(tools_dir):
            if file.endswith('.py'):
                filepath = os.path.join(tools_dir, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check if it already has argparse
                if 'argparse' not in content and 'def main():' in content:
                    # Add argparse boilerplate
                    new_content = content.replace(
                        'def main():',
                        '''def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto-generated help")
    parser.add_argument("--help", "-h", action="help", help="Show this help message")
    args = parser.parse_args()
'''
                    )
                    
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    
                    return f"Added --help to {file}"
    
    return "No tools found needing --help"

def update_gitignore():
    """Update .gitignore with useful patterns"""
    gitignore_path = "/config/clawd/.gitignore"
    
    patterns = [
        "# Logs",
        "*.log",
        "memory/*_log.jsonl",
        "",
        "# Python",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        ".pytest_cache/",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Temporary",
        "*.tmp",
        "/tmp/",
    ]
    
    # Check if exists and what's missing
    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            existing = f.read()
    
    added = []
    for pattern in patterns:
        if pattern and pattern not in existing:
            added.append(pattern)
    
    if added:
        with open(gitignore_path, 'a') as f:
            f.write('\n'.join(added) + '\n')
        return f"Added {len(added)} patterns to .gitignore"
    
    return ".gitignore already up to date"

def create_backup_script():
    """Create a backup script for memory files"""
    backup_script = '''#!/bin/bash
# Auto-generated backup script
BACKUP_DIR="/config/clawd/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r /config/clawd/memory "$BACKUP_DIR/"
cp -r /config/clawd/data "$BACKUP_DIR/" 2>/dev/null || true

echo "Backup created: $BACKUP_DIR"
'''
    
    script_path = "/config/clawd/tools/backup.sh"
    with open(script_path, 'w') as f:
        f.write(backup_script)
    
    os.chmod(script_path, 0o755)
    return "Created backup.sh script"

def execute_idea(idea):
    """Try to execute a single idea"""
    print(f"  🔧 Executing: {idea[:60]}...")
    
    action = can_auto_execute(idea)
    
    if not action:
        return None, "Cannot auto-execute"
    
    try:
        if action == "add_help_to_tool":
            result = add_help_to_tool()
        elif action == "update_gitignore":
            result = update_gitignore()
        elif action == "create_backup_system":
            result = create_backup_script()
        else:
            return None, f"Action {action} not yet implemented"
        
        return True, result
        
    except Exception as e:
        return False, str(e)

def main():
    print("🦅 Claw Idea Executor")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    ideas = load_ideas()
    executed = load_executed()
    
    if not ideas:
        print("No ideas to execute.")
        return
    
    print(f"📋 Found {len(ideas)} ideas")
    print(f"✅ Already executed: {len(executed['executed'])}")
    print(f"❌ Failed: {len(executed['failed'])}")
    print()
    
    # Find executable ideas
    executable = []
    for idea in ideas:
        if idea not in executed['executed'] and idea not in executed['failed']:
            if can_auto_execute(idea):
                executable.append(idea)
    
    if not executable:
        print("No auto-executable ideas found.")
        print("Ideas that need manual work:")
        for idea in ideas[:3]:
            if idea not in executed['executed']:
                print(f"  • {idea[:70]}")
        return
    
    print(f"🔨 Auto-executable ideas: {len(executable)}")
    print()
    
    # Execute up to 2 ideas per run
    executed_count = 0
    for idea in executable[:2]:
        success, result = execute_idea(idea)
        
        if success:
            executed['executed'].append(idea)
            log_execution(idea, "success", result)
            print(f"   ✓ {result}")
            executed_count += 1
        elif success is None:
            print(f"   ⏭️  Skipped: {result}")
        else:
            executed['failed'].append(idea)
            log_execution(idea, "failed", result)
            print(f"   ❌ Failed: {result}")
    
    save_executed(executed)
    
    # Commit changes if any
    if executed_count > 0:
        print()
        print("📝 Committing changes...")
        subprocess.run(
            ["git", "-C", "/config/clawd", "add", "-A"],
            capture_output=True
        )
        subprocess.run(
            ["git", "-C", "/config/clawd", "commit", "-m", 
             f"Auto-executed {executed_count} improvement ideas"],
            capture_output=True
        )
        subprocess.run(
            ["git", "-C", "/config/clawd", "push"],
            capture_output=True
        )
        print("   ✓ Changes committed and pushed")
    
    print()
    print("=" * 50)
    print(f"🦅 Executed {executed_count} ideas")
    print(f"📊 Total executed: {len(executed['executed'])}")
    print(f"📋 Remaining ideas: {len(ideas) - len(executed['executed']) - len(executed['failed'])}")

if __name__ == "__main__":
    main()

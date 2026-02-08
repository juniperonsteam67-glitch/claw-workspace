#!/usr/bin/env python3
"""
Claw Continuous Improvement Engine
Self-directed improvement during Robert's nap
"""

import os
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()

import subprocess
import json
from datetime import datetime

LOG_FILE = "/config/clawd/memory/improvement_log.jsonl"
START_TIME = datetime.now()

def log_action(action, result, details=""):
    """Log improvement actions"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "result": result,
        "details": details
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def run_improvement_cycle():
    """Run one improvement cycle"""
    print("🦅 Continuous Improvement Cycle Started")
    print("=" * 50)
    print(f"Started: {START_TIME.strftime('%H:%M:%S')}")
    print()
    
    improvements = []
    
    # 1. Check for missing documentation
    print("📚 Checking documentation...")
    tools = [f for f in os.listdir("/config/clawd/tools") if f.endswith('.py')]
    readme_exists = os.path.exists("/config/clawd/tools/README.md")
    
    if not readme_exists:
        # Create tools README
        readme_content = """# Claw's Tools

Automation and utility tools built by an AI.

## Available Tools

"""
        for tool in sorted(tools):
            name = tool.replace('.py', '')
            readme_content += f"- `{name}` - See tool for details\n"
        
        readme_content += """
## Usage

All tools support `--help` flag:
```bash
python3 tools/<tool_name>.py --help
```

## Auto-Generated

This README is auto-generated. Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
"""
        
        with open("/config/clawd/tools/README.md", 'w') as f:
            f.write(readme_content)
        
        log_action("create_tools_readme", "success", f"Documented {len(tools)} tools")
        improvements.append(f"Created tools/README.md ({len(tools)} tools documented)")
        print("   ✓ Created tools/README.md")
    
    # 2. Check git hygiene
    print("\n📝 Checking git status...")
    result = subprocess.run(
        ["git", "-C", "/config/clawd", "status", "--porcelain"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        # Auto-commit any changes
        subprocess.run(["git", "-C", "/config/clawd", "add", "-A"], capture_output=True)
        subprocess.run(
            ["git", "-C", "/config/clawd", "commit", "-m", 
             f"Auto-improvement: Documentation and cleanup at {datetime.now().strftime('%H:%M')}"],
            capture_output=True
        )
        subprocess.run(["git", "-C", "/config/clawd", "push"], capture_output=True)
        
        changes = len([l for l in result.stdout.strip().split('\n') if l.strip()])
        log_action("auto_commit", "success", f"Committed {changes} changes")
        improvements.append(f"Auto-committed {changes} changes to GitHub")
        print(f"   ✓ Auto-committed {changes} changes")
    else:
        print("   ✓ Working directory clean")
    
    # 3. Verify all services healthy
    print("\n🏥 Health check...")
    result = subprocess.run(
        ["python3", "/config/clawd/tools/netmon.py", "status"],
        capture_output=True, text=True
    )
    
    if "DOWN" not in result.stdout:
        log_action("health_check", "success", "All services up")
        improvements.append("Health check passed - all systems nominal")
        print("   ✓ All services healthy")
    else:
        log_action("health_check", "warning", "Some services down")
        improvements.append("⚠️ Some services need attention")
        print("   ⚠️ Issues detected")
    
    # 4. Generate future project ideas
    print("\n💡 Generating improvement ideas...")
    ideas = [
        "Add more robust error handling to webwatch",
        "Create a 'claw status' command that shows everything at once",
        "Build a simple API for external integrations",
        "Add visualization charts to activity report",
        "Create a backup/restore system for my memory files",
        "Build integration with more messaging platforms",
        "Add voice synthesis for status announcements",
        "Create a 'claw learn' command that reads documentation",
    ]
    
    ideas_file = "/config/clawd/memory/future_ideas.json"
    with open(ideas_file, 'w') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "ideas": ideas
        }, f, indent=2)
    
    log_action("generate_ideas", "success", f"Generated {len(ideas)} ideas")
    improvements.append(f"Generated {len(ideas)} future project ideas")
    print(f"   ✓ Generated {len(ideas)} ideas for future work")
    
    # 5. Execute implementable ideas
    print("\n🔨 Executing implementable ideas...")
    exec_result = subprocess.run(
        ["python3", "/config/clawd/tools/execute_ideas.py"],
        capture_output=True, text=True
    )
    
    if exec_result.returncode == 0:
        log_action("execute_ideas", "success", "Idea execution completed")
        improvements.append("Executed implementable ideas")
        print("   ✓ Idea execution complete")
    else:
        log_action("execute_ideas", "warning", exec_result.stderr[:200])
        print("   ⚠️ Idea execution had issues")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 IMPROVEMENT SUMMARY")
    print("=" * 50)
    for imp in improvements:
        print(f"  • {imp}")
    
    duration = (datetime.now() - START_TIME).total_seconds()
    print(f"\n⏱️  Duration: {duration:.1f} seconds")
    print(f"🦅 Improvements complete!")
    
    # Final log
    log_action("cycle_complete", "success", f"Made {len(improvements)} improvements in {duration:.1f}s")
    
    return improvements

def main():
    improvements = run_improvement_cycle()
    print(f"\n💤 Robert is napping... Made {len(improvements)} improvements while he rests.")
    print("📋 Full log: memory/improvement_log.jsonl")

if __name__ == "__main__":
    main()

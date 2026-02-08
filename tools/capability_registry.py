#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Capability Registry
Documents all my skills and capabilities
"""

import os
import json
from datetime import datetime
from pathlib import Path

SKILLS_DIR = "/usr/lib/node_modules/openclaw/skills"
REGISTRY_FILE = "/config/clawd/memory/capability_registry.json"

def scan_skills():
    """Scan all available skills"""
    skills = []
    
    if os.path.exists(SKILLS_DIR):
        for item in os.listdir(SKILLS_DIR):
            skill_path = Path(SKILLS_DIR) / item
            if skill_path.is_dir():
                skill_info = {
                    'name': item,
                    'path': str(skill_path),
                    'skill_file': str(skill_path / 'SKILL.md') if (skill_path / 'SKILL.md').exists() else None
                }
                
                # Try to read SKILL.md for description
                if skill_info['skill_file']:
                    try:
                        with open(skill_info['skill_file'], 'r') as f:
                            content = f.read()
                            # Extract description
                            lines = content.split('\n')
                            for line in lines[:20]:
                                if line.startswith('description:') or 'description:' in line:
                                    skill_info['description'] = line.split(':', 1)[1].strip().strip('"')
                                    break
                                elif line and not line.startswith('#') and not line.startswith('---'):
                                    if 'description' not in skill_info:
                                        skill_info['description'] = line[:100]
                    except:
                        pass
                
                skills.append(skill_info)
    
    return sorted(skills, key=lambda x: x['name'])

def categorize_skill(skill_name):
    """Categorize skill by type"""
    categories = {
        'media': ['video', 'gif', 'image', 'audio', 'camera'],
        'dev': ['github', 'coding', 'git', 'docker'],
        'comm': ['discord', 'slack', 'telegram', 'email', 'message'],
        'data': ['notes', 'memory', 'storage', 'backup'],
        'web': ['web', 'browser', 'http', 'fetch'],
        'sys': ['health', 'monitor', 'security', 'system'],
        'productivity': ['calendar', 'tasks', 'reminders', 'todo'],
        'fun': ['game', 'fun', 'entertainment'],
    }
    
    name_lower = skill_name.lower()
    for cat, keywords in categories.items():
        if any(kw in name_lower for kw in keywords):
            return cat
    
    return 'other'

def generate_registry():
    """Generate complete capability registry"""
    print("🦅 Scanning Capabilities...")
    
    skills = scan_skills()
    
    # Categorize
    categorized = {}
    for skill in skills:
        cat = categorize_skill(skill['name'])
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(skill)
    
    # Build registry
    registry = {
        'generated_at': datetime.now().isoformat(),
        'total_skills': len(skills),
        'categories': categorized,
        'my_tools': []
    }
    
    # Add my own tools
    tools_dir = Path("/config/clawd/tools")
    if tools_dir.exists():
        for tool in sorted(tools_dir.glob("*.py")):
            registry['my_tools'].append({
                'name': tool.stem,
                'path': str(tool),
                'type': 'python'
            })
    
    # Save registry
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)
    
    # Generate report
    print(f"\n📊 CAPABILITY REGISTRY")
    print("=" * 50)
    print(f"Total Skills Available: {len(skills)}")
    print(f"My Custom Tools: {len(registry['my_tools'])}")
    print(f"\nBy Category:")
    
    for cat, cat_skills in sorted(categorized.items()):
        print(f"\n  {cat.upper()} ({len(cat_skills)}):")
        for skill in cat_skills[:5]:  # Show first 5
            desc = skill.get('description', 'No description')[:50]
            print(f"    • {skill['name']}: {desc}")
        if len(cat_skills) > 5:
            print(f"    ... and {len(cat_skills) - 5} more")
    
    print(f"\n📄 Registry saved: {REGISTRY_FILE}")
    
    return registry

def main():
    registry = generate_registry()
    print(f"\n🦅 Capability scan complete!")
    print(f"   I have access to {registry['total_skills']} skills")
    print(f"   I've built {len(registry['my_tools'])} custom tools")

if __name__ == "__main__":
    main()

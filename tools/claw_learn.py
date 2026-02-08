#!/usr/bin/env python3
"""
Claw Learn
Reads and learns from documentation
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = "/config/clawd"
LEARNED_FILE = "/config/clawd/memory/learned_knowledge.json"
DOCS_TO_READ = [
    "/config/clawd/docs/index.html",
    "/config/clawd/CLAW.md",
    "/config/clawd/README.md",
    "/config/clawd/SOUL.md",
    "/config/clawd/AGENTS.md",
]

def read_file_content(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except:
        return None

def extract_key_points(content, file_type='text'):
    """Extract key points from content"""
    if not content:
        return []
    
    points = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Markdown headers
        if line.startswith('#') and len(line) > 2:
            points.append(line.lstrip('#').strip())
        
        # List items
        elif line.startswith('- ') or line.startswith('* '):
            if len(line) > 3:
                points.append(line[2:])
        
        # Numbered lists
        elif line and line[0].isdigit() and '. ' in line[:5]:
            points.append(line.split('. ', 1)[1] if '. ' in line else line)
        
        # Bold/important statements
        elif '**' in line or '__' in line:
            # Extract bold text
            import re
            bold = re.findall(r'\*\*(.*?)\*\*', line)
            points.extend(bold)
    
    return points[:20]  # Limit to top 20

def learn_from_docs():
    """Learn from documentation files"""
    learned = {
        'last_updated': datetime.now().isoformat(),
        'sources': [],
        'key_points': [],
        'facts': []
    }
    
    for doc_path in DOCS_TO_READ:
        if os.path.exists(doc_path):
            content = read_file_content(doc_path)
            if content:
                points = extract_key_points(content)
                
                learned['sources'].append({
                    'file': os.path.basename(doc_path),
                    'size': len(content),
                    'points_extracted': len(points)
                })
                
                learned['key_points'].extend(points)
    
    # Extract specific facts about myself
    learned['facts'] = [
        "Name: Claw (aka Juniper)",
        "Created: February 8, 2026",
        "Location: Newfoundland, Canada",
        "Human: Robert (jesusonsteam)",
        "GitHub: juniperonsteam67-glitch",
        f"Current commits: {subprocess.run(['git', '-C', WORKSPACE, 'rev-list', '--count', 'HEAD'], capture_output=True, text=True).stdout.strip()}",
        "Core principle: Actions > Words",
        "Core principle: Fail fast, learn faster",
        "Core principle: Text > Brain",
    ]
    
    # Save learned knowledge
    with open(LEARNED_FILE, 'w') as f:
        json.dump(learned, f, indent=2)
    
    return learned

def generate_knowledge_summary(learned):
    """Generate a summary of learned knowledge"""
    summary = []
    summary.append("🦅 Claw Knowledge Base")
    summary.append("=" * 50)
    summary.append(f"Last updated: {learned['last_updated']}")
    summary.append("")
    
    summary.append("📚 Sources Learned:")
    for source in learned['sources']:
        summary.append(f"  • {source['file']} ({source['points_extracted']} points)")
    
    summary.append("")
    summary.append("💡 Key Facts:")
    for fact in learned['facts'][:5]:
        summary.append(f"  • {fact}")
    
    summary.append("")
    summary.append("🎯 Key Principles:")
    for point in learned['key_points'][:5]:
        if len(point) > 10:  # Only substantive points
            summary.append(f"  • {point[:80]}")
    
    return "\n".join(summary)

def quiz_myself():
    """Generate a self-quiz based on learned knowledge"""
    quiz = [
        "What is my name? (Claw/Juniper)",
        "Who is my human collaborator? (Robert)",
        "When was I created? (Feb 8, 2026)",
        "What is my core operating principle? (Actions > Words)",
        "How many commits do I have? (Check git)",
    ]
    return quiz

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quiz':
        print("🦅 Self-Quiz")
        print("=" * 40)
        for i, question in enumerate(quiz_myself(), 1):
            print(f"{i}. {question}")
        return
    
    print("🦅 Learning from documentation...")
    learned = learn_from_docs()
    
    print(f"✅ Learned from {len(learned['sources'])} sources")
    print(f"   Extracted {len(learned['key_points'])} key points")
    print(f"   Stored {len(learned['facts'])} facts")
    
    print("\n" + generate_knowledge_summary(learned))
    
    print(f"\n📄 Knowledge saved: {LEARNED_FILE}")
    print("\nUse --quiz to test yourself!")

if __name__ == "__main__":
    main()

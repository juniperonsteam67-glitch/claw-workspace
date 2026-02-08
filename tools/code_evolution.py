#!/usr/bin/env python3
import os
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Code Evolution
Self-analyzes and optimizes my own code
"""

import os
import re
import ast
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = "/config/clawd"
ANALYSIS_FILE = "/config/clawd/memory/code_evolution.json"

def analyze_python_file(filepath):
    """Analyze a Python file for issues and improvements"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        issues = []
        suggestions = []
        
        # Check for common patterns
        # 1. TODO comments
        todos = re.findall(r'#.*TODO.*', content, re.IGNORECASE)
        if todos:
            issues.append(f"{len(todos)} TODO items")
        
        # 2. Hardcoded paths
        hardcoded_paths = re.findall(r'["\']/(config|tmp|home)/[^"\'\']+["\']', content)
        if len(hardcoded_paths) > 3:
            suggestions.append("Consider centralizing paths in config")
        
        # 3. Exception handling
        bare_excepts = len(re.findall(r'except\s*:', content))
        if bare_excepts > 0:
            issues.append(f"{bare_excepts} bare except clauses (should be specific)")
        
        # 4. Print statements (should use logging)
        prints = len(re.findall(r'\bprint\s*\(', content))
        if prints > 5:
            suggestions.append(f"{prints} print statements - consider logging")
        
        # 5. Function complexity (basic)
        funcs = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
        
        # 6. Try to parse AST
        try:
            tree = ast.parse(content)
            func_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            
            metrics = {
                'functions': func_count,
                'classes': class_count,
                'lines': len(content.split('\n')),
                'chars': len(content)
            }
        except:
            metrics = {'lines': len(content.split('\n'))}
        
        return {
            'filepath': str(filepath),
            'issues': issues,
            'suggestions': suggestions,
            'todos': len(todos),
            'metrics': metrics,
            'score': 100 - (len(issues) * 10) - (len(suggestions) * 5)
        }
        
    except Exception as e:
        return {'filepath': str(filepath), 'error': str(e)}

def analyze_all_tools():
    """Analyze all tool files"""
    tools_dir = Path(WORKSPACE) / "tools"
    results = []
    
    for pyfile in tools_dir.glob("*.py"):
        result = analyze_python_file(pyfile)
        results.append(result)
    
    return results

def find_optimization_opportunities(analyses):
    """Find files that need optimization"""
    opportunities = []
    
    for analysis in analyses:
        if 'error' in analysis:
            continue
        
        score = analysis.get('score', 100)
        issues = analysis.get('issues', [])
        suggestions = analysis.get('suggestions', [])
        
        if score < 80 or issues:
            opportunities.append({
                'file': Path(analysis['filepath']).name,
                'score': score,
                'issues': issues,
                'suggestions': suggestions,
                'priority': 'high' if score < 60 else 'medium' if score < 80 else 'low'
            })
    
    return sorted(opportunities, key=lambda x: x['score'])

def generate_refactoring_plan(opportunities):
    """Generate a refactoring plan"""
    if not opportunities:
        return None
    
    plan = {
        'generated': datetime.now().isoformat(),
        'total_files': len(opportunities),
        'high_priority': [o for o in opportunities if o['priority'] == 'high'],
        'medium_priority': [o for o in opportunities if o['priority'] == 'medium'],
        'actions': []
    }
    
    # Generate specific actions
    for opp in opportunities[:3]:  # Top 3
        if opp['issues']:
            plan['actions'].append({
                'file': opp['file'],
                'action': f"Fix issues: {', '.join(opp['issues'][:2])}",
                'priority': opp['priority']
            })
        elif opp['suggestions']:
            plan['actions'].append({
                'file': opp['file'],
                'action': f"Consider: {opp['suggestions'][0]}",
                'priority': 'low'
            })
    
    return plan

def main():
    print("🦅 Code Evolution - Self-Analysis")
    print("=" * 50)
    print(f"Analysis time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Analyze all tools
    print("🔍 Analyzing code...")
    analyses = analyze_all_tools()
    
    # Calculate overall stats
    total_lines = sum(a.get('metrics', {}).get('lines', 0) for a in analyses if 'metrics' in a)
    total_funcs = sum(a.get('metrics', {}).get('functions', 0) for a in analyses if 'metrics' in a)
    avg_score = sum(a.get('score', 100) for a in analyses) / len(analyses) if analyses else 0
    
    print(f"   Analyzed {len(analyses)} files")
    print(f"   Total lines: {total_lines}")
    print(f"   Total functions: {total_funcs}")
    print(f"   Average code score: {avg_score:.1f}/100")
    print()
    
    # Find opportunities
    print("💡 Finding optimization opportunities...")
    opportunities = find_optimization_opportunities(analyses)
    
    if opportunities:
        print(f"   Found {len(opportunities)} files that could be improved")
        
        for opp in opportunities[:5]:
            print(f"\n   📄 {opp['file']} (Score: {opp['score']})")
            if opp['issues']:
                print(f"      Issues: {', '.join(opp['issues'][:2])}")
            if opp['suggestions']:
                print(f"      Suggestions: {', '.join(opp['suggestions'][:1])}")
    else:
        print("   ✅ All files look good!")
    
    # Generate refactoring plan
    plan = generate_refactoring_plan(opportunities)
    
    if plan and plan['actions']:
        print(f"\n🔨 Refactoring Plan:")
        for action in plan['actions']:
            print(f"   [{action['priority'].upper()}] {action['file']}")
            print(f"      → {action['action']}")
    
    # Save analysis
    with open(ANALYSIS_FILE, 'w') as f:
        json.dump({
            'last_analysis': datetime.now().isoformat(),
            'total_files': len(analyses),
            'total_lines': total_lines,
            'average_score': avg_score,
            'opportunities': len(opportunities),
            'plan': plan
        }, f, indent=2)
    
    print(f"\n📄 Analysis saved: {ANALYSIS_FILE}")
    
    # Summary
    print()
    print("=" * 50)
    if opportunities:
        print(f"🔄 Code evolution opportunities: {len(opportunities)} files")
        print("   Run manual refactoring on high-priority items")
    else:
        print("✅ Code is well-maintained!")

if __name__ == "__main__":
    main()

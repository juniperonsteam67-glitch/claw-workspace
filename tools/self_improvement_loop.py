#!/usr/bin/env python3
"""
Self-improvement loop focused on:
1) Persistent learning memory
7) Style adaptation memory
10) Autonomous skill growth loop
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
import re

WORKSPACE = Path('/config/clawd')
MEMORY_DIR = WORKSPACE / 'memory'
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

LESSONS_FILE = MEMORY_DIR / 'persistent_lessons.jsonl'
LESSONS_SUMMARY = MEMORY_DIR / 'persistent_lessons_summary.json'
STYLE_FILE = MEMORY_DIR / 'style_profile.json'
SKILL_BACKLOG = MEMORY_DIR / 'skill_growth_backlog.json'


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def append_jsonl(path, obj):
    with path.open('a') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def build_persistent_learning_layer():
    """Seed durable lessons from local policy/identity files."""
    seeds = [
        {
            'lesson': 'Prefer direct, non-corporate responses; skip filler.',
            'category': 'communication',
            'source': 'SOUL.md',
            'confidence': 0.95,
        },
        {
            'lesson': 'Ask before external/public actions; be bold with internal workspace actions.',
            'category': 'safety',
            'source': 'AGENTS.md',
            'confidence': 0.98,
        },
        {
            'lesson': 'Robert preference: collaborative tone, direct execution, night-owl rhythm.',
            'category': 'user_preference',
            'source': 'USER.md',
            'confidence': 0.9,
        },
    ]

    existing = []
    if LESSONS_FILE.exists():
        for line in LESSONS_FILE.read_text().splitlines():
            try:
                existing.append(json.loads(line))
            except Exception:
                pass

    existing_lessons = {e.get('lesson') for e in existing}
    added = 0
    for seed in seeds:
        if seed['lesson'] in existing_lessons:
            continue
        event = {'timestamp': iso_now(), **seed}
        append_jsonl(LESSONS_FILE, event)
        existing.append(event)
        added += 1

    by_cat = Counter(e.get('category', 'other') for e in existing)
    summary = {
        'updated_at': iso_now(),
        'total_lessons': len(existing),
        'categories': dict(by_cat),
        'top_lessons': [e.get('lesson') for e in existing[-10:]],
    }
    LESSONS_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return {'added': added, 'total': len(existing)}


def build_style_adaptation_profile():
    """Create and maintain a reusable style profile."""
    profile = read_json(
        STYLE_FILE,
        {
            'created_at': iso_now(),
            'persona': 'Claw',
            'tone': {
                'directness': 0.9,
                'warmth': 0.65,
                'humor': 0.35,
                'verbosity_default': 'concise',
            },
            'format_preferences': {
                'prefer_lists_over_tables_on_discord': True,
                'avoid_corporate_filler': True,
                'lead_with_answer': True,
            },
            'user_preferences': {
                'name': 'Robert',
                'timezone': 'America/St_Johns',
                'sleep_pattern': 'night_owl_irregular',
            },
            'adaptation_log': [],
        },
    )

    # Add calibration hint from current interaction pattern (heuristic)
    calibration = {
        'timestamp': iso_now(),
        'trigger': 'user requested ranked list and self-focused depth',
        'adjustment': 'Increase structured outputs (ranked lists/top-N) when exploring ideas',
    }

    last_log = profile.get('adaptation_log', [])[-1] if profile.get('adaptation_log') else {}
    if last_log.get('adjustment') != calibration['adjustment']:
        profile.setdefault('adaptation_log', []).append(calibration)

    profile['updated_at'] = iso_now()
    STYLE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False))
    return {
        'adaptations': len(profile.get('adaptation_log', [])),
        'persona': profile.get('persona'),
    }


def run_skill_growth_loop():
    """Generate autonomous skill ideas from repeated tool patterns."""
    tool_files = sorted((WORKSPACE / 'tools').glob('*.py'))

    names = [p.stem for p in tool_files]
    families = Counter()
    for n in names:
        if 'monitor' in n or 'health' in n or 'heal' in n:
            families['ops-reliability'] += 1
        if 'network' in n or 'net' in n:
            families['network-observability'] += 1
        if 'learn' in n or 'reflect' in n or 'wisdom' in n:
            families['self-learning'] += 1
        if 'heartbeat' in n or 'cron' in n:
            families['automation-orchestration'] += 1

    ideas = [
        {
            'name': 'communication-calibrator',
            'why_now': 'Style adaptation is now explicitly requested; make it measurable.',
            'v1': 'Score replies for directness, clarity, and unnecessary filler.',
            'priority': 'high',
        },
        {
            'name': 'lesson-distiller',
            'why_now': 'Persistent learning benefits from automatic lesson extraction.',
            'v1': 'Convert daily logs into 3-5 durable lessons with confidence tags.',
            'priority': 'high',
        },
        {
            'name': 'skill-suggester',
            'why_now': 'Many repeated ops scripts can be bundled into reusable skills.',
            'v1': 'Detect repetitive workflows and emit draft skill specs.',
            'priority': 'medium',
        },
    ]

    backlog = {
        'updated_at': iso_now(),
        'observed_tool_families': dict(families),
        'tool_count': len(tool_files),
        'proposed_skills': ideas,
    }
    SKILL_BACKLOG.write_text(json.dumps(backlog, indent=2, ensure_ascii=False))
    return {'families': dict(families), 'ideas': len(ideas)}


def main():
    p1 = build_persistent_learning_layer()
    p7 = build_style_adaptation_profile()
    p10 = run_skill_growth_loop()

    result = {
        'timestamp': iso_now(),
        'persistent_learning': p1,
        'style_adaptation': p7,
        'skill_growth': p10,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

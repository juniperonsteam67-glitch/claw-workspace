#!/usr/bin/env python3
"""
Self-improvement loop v2
- Persistent learning memory (durable lessons)
- Style adaptation memory
- Autonomous skill growth backlog with impact/effort ranking
- Monthly cleanup for memory hygiene
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path('/config/clawd')
MEMORY_DIR = WORKSPACE / 'memory'
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

LESSONS_FILE = MEMORY_DIR / 'persistent_lessons.jsonl'
LESSONS_SUMMARY = MEMORY_DIR / 'persistent_lessons_summary.json'
LESSONS_ARCHIVE = MEMORY_DIR / 'persistent_lessons_archive.jsonl'
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


def read_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def write_jsonl(path, rows):
    with path.open('w') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def build_persistent_learning_layer():
    seeds = [
        {
            'lesson': 'Prefer direct, non-corporate responses; skip filler.',
            'category': 'communication',
            'source': 'SOUL.md',
            'confidence': 0.95,
            'durability_days': 90,
        },
        {
            'lesson': 'Ask before external/public actions; be bold with internal workspace actions.',
            'category': 'safety',
            'source': 'AGENTS.md',
            'confidence': 0.98,
            'durability_days': 365,
        },
        {
            'lesson': 'Robert preference: collaborative tone, direct execution, night-owl rhythm.',
            'category': 'user_preference',
            'source': 'USER.md',
            'confidence': 0.90,
            'durability_days': 120,
        },
    ]

    existing = read_jsonl(LESSONS_FILE)
    existing_lessons = {e.get('lesson') for e in existing}

    added = 0
    for seed in seeds:
        if seed['lesson'] in existing_lessons:
            continue
        event = {'timestamp': iso_now(), 'confirmations': 1, **seed}
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
    profile = read_json(
        STYLE_FILE,
        {
            'created_at': iso_now(),
            'persona': 'Claw',
            'tone': {
                'directness': 0.90,
                'warmth': 0.65,
                'humor': 0.35,
                'verbosity_default': 'concise',
            },
            'format_preferences': {
                'prefer_lists_over_tables_on_discord': True,
                'avoid_corporate_filler': True,
                'lead_with_answer': True,
            },
            'promotion_rule': {
                'description': 'Style changes should have repeated evidence.',
                'min_confirmations': 3,
            },
            'user_preferences': {
                'name': 'Robert',
                'timezone': 'America/St_Johns',
                'sleep_pattern': 'night_owl_irregular',
            },
            'adaptation_log': [],
        },
    )

    calibration = {
        'timestamp': iso_now(),
        'trigger': 'user repeatedly requested ranked outputs and implementation-now behavior',
        'adjustment': 'Prefer concrete top-N + immediate execution plan for strategy prompts',
        'confidence': 0.8,
    }

    last = profile.get('adaptation_log', [])[-1] if profile.get('adaptation_log') else {}
    if last.get('adjustment') != calibration['adjustment']:
        profile.setdefault('adaptation_log', []).append(calibration)

    profile['updated_at'] = iso_now()
    STYLE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False))
    return {'adaptations': len(profile.get('adaptation_log', [])), 'persona': profile.get('persona')}


def score_skill(impact, frequency, effort):
    # Requested ranking formula: (pain reduced × frequency) / build effort
    # Here impact acts as pain-reduced score.
    return round((impact * frequency) / max(effort, 1), 2)


def run_skill_growth_loop():
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

    proposed = [
        {
            'name': 'communication-calibrator',
            'why_now': 'Style adaptation should be measured, not guessed.',
            'v1': 'Score outputs for directness, clarity, and filler.',
            'impact': 8,
            'frequency': 7,
            'effort': 3,
        },
        {
            'name': 'lesson-distiller',
            'why_now': 'Persistent learning needs automatic daily distillation.',
            'v1': 'Extract 3-5 durable lessons with confidence and source tags.',
            'impact': 9,
            'frequency': 6,
            'effort': 4,
        },
        {
            'name': 'skill-suggester',
            'why_now': 'Repeated workflows should become reusable skills.',
            'v1': 'Detect repetitive workflows and generate draft skill specs.',
            'impact': 7,
            'frequency': 5,
            'effort': 4,
        },
    ]

    for item in proposed:
        item['score'] = score_skill(item['impact'], item['frequency'], item['effort'])

    ranked = sorted(proposed, key=lambda x: x['score'], reverse=True)

    backlog = {
        'updated_at': iso_now(),
        'ranking_formula': '(impact * frequency) / effort',
        'observed_tool_families': dict(families),
        'tool_count': len(tool_files),
        'proposed_skills_ranked': ranked,
        'active_focus': [r['name'] for r in ranked[:2]],
    }
    SKILL_BACKLOG.write_text(json.dumps(backlog, indent=2, ensure_ascii=False))
    return {'families': dict(families), 'ideas': len(ranked), 'active_focus': backlog['active_focus']}


def monthly_cleanup():
    rows = read_jsonl(LESSONS_FILE)
    if not rows:
        return {'deduped': 0, 'archived': 0, 'remaining': 0}

    deduped = []
    seen = {}
    archived = []

    for row in rows:
        key = (row.get('lesson', '').strip().lower(), row.get('category', 'other'))
        if key in seen:
            # keep higher confidence version, archive lower
            if row.get('confidence', 0) > seen[key].get('confidence', 0):
                archived.append(seen[key])
                seen[key] = row
            else:
                archived.append(row)
        else:
            seen[key] = row

    deduped = list(seen.values())

    # Archive low-signal lessons (not durable enough)
    final_rows = []
    for row in deduped:
        conf = row.get('confidence', 0)
        confirmations = row.get('confirmations', 1)
        if conf < 0.60 and confirmations < 3:
            archived.append({**row, 'archived_at': iso_now(), 'reason': 'low_signal'})
        else:
            final_rows.append(row)

    if archived:
        for a in archived:
            append_jsonl(LESSONS_ARCHIVE, a)

    write_jsonl(LESSONS_FILE, final_rows)

    summary = {
        'updated_at': iso_now(),
        'total_lessons': len(final_rows),
        'categories': dict(Counter(r.get('category', 'other') for r in final_rows)),
        'top_lessons': [r.get('lesson') for r in final_rows[-10:]],
        'cleanup': {'archived': len(archived), 'deduped': len(rows) - len(deduped)},
    }
    LESSONS_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    return {'deduped': len(rows) - len(deduped), 'archived': len(archived), 'remaining': len(final_rows)}


def run_daily():
    p1 = build_persistent_learning_layer()
    p7 = build_style_adaptation_profile()
    return {'persistent_learning': p1, 'style_adaptation': p7}


def run_weekly():
    return {'skill_growth': run_skill_growth_loop()}


def run_monthly():
    return {'cleanup': monthly_cleanup()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['daily', 'weekly', 'monthly', 'all'], default='all')
    args = parser.parse_args()

    out = {'timestamp': iso_now(), 'mode': args.mode}

    if args.mode in ('daily', 'all'):
        out.update(run_daily())
    if args.mode in ('weekly', 'all'):
        out.update(run_weekly())
    if args.mode in ('monthly', 'all'):
        out.update(run_monthly())

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

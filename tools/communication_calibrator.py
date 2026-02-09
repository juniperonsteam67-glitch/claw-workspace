#!/usr/bin/env python3
"""
Communication Calibrator
Scores text for directness, clarity, and filler density.
Usage:
  python3 communication_calibrator.py --text "your draft"
  echo "your draft" | python3 communication_calibrator.py
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path('/config/clawd')
MEMORY_DIR = WORKSPACE / 'memory'
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = MEMORY_DIR / 'communication_calibration.jsonl'

FILLER_PHRASES = [
    'great question',
    "i'd be happy to",
    'as an ai',
    'i hope this helps',
    'let me know if you have any questions',
    'absolutely',
    'certainly',
]


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def sentence_count(text: str) -> int:
    return max(1, len([s for s in re.split(r'[.!?]+', text) if s.strip()]))


def score_text(text: str):
    lowered = text.lower()
    words = re.findall(r"\b[\w'-]+\b", text)
    wc = max(1, len(words))

    filler_hits = sum(lowered.count(p) for p in FILLER_PHRASES)
    hedges = len(re.findall(r"\b(maybe|perhaps|might|could|sort of|kind of|possibly)\b", lowered))
    passive = len(re.findall(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", lowered))

    bullets = len(re.findall(r'^\s*[-*]\s+', text, flags=re.M))
    avg_sentence_len = wc / sentence_count(text)

    directness = max(0, min(100, int(100 - (filler_hits * 12 + hedges * 5))))
    clarity = max(0, min(100, int(100 - abs(avg_sentence_len - 16) * 2 - passive * 4 + bullets * 2)))
    filler_density = round((filler_hits / wc) * 100, 2)

    overall = int((directness * 0.5) + (clarity * 0.5))

    suggestions = []
    if filler_hits > 0:
        suggestions.append('Cut greeting/filler phrases and lead with the answer.')
    if hedges >= 2:
        suggestions.append('Reduce hedging; use firmer wording where confidence is high.')
    if avg_sentence_len > 24:
        suggestions.append('Split long sentences for readability.')
    if bullets == 0 and '\n' not in text and wc > 80:
        suggestions.append('Use short bullets for multi-point responses.')
    if not suggestions:
        suggestions.append('Looks good: concise and direct.')

    return {
        'timestamp': iso_now(),
        'word_count': wc,
        'metrics': {
            'directness': directness,
            'clarity': clarity,
            'filler_density_pct': filler_density,
            'overall': overall,
        },
        'signals': {
            'filler_hits': filler_hits,
            'hedges': hedges,
            'passive_patterns': passive,
            'avg_sentence_len': round(avg_sentence_len, 2),
            'bullets': bullets,
        },
        'suggestions': suggestions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default='')
    args = parser.parse_args()

    text = args.text.strip()
    if not text:
        text = sys.stdin.read().strip()

    if not text:
        print(json.dumps({'error': 'No text provided'}))
        sys.exit(1)

    result = score_text(text)

    with LOG_PATH.open('a') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

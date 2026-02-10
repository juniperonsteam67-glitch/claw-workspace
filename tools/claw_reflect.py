#!/usr/bin/env python3
"""
claw_reflect.py - Daily Log Reflection System

Periodically reviews daily markdown logs, synthesizes insights, and updates
MEMORY.md with distilled wisdom.

Key: This synthesizes, not summarizes. Extracts the *why* things mattered,
not just *what* happened.

Usage:
    python claw_reflect.py              # Run reflection and update MEMORY.md
    python claw_reflect.py --dry-run    # Preview insights without writing
    python claw_reflect.py --days 7     # Analyze last N days (default: 3)
"""

import os
import re
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

# Configuration
WORKSPACE = "/config/clawd"
MEMORY_DIR = Path(WORKSPACE) / "memory"
MEMORY_FILE = Path(WORKSPACE) / "MEMORY.md"
DEFAULT_LOOKBACK_DAYS = 3

# Patterns for extracting significance from logs
SIGNIFICANCE_PATTERNS = {
    'decision': [
        r'decided to\s+(.+?)(?:\.|\n|$)',
        r'chose to\s+(.+?)(?:\.|\n|$)',
        r'opted for\s+(.+?)(?:\.|\n|$)',
        r'settled on\s+(.+?)(?:\.|\n|$)',
        r'conclusion:\s*(.+?)(?:\.|\n|$)',
        r'resolved to\s+(.+?)(?:\.|\n|$)',
    ],
    'lesson': [
        r'learned that\s+(.+?)(?:\.|\n|$)',
        r'realized that\s+(.+?)(?:\.|\n|$)',
        r'key insight:\s*(.+?)(?:\.|\n|$)',
        r'takeaway:\s*(.+?)(?:\.|\n|$)',
        r'lesson learned:\s*(.+?)(?:\.|\n|$)',
        r'note to self:\s*(.+?)(?:\.|\n|$)',
    ],
    'problem': [
        r'issue:\s*(.+?)(?:\.|\n|$)',
        r'problem:\s*(.+?)(?:\.|\n|$)',
        r'bug:\s*(.+?)(?:\.|\n|$)',
        r'failed to\s+(.+?)(?:\.|\n|$)',
        r'error:\s*(.+?)(?:\.|\n|$)',
        r'fixed\s+(.+?)(?:\.|\n|$)',
        r'⚠️\s*\*\*(.+?)\*\*',
        r'🔴\s*\*\*(.+?)\*\*',
    ],
    'success': [
        r'successfully\s+(.+?)(?:\.|\n|$)',
        r'completed\s+(.+?)(?:\.|\n|$)',
        r'achieved\s+(.+?)(?:\.|\n|$)',
        r'working:\s*(.+?)(?:\.|\n|$)',
        r'deployed\s+(.+?)(?:\.|\n|$)',
        r'✅\s*(.+?)(?:\.|\n|$)',
        r'restored|recovered|restarted',
    ],
    'pattern': [
        r'pattern:\s*(.+?)(?:\.|\n|$)',
        r'recurring:\s*(.+?)(?:\.|\n|$)',
        r'always\s+(.+?)(?:\.|\n|$)',
        r'usually\s+(.+?)(?:\.|\n|$)',
        r'tends? to\s+(.+?)(?:\.|\n|$)',
    ]
}


class Insight:
    """Represents a synthesized insight from logs."""
    
    def __init__(self, category: str, content: str, source_date: str, 
                 significance: int = 1, context: str = ""):
        self.category = category
        self.content = content.strip()
        self.source_date = source_date
        self.significance = significance  # 1-5 scale
        self.context = context
    
    def __str__(self) -> str:
        return f"[{self.category.upper()}] {self.content}"
    
    def to_markdown(self) -> str:
        """Format insight for MEMORY.md."""
        icon = {
            'decision': '⚡',
            'lesson': '💡',
            'problem': '🔧',
            'success': '✅',
            'pattern': '🔄',
        }.get(self.category, '•')
        
        return f"- {icon} **{self.content}** ({self.source_date})"


class ReflectionEngine:
    """Analyzes daily logs and synthesizes wisdom."""
    
    def __init__(self, lookback_days: int = DEFAULT_LOOKBACK_DAYS):
        self.lookback_days = lookback_days
        self.insights: List[Insight] = []
        self.raw_entries: List[Dict] = []
        
    def get_recent_log_files(self) -> List[Path]:
        """Find daily log files from the last N days."""
        log_files = []
        today = datetime.now()
        
        for i in range(self.lookback_days):
            date = today - timedelta(days=i)
            # Try both YYYY-MM-DD.md format
            log_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
            if log_file.exists():
                log_files.append(log_file)
        
        # Also look for any YYYY-MM-DD*.md files and sort by mtime
        all_logs = list(MEMORY_DIR.glob('*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.md'))
        # Filter to recent ones
        cutoff = today - timedelta(days=self.lookback_days)
        recent_logs = [
            f for f in all_logs 
            if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff
        ]
        
        # Combine and deduplicate
        combined = list(set(log_files + recent_logs))
        combined.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        return combined[:self.lookback_days * 2]  # Allow some extra files per day
    
    def parse_log_file(self, filepath: Path) -> Dict:
        """Parse a daily log file and extract structured information."""
        content = filepath.read_text(encoding='utf-8')
        
        # Extract date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filepath.name)
        date_str = date_match.group(1) if date_match else filepath.stem
        
        # Extract sections
        sections = self._extract_sections(content)
        
        # Extract decisions, lessons, problems, etc.
        extracted = self._extract_significance(content)
        
        return {
            'date': date_str,
            'filename': filepath.name,
            'content': content,
            'sections': sections,
            'extracted': extracted,
        }
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract markdown sections from content."""
        sections = []
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Match headers
            header_match = re.match(r'^(#{1,4})\s+(.+)$', line)
            if header_match:
                if current_section:
                    sections.append({
                        'level': len(current_section[0]),
                        'title': current_section[1],
                        'content': '\n'.join(current_content).strip()
                    })
                current_section = header_match.groups()
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append({
                'level': len(current_section[0]),
                'title': current_section[1],
                'content': '\n'.join(current_content).strip()
            })
        
        return sections
    
    def _extract_significance(self, content: str) -> Dict[str, List[str]]:
        """Extract significant events/patterns from content."""
        extracted = defaultdict(list)
        
        for category, patterns in SIGNIFICANCE_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                extracted[category].extend(matches)
        
        return dict(extracted)
    
    def analyze_logs(self) -> None:
        """Analyze all recent logs and synthesize insights."""
        log_files = self.get_recent_log_files()
        
        if not log_files:
            print("No recent log files found.")
            return
        
        print(f"📚 Analyzing {len(log_files)} log file(s)...")
        
        for log_file in log_files:
            log_data = self.parse_log_file(log_file)
            self.raw_entries.append(log_data)
            self._synthesize_insights(log_data)
        
        # Post-process: deduplicate and rank
        self._deduplicate_insights()
        self._rank_insights()
    
    def _synthesize_insights(self, log_data: Dict) -> None:
        """Synthesize insights from parsed log data."""
        date = log_data['date']
        extracted = log_data['extracted']
        content = log_data['content']
        
        # Create insights from extracted patterns
        for category, items in extracted.items():
            for item in items:
                # Clean up the extraction
                clean_item = item.strip()
                
                # Skip trivial or low-quality extractions
                if len(clean_item) < 10:
                    continue
                if len(clean_item) > 200:
                    clean_item = clean_item[:197] + "..."
                
                # Skip table cell fragments and status codes
                skip_patterns = [
                    r'^OK\s*\|',
                    r'^ws://',
                    r'^http://',
                    r'^[0-9]+% used',
                    r'^OK\s*$',
                    r'^\d+G/\d+G',
                    r'^\d+ critical',
                ]
                if any(re.match(p, clean_item, re.IGNORECASE) for p in skip_patterns):
                    continue
                
                # Infer significance based on context
                significance = self._infer_significance(clean_item, content)
                
                insight = Insight(
                    category=category,
                    content=clean_item,
                    source_date=date,
                    significance=significance,
                    context=self._get_context(clean_item, content)
                )
                self.insights.append(insight)
        
        # Synthesize meta-insights from patterns across sections
        self._synthesize_meta_insights(log_data)
    
    def _infer_significance(self, item: str, content: str) -> int:
        """Infer significance level (1-5) based on context."""
        significance = 1
        
        # Higher significance for certain keywords
        high_sig_words = ['critical', 'important', 'breaking', 'architectural', 
                          'fundamental', 'major', 'significant', 'essential']
        if any(word in item.lower() for word in high_sig_words):
            significance += 2
        
        # Check if mentioned multiple times (indicates importance)
        mentions = content.lower().count(item.lower().split()[0] if item else '')
        if mentions > 2:
            significance += 1
        
        # Recovery/fixes are significant
        if any(word in item.lower() for word in ['fixed', 'solved', 'resolved', 'working']):
            significance += 1
        
        return min(significance, 5)
    
    def _get_context(self, item: str, content: str) -> str:
        """Get surrounding context for an item."""
        # Find the paragraph containing this item
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if item.split()[0] in para:
                return para.strip()[:300]
        return ""
    
    def _synthesize_meta_insights(self, log_data: Dict) -> None:
        """Synthesize insights that aren't directly extracted but inferred."""
        content = log_data['content'].lower()
        date = log_data['date']
        sections = log_data.get('sections', [])
        section_titles = [s.get('title', '').lower() for s in sections]
        
        # Detect self-healing / automation success
        is_heal_check = any(kw in content for kw in ['self-heal', 'health check', 'auto-restart', 'auto-heal'])
        has_recovery = any(kw in content for kw in ['recovered', 'restarted', 'restored', '→ restored', 'down initially, restarted'])
        all_healthy = '✅' in log_data['content'] or 'all systems operational' in content or 'all services operational' in content
        
        if is_heal_check:
            if has_recovery and all_healthy:
                self.insights.append(Insight(
                    category='lesson',
                    content='Self-healing infrastructure successfully detected and recovered from failures without human intervention',
                    source_date=date,
                    significance=5
                ))
            elif all_healthy:
                self.insights.append(Insight(
                    category='pattern',
                    content='Proactive health monitoring maintaining system stability through automated checks',
                    source_date=date,
                    significance=3
                ))
        
        # Detect service resilience patterns
        if 'dashboard' in content and ('down' in content or 'restart' in content):
            if 'recovered' in content or 'restored' in content or '200' in content:
                self.insights.append(Insight(
                    category='success',
                    content='Dashboard service resilience demonstrated through automatic restart and recovery',
                    source_date=date,
                    significance=4
                ))
        
        # Detect multi-service operational maturity
        services_mentioned = set()
        service_keywords = ['dashboard', 'gateway', 'discord bot', 'plex', 'home assistant']
        for service in service_keywords:
            if service in content:
                services_mentioned.add(service)
        
        if len(services_mentioned) >= 2:
            self.insights.append(Insight(
                category='pattern',
                content=f'Multi-service ecosystem monitored: {", ".join(sorted(services_mentioned))}',
                source_date=date,
                significance=2
            ))
        
        # Detect iteration/improvement cycles from section count
        meaningful_sections = [s for s in sections if len(s.get('content', '')) > 50]
        if len(meaningful_sections) > 3:
            self.insights.append(Insight(
                category='pattern',
                content=f'High operational activity with {len(meaningful_sections)} distinct work segments',
                source_date=date,
                significance=2
            ))
        
        # Detect automation maturation
        if any('cron' in title for title in section_titles):
            self.insights.append(Insight(
                category='pattern',
                content='Scheduled automation (cron) integrated into operational workflow',
                source_date=date,
                significance=3
            ))
    
    def _deduplicate_insights(self) -> None:
        """Remove near-duplicate insights."""
        seen = set()
        unique = []
        
        for insight in self.insights:
            # Create a normalized key for comparison
            key = f"{insight.category}:{insight.content.lower()[:50]}"
            if key not in seen:
                seen.add(key)
                unique.append(insight)
        
        self.insights = unique
    
    def _rank_insights(self) -> None:
        """Sort insights by significance and recency."""
        self.insights.sort(key=lambda i: (i.significance, i.source_date), reverse=True)
    
    def get_insights_by_category(self) -> Dict[str, List[Insight]]:
        """Group insights by category."""
        grouped = defaultdict(list)
        for insight in self.insights:
            grouped[insight.category].append(insight)
        return dict(grouped)
    
    def generate_wisdom_summary(self) -> str:
        """Generate a synthesized wisdom summary."""
        if not self.insights:
            return "No significant insights found in recent logs."
        
        lines = []
        lines.append("## Synthesized Wisdom")
        lines.append("")
        lines.append(f"*Reflection from last {self.lookback_days} days • Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")
        
        # Group by category
        grouped = self.get_insights_by_category()
        
        category_names = {
            'lesson': '💡 Key Lessons',
            'decision': '⚡ Important Decisions',
            'pattern': '🔄 Patterns & Trends',
            'problem': '🔧 Challenges Faced',
            'success': '✅ Wins & Achievements',
        }
        
        # Order categories by importance
        for cat_key, cat_title in category_names.items():
            if cat_key in grouped and grouped[cat_key]:
                lines.append(f"### {cat_title}")
                lines.append("")
                
                # Take top insights from this category
                for insight in grouped[cat_key][:5]:
                    lines.append(insight.to_markdown())
                
                lines.append("")
        
        # Add synthesis paragraph
        lines.append("### 🧠 Synthesis")
        lines.append("")
        lines.append(self._generate_synthesis_paragraph())
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_synthesis_paragraph(self) -> str:
        """Generate a paragraph synthesizing the main themes."""
        themes = []
        
        grouped = self.get_insights_by_category()
        
        # Count by category to understand focus areas
        if len(grouped.get('lesson', [])) > 2:
            themes.append("continuous learning")
        if len(grouped.get('problem', [])) > 2:
            themes.append("active problem-solving")
        if len(grouped.get('success', [])) > 2:
            themes.append("steady progress")
        if len(grouped.get('pattern', [])) > 1:
            themes.append("system maturation")
        if any('auto' in i.content.lower() or 'self' in i.content.lower() 
               for i in self.insights):
            themes.append("automation maturity")
        
        if not themes:
            themes.append("steady operation")
        
        return (
            f"Recent activity shows a focus on {', '.join(themes)}. "
            f"The system is demonstrating {'resilience through self-correction' if 'automation maturity' in themes else 'consistent operation'}. "
            f"Key growth areas include: {', '.join(list(grouped.keys())[:3]) or 'general maintenance'}."
        )


class MemoryManager:
    """Manages the MEMORY.md file."""
    
    def __init__(self, memory_file: Path = MEMORY_FILE):
        self.memory_file = memory_file
        
    def read_existing(self) -> str:
        """Read existing MEMORY.md content."""
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding='utf-8')
        return self._create_template()
    
    def _create_template(self) -> str:
        """Create template for new MEMORY.md."""
        return """# MEMORY.md

*Long-term distilled wisdom from daily operations.*

---

"""
    
    def update(self, new_content: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Update MEMORY.md with new insights."""
        existing = self.read_existing()
        
        # Check if this content is already present (avoid duplication)
        # Use a hash of the core content to check
        content_hash = self._hash_content(new_content)
        if content_hash in existing:
            return False, "Content already present in MEMORY.md"
        
        # Insert new content after the header
        lines = existing.split('\n')
        insert_idx = 0
        
        # Find where to insert (after title and divider)
        for i, line in enumerate(lines):
            if line.startswith('---'):
                insert_idx = i + 1
                break
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_section = f"\n{new_content}\n<!-- reflection: {timestamp} -->\n"
        
        lines.insert(insert_idx, new_section)
        updated = '\n'.join(lines)
        
        if dry_run:
            return True, updated
        
        # Write updated content
        self.memory_file.write_text(updated, encoding='utf-8')
        return True, f"Updated {self.memory_file}"
    
    def _hash_content(self, content: str) -> str:
        """Create a simple hash of content for deduplication."""
        import hashlib
        # Normalize: lowercase, strip whitespace, take first 100 chars
        normalized = content.lower().strip()[:100]
        return hashlib.md5(normalized.encode()).hexdigest()[:16]


def main():
    parser = argparse.ArgumentParser(
        description='Reflect on daily logs and synthesize wisdom for MEMORY.md'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview insights without updating MEMORY.md'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help=f'Number of days to look back (default: {DEFAULT_LOOKBACK_DAYS})'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file (default: update MEMORY.md)'
    )
    
    args = parser.parse_args()
    
    print("🦅 Claw Reflection System")
    print("=" * 50)
    print(f"📅 Analyzing last {args.days} days of logs...")
    print()
    
    # Analyze logs
    engine = ReflectionEngine(lookback_days=args.days)
    engine.analyze_logs()
    
    # Generate wisdom
    wisdom = engine.generate_wisdom_summary()
    
    # Output results
    if args.dry_run:
        print("🔍 DRY RUN - Would add to MEMORY.md:")
        print("-" * 50)
        print(wisdom)
        print("-" * 50)
        print(f"\n📊 Found {len(engine.insights)} insights from {len(engine.raw_entries)} log files")
        
        # Show breakdown
        grouped = engine.get_insights_by_category()
        if grouped:
            print("\n📈 Insight breakdown:")
            for cat, items in grouped.items():
                print(f"   • {cat}: {len(items)}")
        
        return 0
    
    # Update MEMORY.md
    manager = MemoryManager()
    
    if args.output:
        # Write to alternate file
        output_path = Path(args.output)
        output_path.write_text(wisdom, encoding='utf-8')
        print(f"✅ Written to {output_path}")
    else:
        success, message = manager.update(wisdom, dry_run=False)
        if success:
            print(f"✅ {message}")
            print(f"📊 Added {len(engine.insights)} insights from {len(engine.raw_entries)} log files")
        else:
            print(f"⚠️  {message}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

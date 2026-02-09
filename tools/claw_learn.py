#!/usr/bin/env python3
"""
claw_learn.py - Documentation learning tool for OpenClaw

Reads documentation from various sources (man pages, URLs, local files)
and extracts structured knowledge for later retrieval.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import urllib.request
import urllib.error

# Configuration
MEMORY_DIR = Path("/config/clawd/memory/learned_docs")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


class DocLearner:
    """Main class for learning and storing documentation."""
    
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_content(self, source: str) -> tuple[str, str]:
        """
        Fetch content from various sources.
        Returns (content, source_type).
        """
        # Check if it's a URL
        if source.startswith(('http://', 'https://')):
            return self._fetch_url(source), "url"
        
        # Check if it's a man page request
        if source.startswith('man:'):
            return self._fetch_manpage(source[4:]), "manpage"
        
        # Treat as local file
        return self._fetch_file(source), "file"
    
    def _fetch_url(self, url: str) -> str:
        """Fetch content from a URL."""
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")
    
    def _fetch_manpage(self, command: str) -> str:
        """Fetch man page content."""
        try:
            result = subprocess.run(
                ['man', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                # Try with man -P cat for plain text
                result = subprocess.run(
                    ['man', '-P', 'cat', command],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            if result.returncode != 0:
                raise RuntimeError(f"Man page for '{command}' not found")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout fetching man page for '{command}'")
        except FileNotFoundError:
            raise RuntimeError("'man' command not found on this system")
    
    def _fetch_file(self, filepath: str) -> str:
        """Fetch content from a local file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        return path.read_text(encoding='utf-8', errors='ignore')
    
    def parse_manpage(self, content: str) -> dict[str, Any]:
        """Parse man page content and extract structured info."""
        data = {
            "type": "manpage",
            "name": "",
            "description": "",
            "synopsis": "",
            "options": [],
            "examples": [],
            "sections": {}
        }
        
        lines = content.split('\n')
        current_section = None
        section_buffer = []
        
        for line in lines:
            # Detect section headers (all caps or specific patterns)
            section_match = re.match(r'^([A-Z][A-Z\s]+[A-Z])\s*$', line)
            if section_match:
                # Save previous section
                if current_section and section_buffer:
                    section_text = '\n'.join(section_buffer).strip()
                    data["sections"][current_section] = section_text
                    
                    # Extract specific sections
                    if current_section == "NAME":
                        data["name"] = self._extract_name(section_text)
                    elif current_section == "DESCRIPTION":
                        data["description"] = section_text
                    elif current_section == "SYNOPSIS":
                        data["synopsis"] = section_text
                    elif current_section == "OPTIONS":
                        data["options"] = self._extract_options(section_text)
                    elif current_section in ["EXAMPLES", "EXAMPLE"]:
                        data["examples"] = self._extract_examples(section_text)
                
                current_section = section_match.group(1).strip()
                section_buffer = []
            else:
                if current_section:
                    section_buffer.append(line)
        
        # Don't forget the last section
        if current_section and section_buffer:
            section_text = '\n'.join(section_buffer).strip()
            data["sections"][current_section] = section_text
            
            if current_section == "NAME":
                data["name"] = self._extract_name(section_text)
            elif current_section == "DESCRIPTION":
                data["description"] = section_text
            elif current_section == "SYNOPSIS":
                data["synopsis"] = section_text
            elif current_section == "OPTIONS":
                data["options"] = self._extract_options(section_text)
            elif current_section in ["EXAMPLES", "EXAMPLE"]:
                data["examples"] = self._extract_examples(section_text)
        
        return data
    
    def _extract_name(self, text: str) -> str:
        """Extract command name from NAME section."""
        # Usually format: command - description
        match = re.match(r'^([\w\-]+)\s*-\s*(.+)', text.strip())
        if match:
            return match.group(1)
        return text.strip().split()[0] if text.strip() else ""
    
    def _extract_options(self, text: str) -> list[dict]:
        """Extract options from OPTIONS section."""
        options = []
        lines = text.split('\n')
        current_option = None
        
        for line in lines:
            # Look for option patterns: -x, --option, -x, --long
            opt_match = re.match(r'^\s+(-[\w\?]|--[\w\-]+)(?:\s+([\w\[\]_-]+))?\s*(.*)', line)
            if opt_match:
                if current_option:
                    options.append(current_option)
                current_option = {
                    "flag": opt_match.group(1),
                    "argument": opt_match.group(2) or "",
                    "description": opt_match.group(3) or ""
                }
            elif current_option and line.strip() and not line.strip().startswith('-'):
                # Continuation of description
                current_option["description"] += " " + line.strip()
        
        if current_option:
            options.append(current_option)
        
        return options
    
    def _extract_examples(self, text: str) -> list[str]:
        """Extract examples from EXAMPLES section."""
        examples = []
        lines = text.split('\n')
        current_example = []
        
        for line in lines:
            # Examples often start with $ or are indented code blocks
            if line.strip().startswith('$') or (line.startswith('       ') and not line.strip().startswith('-')):
                if current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                current_example.append(line.strip().lstrip('$ '))
            elif current_example and line.strip():
                current_example.append(line.strip())
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples
    
    def parse_markdown(self, content: str, source: str) -> dict[str, Any]:
        """Parse markdown (README) content and extract structured info."""
        data = {
            "type": "markdown",
            "source": source,
            "title": "",
            "description": "",
            "sections": {},
            "commands": [],
            "code_blocks": []
        }
        
        lines = content.split('\n')
        current_section = None
        section_buffer = []
        in_code_block = False
        code_buffer = []
        code_lang = ""
        
        for i, line in enumerate(lines):
            # Title (first # line)
            if line.startswith('# ') and not data["title"]:
                data["title"] = line[2:].strip()
            
            # Section headers
            section_match = re.match(r'^#{2,4}\s+(.+)$', line)
            if section_match:
                # Save previous section
                if current_section and section_buffer:
                    data["sections"][current_section] = '\n'.join(section_buffer).strip()
                
                current_section = section_match.group(1).strip()
                section_buffer = []
                continue
            
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    code_content = '\n'.join(code_buffer)
                    data["code_blocks"].append({
                        "language": code_lang,
                        "content": code_content
                    })
                    
                    # Check if it looks like commands/examples
                    if code_lang in ['bash', 'sh', 'shell', '']:
                        data["commands"].extend(self._extract_commands_from_code(code_content))
                    
                    in_code_block = False
                    code_buffer = []
                    code_lang = ""
                else:
                    # Start of code block
                    in_code_block = True
                    code_lang = line[3:].strip()
                continue
            
            if in_code_block:
                code_buffer.append(line)
            elif current_section is not None:
                section_buffer.append(line)
        
        # Save last section
        if current_section and section_buffer:
            data["sections"][current_section] = '\n'.join(section_buffer).strip()
        
        # Extract description from first paragraph or section
        if "Description" in data["sections"]:
            data["description"] = data["sections"]["Description"]
        elif "Introduction" in data["sections"]:
            data["description"] = data["sections"]["Introduction"]
        elif data["sections"]:
            first_section = list(data["sections"].values())[0]
            data["description"] = first_section[:500]  # First 500 chars
        
        return data
    
    def _extract_commands_from_code(self, code: str) -> list[dict]:
        """Extract commands from code blocks."""
        commands = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for command patterns
            if line and not line.startswith('#'):
                # Skip obvious non-commands
                if any(line.startswith(prefix) for prefix in ['$ ', './', 'python', 'npm', 'pip', 'git', 'docker', 'make', 'cargo', 'go ', 'curl', 'wget']):
                    commands.append({
                        "command": line.lstrip('$ ').strip(),
                        "context": "example"
                    })
        
        return commands
    
    def learn(self, source: str, name: str = None) -> dict[str, Any]:
        """
        Learn from a documentation source.
        Returns the extracted structured data.
        """
        content, source_type = self.fetch_content(source)
        
        # Parse based on source type
        if source_type == "manpage":
            data = self.parse_manpage(content)
            data["raw_source"] = source
        elif source.endswith('.md') or source.endswith('.markdown'):
            data = self.parse_markdown(content, source)
        else:
            # Try to auto-detect
            if 'NAME' in content[:1000] and 'SYNOPSIS' in content[:2000]:
                data = self.parse_manpage(content)
            else:
                data = self.parse_markdown(content, source)
        
        # Add metadata
        data["learned_from"] = source
        data["source_type"] = source_type
        
        # Determine storage name
        if not name:
            if source_type == "manpage":
                name = source[4:]  # Remove 'man:' prefix
            elif source_type == "url":
                name = Path(urlparse(source).path).stem or "doc"
            else:
                name = Path(source).stem
        
        # Sanitize name
        name = re.sub(r'[^\w\-]', '_', name)
        data["name"] = name
        
        return data
    
    def store(self, data: dict[str, Any]) -> Path:
        """Store learned data to memory."""
        name = data.get("name", "unknown")
        filepath = self.memory_dir / f"{name}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def query(self, keyword: str, limit: int = 5) -> list[dict]:
        """Query stored documentation for relevant knowledge."""
        results = []
        keyword_lower = keyword.lower()
        
        for json_file in self.memory_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                score = 0
                matches = []
                
                # Check various fields
                if keyword_lower in data.get("name", "").lower():
                    score += 10
                    matches.append(f"name: {data.get('name', '')}")
                
                if keyword_lower in data.get("description", "").lower():
                    score += 5
                    desc = data.get("description", "")
                    # Find context around keyword
                    idx = desc.lower().find(keyword_lower)
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(desc), idx + len(keyword) + 50)
                        matches.append(f"description: ...{desc[start:end]}...")
                
                # Check sections
                for section_name, section_content in data.get("sections", {}).items():
                    if keyword_lower in section_name.lower():
                        score += 3
                        matches.append(f"section: {section_name}")
                    if keyword_lower in section_content.lower():
                        score += 2
                        idx = section_content.lower().find(keyword_lower)
                        if idx >= 0:
                            start = max(0, idx - 30)
                            end = min(len(section_content), idx + len(keyword) + 30)
                            matches.append(f"in {section_name}: ...{section_content[start:end]}...")
                
                # Check options for manpages
                for opt in data.get("options", []):
                    if keyword_lower in opt.get("flag", "").lower() or keyword_lower in opt.get("description", "").lower():
                        score += 3
                        matches.append(f"option: {opt.get('flag', '')}")
                
                if score > 0:
                    results.append({
                        "name": data.get("name", json_file.stem),
                        "type": data.get("type", "unknown"),
                        "source": data.get("learned_from", "unknown"),
                        "score": score,
                        "matches": matches[:3]  # Limit matches
                    })
            except Exception as e:
                print(f"Warning: Failed to read {json_file}: {e}", file=sys.stderr)
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def list_learned(self) -> list[dict]:
        """List all learned documentation."""
        docs = []
        for json_file in self.memory_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                docs.append({
                    "name": data.get("name", json_file.stem),
                    "type": data.get("type", "unknown"),
                    "source": data.get("learned_from", "unknown"),
                    "title": data.get("title", "") or data.get("name", "")
                })
            except Exception:
                docs.append({
                    "name": json_file.stem,
                    "type": "unknown",
                    "source": str(json_file),
                    "title": ""
                })
        return docs
    
    def show(self, name: str) -> dict | None:
        """Show full details of a learned document."""
        filepath = self.memory_dir / f"{name}.json"
        if not filepath.exists():
            # Try to find by partial match
            for json_file in self.memory_dir.glob("*.json"):
                if name.lower() in json_file.stem.lower():
                    filepath = json_file
                    break
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Learn and store documentation for later retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s learn man:ls                    # Learn from man page
  %(prog)s learn README.md                 # Learn from local README
  %(prog)s learn https://example.com/doc   # Learn from URL
  %(prog)s query "list files"              # Query learned docs
  %(prog)s list                            # List all learned docs
  %(prog)s show ls                         # Show details of learned doc
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Learn command
    learn_parser = subparsers.add_parser('learn', help='Learn from a documentation source')
    learn_parser.add_argument('source', help='Source to learn from (file, URL, or man:command)')
    learn_parser.add_argument('-n', '--name', help='Name to store as (optional)')
    learn_parser.add_argument('--dry-run', action='store_true', help='Parse but don\'t store')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query learned documentation')
    query_parser.add_argument('keyword', help='Keyword to search for')
    query_parser.add_argument('-l', '--limit', type=int, default=5, help='Max results (default: 5)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all learned documentation')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of a learned document')
    show_parser.add_argument('name', help='Name of the learned document')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    learner = DocLearner()
    
    if args.command == 'learn':
        try:
            print(f"Learning from: {args.source}")
            data = learner.learn(args.source, args.name)
            
            if args.dry_run:
                print("\n--- Parsed Data (not stored) ---")
                print(json.dumps(data, indent=2)[:2000])
                print("...")
            else:
                filepath = learner.store(data)
                print(f"✓ Learned and stored: {filepath}")
                print(f"  Name: {data.get('name', 'unknown')}")
                print(f"  Type: {data.get('type', 'unknown')}")
                if data.get('description'):
                    desc = data['description'][:100].replace('\n', ' ')
                    print(f"  Description: {desc}...")
                if data.get('options'):
                    print(f"  Options extracted: {len(data['options'])}")
                if data.get('examples'):
                    print(f"  Examples extracted: {len(data['examples'])}")
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'query':
        results = learner.query(args.keyword, args.limit)
        if results:
            print(f"Found {len(results)} result(s) for '{args.keyword}':\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['name']} ({result['type']})")
                print(f"   Source: {result['source']}")
                print(f"   Relevance: {result['score']}")
                for match in result['matches']:
                    print(f"   • {match}")
                print()
        else:
            print(f"No results found for '{args.keyword}'")
    
    elif args.command == 'list':
        docs = learner.list_learned()
        if docs:
            print(f"Learned documentation ({len(docs)} items):\n")
            print(f"{'Name':<20} {'Type':<12} {'Source':<30}")
            print("-" * 62)
            for doc in docs:
                source = doc['source'][:29] if len(doc['source']) > 29 else doc['source']
                print(f"{doc['name']:<20} {doc['type']:<12} {source:<30}")
        else:
            print("No documentation learned yet.")
            print(f"Use 'claw_learn.py learn <source>' to learn from a source.")
    
    elif args.command == 'show':
        data = learner.show(args.name)
        if data:
            print(json.dumps(data, indent=2))
        else:
            print(f"Document '{args.name}' not found.")
            print(f"Use 'claw_learn.py list' to see available documents.")
            sys.exit(1)


if __name__ == '__main__':
    main()

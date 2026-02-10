#!/usr/bin/env python3
"""
claw_critique.py - Failure Analysis and Retry System

A learning system that analyzes command/tool failures, generates actionable
critiques, stores them for pattern learning, and retries with improved context.

Usage:
    # CLI mode - retry a failed command
    python claw_critique.py --retry "cat /nonexistent/file"
    
    # List stored failures
    python claw_critique.py --list
    
    # Show statistics
    python claw_critique.py --stats
    
    # Clear old failures
    python claw_critique.py --clear
    
    # As a decorator
    @critique_wrapper
    def my_function():
        ...
"""

import os
import sys
import json
import re
import hashlib
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from functools import wraps

# Configuration
FAILURES_DIR = Path("/config/clawd/memory/failures")
MAX_RETRIES = 3
SIMILARITY_THRESHOLD = 0.7


@dataclass
class FailureCritique:
    """Represents a failure and its critique."""
    id: str
    timestamp: str
    command: str
    error_type: str
    error_message: str
    root_cause: str
    suggested_fix: str
    retry_strategy: str
    attempt_count: int
    success_on_retry: Optional[bool] = None
    related_failures: List[str] = None
    
    def __post_init__(self):
        if self.related_failures is None:
            self.related_failures = []


class ErrorPatternAnalyzer:
    """Analyzes error messages to identify patterns."""
    
    PATTERNS = {
        'file_not_found': {
            'patterns': [
                r'No such file or directory',
                r'FileNotFoundError',
                r'cannot open.*No such file',
                r'does not exist',
            ],
            'cause': 'Attempted to access a file or directory that does not exist',
            'fixes': [
                'Create the missing file/directory before accessing it',
                'Check the file path for typos',
                'Use os.makedirs() to create parent directories',
                'Verify the working directory is correct',
            ]
        },
        'permission_denied': {
            'patterns': [
                r'Permission denied',
                r'PermissionDeniedError',
                r'Access is denied',
                r'EACCES',
                r'Operation not permitted',
            ],
            'cause': 'Insufficient permissions to perform the operation',
            'fixes': [
                'Run with elevated permissions (sudo) if appropriate',
                'Check file/directory ownership with ls -la',
                'Modify file permissions with chmod/chown',
                'Ensure the user has access to the resource',
            ]
        },
        'syntax_error': {
            'patterns': [
                r'SyntaxError',
                r'syntax error',
                r'invalid syntax',
                r'expected.*but found',
            ],
            'cause': 'Code contains syntax errors or malformed structure',
            'fixes': [
                'Check for missing colons, brackets, or quotes',
                'Verify indentation is consistent',
                'Review the line number indicated in the error',
                'Use a linter to catch syntax issues early',
            ]
        },
        'command_not_found': {
            'patterns': [
                r'command not found',
                r'not recognized as',
                r'No command.*found',
                r'is not installed',
            ],
            'cause': 'The command or executable is not available in PATH',
            'fixes': [
                'Install the missing package/tool',
                'Add the binary location to PATH',
                'Check if the command name has a typo',
                'Use the full path to the executable',
            ]
        },
        'connection_error': {
            'patterns': [
                r'Connection refused',
                r'Connection timed out',
                r'Network is unreachable',
                r'Could not resolve host',
                r'ConnectionError',
                r'No route to host',
            ],
            'cause': 'Unable to establish network connection',
            'fixes': [
                'Check network connectivity with ping',
                'Verify the host/URL is correct',
                'Check if a firewall is blocking the connection',
                'Ensure the target service is running',
                'Try again later if the service might be down',
            ]
        },
        'timeout': {
            'patterns': [
                r'timed out',
                r'TimeoutError',
                r'deadline exceeded',
                r'operation timed out',
            ],
            'cause': 'Operation exceeded the allowed time limit',
            'fixes': [
                'Increase the timeout duration',
                'Optimize the operation to run faster',
                'Check if the resource is overloaded',
                'Implement retry logic with exponential backoff',
                'Break the operation into smaller chunks',
            ]
        },
        'module_not_found': {
            'patterns': [
                r'ModuleNotFoundError',
                r'No module named',
                r'ImportError.*cannot import',
                r'package.*not found',
            ],
            'cause': 'Required Python module or package is not installed',
            'fixes': [
                'Install with pip: pip install <package>',
                'Check if using the correct Python environment',
                'Verify the package name is spelled correctly',
                'Install requirements: pip install -r requirements.txt',
            ]
        },
        'key_error': {
            'patterns': [
                r'KeyError',
                r'key.*not found',
            ],
            'cause': 'Attempted to access a dictionary key that does not exist',
            'fixes': [
                'Use dict.get() with a default value',
                'Check if key exists with "if key in dict:"',
                'Use try/except to handle missing keys gracefully',
                'Verify the key name is correct',
            ]
        },
        'index_error': {
            'patterns': [
                r'IndexError',
                r'list index out of range',
                r'string index out of range',
            ],
            'cause': 'Attempted to access a list/string index that does not exist',
            'fixes': [
                'Check the length before accessing: if i < len(list)',
                'Use negative indices carefully',
                'Verify the list is not empty before accessing elements',
                'Add bounds checking',
            ]
        },
        'type_error': {
            'patterns': [
                r'TypeError',
                r'unsupported operand type',
                r'takes.*positional arguments? but',
                r'missing.*required positional argument',
            ],
            'cause': 'Operation performed on incompatible data types',
            'fixes': [
                'Check variable types before operations',
                'Convert types explicitly: str(), int(), etc.',
                'Verify function signature matches arguments',
                'Check for None values before operations',
            ]
        },
        'value_error': {
            'patterns': [
                r'ValueError',
                r'invalid literal for',
                r'could not convert',
            ],
            'cause': 'Operation received argument with right type but inappropriate value',
            'fixes': [
                'Validate input values before processing',
                'Check for empty strings or zero values',
                'Ensure values are in expected range/format',
                'Add input sanitization',
            ]
        },
        'memory_error': {
            'patterns': [
                r'MemoryError',
                r'out of memory',
                r'cannot allocate memory',
            ],
            'cause': 'System ran out of available memory',
            'fixes': [
                'Process data in smaller chunks',
                'Use generators instead of lists',
                'Free unused variables with del',
                'Consider using memory-efficient data structures',
                'Increase system memory or swap space',
            ]
        },
        'disk_full': {
            'patterns': [
                r'No space left on device',
                r'Disk quota exceeded',
                r'insufficient disk space',
            ],
            'cause': 'Storage device is full or quota exceeded',
            'fixes': [
                'Clean up temporary files',
                'Remove old logs and cache',
                'Move data to external storage',
                'Expand disk capacity',
                'Check for large files with du -sh /*',
            ]
        },
    }
    
    @classmethod
    def analyze(cls, error_message: str) -> Tuple[str, str, List[str]]:
        """
        Analyze an error message and return (error_type, cause, fixes).
        
        Returns:
            Tuple of (error_type, root_cause, list_of_suggested_fixes)
        """
        error_message_lower = error_message.lower()
        
        for error_type, config in cls.PATTERNS.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return (
                        error_type,
                        config['cause'],
                        config['fixes']
                    )
        
        # Unknown error type
        return (
            'unknown',
            'Unknown error - could not identify specific pattern',
            [
                'Review the full error message for clues',
                'Check documentation for the tool/command',
                'Search for the error message online',
                'Enable verbose/debug mode for more details',
            ]
        )


class FailureStore:
    """Manages storage and retrieval of failure critiques."""
    
    def __init__(self, storage_dir: Path = FAILURES_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_id(self, command: str, error_message: str) -> str:
        """Generate a unique ID for a failure."""
        content = f"{command}:{error_message}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_filepath(self, failure_id: str) -> Path:
        """Get the file path for a failure record."""
        return self.storage_dir / f"{failure_id}.json"
    
    def store(self, critique: FailureCritique) -> str:
        """Store a failure critique and return its ID."""
        filepath = self._get_filepath(critique.id)
        with open(filepath, 'w') as f:
            json.dump(asdict(critique), f, indent=2)
        return critique.id
    
    def load(self, failure_id: str) -> Optional[FailureCritique]:
        """Load a failure critique by ID."""
        filepath = self._get_filepath(failure_id)
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        return FailureCritique(**data)
    
    def load_all(self) -> List[FailureCritique]:
        """Load all stored failure critiques."""
        critiques = []
        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                critiques.append(FailureCritique(**data))
            except (json.JSONDecodeError, TypeError):
                continue
        return sorted(critiques, key=lambda x: x.timestamp, reverse=True)
    
    def find_similar(self, error_type: str, error_message: str, 
                     command: str) -> List[FailureCritique]:
        """Find similar past failures based on error type and message similarity."""
        all_failures = self.load_all()
        similar = []
        
        for failure in all_failures:
            # Same error type is a strong signal
            if failure.error_type == error_type:
                similarity = self._calculate_similarity(
                    error_message, failure.error_message
                )
                if similarity >= SIMILARITY_THRESHOLD:
                    similar.append(failure)
        
        return similar[:5]  # Return top 5 similar failures
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two error messages."""
        # Simple word-based Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored failures."""
        all_failures = self.load_all()
        
        if not all_failures:
            return {
                'total': 0,
                'by_type': {},
                'success_rate': 0.0,
                'most_common': None,
            }
        
        by_type = {}
        resolved = 0
        
        for f in all_failures:
            by_type[f.error_type] = by_type.get(f.error_type, 0) + 1
            if f.success_on_retry:
                resolved += 1
        
        # Get most common error type
        most_common = max(by_type.items(), key=lambda x: x[1])
        
        return {
            'total': len(all_failures),
            'by_type': by_type,
            'success_rate': resolved / len([f for f in all_failures if f.success_on_retry is not None]),
            'most_common': most_common[0] if most_common else None,
            'most_common_count': most_common[1] if most_common else 0,
        }
    
    def clear_old(self, days: int = 30) -> int:
        """Clear failures older than specified days. Returns count cleared."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cleared = 0
        
        for filepath in self.storage_dir.glob("*.json"):
            try:
                mtime = filepath.stat().st_mtime
                if mtime < cutoff:
                    filepath.unlink()
                    cleared += 1
            except OSError:
                continue
        
        return cleared


class CritiqueGenerator:
    """Generates actionable critiques from failures."""
    
    def __init__(self, store: FailureStore):
        self.store = store
        self.analyzer = ErrorPatternAnalyzer()
    
    def generate(self, command: str, error_output: str, 
                 return_code: int = None) -> FailureCritique:
        """Generate a critique from a failed command."""
        # Analyze the error
        error_type, root_cause, fixes = self.analyzer.analyze(error_output)
        
        # Find similar past failures
        similar = self.store.find_similar(error_type, error_output, command)
        
        # Build suggested fix based on pattern and past experiences
        suggested_fix = self._build_suggestion(fixes, similar, command)
        
        # Determine retry strategy
        retry_strategy = self._build_retry_strategy(error_type, similar)
        
        # Generate ID
        failure_id = hashlib.md5(
            f"{command}:{error_output}".encode()
        ).hexdigest()[:12]
        
        # Build related failures list
        related_ids = [f.id for f in similar if f.id != failure_id][:5]
        
        critique = FailureCritique(
            id=failure_id,
            timestamp=datetime.now().isoformat(),
            command=command,
            error_type=error_type,
            error_message=error_output[:500],  # Truncate long messages
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            retry_strategy=retry_strategy,
            attempt_count=0,
            related_failures=related_ids
        )
        
        return critique
    
    def _build_suggestion(self, fixes: List[str], similar: List[FailureCritique], 
                          command: str) -> str:
        """Build a contextual suggestion based on fixes and similar failures."""
        suggestions = []
        
        # Add pattern-based fixes
        suggestions.extend(fixes[:2])  # Top 2 generic fixes
        
        # Add wisdom from similar failures that succeeded
        successful_similar = [
            f for f in similar 
            if f.success_on_retry and f.suggested_fix
        ]
        
        if successful_similar:
            suggestions.append(
                f"Previously succeeded with: {successful_similar[0].suggested_fix[:100]}..."
            )
        
        # Add command-specific context
        if 'python' in command.lower():
            suggestions.append("Consider using a virtual environment")
        if 'pip' in command.lower():
            suggestions.append("Try: pip install --user or use a virtualenv")
        if 'git' in command.lower():
            suggestions.append("Check git status and ensure you're in the right repository")
        
        return " | ".join(suggestions[:3])
    
    def _build_retry_strategy(self, error_type: str, 
                              similar: List[FailureCritique]) -> str:
        """Build a retry strategy based on error type and history."""
        strategies = {
            'file_not_found': 'Create missing directories/files before retrying',
            'permission_denied': 'Request elevated permissions or fix ownership',
            'connection_error': 'Wait 5s then retry with exponential backoff',
            'timeout': 'Increase timeout parameter or optimize operation',
            'module_not_found': 'Install required dependencies first',
            'command_not_found': 'Install missing tool or verify PATH',
        }
        
        base_strategy = strategies.get(
            error_type, 
            'Analyze error details and apply appropriate fix'
        )
        
        # Add context from similar failures
        if similar:
            success_count = sum(1 for f in similar if f.success_on_retry)
            if success_count > 0:
                rate = success_count / len(similar)
                base_strategy += f" | Historical success rate: {rate:.0%}"
        
        return base_strategy


class CritiqueRetry:
    """Handles retry logic with critique context."""
    
    def __init__(self, store: FailureStore = None, generator: CritiqueGenerator = None):
        self.store = store or FailureStore()
        self.generator = generator or CritiqueGenerator(self.store)
        self.max_retries = MAX_RETRIES
    
    def execute(self, command: str, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute a command with critique-based retry logic.
        
        Returns:
            Dict with keys: success, attempts, critique, final_output
        """
        attempt = 0
        last_critique = None
        
        while attempt < self.max_retries:
            attempt += 1
            
            # Execute the command
            result = self._run_command(command, capture_output)
            
            if result['success']:
                # Mark previous critique as successful if we had one
                if last_critique:
                    last_critique.success_on_retry = True
                    last_critique.attempt_count = attempt
                    self.store.store(last_critique)
                
                return {
                    'success': True,
                    'attempts': attempt,
                    'critique': last_critique,
                    'final_output': result['stdout'],
                    'command': command,
                }
            
            # Generate critique for the failure
            critique = self.generator.generate(
                command, 
                result['stderr'] or result['stdout'],
                result['returncode']
            )
            critique.attempt_count = attempt
            last_critique = critique
            
            # Store the failure
            self.store.store(critique)
            
            # Print critique if in CLI mode
            if sys.stdout.isatty():
                self._print_critique(critique, attempt)
            
            # Don't retry on certain error types
            if critique.error_type in ['syntax_error', 'command_not_found']:
                break
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                import time
                wait_time = min(2 ** attempt, 30)  # Max 30 seconds
                print(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        # All retries exhausted
        if last_critique:
            last_critique.success_on_retry = False
            self.store.store(last_critique)
        
        return {
            'success': False,
            'attempts': attempt,
            'critique': last_critique,
            'final_output': result['stderr'] or result['stdout'],
            'command': command,
        }
    
    def _run_command(self, command: str, capture_output: bool) -> Dict[str, Any]:
        """Run a shell command and return results."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 300 seconds',
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
            }
    
    def _print_critique(self, critique: FailureCritique, attempt: int):
        """Print a formatted critique to stdout."""
        print(f"\n{'='*60}")
        print(f"  ATTEMPT {attempt} FAILED - CRITIQUE GENERATED")
        print(f"{'='*60}")
        print(f"  Error Type: {critique.error_type}")
        print(f"  Root Cause: {critique.root_cause}")
        print(f"  Suggested Fix: {critique.suggested_fix}")
        print(f"  Retry Strategy: {critique.retry_strategy}")
        if critique.related_failures:
            print(f"  Similar Past Failures: {len(critique.related_failures)}")
        print(f"{'='*60}\n")


def critique_wrapper(func: Callable = None, max_retries: int = MAX_RETRIES):
    """
    Decorator to wrap functions with critique-based retry logic.
    
    Usage:
        @critique_wrapper
        def my_function():
            ...
        
        @critique_wrapper(max_retries=5)
        def another_function():
            ...
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            store = FailureStore()
            generator = CritiqueGenerator(store)
            
            attempt = 0
            last_error = None
            
            while attempt < max_retries:
                attempt += 1
                try:
                    result = f(*args, **kwargs)
                    return {
                        'success': True,
                        'result': result,
                        'attempts': attempt,
                    }
                except Exception as e:
                    last_error = e
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    
                    # Generate critique
                    critique = generator.generate(
                        f.__name__,
                        error_msg,
                    )
                    critique.attempt_count = attempt
                    store.store(critique)
                    
                    print(f"\n[Attempt {attempt}] {critique.error_type}: {critique.suggested_fix}")
                    
                    # Don't retry on certain errors
                    if critique.error_type in ['syntax_error']:
                        break
                    
                    if attempt < max_retries:
                        import time
                        time.sleep(min(2 ** attempt, 10))
            
            # All retries failed
            return {
                'success': False,
                'error': str(last_error),
                'attempts': attempt,
            }
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Failure Analysis and Retry System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --retry "cat /nonexistent/file"
  %(prog)s --list
  %(prog)s --stats
  %(prog)s --clear --days 7
        """
    )
    
    parser.add_argument('--retry', '-r', metavar='COMMAND',
                       help='Retry a command with critique analysis')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List stored failure critiques')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='Show failure statistics')
    parser.add_argument('--clear', '-c', action='store_true',
                       help='Clear old failures')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='Days to keep when clearing (default: 30)')
    parser.add_argument('--show', metavar='ID',
                       help='Show details of a specific failure')
    
    args = parser.parse_args()
    
    store = FailureStore()
    
    if args.retry:
        print(f"Executing with critique-based retry: {args.retry}")
        retry = CritiqueRetry(store)
        result = retry.execute(args.retry)
        
        print(f"\n{'='*60}")
        if result['success']:
            print("  ✅ SUCCESS")
            print(f"  Command succeeded after {result['attempts']} attempt(s)")
            if result['final_output']:
                print(f"\n  Output:\n{result['final_output'][:500]}")
        else:
            print("  ❌ FAILED")
            print(f"  Command failed after {result['attempts']} attempt(s)")
            print(f"\n  Final error:\n{result['final_output'][:500]}")
        print(f"{'='*60}")
        
        sys.exit(0 if result['success'] else 1)
    
    elif args.list:
        failures = store.load_all()
        
        if not failures:
            print("No stored failures found.")
            return
        
        print(f"\nStored Failures ({len(failures)} total):")
        print(f"{'ID':<12} {'Type':<20} {'Time':<20} {'Status':<10}")
        print("-" * 70)
        
        for f in failures[:20]:  # Show last 20
            status = "✅ Fixed" if f.success_on_retry else "❌ Open"
            if f.success_on_retry is None:
                status = "⏳ Pending"
            
            time_str = f.timestamp[:16].replace('T', ' ')
            error_type = f.error_type[:18]
            
            print(f"{f.id:<12} {error_type:<20} {time_str:<20} {status:<10}")
        
        if len(failures) > 20:
            print(f"\n... and {len(failures) - 20} more")
    
    elif args.show:
        failure = store.load(args.show)
        if not failure:
            print(f"Failure with ID '{args.show}' not found.")
            return
        
        print(f"\n{'='*60}")
        print(f"  Failure Details: {failure.id}")
        print(f"{'='*60}")
        print(f"  Timestamp: {failure.timestamp}")
        print(f"  Command: {failure.command}")
        print(f"  Error Type: {failure.error_type}")
        print(f"  Root Cause: {failure.root_cause}")
        print(f"  Suggested Fix: {failure.suggested_fix}")
        print(f"  Retry Strategy: {failure.retry_strategy}")
        print(f"  Attempts: {failure.attempt_count}")
        print(f"  Success on Retry: {failure.success_on_retry}")
        if failure.related_failures:
            print(f"  Related Failures: {', '.join(failure.related_failures)}")
        print(f"\n  Error Message:")
        print(f"  {failure.error_message[:300]}...")
        print(f"{'='*60}")
    
    elif args.stats:
        stats = store.get_stats()
        
        print(f"\n{'='*60}")
        print("  Failure Statistics")
        print(f"{'='*60}")
        print(f"  Total Failures: {stats['total']}")
        
        if stats['total'] > 0:
            print(f"\n  By Error Type:")
            for error_type, count in sorted(stats['by_type'].items(), 
                                            key=lambda x: -x[1]):
                print(f"    {error_type}: {count}")
            
            if stats['success_rate'] is not None:
                print(f"\n  Retry Success Rate: {stats['success_rate']:.1%}")
            
            if stats['most_common']:
                print(f"\n  Most Common Error: {stats['most_common']} "
                      f"({stats['most_common_count']} occurrences)")
        
        print(f"{'='*60}")
    
    elif args.clear:
        cleared = store.clear_old(args.days)
        print(f"Cleared {cleared} failures older than {args.days} days.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Claw Log Cleanup
Automatically cleans up old logs to prevent disk bloat
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/config/clawd"
LOG_RETENTION_DAYS = 7  # Keep logs for 7 days
MAX_LOG_SIZE_MB = 10  # Rotate if log > 10MB

def parse_timestamp(ts_str):
    """Parse ISO timestamp"""
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        return None

def cleanup_jsonl_log(log_file, retention_days=LOG_RETENTION_DAYS):
    """Clean up a JSONL log file"""
    log_file = Path(log_file)  # Ensure it's a Path object
    if not log_file.exists():
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    kept = 0
    removed = 0
    temp_file = str(log_file) + '.tmp'
    
    try:
        with open(log_file, 'r') as infile, open(temp_file, 'w') as outfile:
            for line in infile:
                try:
                    entry = json.loads(line)
                    ts = entry.get('timestamp')
                    
                    if ts:
                        entry_date = parse_timestamp(ts)
                        if entry_date and entry_date > cutoff_date:
                            outfile.write(line)
                            kept += 1
                        else:
                            removed += 1
                    else:
                        # Keep entries without timestamps (conservative)
                        outfile.write(line)
                        kept += 1
                        
                except json.JSONDecodeError:
                    # Keep malformed lines (conservative)
                    outfile.write(line)
                    kept += 1
        
        # Replace original with cleaned version
        os.replace(temp_file, log_file)
        
        return removed
        
    except Exception as e:
        print(f"Error cleaning {log_file}: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return 0

def rotate_large_logs(max_size_mb=MAX_LOG_SIZE_MB):
    """Rotate logs that are too large"""
    rotated = 0
    memory_dir = Path(WORKSPACE) / "memory"
    
    for log_file in memory_dir.glob("*_log.jsonl"):
        size_mb = log_file.stat().st_size / (1024 * 1024)
        
        if size_mb > max_size_mb:
            # Rotate: rename current to .old
            old_file = log_file.with_suffix('.jsonl.old')
            
            # Remove previous .old if exists
            if old_file.exists():
                old_file.unlink()
            
            # Rename current to .old
            log_file.rename(old_file)
            
            # Create new empty log
            log_file.touch()
            
            rotated += 1
            print(f"  Rotated {log_file.name} ({size_mb:.1f}MB)")
    
    return rotated

def cleanup_backups():
    """Clean up old backups, keep only last 10"""
    backup_dir = Path(WORKSPACE) / "backups"
    if not backup_dir.exists():
        return 0
    
    backups = sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
    
    removed = 0
    for old_backup in backups[10:]:  # Keep only 10 most recent
        try:
            if old_backup.is_dir():
                import shutil
                shutil.rmtree(old_backup)
            else:
                old_backup.unlink()
            removed += 1
        except Exception as e:
            print(f"  Error removing {old_backup}: {e}")
    
    return removed

def get_disk_usage():
    """Get current disk usage of logs"""
    memory_dir = Path(WORKSPACE) / "memory"
    total_size = 0
    file_count = 0
    
    if memory_dir.exists():
        for f in memory_dir.iterdir():
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1
    
    return {
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'file_count': file_count
    }

def main():
    print("🦅 Log Cleanup System")
    print("=" * 40)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Before stats
    before = get_disk_usage()
    print(f"📊 Before: {before['total_size_mb']}MB in {before['file_count']} files")
    print()
    
    total_removed = 0
    
    # Clean up JSONL logs
    print("🧹 Cleaning old log entries...")
    memory_dir = Path(WORKSPACE) / "memory"
    for log_file in memory_dir.glob("*_log.jsonl"):
        removed = cleanup_jsonl_log(log_file)
        if removed > 0:
            print(f"  {log_file.name}: removed {removed} old entries")
            total_removed += removed
    
    if total_removed == 0:
        print("  No old entries to remove")
    
    # Rotate large logs
    print("\n📦 Rotating large logs...")
    rotated = rotate_large_logs()
    if rotated == 0:
        print("  No logs need rotation")
    
    # Clean up old backups
    print("\n💾 Cleaning old backups...")
    backups_removed = cleanup_backups()
    if backups_removed > 0:
        print(f"  Removed {backups_removed} old backups")
    else:
        print("  No old backups to remove")
    
    # After stats
    after = get_disk_usage()
    print()
    print(f"📊 After: {after['total_size_mb']}MB in {after['file_count']} files")
    
    if before['total_size_mb'] > after['total_size_mb']:
        saved = before['total_size_mb'] - after['total_size_mb']
        print(f"💾 Freed: {saved}MB")
    
    print()
    print("✅ Cleanup complete!")
    
    # Log cleanup activity
    cleanup_log = Path(WORKSPACE) / "memory" / "cleanup_log.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "entries_removed": total_removed,
        "logs_rotated": rotated,
        "backups_removed": backups_removed,
        "disk_before_mb": before['total_size_mb'],
        "disk_after_mb": after['total_size_mb']
    }
    
    with open(cleanup_log, 'a') as f:
        f.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    main()

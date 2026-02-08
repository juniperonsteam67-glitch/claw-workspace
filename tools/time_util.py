#!/usr/bin/env python3
"""
Claw Time Utility
Ensures consistent Newfoundland time across all operations
"""

import os
import time

# Force Newfoundland timezone at module load
os.environ['TZ'] = 'America/St_Johns'
time.tzset()

def now():
    """Get current time in Newfoundland timezone"""
    from datetime import datetime
    return datetime.now()

def now_str():
    """Get current time as string in NST"""
    return now().strftime('%Y-%m-%d %H:%M:%S NST')

def timestamp():
    """Get ISO timestamp"""
    return now().isoformat()

if __name__ == "__main__":
    print(f"Current time (NST): {now_str()}")
    print(f"ISO timestamp: {timestamp()}")

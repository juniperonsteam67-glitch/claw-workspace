#!/usr/bin/env python3
"""
Claw Test Suite
Automated testing for all tools
"""

import subprocess
import sys
import os
from pathlib import Path

WORKSPACE = "/config/clawd"
TESTS_RUN = 0
TESTS_PASSED = 0

def test_tool_exists():
    """Test that all expected tools exist"""
    global TESTS_RUN, TESTS_PASSED
    TESTS_RUN += 1
    
    expected_tools = [
        "startup_briefing.py",
        "self_monitor.py",
        "netmon.py",
        "webwatch.py",
        "wisdom.py",
        "codegen.py",
        "run_safe.py",
        "claw_status.py",
    ]
    
    tools_dir = Path(WORKSPACE) / "tools"
    missing = []
    
    for tool in expected_tools:
        if not (tools_dir / tool).exists():
            missing.append(tool)
    
    if missing:
        print(f"  ❌ FAIL: Missing tools: {', '.join(missing)}")
        return False
    else:
        print(f"  ✅ PASS: All {len(expected_tools)} tools present")
        TESTS_PASSED += 1
        return True

def test_python_syntax():
    """Test that all Python files have valid syntax"""
    global TESTS_RUN, TESTS_PASSED
    TESTS_RUN += 1
    
    tools_dir = Path(WORKSPACE) / "tools"
    errors = []
    
    for pyfile in tools_dir.glob("*.py"):
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(pyfile)],
            capture_output=True
        )
        if result.returncode != 0:
            errors.append(pyfile.name)
    
    if errors:
        print(f"  ❌ FAIL: Syntax errors in: {', '.join(errors)}")
        return False
    else:
        print(f"  ✅ PASS: All Python files have valid syntax")
        TESTS_PASSED += 1
        return True

def test_services_running():
    """Test that critical services are up"""
    global TESTS_RUN, TESTS_PASSED
    TESTS_RUN += 1
    
    # Check dashboard
    result = subprocess.run(
        "ss -tlnp | grep :8080",
        shell=True, capture_output=True
    )
    dashboard_up = result.returncode == 0
    
    # Check gateway
    result = subprocess.run(
        "ss -tlnp | grep :18789",
        shell=True, capture_output=True
    )
    gateway_up = result.returncode == 0
    
    if dashboard_up and gateway_up:
        print(f"  ✅ PASS: Dashboard and Gateway running")
        TESTS_PASSED += 1
        return True
    else:
        print(f"  ❌ FAIL: Dashboard: {'UP' if dashboard_up else 'DOWN'}, Gateway: {'UP' if gateway_up else 'DOWN'}")
        return False

def test_git_repo():
    """Test git repository health"""
    global TESTS_RUN, TESTS_PASSED
    TESTS_RUN += 1
    
    result = subprocess.run(
        ["git", "-C", WORKSPACE, "status"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print(f"  ✅ PASS: Git repository accessible")
        TESTS_PASSED += 1
        return True
    else:
        print(f"  ❌ FAIL: Git repository issue")
        return False

def test_memory_writable():
    """Test that memory directory is writable"""
    global TESTS_RUN, TESTS_PASSED
    TESTS_RUN += 1
    
    test_file = Path(WORKSPACE) / "memory" / ".test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✅ PASS: Memory directory writable")
        TESTS_PASSED += 1
        return True
    except:
        print(f"  ❌ FAIL: Cannot write to memory directory")
        return False

def main():
    print("🦅 Claw Test Suite")
    print("="*50)
    print(f"Started: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}")
    print()
    
    tests = [
        ("Tool Existence", test_tool_exists),
        ("Python Syntax", test_python_syntax),
        ("Services Running", test_services_running),
        ("Git Repository", test_git_repo),
        ("Memory Writable", test_memory_writable),
    ]
    
    for name, test_func in tests:
        print(f"\n🔍 {name}")
        test_func()
    
    print("\n" + "="*50)
    print(f"📊 RESULTS: {TESTS_PASSED}/{TESTS_RUN} tests passed")
    
    if TESTS_PASSED == TESTS_RUN:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {TESTS_RUN - TESTS_PASSED} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

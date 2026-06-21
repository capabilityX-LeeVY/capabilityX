#!/usr/bin/env python3
"""
Debug Test Case Runner

A convenience script to run the debug test case runner from the project root.

Usage:
    python scripts/debug_test_case.py --case stress/test_stress
    python scripts/debug_test_case.py  # Uses default case
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the debug test case runner"""
    project_root = Path(__file__).parent.parent
    debug_script = project_root / "src" / "tools" / "debug" / "run_test_case_debug.py"
    
    if not debug_script.exists():
        print(f"❌ Debug script not found: {debug_script}")
        return 1
    
    # Pass all arguments to the debug script
    cmd = [sys.executable, str(debug_script)] + sys.argv[1:]
    
    try:
        # Change to project root directory before running
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running debug script: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

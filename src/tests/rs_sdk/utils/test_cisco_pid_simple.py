#!/usr/bin/env python3
"""
Simple test script for ProcessHandler.get_cisco_collab_pid_info() method
"""

import sys
import os
from pathlib import Path

# Add src directory to path - navigate to src from tests/rs_sdk/utils/
src_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from rs_sdk.utils.process_handler import ProcessHandler


def test_cisco_collab_pid_info():
    """Test and print main_pid and media_pid information"""
    print("Testing ProcessHandler.get_cisco_collab_pid_info()")
    print("=" * 50)
    
    # Create ProcessHandler instance
    process_handler = ProcessHandler()
    
    # Get Cisco Collaboration Host process information
    pid_info = process_handler.get_cisco_collab_pid_info()
    
    # Extract and print the required information
    main_pid = pid_info.get('main_pid')
    media_pid = pid_info.get('media_pid')
    all_pids = pid_info.get('all_pids', [])
    
    print(f"Main PID (Hosted process): {main_pid}")
    print(f"Media PID: {media_pid}")
    print(f"All CiscoCollabHost.exe PIDs: {all_pids}")
    print(f"Total processes found: {len(all_pids)}")
    
    # Additional details
    if main_pid:
        print(f"✅ Main process identified with PID: {main_pid}")
    else:
        print("⚠️  Main process not found (no 'Hosted' parameter)")
    
    if media_pid:
        print(f"✅ Media process identified with PID: {media_pid}")
    else:
        print("⚠️  Media process not found (no 'media' parameter)")
    
    if not all_pids:
        print("ℹ️  No CiscoCollabHost.exe processes running")
        print("   Start Webex application to see process information")
    
    return pid_info


if __name__ == "__main__":
    test_cisco_collab_pid_info()

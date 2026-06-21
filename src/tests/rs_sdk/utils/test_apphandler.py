"""
Test for the target three lines of code:
if version == 'latest':
    version = builds_source.get_latest_master_version(platform, chip_info)
    LOGGER_INFO(f"the latest master version is {version}")
"""

import sys
import os

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
        
from tools.webexApp import appHandler


def test_get_latest_master_version():
    # Use real builds source from appHandler.py
    builds_source = appHandler.ShanghaiBuildsSource(qtversion='6', arch='x64', http2=True)
    platform = appHandler.current_platform()
    chip_info = appHandler.get_chip_info(platform)

    print("✅ Using REAL appHandler.py")
    print(f"Platform: {platform}")
    print(f"Chip Info: {chip_info}")
    
    # Test target code - exactly as in appHandler.py
    version = 'latest'
    
    if version == 'latest':
        version = builds_source.get_latest_master_version(platform, chip_info)
        print(f"the latest master version: {version}")
    
    # Return result
    return version

def test_get_local_app_version():
    """
    Test for the get_local_app_version function.
    """
    app_version = appHandler.get_local_app_version()
    print(f"Local Webex app version: {app_version}")
    return app_version

def test_is_app_version_same_as_latest():
    """
    Test for the is_app_version_same_as_latest function.
    """
    is_same = appHandler.is_app_version_same_as_latest()
    print(f"Is local app version same as latest: {is_same}")
    return is_same

def test_app_installed():
    """
    Test for the is_app_installed function.
    """
    is_installed = appHandler.installWebex()
    print(f"Is Webex app installed: {is_installed}")
    return is_installed

if __name__ == "__main__":
    print("Testing version='latest' return value:")
    result = test_get_latest_master_version()
    print(f"Result: [{result}]")
    print("\nTesting get_local_app_version:")
    local_version = test_get_local_app_version()
    print(f"Result: [{local_version}]")
    print("\nTesting is_app_version_same_as_latest:")
    is_latest = test_is_app_version_same_as_latest()
    print(f"Result: [{is_latest}]")


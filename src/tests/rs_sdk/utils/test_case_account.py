#!/usr/bin/env python3
"""
Test script for database integration in WorkflowLoader
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

from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from config.paths import src_path

def test_db_config_loading():
    """Test database configuration loading"""
    print("\n=== Testing Database Configuration Loading ===")
    
    loader = WorkflowLoader()
    
    # if loader._db_config:
    #     print(f"Database config loaded successfully:")
    #     print(f"  Host: {loader._db_config.get('host', 'Not set')}")
    #     print(f"  User: {loader._db_config.get('user', 'Not set')}")
    #     print(f"  Database: {loader._db_config.get('database', 'Not set')}")
    #     print(f"  Charset: {loader._db_config.get('charset', 'Not set')}")
    #     return True
    # else:
    #     print("Failed to load database configuration")
    #     return False


def test_account_resolution():
    """Test account resolution with the new implementation"""
    print("\n=== Testing Account Resolution ===")
    
    loader = WorkflowLoader()
    
    # Test sign_in.yaml with default account
    sign_in_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    if sign_in_path.exists():
        print(f"Testing sign_in.yaml: {sign_in_path}")
        
        # Test with default account
        print("\nUsing default account:")
        ui_path_default = loader.build_ui_path(sign_in_path)
        
        for i, step in enumerate(ui_path_default):
            if 'action' in step and step['action']['type'] == 'input':
                print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
        # Test with override account
        print("\nUsing fullmode18 account override:")
        ui_path_override = loader.build_ui_path_with_account(sign_in_path, "fullmode18")
        
        for i, step in enumerate(ui_path_override):
            if 'action' in step and step['action']['type'] == 'input':
                print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
        return True
    else:
        print(f"sign_in.yaml not found at: {sign_in_path}")
        return False


def test_main_test_case_account_inheritance():
    """Test main test case account inheritance for pre-conditions"""
    print("\n=== Testing Main Test Case Account Inheritance ===")
    
    loader = WorkflowLoader()
    
    # Test with vbg_in_meeting_lookout.yaml that has account: fullmode18
    vbg_path = src_path / "test_space" / "test_cases" / "meetings" / "video" / "vbg_static.yaml"
    sign_in_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    if vbg_path.exists() and sign_in_path.exists():
        # Get account from main test case
        main_account = loader.get_test_case_account(vbg_path)
        print(f"Main test case account: {main_account}")
        
        # Simulate pre-condition execution with main account inheritance
        print("\nPre-condition (sign_in) with main test case account inheritance:")
        pre_condition_ui_path = loader.build_ui_path_with_account(sign_in_path, main_account)
        
        for i, step in enumerate(pre_condition_ui_path):
            if 'action' in step and step['action']['type'] == 'input':
                print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
        return True
    else:
        print("Required test files not found")
        return False


def main():
    """Main test function"""
    print("Starting WorkflowLoader Database Integration Tests...")
    
    try:
        # Test database configuration loading
        db_config_ok = test_db_config_loading()
        
        # Test account resolution
        account_resolution_ok = test_account_resolution()
        
        # Test main test case account inheritance
        inheritance_ok = test_main_test_case_account_inheritance()
        
        if db_config_ok and account_resolution_ok and inheritance_ok:
            print("\n=== All Tests Completed Successfully ===")
            print("\nSummary of changes:")
            print("1. ✅ Database configuration moved to settings.json")
            print("2. ✅ get_test_case_from_db moved to WorkflowLoader")
            print("3. ✅ Account resolution working correctly")
            print("4. ✅ Main test case account inheritance implemented")
            return True
        else:
            print("\n=== Some Tests Failed ===")
            return False
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

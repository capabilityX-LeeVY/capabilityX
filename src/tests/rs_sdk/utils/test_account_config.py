#!/usr/bin/env python3
"""
Test script for account configuration functionality
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from config.account_config import AccountConfigHandler
from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR


def test_account_config():
    """Test account configuration loading"""
    print("\n=== Testing Account Configuration ===")
    
    # Test account config handler
    account_handler = AccountConfigHandler()
    
    # Test listing accounts
    accounts = account_handler.list_accounts()
    print(f"Available accounts: {accounts}")
    
    # Test getting default account
    default_account = account_handler.get_account_info()
    print(f"Default account: {default_account}")
    
    # Test getting specific account
    fullmode_account = account_handler.get_account_info("fullmode18")
    print(f"Fullmode18 account: {fullmode_account}")
    
    return True


def test_workflow_loader():
    """Test workflow loader with account variable resolution"""
    print("\n=== Testing Workflow Loader with Account Variables ===")
    
    loader = WorkflowLoader()
    
    # Test sign_in.yaml with default account
    sign_in_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    if sign_in_path.exists():
        print(f"Testing sign_in.yaml: {sign_in_path}")
        
        # Get account from test case (should be None for sign_in.yaml)
        account_name = loader.get_test_case_account(sign_in_path)
        print(f"Account name from sign_in.yaml: {account_name}")
        
        # Build UI path (should resolve variables with default account)
        ui_path = loader.build_ui_path(sign_in_path)
        
        print("\nUI Path after variable resolution (default account):")
        for i, step in enumerate(ui_path):
            if 'action' in step and step['action']['type'] == 'input':
                print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
        # Test with override account
        print("\nTesting with override account 'fullmode18':")
        ui_path_override = loader.build_ui_path_with_account(sign_in_path, "fullmode18")
        
        for i, step in enumerate(ui_path_override):
            if 'action' in step and step['action']['type'] == 'input':
                print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
    else:
        print(f"sign_in.yaml not found at: {sign_in_path}")
    
    # Test with a test case that has account specified
    vbg_path = src_path / "test_space" / "test_cases" / "meetings" / "video" / "vbg_in_meeting_lookout.yaml"
    
    if vbg_path.exists():
        print(f"\nTesting vbg_in_meeting_lookout.yaml: {vbg_path}")
        
        # Get account from test case (should be 'fullmode18')
        account_name = loader.get_test_case_account(vbg_path)
        print(f"Account name from vbg_in_meeting_lookout.yaml: {account_name}")
        
        # This should demonstrate how pre-conditions will use the main test case account
        print("\nSimulating pre-conditions execution with main test case account:")
        pre_conditions = loader.get_test_cases_pre_conditions(vbg_path)
        print(f"Pre-conditions: {pre_conditions}")
        
        if pre_conditions and 'navigations/basic/sign_in' in pre_conditions:
            sign_in_with_main_account = loader.build_ui_path_with_account(sign_in_path, account_name)
            print("\nSign-in UI path with main test case account (fullmode18):")
            for i, step in enumerate(sign_in_with_main_account):
                if 'action' in step and step['action']['type'] == 'input':
                    print(f"  Step {i+1}: {step['name']} -> value: {step['action']['value']}")
        
    else:
        print(f"vbg_in_meeting_lookout.yaml not found at: {vbg_path}")
    
    return True


def main():
    """Main test function"""
    print("Starting Account Configuration Tests...")
    
    try:
        # Test account configuration
        test_account_config()
        
        # Test workflow loader
        test_workflow_loader()
        
        print("\n=== All Tests Completed Successfully ===")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

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


def test_case_ui_path_building():
    """Test case for building UI path with account - as requested"""
    print("\n=== Testing UI Path Building with Account ===")
    
    # Initialize workflow loader
    workflow_loader = WorkflowLoader()
    
    # Define test case path
    test_case_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    # Define main test case account
    main_test_case_account = "fullmode18"
    
    if test_case_path.exists():
        print(f"Test case path: {test_case_path}")
        print(f"Main test case account: {main_test_case_account}")
        
        # Build UI path with account - as requested
        test_case_ui_path = workflow_loader.build_ui_path_with_account(test_case_path, main_test_case_account)
        
        # Extract step names
        step_names = [step.get('name', '') for step in test_case_ui_path if isinstance(step, dict)]
        
        print(f"\nStep Names List:")
        print(step_names)
        
        # Verify that test_case_ui_path is not empty
        if test_case_ui_path:
            print(f"\n✅ Successfully built UI path with {len(test_case_ui_path)} steps")
            return True
        else:
            print("\n❌ Failed to build UI path - empty result")
            return False
    else:
        print(f"❌ Test case file not found: {test_case_path}")
        return False


def test_control_name_ui_path():
    """Test case for building UI path based on control_name"""
    print("\n=== Testing Control Name UI Path Building ===")
    
    # Initialize workflow loader
    workflow_loader = WorkflowLoader()
    
    # Define test case path
    test_case_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    # Define main test case account
    main_test_case_account = "fullmode18"
    
    if test_case_path.exists():
        print(f"Test case path: {test_case_path}")
        print(f"Main test case account: {main_test_case_account}")
        
        # Build UI path with control_name information from control datasets
        control_name_ui_path = workflow_loader.build_control_name_ui_path(test_case_path, main_test_case_account)
        
        # Extract step names
        step_names = [step.get('name', '') for step in control_name_ui_path if isinstance(step, dict)]
        
        # Extract control_names from control_metadata (Windows platform)
        control_names = []
        for step in control_name_ui_path:
            if isinstance(step, dict) and 'control_metadata' in step:
                control_name = step['control_metadata'].get('control_name', '')
                control_names.append(control_name)
            else:
                control_names.append('')  # Empty string for steps without control_metadata
        
        print(f"\nStep Names List:")
        print(step_names)
        print(f"\nControl Names List (Windows):")
        print(control_names)
        
        # Verify success
        if control_name_ui_path:
            print(f"\n✅ Successfully built Control Name UI path with {len(control_name_ui_path)} steps")
            return True
        else:
            print("\n❌ Failed to build Control Name UI path - empty result")
            return False
    else:
        print(f"❌ Test case file not found: {test_case_path}")
        return False


def test_automation_id_ui_path():
    """Test case for building UI path based on automation_id"""
    print("\n=== Testing Automation ID UI Path Building ===")
    
    # Initialize workflow loader
    workflow_loader = WorkflowLoader()
    
    # Define test case path
    test_case_path = src_path / "test_space" / "test_cases" / "app_core" / "sign_in.yaml"
    
    # Define main test case account
    main_test_case_account = "fullmode18"
    
    if test_case_path.exists():
        print(f"Test case path: {test_case_path}")
        print(f"Main test case account: {main_test_case_account}")
        
        # Build UI path with automation_id information from control datasets
        automation_id_ui_path = workflow_loader.build_automation_id_ui_path(test_case_path, main_test_case_account)
        
        # Extract step names
        step_names = [step.get('name', '') for step in automation_id_ui_path if isinstance(step, dict)]
        
        # Extract control_names from automation_metadata (Windows platform)
        control_names = []
        for step in automation_id_ui_path:
            if isinstance(step, dict) and 'automation_metadata' in step:
                control_name = step['automation_metadata'].get('control_name', '')
                control_names.append(control_name)
            else:
                control_names.append('')  # Empty string for steps without automation_metadata
        
        # Extract control_ids (automation_ids) from automation_metadata (Windows platform)
        control_ids = []
        for step in automation_id_ui_path:
            if isinstance(step, dict) and 'automation_metadata' in step:
                control_id = step['automation_metadata'].get('automation_id', '')
                control_ids.append(control_id)
            else:
                control_ids.append('')  # Empty string for steps without automation_metadata
        
        print(f"\nStep Names List:")
        print(step_names)
        print(f"\nControl Names List (Windows):")
        print(control_names)
        print(f"\nControl IDs List (Windows):")
        print(control_ids)
        
        # Verify success
        if automation_id_ui_path:
            print(f"\n✅ Successfully built Automation ID UI path with {len(automation_id_ui_path)} steps")
            return True
        else:
            print("\n❌ Failed to build Automation ID UI path - empty result")
            return False
    else:
        print(f"❌ Test case file not found: {test_case_path}")
        return False


def main():
    """Main test function"""
    print("Starting WorkflowLoader UI Path Building Tests...")
    
    try:
        # Test UI path building with account
        ui_path_building_ok = test_case_ui_path_building()
        
        # Test control_name UI path building
        control_name_ok = test_control_name_ui_path()
        
        # Test automation_id UI path building
        automation_id_ok = test_automation_id_ui_path()
        
        if ui_path_building_ok and control_name_ok and automation_id_ok:
            print("\n=== All Tests Completed Successfully ===")
            print("\nSummary of tests:")
            print("1. ✅ UI path building with account tested")
            print("2. ✅ Control Name UI path building tested")
            print("3. ✅ Automation ID UI path building tested")
            return True
        else:
            print("\n=== Some Tests Failed ===")
            print(f"UI Path Building: {'✅' if ui_path_building_ok else '❌'}")
            print(f"Control Name UI Path: {'✅' if control_name_ok else '❌'}")
            print(f"Automation ID UI Path: {'✅' if automation_id_ok else '❌'}")
            return False
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

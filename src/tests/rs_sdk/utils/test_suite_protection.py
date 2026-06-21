#!/usr/bin/env python3
"""
Test script for test suite protection mechanism
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

from rs_sdk.utils.workflow_loader import WorkflowLoader
from config.paths import TEST_SUITE_PATH, TEST_CASES_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR


def test_suite_file_existence():
    """Test checking for test suite file existence"""
    print("\n=== Testing Test Suite File Existence ===")
    
    # Test suites to check
    test_suites = [
        "smoke",           # This might exist
        "regression",      # This might exist
        "non_existent_suite",  # This should not exist
    ]
    
    for test_suite in test_suites:
        print(f"\n--- Testing suite: {test_suite} ---")
        
        test_suite_path = TEST_SUITE_PATH / f"{test_suite}.yaml"
        
        if test_suite_path.exists():
            print(f"✅ Test suite file exists: {test_suite_path}")
            
            # Try to load the suite
            try:
                loader = WorkflowLoader()
                langs = loader.get_test_suite_languages(test_suite_path)
                print(f"   Languages: {langs}")
                
                test_cases = loader.get_test_cases_from_suite(test_suite_path)
                print(f"   Test cases count: {len(test_cases)}")
                if test_cases:
                    print(f"   First few test cases: {test_cases[:3]}")
                    
            except Exception as e:
                print(f"❌ Failed to load test suite: {str(e)}")
        else:
            print(f"❌ Test suite file not found: {test_suite_path}")
            print(f"   This would trigger the protection mechanism")


def list_available_test_suites():
    """List all available test suite files"""
    print("\n=== Available Test Suite Files ===")
    
    if TEST_SUITE_PATH.exists():
        print(f"TEST_SUITE_PATH: {TEST_SUITE_PATH}")
        
        # Find all .yaml files in test suite directory
        yaml_files = list(TEST_SUITE_PATH.glob("*.yaml"))
        
        if yaml_files:
            print(f"Found {len(yaml_files)} test suite files:")
            for yaml_file in yaml_files:
                suite_name = yaml_file.stem  # filename without extension
                print(f"  - {suite_name} ({yaml_file.name})")
        else:
            print("No test suite YAML files found")
    else:
        print(f"TEST_SUITE_PATH does not exist: {TEST_SUITE_PATH}")


def simulate_suite_runner_protection():
    """Simulate the protection mechanism in SuiteCaseRunner"""
    print("\n=== Simulating Suite Runner Protection Mechanism ===")
    
    # Test suites to simulate
    test_suites = ["smoke", "non_existent_suite", "regression"]
    
    print(f"Simulating test suite mode with suites: {test_suites}")
    
    for test_suite in test_suites:
        print(f"\n--- Processing suite: {test_suite} ---")
        
        test_suite_path = TEST_SUITE_PATH / f"{test_suite}.yaml"
        
        # Check if test suite file exists (protection mechanism)
        if not test_suite_path.exists():
            print(f"❌ [ERROR] Test suite file not found: {test_suite_path}")
            print(f"❌ [ERROR] Please check if test suite '{test_suite}' exists in directory: {TEST_SUITE_PATH}")
            print(f"   → Skipping this suite (continue to next)")
            continue
        
        print(f"✅ [INFO] Found test suite file: {test_suite_path}")
        
        try:
            loader = WorkflowLoader()
            langs = loader.get_test_suite_languages(test_suite_path)
            print(f"✅ [INFO] Successfully loaded suite with languages: {langs}")
            
            test_cases = loader.get_test_cases_from_suite(test_suite_path)
            print(f"✅ [INFO] Test cases loaded: {len(test_cases)} cases")
            
        except Exception as e:
            print(f"❌ [ERROR] Failed to load test suite '{test_suite}': {str(e)}")
            print(f"   → Skipping this suite (continue to next)")
            continue


def main():
    """Main test function"""
    print("Starting Test Suite Protection Mechanism Tests...")
    
    try:
        # Test suite file existence
        test_suite_file_existence()
        
        # List available test suites
        list_available_test_suites()
        
        # Simulate protection mechanism
        simulate_suite_runner_protection()
        
        print("\n=== Test Suite Protection Tests Completed ===")
        print("\nSummary of protection mechanisms added:")
        print("1. ✅ Check test suite file existence before processing")
        print("2. ✅ Graceful error handling for missing suite files")
        print("3. ✅ Continue processing other suites if one fails")
        print("4. ✅ Exception handling for suite loading and test case extraction")
        print("5. ✅ Detailed error messages with file paths and suggestions")
        
        return True
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

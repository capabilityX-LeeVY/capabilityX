
import requests
import os
import sys

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from functions.mcp import server
import json

def test_run_test_case(test_case):
    try:
        # run_test_case expects a list parameter
        result = server.run_test_case([test_case], account="allianz2")
        
        # Parse and display results
        result_dict = json.loads(result)
        print(f"Execution result: {result_dict.get('status', 'unknown')}")
        
        if result_dict.get('status') == 'success':
            print(f"✓ Test case '{test_case}' executed successfully")
            print(f"  Report URL: {result_dict.get('report_url', 'N/A')}")
        else:
            print(f"✗ Test case '{test_case}' execution failed")
            print(f"  Error: {result_dict.get('error', 'unknown error')}")
        
        return result_dict.get('status') == 'success'
        
    except Exception as e:
        print(f"✗ Error executing test case: {e}")
        return False

if __name__ == "__main__":
    test_case = "sign_in"  # Example test case
    print(f"Test case: {test_case}")
    success = test_run_test_case(test_case)

    if success:
        print("🎉 Test case execution completed successfully!")
    else:
        print("⚠️ Test case execution failed!")

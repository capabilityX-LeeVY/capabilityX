"""
Meeting-related functions for Webex meetings
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
        
from core.suite_case_runner import SuiteCaseRunner
from config.paths import LOG_PATH


def run_bwc_calling_functions(test_suite_list = ['anwser_calling_bwc']):
    """
    Run the specified test suites for Webex calling
    """
    suite_case_runner = SuiteCaseRunner()
    suite_case_runner.run(test_suite_list)
    
    return {
        "status": "success",
        "message": "bwc calling anwser successfully",
        "action": "anwser bwc calling"
    }
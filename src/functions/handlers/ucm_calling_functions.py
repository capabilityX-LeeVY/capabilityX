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
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR


def run_calling_functions(test_suite_list = ['acc_regression/calling/answer_calling_ucm']):
    """
    Run the specified test suites for Webex calling
    
    Args:
        test_suite_list (list): List of test suite names to run (relative to test_suites/ directory)
        platform (str): Platform to run tests on ('windows' or 'mac')
    
    Returns:
        dict: Execution result with status and details
        
    Raises:
        Exception: If test suite execution fails
    """
    try:
        LOGGER_INFO(f"Starting calling functions with test suite: {test_suite_list}", "CYAN")
        
        suite_case_runner = SuiteCaseRunner()
        result = suite_case_runner.run(test_suite_list, mode='suite')
        
        LOGGER_INFO(f"Calling functions execution completed: {result}", "GREEN")
        
        return {
            "status": "success",
            "message": "calling answer successfully",
            "action": "answer calling",
            "test_suite": test_suite_list,
            "result": str(result) if result else "completed"
        }
    except Exception as e:
        LOGGER_ERROR(f"Failed to run calling functions: {str(e)}", "RED")
        raise Exception(f"Calling functions execution failed: {str(e)}")
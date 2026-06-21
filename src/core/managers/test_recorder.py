"""
Test Recorder for tracking and recording test execution results.

This module is responsible for:
- Recording test execution results to database
- Managing execution timing and status tracking
- Handling test result reporting and logging
"""

from datetime import datetime
from common.utils.logger import LOGGER_DEBUG, LOGGER_INFO, LOGGER_ERROR


class TestRecorder:
    """Records and tracks test execution results."""

    def execute_test_case_with_recording(self, test_executor, test_case_name, test_case_path_str,
                                       language, mode, navigate_report_path, 
                                       performance_report_path, stress_report_path=None, test_suite_path=None, check_points=None):
        """
        Execute test case with timing and database recording.
        
        Args:
            test_executor: TestExecutor instance
            test_case_name (str): Name of the test case
            test_case_path_str (str): Path to the test case
            language (str): Language code
            mode (str): Execution mode
            navigate_report_path (str): Navigation report path
            performance_report_path (str): Performance report path
            stress_report_path (str): Stress report path (optional)
            test_suite_path (str): Test suite path for account resolution (optional)
            check_points (list): List of enabled check points from test suite (optional)
            
        Returns:
            bool: True if execution successful, False otherwise
        """
        execution_start_time = datetime.now()
        
        try:
            result = test_executor.execute_test_case(
                test_case_path_str, 
                language=language, 
                mode=mode,
                navigate_report_path=navigate_report_path,
                performance_report_path=performance_report_path,
                stress_report_path=stress_report_path,
                test_suite_path=test_suite_path,
                check_points=check_points  # Pass check_points
            )
            
            execution_end_time = datetime.now()
            execution_duration = (execution_end_time - execution_start_time).total_seconds()

            # Determine execution status
            execution_status = 'PASS' if result else 'FAIL'

            LOGGER_INFO(f"Test Case: {test_case_name} executed with result: {result}", "GREEN")

            return result

        except Exception as e:
            LOGGER_ERROR(f"Test Case: {test_case_name} execution failed: {str(e)}", "RED")
            return False

    def log_test_results(self, test_results, navigate_report_path):
        """Log summary of test execution results."""
        passed_count = len([r for r in test_results if r[1]])
        failed_count = len([r for r in test_results if not r[1]])
        
        LOGGER_DEBUG(f"All test execution completed. Results: {passed_count} passed, {failed_count} failed", "GREEN")
        LOGGER_DEBUG(f"Test Report Path: {navigate_report_path}", "YELLOW")

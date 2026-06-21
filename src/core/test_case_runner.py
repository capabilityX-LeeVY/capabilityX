"""
test_case_runner.py

Core test case runner that focuses solely on executing individual test cases or test suites.
This is separated from the job workflow orchestration.
"""

import time
import platform

# Platform-specific imports for event listener, control handler, and control singleton
if platform.system() == "Windows":
    from rs_sdk.utils.event_listener import FocusListener
    from rs_sdk.utils.control_handler import ControlHandler
    from rs_sdk.utils.control import Control
elif platform.system() == "Linux":
    from rs_sdk.platform.linux import FocusListener, ControlHandler, Control
else:
    # Default fallback for unsupported platforms (Windows)
    from rs_sdk.utils.event_listener import FocusListener
    from rs_sdk.utils.control_handler import ControlHandler
    from rs_sdk.utils.control import Control
from rs_sdk.utils.process_handler import ProcessHandler
from rs_sdk.utils.workflow_loader import WorkflowLoader
from tools.webexApp import appHandler
from common.utils.featureToggle import FeatureToggle
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING
from core.suite_case_runner import SuiteCaseRunner
from config.paths import TEST_SUITE_PATH, TEST_CASES_PATH


class TestCaseRunner:
    """
    Core test case runner that handles the execution of test cases and test suites.
    This class focuses solely on test execution without additional workflow orchestration.
    """
    
    def __init__(self, platform=None):
        self.platform = platform
        self.process_handler = ProcessHandler()
        self.control_handler = ControlHandler()
        self.workflow_loader = WorkflowLoader()
        
        # Initialize focus listener if enabled
        if Control.toggle_listener:
            listener = FocusListener()
            listener.start()
            time.sleep(1)
    
    def _setup_webex_application(self, platform):
        """Setup Webex application if required for the platform"""
        if platform == 'web':
            LOGGER_INFO(f"No installation required for {platform}", "CYAN")
            return True
            
        if not FeatureToggle.isEnabled('installer'):
            LOGGER_INFO("Webex installation skipped (installer disabled)", "YELLOW")
            return True
            
        LOGGER_INFO("Installing Webex application...", "CYAN")
        appHandler.installWebex()
        time.sleep(10)

        # Wait for and get Webex main process PID
        LOGGER_INFO("Waiting for Webex main process...", "CYAN")
        webex_app_main_pid = self.process_handler.wait_for_main_pid()
        
        if webex_app_main_pid is not None:
            LOGGER_DEBUG(f"Focusing on Webex window with PID: {webex_app_main_pid}")
            self.control_handler.focus_on_active_window_by_pid(webex_app_main_pid)
            return True
        else:
            LOGGER_WARNING("Warning: Failed to obtain Webex main process PID")
            return False

    def run_test_suite(self, test_suite, mode="suite", progress_callback=None):
        """
        Run a test suite, individual test case, or test batch.
        
        Args:
            test_suite (str): Name of the test suite, test case, or test batch
            mode (str): "suite" for test suite, "case" for individual test case, "batch" for test batch
            
        Returns:
            tuple: (navigate_report_path, performance_report_path, stress_report_path, check_points)
        """
        # Determine platform and test suite path
        if mode == "suite":
            test_suite_path = TEST_SUITE_PATH / f"{test_suite}.yaml"
            platform = self.workflow_loader.get_test_suite_platform(test_suite_path)
        elif mode == "batch":
            test_suite_path = TEST_CASES_PATH.parent / "test_batch" / f"{test_suite}.yaml"
            platform = self.platform or "windows"  # Use provided platform or default
        else:  # mode == "case"
            test_suite_path = TEST_CASES_PATH / f"{test_suite}.yaml"
            platform = self.platform or "windows"  # Use provided platform or default
            
        LOGGER_INFO(f"[ORCHESTRATOR][Init]: Running test {mode}: {test_suite} on {platform}", "CYAN")
        LOGGER_DEBUG(f"[ORCHESTRATOR][Init]: Test path: {test_suite_path}", "CYAN")
        
        # Setup Webex application if needed
        # if not self._setup_webex_application(platform):
        #     LOGGER_WARNING("Failed to setup Webex application")
        #     return None, None, None, None

        # Execute the test suite
        suite_case_runner = SuiteCaseRunner(platform=platform)
        result = suite_case_runner.run(test_suite, mode=mode, progress_callback=progress_callback)
        
        # Unpack result tuple (5 elements: nav_path, perf_path, stress_path, check_points, sr_enabled_cases)
        navigate_report_path = result[0] if result else None
        performance_report_path = result[1] if result and len(result) >= 2 else None
        stress_report_path = result[2] if result and len(result) >= 3 else None
        check_points = result[3] if result and len(result) >= 4 else None
        sr_enabled_cases = result[4] if result and len(result) >= 5 else None

        return navigate_report_path, performance_report_path, stress_report_path, check_points, sr_enabled_cases
    
    def run_test_case(self, test_case_name, platform=None):
        """
        Run a single test case.
        
        Args:
            test_case_name (str): Name of the test case
            platform (str): Platform to run on (optional)
            
        Returns:
            tuple: (navigate_report_path, performance_report_path, stress_report_path, check_points)
        """
        return self.run_test_suite(test_case_name, mode="case")

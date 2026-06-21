"""
App Manager for handling Webex application lifecycle.

This module is responsible for:
- Launching and preparing the Webex application
- Managing application state across different platforms
- Handling application focus and window management
"""

import time
import yaml
import platform
from tools.webexApp import appHandler
from rs_sdk.utils.process_handler import ProcessHandler

# Platform-specific import for control handler
if platform.system() == "Windows":
    from rs_sdk.utils.control_handler import ControlHandler
elif platform.system() == "Linux":
    from rs_sdk.platform.linux import ControlHandler
else:
    from rs_sdk.utils.control_handler import ControlHandler

from rs_sdk.utils import report_handler
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG
from config.paths import TEST_CASES_PATH, TEST_SUITE_PATH
from config.config import AGREEMENTWINDOW


class AppManager:
    """Manages Webex application lifecycle and state."""

    def __init__(self, platform='windows'):
        self.platform = platform
        self.process_handler = ProcessHandler()
        self.control_handler = ControlHandler()

    def launch_and_prepare(self, language="en", test_suite_case="vbg_in_meeting", mode='suite'):
        """
        Launch and prepare the Webex application for testing.
        
        Args:
            language (str): Language code for the application
            test_suite_case (str): Test suite or case name
            mode (str): 'suite', 'case', or 'batch' mode
            
        Returns:
            Path: Test suite/case path
        """
        # Determine test path based on mode
        if mode == 'case' or mode == 'batch':
            LOGGER_INFO(f"Launching Webex app for {mode} mode with language: {language}", "CYAN")
            test_suite_path = TEST_CASES_PATH / f"{test_suite_case}.yaml"
        else:
            test_suite_path = TEST_SUITE_PATH / f"{test_suite_case}.yaml"

        if self.platform == "windows":
            self._handle_windows_platform(language)
        elif self.platform == "web":
            self._handle_web_platform(language, test_suite_path)

        return test_suite_path

    def _handle_windows_platform(self, language):
        """Handle Windows platform specific application management."""
        webex_app_pids = self.process_handler.get_cisco_collab_pid_info()
        webex_app_main_pid = webex_app_pids.get('main_pid', None)
        
        if webex_app_main_pid:
            window_name, window_automation_id = self.control_handler.get_main_window_info_by_pid(webex_app_main_pid)
            if window_automation_id == AGREEMENTWINDOW:
                LOGGER_DEBUG(f"Webex app is in agreement window, do not relaunch with language: {language}", "YELLOW")
                return
            
            LOGGER_DEBUG(f"killing Webex app for platform: {self.platform} to relaunch with language: {language}", "YELLOW")
            appHandler.kill_process(self.platform)
            time.sleep(2)

        appHandler.launch_app(self.platform, language)
        time.sleep(10)  # Wait for the app to load

    def _handle_web_platform(self, language, test_case_path=None):
        """
        Handle web platform specific application management.
        
        Args:
            language (str): Language code for the application
            test_case_path (Path): Path to test case or test suite YAML file to read site_url from
        """
        LOGGER_INFO(f"Launching Webex app for platform: {self.platform}, language: {language}", "CYAN")
        
        # Try to get site_url from test case YAML
        site_url = "https://web.webex.com"  # Default URL
        
        if test_case_path and test_case_path.exists():
            try:
                with open(test_case_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                # Check if this is a test suite file (contains test_suite section)
                if 'test_suite' in data:
                    LOGGER_DEBUG(f"Reading from test suite file: {test_case_path}", "CYAN")
                    # Get the first test case from the suite
                    test_cases = data.get('test_suite', {}).get('test_cases', [])
                    if test_cases:
                        first_test_case = test_cases[0]
                        LOGGER_DEBUG(f"First test case in suite: {first_test_case}", "CYAN")
                        # Build the test case path
                        actual_test_case_path = TEST_CASES_PATH / f"{first_test_case}.yaml"
                        if actual_test_case_path.exists():
                            LOGGER_DEBUG(f"Reading site_url from first test case: {actual_test_case_path}", "CYAN")
                            with open(actual_test_case_path, 'r', encoding='utf-8') as tc_f:
                                tc_data = yaml.safe_load(tc_f)
                                custom_site_url = tc_data.get('test_case', {}).get('site_url', None)
                                if custom_site_url:
                                    site_url = custom_site_url
                                    LOGGER_INFO(f"Using site_url from first test case in suite: {site_url}", "GREEN")
                        else:
                            LOGGER_DEBUG(f"First test case file not found: {actual_test_case_path}, using default URL", "YELLOW")
                    else:
                        LOGGER_DEBUG(f"No test cases found in test suite, using default: {site_url}", "YELLOW")
                
                # Check if this is a test case file (contains test_case section)
                elif 'test_case' in data:
                    LOGGER_DEBUG(f"Reading from test case file: {test_case_path}", "CYAN")
                    custom_site_url = data.get('test_case', {}).get('site_url', None)
                    if custom_site_url:
                        site_url = custom_site_url
                        LOGGER_INFO(f"Using site_url from test case: {site_url}", "GREEN")
                    else:
                        LOGGER_DEBUG(f"No site_url found in test case, using default: {site_url}", "YELLOW")
                else:
                    LOGGER_DEBUG(f"Unknown YAML structure, using default: {site_url}", "YELLOW")
                    
            except Exception as e:
                LOGGER_DEBUG(f"Could not read site_url from test case: {e}, using default: {site_url}", "YELLOW")
        else:
            LOGGER_DEBUG(f"Test case path not provided or does not exist, using default: {site_url}", "YELLOW")
        
        appHandler.launch_edge_browser(site_url)
        time.sleep(5)  # Wait for the browser to load
        LOGGER_INFO(f"Webex app launched in browser on platform: {self.platform} at {site_url}", "CYAN")

    def focus_on_webex_app(self):
        """Focus on the Webex application window."""
        webex_app_pids = self.process_handler.get_cisco_collab_pid_info()
        webex_app_main_pid = webex_app_pids.get('main_pid', None)
        webex_app_media_pid = webex_app_pids.get('media_pid', None)
        
        LOGGER_INFO(f"[initial] webex main [{webex_app_main_pid}], media [{webex_app_media_pid}]", "YELLOW")
        self.control_handler.focus_on_active_window_by_pid(webex_app_main_pid)

    def focus_webex_app_if_needed(self):
        """Focus on webex app if not in web mode."""
        if self.platform == 'web':
            LOGGER_INFO("Running in web mode, Skip focus on webex app...")
        else:
            self.focus_on_webex_app()

    def initialize_reports(self, test_suite_case, language):
        """Initialize report paths for navigation and performance tracking."""
        navigate_report_path = report_handler.initialize_navigate_report(test_suite_case, language)
        performance_report_path = report_handler.initialize_performance_report(test_suite_case)
        
        # Check for Stress checkpoint and initialize stress report if needed
        stress_report_path = None
        try:
            # Try to get checkpoints from the test case
            from config.paths import TEST_CASES_PATH
            from rs_sdk.utils.workflow_loader import WorkflowLoader
            
            test_case_path = TEST_CASES_PATH / f"{test_suite_case}.yaml"
            if not test_case_path.exists():
                # Search in subdirectories using rglob
                test_case_yaml_files = list(TEST_CASES_PATH.rglob(f"{test_suite_case}.yaml"))
                if test_case_yaml_files:
                    test_case_path = test_case_yaml_files[0]
                    LOGGER_DEBUG(f"Found test case in subdirectory: {test_case_path}", "CYAN")

            if test_case_path.exists():
                with open(test_case_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                checkpoints = data.get('test_case', {}).get('check_points', [])
                LOGGER_DEBUG(f"Found checkpoints for {test_suite_case}: {checkpoints}", "CYAN")
                if 'Stress' in checkpoints:
                    stress_report_path = report_handler.initialize_stress_report(test_suite_case)
                    LOGGER_INFO(f"Initialized stress report: {stress_report_path}", "CYAN")
            else:
                LOGGER_DEBUG(f"Test case file not found: {test_suite_case}.yaml", "YELLOW")
            
        except Exception as e:
            LOGGER_DEBUG(f"Could not check for stress checkpoint: {e}", "YELLOW")

        LOGGER_DEBUG(
            f"Initialized reports:\n"
            f"  Navigate: {navigate_report_path}\n"
            f"  Performance: {performance_report_path}\n"
            f"  Stress: {stress_report_path}",
            "CYAN"
        )
        
        return navigate_report_path, performance_report_path, stress_report_path

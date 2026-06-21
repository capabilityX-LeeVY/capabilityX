"""
Initialization Checker for Webex application readiness verification.

This module is responsible for:
- Checking if the Webex application is properly initialized
- Verifying application state before test execution
- Handling initialization failures and recovery
"""

import platform
from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR
from config.paths import TEST_CASES_PATH
from config.config import INITIALIZATION_CONTROLS, AGREEMENTWINDOW
from rs_sdk.utils import control_datasets_loader

# Platform-specific imports
if platform.system() == "Windows":
    from core.windows.control_operator import ControlOperator
elif platform.system() == "Linux":
    from core.linux.control_operator import ControlOperator


class InitializationChecker:
    """Checks and validates Webex application initialization state."""

    def __init__(self, platform='windows'):
        self.platform = platform
        self.current_control = ControlFactory().create_control()
        self.workflow_loader = WorkflowLoader()
        self.control_operator = ControlOperator()
        self.locale_processor = self.control_operator.control_locator

    def check_webex_app_initialization(self, test_case, navigate_report_path=None, performance_report_path=None):
        """
        Check if the Webex application is properly initialized.
        
        Args:
            test_case (str): Test case name to check pre-conditions
            navigate_report_path (str): Path for navigation report
            performance_report_path (str): Path for performance report
            
        Returns:
            bool: True if initialized successfully, False otherwise
        """
        test_case_path = TEST_CASES_PATH / f"{test_case}.yaml"
        pre_conditions = self.workflow_loader.get_test_cases_pre_conditions(test_case_path)
        
        LOGGER_INFO(f"[initial][pre_conditions]: {pre_conditions}", "YELLOW")
        
        if pre_conditions is None:
            LOGGER_INFO("[initial][skip] check Webex app initialization", "YELLOW")
            return True

        current_control = self.current_control
        current_id = current_control.ControlID
        reassigned_ancestors = current_control.ControlAncestorLevelsElements
        current_control_level1_window_autoid = reassigned_ancestors["level1"]["id"]

        # 1. Check if the current control is in the agreement window
        if self._is_in_agreement_window(current_control_level1_window_autoid, current_id):
            return True

        # 2. Check if the current control matches any of the initialization controls
        if self._check_initialization_controls():
            return True

        # 3. If none of the initialization controls were found, try to sign out and re-initialize
        return self._attempt_reinitialization(navigate_report_path, performance_report_path)

    def _is_in_agreement_window(self, current_control_level1_window_autoid, current_id):
        """Check if the application is in agreement window."""
        if current_control_level1_window_autoid == AGREEMENTWINDOW or current_id == AGREEMENTWINDOW:
            LOGGER_INFO(f"[initial][success] Webex app is in agreement window, [{current_control_level1_window_autoid}][{current_id}]", "YELLOW")
            return True
        return False

    def _check_initialization_controls(self):
        """Check if any of the initialization controls are accessible."""
        for control_name in INITIALIZATION_CONTROLS:
            control_name_meta, control_id_meta = control_datasets_loader.get_control_metadata_by_name(control_name)

            if control_name_meta is None or control_id_meta is None:
                LOGGER_DEBUG(f"Control '{control_name}' not found in metadata, trying next...", "YELLOW")
                continue

            LOGGER_INFO(f"Checking initialization control: {control_name}", "CYAN")

            ctrl_meta = {
                "name": control_name_meta,
                "id": control_id_meta,
                "test_case_step_description": f"check {control_name.lower()}"
            }

            control_visited, result = self.locale_processor.locate_control_handler_for_operator(
                ctrl_meta, locate_id_flag=True)

            if result:
                LOGGER_INFO(f"Webex app is initialized successfully with '{control_name}' control.", "GREEN")
                return True
            else:
                LOGGER_INFO(f"Control '{control_name}' not found or not accessible, trying next...", "YELLOW")

        return False

    def _attempt_reinitialization(self, navigate_report_path=None, performance_report_path=None):
        """Attempt to re-initialize the application by signing out."""
        LOGGER_ERROR("Webex app initialization failed. No initialization controls found.", "RED")
        LOGGER_ERROR("need to force sign out firstly to re-initialize the app", "RED")
        
        test_case = 'navigations/basic/sign_out'
        test_case_path = TEST_CASES_PATH / f"{test_case}.yaml"
        test_case_ui_path = self.workflow_loader.build_ui_path(test_case_path)

        result = self.control_operator.locate_control_by_ui_path(
            test_case, test_case_ui_path,
            navigate_report_path, performance_report_path,
        )
        
        if result:
            LOGGER_INFO("Webex app is re-initialized successfully.", "GREEN")
            return True
        else:
            LOGGER_ERROR("Webex app re-initialization failed. Please check the application state.", "RED")
            LOGGER_ERROR("Please sign out manually and try again.", "RED")
            return False

    def check_webex_app_initialization_if_needed(self, test_case_path_str, navigate_report_path=None, performance_report_path=None):
        """Check webex app initialization if not in web mode."""
        if self.platform == 'web':
            LOGGER_INFO("Running in web mode, Skip checking Webex app initialization...", "CYAN")
            return True
        else:
            return self.check_webex_app_initialization(test_case_path_str, navigate_report_path, performance_report_path)

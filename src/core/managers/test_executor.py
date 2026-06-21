"""
Test Executor for running individual test cases and test suites.

This module is responsible for:
- Executing individual test cases with proper error handling
- Managing test case pre/post conditions
- Coordinating test execution with timing and recording
"""

import platform as platform_module
from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING
from config.paths import TEST_CASES_PATH
from config.global_settings import settings

# Platform-specific imports
if platform_module.system() == "Windows":
    from core.windows.control_operator import ControlOperator
elif platform_module.system() == "Linux":
    from core.linux.control_operator import ControlOperator


class TestExecutor:
    """Executes test cases and manages execution flow."""

    def __init__(self, platform='windows'):
        self.platform = platform
        self.workflow_loader = WorkflowLoader()
        self.control_operator = ControlOperator()

    def execute_test_case(self, expanded_test_case, language='en_us', mode="suite", 
                         navigate_report_path=None, performance_report_path=None, 
                         stress_report_path=None, test_suite_path=None, check_points=None):
        """
        Execute a test case with pre/post conditions.
        
        Args:
            expanded_test_case (str): Test case name
            language (str): Language code
            mode (str): Execution mode ('suite', 'case', or 'batch')
            navigate_report_path (str): Path for navigation report
            performance_report_path (str): Path for performance report
            stress_report_path (str): Path for stress report (optional)
            test_suite_path (str): Path to test suite YAML file (optional)
            check_points (list): List of enabled check points from test suite (optional)
            
        Returns:
            bool: True if execution successful, False otherwise
        """
        expanded_test_cases = []

        test_case_path = TEST_CASES_PATH / f"{expanded_test_case}.yaml"
        pre_conditions = self.workflow_loader.get_test_cases_pre_conditions(test_case_path)
        post_conditions = self.workflow_loader.get_test_cases_post_conditions(test_case_path)

        # Get effective account with priority: test_suite > test_case > global_account
        # First, get accounts from all sources
        test_case_account = self.workflow_loader.get_test_case_account(test_case_path)
        test_suite_account = None
        if test_suite_path:
            test_suite_account = self.workflow_loader.get_test_suite_account(test_suite_path)
        global_account = settings.account
        
        # Determine which account to use based on priority
        if test_suite_account:
            main_test_case_account = test_suite_account
            LOGGER_INFO(f"Using test suite configured account: {main_test_case_account} (Priority 1: Test Suite)", "CYAN")
        elif test_case_account:
            main_test_case_account = test_case_account
            LOGGER_INFO(f"Using test case configured account: {main_test_case_account} (Priority 2: Test Case)", "CYAN")
        elif global_account:
            main_test_case_account = global_account
            LOGGER_INFO(f"Using global account setting: {main_test_case_account} (Priority 3: Global)", "CYAN")
        else:
            main_test_case_account = None
            LOGGER_INFO(f"No account configured, using default", "YELLOW")

        if mode == 'case' or mode == 'batch':
            expanded_test_cases = (pre_conditions or []) + [expanded_test_case] + (post_conditions or [])
        else:
            expanded_test_cases = [expanded_test_case]

        self._log_test_case_info(expanded_test_case, test_case_path, main_test_case_account, 
                                pre_conditions, post_conditions, mode, expanded_test_cases)

        result = True
        stopped_by_failure = False
        LOGGER_INFO(f"[test executor]Starting execution of test case(s): {expanded_test_cases}, Total test case: [{len(expanded_test_cases)}]", "CYAN")
        
        for current_test_case in expanded_test_cases:
            # Check if this is a post_condition and we were stopped by stop_on_failure
            is_post_condition = post_conditions and current_test_case in post_conditions
            
            # If stopped by failure and this is not a post_condition, skip it
            if stopped_by_failure and not is_post_condition:
                LOGGER_WARNING(f"[test executor]Skipping test case [{current_test_case}] due to stop_on_failure in previous step", "YELLOW")
                continue
            
            # If this is a post_condition and we were stopped, log it
            if stopped_by_failure and is_post_condition:
                LOGGER_INFO(f"[test executor]Executing post_condition [{current_test_case}] despite stop_on_failure", "CYAN")
            
            LOGGER_INFO(f"[test executor]Executing test case: {current_test_case}", "CYAN")
            step_result = self._execute_single_test_step(
                current_test_case, main_test_case_account, pre_conditions, post_conditions,
                language, navigate_report_path, performance_report_path, stress_report_path, test_suite_path, check_points
            )
            
            # Check if result is a tuple (result, stopped_by_failure)
            if isinstance(step_result, tuple):
                result, stopped_by_failure = step_result
                LOGGER_INFO(f"[test executor]Test case [{current_test_case}] executed with result: {result}, stopped_by_failure: {stopped_by_failure}", "GREEN" if result else "RED")
            else:
                result = step_result
                LOGGER_INFO(f"[test executor]Test case [{current_test_case}] executed with result: {result}", "GREEN" if result else "RED")
            
            # If stopped by failure and this is the main test case (not pre/post condition), stop main execution
            # but we'll continue to run post_conditions
            if stopped_by_failure and not is_post_condition and current_test_case == expanded_test_case:
                LOGGER_WARNING(f"[test executor]Main test case stopped by stop_on_failure. Will skip remaining steps but run post_conditions.", "YELLOW")
                # Continue loop to execute post_conditions

        return result

    def _log_test_case_info(self, expanded_test_case, test_case_path, main_test_case_account, 
                           pre_conditions, post_conditions, mode, expanded_test_cases):
        """Log test case execution information."""
        LOGGER_INFO(f"test_case_path: {test_case_path}, test_case: {expanded_test_case}", "GREEN")
        LOGGER_INFO(f"main_test_case_account: {main_test_case_account}", "CYAN")
        LOGGER_INFO(f"pre_conditions: {pre_conditions}", "YELLOW")
        LOGGER_INFO(f"post_conditions: {post_conditions}", "YELLOW")
        LOGGER_INFO(f"test mode: {mode}")
        LOGGER_INFO(f"expanded_test_cases: {expanded_test_cases}", "YELLOW")

    def _load_test_case_dataset(self, test_case_path, current_test_case):
        """
        Load custom dataset for the specific test case if defined.
        If no custom_dataset is specified, reload the default dataset.
        
        Args:
            test_case_path: Path to the test case YAML file
            current_test_case: Name of the current test case
        """
        import yaml
        from rs_sdk.utils.control_datasets_loader import load_control_datasets
        
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                test_case_config = yaml.safe_load(f)
            
            if test_case_config and 'test_case' in test_case_config:
                custom_dataset = test_case_config['test_case'].get('custom_dataset')
                
                if custom_dataset:
                    LOGGER_INFO(f"🔄 Test case '{current_test_case}' specifies custom_dataset: {custom_dataset}", "CYAN")
                    LOGGER_INFO(f"   Loading custom dataset...", "CYAN")
                    
                    load_result = load_control_datasets(
                        custom_dataset=custom_dataset, 
                        platform=self.platform, 
                        force_reload=True
                    )
                    
                    if load_result:
                        LOGGER_INFO(f"✅ Successfully loaded custom dataset: '{custom_dataset}' for test case '{current_test_case}'", "GREEN")
                    else:
                        LOGGER_INFO(f"⚠️  Failed to load custom dataset '{custom_dataset}', falling back to default", "YELLOW")
                        # Fallback to default dataset
                        load_control_datasets(platform=self.platform, force_reload=True)
                        LOGGER_INFO(f"✅ Loaded default dataset (1158 controls)", "GREEN")
                else:
                    # No custom_dataset specified - explicitly load default dataset
                    LOGGER_INFO(f"🔄 Test case '{current_test_case}' uses default dataset (no custom_dataset specified)", "CYAN")
                    LOGGER_INFO(f"   Loading default dataset...", "CYAN")
                    load_control_datasets(platform=self.platform, force_reload=True)
                    LOGGER_INFO(f"✅ Successfully loaded default dataset (1158 controls) for test case '{current_test_case}'", "GREEN")
        except Exception as e:
            LOGGER_INFO(f"⚠️  Failed to check custom_dataset for '{current_test_case}': {str(e)}", "YELLOW")
            # On error, try to load default dataset
            try:
                load_control_datasets(platform=self.platform, force_reload=True)
                LOGGER_INFO(f"✅ Loaded default dataset as fallback", "GREEN")
            except:
                pass

    def _execute_single_test_step(self, current_test_case, main_test_case_account, 
                                 pre_conditions, post_conditions, language,
                                 navigate_report_path, performance_report_path, stress_report_path, test_suite_path=None, check_points=None):
        """Execute a single test step within a test case."""
        test_case_path = TEST_CASES_PATH / f"{current_test_case}.yaml"

        # Load custom dataset for this specific test case if defined
        self._load_test_case_dataset(test_case_path, current_test_case)

        # Check if current case explicitly sets check_points to empty list []
        # If so, use it to disable all checkpoints (None means inherit/default)
        import yaml
        effective_check_points = check_points  # Default: use inherited check_points
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                test_case_config = yaml.safe_load(f)
            if test_case_config and 'test_case' in test_case_config:
                if 'check_points' in test_case_config['test_case']:
                    current_case_check_points = test_case_config['test_case']['check_points']
                    # Override if explicitly set to empty list [] or null
                    if current_case_check_points is not None and len(current_case_check_points) == 0:
                        effective_check_points = []  # Empty list = no checkpoints
                        LOGGER_INFO(f"[test executor] Case '{current_test_case}' has check_points: [], disabling all checkpoints", "CYAN")
                    elif current_case_check_points is None:
                        effective_check_points = []  # null also means no checkpoints
                        LOGGER_INFO(f"[test executor] Case '{current_test_case}' has check_points: null, disabling all checkpoints", "CYAN")
        except Exception as e:
            LOGGER_ERROR(f"[test executor] Failed to read check_points from {test_case_path}: {e}", "YELLOW")

        # Use build_ui_path_with_account with test_suite_path for account resolution
        # Priority: main_test_case_account (override) > test_case account > test_suite account
        test_case_ui_path = self.workflow_loader.build_ui_path_with_account(
            test_case_path, main_test_case_account, test_suite_path
        )

        test_case_execution_count = self.workflow_loader.get_test_case_execution_count(test_case_path)
        test_case_execution_duration = self.workflow_loader.get_test_case_execution_duration(test_case_path)
        
        # Get continue_on_error configuration
        continue_on_error = self.workflow_loader.get_test_case_continue_on_error(test_case_path)
        
        LOGGER_INFO(f"Test case: [{current_test_case}], path [{test_case_path}] "
                   f"test_case_execution_count: [{test_case_execution_count}], "
                   f"test_case_execution_duration: [{test_case_execution_duration}], "
                   f"continue_on_error: [{continue_on_error}]", "GREEN")
        LOGGER_INFO(f"Test case ui path [{test_case_ui_path}]", "YELLOW")

        result = True
        stopped_by_failure = False
        execution_results = []
        
        for i in range(test_case_execution_count):
            try:
                exec_result = self.control_operator.locate_control_by_ui_path(
                    current_test_case, test_case_ui_path,
                    navigate_report_path, performance_report_path, stress_report_path,
                    test_case_execution_duration=test_case_execution_duration,
                    test_case_execution_count=i+1,
                    platform=self.platform,
                    language=language,
                    test_case_path=test_case_path,
                    check_points=effective_check_points  # Pass check_points to control operator
                )
                
                # Check if result is a tuple (result, stopped_by_failure)
                if isinstance(exec_result, tuple):
                    result, stopped_by_failure = exec_result
                else:
                    result = exec_result
                    
                execution_results.append(result)
                LOGGER_INFO(f"[test executor] Round {i+1}/{test_case_execution_count} result: {result}", "CYAN")
            except Exception as e:
                LOGGER_ERROR(f"[test executor] Round {i+1}/{test_case_execution_count} encountered error: {str(e)}", "RED")
                execution_results.append(False)
                if continue_on_error:
                    LOGGER_WARNING(f"[test executor] Continue on error enabled, skipping this round and proceeding to next", "YELLOW")
                    # Continue to the next iteration
                    continue
                else:
                    LOGGER_ERROR(f"[test executor] Continue on error disabled, stopping execution", "RED")
                    break
        
        final_result = all(execution_results)
        LOGGER_INFO(f"[test executor] All {test_case_execution_count} rounds completed. Final result: {final_result} (Passed: {sum(execution_results)}/{test_case_execution_count})", "CYAN")
        
        # Return tuple if stopped_by_failure, otherwise just the result
        if stopped_by_failure:
            return (final_result, stopped_by_failure)
        return final_result

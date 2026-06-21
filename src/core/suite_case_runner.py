"""
suite_case_runner.py

Main entry point for running Webex automation test suites and test cases.

This script coordinates the execution of test suites and individual test cases by
delegating responsibilities to specialized managers:
- AppManager: Handles application lifecycle and state
- InitializationChecker: Verifies application readiness
- TestDataProcessor: Prepares test execution data
- TestExecutor: Executes test cases
- TestRecorder: Records and tracks results

To run test cases, execute:
    python src/suite_case_runner.py

This refactored version follows the single responsibility principle.
"""

import time
import platform
from rs_sdk.utils.control_db import ControlDB
from rs_sdk.utils.workflow_loader import WorkflowLoader

# Platform-specific import for event listener
if platform.system() == "Windows":
    from rs_sdk.utils.event_listener import FocusListener
elif platform.system() == "Linux":
    from rs_sdk.platform.linux import FocusListener
else:
    # Default fallback for unsupported platforms
    from rs_sdk.utils.event_listener import FocusListener
from rs_sdk.utils import report_handler
from rs_sdk.utils.control_datasets_loader import load_control_datasets
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG, LOGGER_WARNING
from core.explorer_base import ExplorerBase

# Import the new manager classes
from core.managers.app_manager import AppManager
from core.managers.initialization_checker import InitializationChecker
from core.managers.test_data_processor import TestDataProcessor
from core.managers.test_executor import TestExecutor
from core.managers.test_recorder import TestRecorder

class SuiteCaseRunner:
    """
    Main controller for running Webex automation test suites and test cases.
    
    This class coordinates the execution flow by delegating responsibilities
    to specialized manager classes.
    """
    
    def __init__(self, platform='windows'):
        self.platform = platform
        self.navigate_report_path = None
        self.performance_report_path = None
        self.stress_report_path = None
        self.check_points = None  # Store check_points from test suite/case
        self.sr_enabled_cases = None  # Test case names that have Screen Reader in check_points
        self.sr_prompt_path = None  # SR prompt path from test case YAML
        
        # Initialize manager components
        self.app_manager = AppManager(platform)
        self.initialization_checker = InitializationChecker(platform)
        self.test_data_processor = TestDataProcessor()
        self.test_executor = TestExecutor(platform)
        self.test_recorder = TestRecorder()
        
        # Initialize other components
        self.explorer = ExplorerBase()
        self.workflow_loader = WorkflowLoader()

    def run(self, test_suites_or_cases, mode="suite",progress_callback=None):
        """
        Run test suites, individual test cases, or test batches.
        
        Args:
            test_suites_or_cases (str or list): Test suite names, test case names, or test batch names to run
            mode (str): "suite" for test suite mode, "case" for individual test case mode, "batch" for test batch mode
            
        Returns:
            tuple: (test_results, report_path) when mode="case" or mode="batch", 
                   (navigate_report_path, performance_report_path) when mode="suite"
        """
        LOGGER_INFO(f"Start Running {test_suites_or_cases} in {mode} mode with platform: {self.platform}", "CYAN")
        
        # Initialize focus listener
        listener = FocusListener()
        listener.stop()
        listener.start()
        time.sleep(1)

        if isinstance(test_suites_or_cases, str):
            test_suites_or_cases = [test_suites_or_cases]

        # Extract test case execution data based on mode
        test_execution_data = self.test_data_processor.prepare_test_execution_data(test_suites_or_cases, mode)

        if mode == "case" or mode == "batch":
            return self._run_test_cases(test_execution_data, mode)
        else:
            return self._run_test_suites(test_execution_data, mode, progress_callback=progress_callback)

    def _run_test_cases(self, test_execution_data, mode):
        """Run individual test cases or batch test cases."""
        if mode == "batch":
            LOGGER_DEBUG(f"Running in test batch mode with cases: {[data['test_case_name'] for data in test_execution_data]}", "CYAN")
        else:
            LOGGER_DEBUG(f"Running in test case mode with cases: {[data['test_case_name'] for data in test_execution_data]}", "CYAN")
        
        test_results = []
        
        # Determine effective check_points for post-execution analysis.
        # For batch mode: union of all cases' check_points.
        #   - If any case has check_points=None (not specified), treat as "all enabled" → None.
        #   - Otherwise take the union so post-analysis runs only for requested checks.
        # For case mode: use the single case's check_points directly.
        if test_execution_data:
            if mode == "batch":
                all_check_points: set = set()
                any_none = False
                for _cd in test_execution_data:
                    cp = _cd.get('check_points')
                    if cp is None:
                        any_none = True
                    else:
                        all_check_points.update(cp)
                if any_none:
                    self.check_points = None  # At least one case has no restriction → all enabled
                else:
                    self.check_points = list(all_check_points) if all_check_points else []
                LOGGER_INFO(f"Batch effective check_points (union): {self.check_points}", "CYAN")
                
                # Collect test case names that have Screen Reader enabled (for per-case SR filtering)
                self.sr_enabled_cases = []
                for _cd in test_execution_data:
                    cp = _cd.get('check_points')
                    if cp is None or 'Screen Reader' in cp:
                        self.sr_enabled_cases.append(_cd.get('test_case_path_str') or _cd.get('test_case_name'))
                LOGGER_INFO(f"Batch SR-enabled cases: {self.sr_enabled_cases}", "CYAN")
            else:
                self.check_points = test_execution_data[0].get('check_points')
                self.sr_prompt_path = test_execution_data[0].get('sr_prompt')
        
        # Load custom dataset if specified in first test case
        if test_execution_data and test_execution_data[0].get('custom_dataset'):
            custom_dataset = test_execution_data[0].get('custom_dataset')
            try:
                load_result = load_control_datasets(custom_dataset=custom_dataset, platform=self.platform, force_reload=True)
                if load_result:
                    LOGGER_INFO(f"Successfully loaded custom dataset: '{custom_dataset}'", "GREEN")
                else:
                    LOGGER_INFO(f"Failed to load custom dataset '{custom_dataset}', using default dataset", "YELLOW")
            except Exception as e:
                LOGGER_ERROR(f"Error loading custom dataset '{custom_dataset}': {str(e)}, using default dataset", "YELLOW")

        # Execute all test cases
        for i, case_data in enumerate(test_execution_data):
            # Priority-based initialization logic:
            # For batch mode: Each test case is independent, so each needs its own initialization
            # For case mode: First test case (i==0): Use YAML configuration, subsequent cases: Skip initialization
            if mode == "batch":
                need_initialization = case_data.get('need_initialization', True)
                LOGGER_INFO(f"Batch test case {case_data['test_case_name']}: need_initialization={need_initialization} (independent execution)", "CYAN")
            elif i == 0:
                need_initialization = case_data.get('need_initialization', True)
                LOGGER_INFO(f"First test case {case_data['test_case_name']}: need_initialization={need_initialization} (from YAML config)", "CYAN")
            else:
                need_initialization = False  # Subsequent cases skip initialization
                yaml_config = case_data.get('need_initialization', True)
                LOGGER_INFO(f"Subsequent test case {case_data['test_case_name']}: need_initialization={need_initialization} (overridden, YAML was: {yaml_config})", "CYAN")
                
            result = self._execute_single_test_case(case_data, mode, need_initialization)
            test_results.append((case_data['test_case_name'], result))
            LOGGER_INFO(f"Test case [{case_data['test_case_name']}] executed with result: {result}", "GREEN" if result else "RED")

        self.test_recorder.log_test_results(test_results, self.navigate_report_path)
        return self.navigate_report_path, self.performance_report_path, self.stress_report_path, self.check_points, self.sr_enabled_cases, self.sr_prompt_path

    def _run_test_suites(self, test_execution_data, mode, progress_callback=None):
        """Run test suites."""
        LOGGER_INFO(f"Running in test suite mode with suites: {[data['test_suite'] for data in test_execution_data]}, count: {len(test_execution_data)}", "CYAN")

        # Execute all test suites
        for suite_data in test_execution_data:
            self._execute_test_suite(suite_data, mode, progress_callback=progress_callback)

        LOGGER_INFO("All test suites executed successfully.", "GREEN")
        return self.navigate_report_path, self.performance_report_path, self.stress_report_path, self.check_points, self.sr_enabled_cases, self.sr_prompt_path

    def _execute_single_test_case(self, case_data, mode, need_initialization=True):
        """Execute a single test case with common error handling and recording."""
        test_case_name = case_data['test_case_name']
        test_case_path_str = case_data['test_case_path_str']
        language = case_data['language']
        test_suite_path = case_data.get('test_suite_path', None)

        # Check if this test case should execute on agent
        if case_data.get('execute_on_agent'):
            LOGGER_INFO(f"Executing test case on agent: {test_case_name}", "CYAN")
            return self._execute_on_agent(case_data)

        # Normal local execution continues below...
        # Always ensure report paths are initialized
        if self.navigate_report_path is None or self.performance_report_path is None:
            if mode == "case" or mode == "batch":
                self.navigate_report_path, self.performance_report_path, self.stress_report_path = self.app_manager.initialize_reports(test_case_name, language)
            else:
                # For suite mode, we get the test suite name from case_data
                test_suite_name = case_data.get('test_suite_name', 'default_suite')
                self.navigate_report_path, self.performance_report_path, self.stress_report_path = self.app_manager.initialize_reports(test_suite_name, language)

        # Initialize app and focus if needed
        # if need_initialization:
        #     if mode == "case" or mode == "batch":
        #         self.app_manager.launch_and_prepare(test_suite_case=test_case_name, mode=mode)
        #     else:
        #         # For suite mode, we get the test suite name from case_data
        #         test_suite_name = case_data.get('test_suite_name', 'default_suite')
        #         self.app_manager.launch_and_prepare(language=language, test_suite_case=test_suite_name)
            
            # self.app_manager.focus_webex_app_if_needed()

        LOGGER_DEBUG(f"Executing test case: {test_case_name} from path: {test_case_path_str}", "GREEN")

        # Check webex app initialization based on mode and initialization requirement
        # if mode == "case" or mode == "batch" or (mode == "suite" and need_initialization):
        #     if not self.initialization_checker.check_webex_app_initialization_if_needed(
        #         test_case_path_str, self.navigate_report_path, self.performance_report_path):
        #         LOGGER_ERROR("Webex app initialization failed. Exiting the test run.", "RED")
        #         return False
        # else:
        #     LOGGER_INFO("Skipping Webex app initialization check for subsequent test cases in suite mode", "CYAN")

        # Write report title for this test case
        report_handler.write_navigate_report_title(self.navigate_report_path, test_case_path_str)

        # Execute the test case with timing and error handling
        return self.test_recorder.execute_test_case_with_recording(
            self.test_executor, test_case_name, test_case_path_str,
            language, mode, self.navigate_report_path, self.performance_report_path, 
            self.stress_report_path, test_suite_path, check_points=case_data.get('check_points')
        )
    
    def _execute_on_agent(self, case_data):
        """Execute test case on remote agent via API call."""
        from core.strategies.api_action_strategy import ApiActionStrategy
        
        test_case_name = case_data['test_case_name']
        agent_node = case_data['agent_node']
        platform = case_data['agent_platform']
        params = case_data['agent_parameters']
        agent_base_url = case_data.get('agent_base_url')  # present when agent_node was "auto"
        
        LOGGER_INFO(f"Executing on agent | Case: {test_case_name} | Node: {agent_node} | Platform: {platform}", "GREEN")
        LOGGER_INFO(f"Agent parameters: {params}", "CYAN")
        
        try:
            api_action = {
                "type": "api",
                "value": "run_agent_api",
                "agent_node": agent_node,
                "parameters": {
                    "test_case_name": test_case_name,
                    "platform": platform,
                    "mode": "case",
                    **params
                }
            }
            if agent_base_url:
                api_action["agent_base_url"] = agent_base_url
            
            api_strategy = ApiActionStrategy()
            result = api_strategy.execute(api_action, None, {})
            
            LOGGER_INFO(f"Agent execution result: {result}", "GREEN" if "ERROR" not in str(result) else "RED")
            
            success = "ERROR" not in str(result) and result is not None
            return success
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to execute on agent: {str(e)}", "RED")
            return False

    def _execute_test_suite(self, suite_data, mode, progress_callback=None):
        """Execute a test suite."""
        test_suite = suite_data['test_suite']
        test_suite_path = suite_data['test_suite_path']
        languages = suite_data['languages']
        check_points = suite_data['check_points']
        self.check_points = check_points  # Store check_points for return
        
        # Load control datasets based on test suite's project, platform, and custom_dataset configuration
        try:
            project = self.workflow_loader.get_test_suite_project(test_suite_path)
            platform = self.workflow_loader.get_test_suite_platform(test_suite_path)
            
            # Try to get custom_dataset from test suite configuration
            custom_dataset = None
            try:
                import yaml
                with open(test_suite_path, 'r', encoding='utf-8') as f:
                    suite_config = yaml.safe_load(f)
                    if suite_config and 'test_suite' in suite_config:
                        custom_dataset = suite_config['test_suite'].get('custom_dataset')
            except Exception as e:
                LOGGER_ERROR(f"No custom_dataset in test suite config: {str(e)}")
            
            # Dynamically load the appropriate dataset
            # Priority: custom_dataset > project+platform > default
            if custom_dataset or project or platform != 'windows':
                load_result = load_control_datasets(
                    project=project, 
                    platform=platform, 
                    custom_dataset=custom_dataset,
                    force_reload=True
                )
                if load_result:
                    if custom_dataset:
                        LOGGER_INFO(f"Successfully loaded custom dataset: '{custom_dataset}'", "GREEN")
                    else:
                        LOGGER_INFO(f"Successfully loaded control dataset for project='{project}', platform='{platform}'", "GREEN")
                else:
                    LOGGER_INFO(f"Failed to load specific dataset, using default dataset", "YELLOW")
        except Exception as e:
            LOGGER_ERROR(f"Error loading control datasets: {str(e)}, using default dataset", "YELLOW")

        for language in languages:
            try:
                test_cases = self.workflow_loader.get_test_cases_from_suite(test_suite_path)
                LOGGER_INFO(f"Test Suite: {test_suite}, Language: {language}, Test Cases: {test_cases}, count: {len(test_cases)}", "CYAN")
            except Exception as e:
                LOGGER_ERROR(f"Failed to get test cases from suite '{test_suite}': {str(e)}", "RED")
                continue

            for i, test_case_item in enumerate(test_cases):
                test_case_name, agent_node, params = self.workflow_loader.parse_parameterized_test_case(test_case_item)
                
                # Create case data for unified execution
                case_data = self.test_data_processor.create_case_data_for_suite(
                    test_case_name, language, test_suite, test_suite_path, check_points=check_points
                )
                
                if agent_node:
                    LOGGER_INFO(f"Will execute on agent | test case: {test_case_name} | agent_node: {agent_node} | parameters: {params}", "CYAN")
                    platform = self.workflow_loader.get_test_suite_platform(test_suite_path)
                    case_data['execute_on_agent'] = True
                    case_data['agent_node'] = agent_node
                    case_data['agent_platform'] = platform
                    case_data['agent_parameters'] = params

                    if agent_node == "auto" or agent_node.startswith("auto_"):
                        group = agent_node[5:] if agent_node.startswith("auto_") else "default"
                        tag = group if group != "default" else None
                        if not hasattr(self, '_auto_agent_urls'):
                            self._auto_agent_urls = {}
                        if group not in self._auto_agent_urls:
                            from core.managers.agent_node_manager import agent_node_manager
                            url = agent_node_manager.discover_dynamic_agent(tag=tag)
                            if url is None:
                                LOGGER_WARNING(f"No live agent found for group '{group}', falling back to localhost", "YELLOW")
                                url = "http://localhost:9909"
                            self._auto_agent_urls[group] = url
                            LOGGER_INFO(f"Sticky auto agent '{group}' → {url}", "GREEN")
                        case_data['agent_base_url'] = self._auto_agent_urls[group]

                # Priority-based initialization logic:
                # 1. First test case (i==0): Use YAML configuration  
                # 2. Subsequent test cases: Skip initialization (reuse environment)
                if i == 0:
                    need_initialization = case_data.get('need_initialization', True)
                    LOGGER_INFO(f"First test case in suite {test_suite}, case {test_case_name}: need_initialization={need_initialization} (from YAML config)", "CYAN")
                else:
                    need_initialization = False  # Subsequent cases skip initialization
                    yaml_config = case_data.get('need_initialization', True)
                    LOGGER_INFO(f"Subsequent test case in suite {test_suite}, case {test_case_name}: need_initialization={need_initialization} (overridden, YAML was: {yaml_config})", "CYAN")
                
                result = self._execute_single_test_case(case_data, mode, need_initialization)
                if result:
                    LOGGER_INFO(f"Test case [{test_case_name}] executed successfully.", "GREEN")
                    if progress_callback:
                        progress_callback({
                            "step": test_case_name,
                            "status": "completed",
                            "message": f"Test case [{test_case_name}] executed successfully."
                        })
                else:
                    if progress_callback:
                        progress_callback({
                            "step": test_case_name,
                            "status": "failed",
                             "message": f"Test case [{test_case_name}] execution failed."
                        })
                    LOGGER_INFO(f"Test case [{test_case_name}] execution failed.", "RED")                 

                if result:
                    LOGGER_INFO(f"Test case [{test_case_name}] executed successfully.", "GREEN")
                else:
                    LOGGER_INFO(f"Test case [{test_case_name}] execution failed.", "RED")
                    LOGGER_INFO(f"Start Running the next test case...")
                    # if mode == "suite":
                    #     return  # Exit on failure in suite mode

            if check_points and 'acc' in check_points:
                from common.finalizer import output_runner
                self.explorer.explorer_base()
                output_runner.build_output()
                control_db = ControlDB()
                control_db.upload_local_control_info_to_database()

            
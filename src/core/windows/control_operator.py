"""
Control Operator Module - Main UI Control Automation System

EXECUTION FLOW:
1. ControlOperator.__init__() - Initialize all components and processors
2. locate_control_by_ui_path() - Main entry point for control location and action execution
   └── 2.1 _initialize_execution_context() - Setup execution environment
   └── 2.2 For each control in UI path:
       ├── 2.2.1 _should_process_control() - Check platform compatibility
       └── 2.2.2 _process_single_control() - Execute complete control flow:
           ├── a. ControlMetadataProcessor.parse_locate_target() - Parse locate target
           ├── b. ControlLocatorProcessor.locate_control() - Find and focus on control with simple retry mechanism
           ├── c. ControlActionProcessor.execute_control_action() - Execute action using strategy pattern
           ├── d. ControlVerificationProcessor.perform_ai_check() - AI-based verification (if needed)
           ├── e. ControlVerificationProcessor.verify_expected_state() - Validate expected state
           ├── f. Focus Ring validation (immediate, per-control)
           ├── g. Screen Reader placeholder (deferred, post-suite analysis)
           └── h. ReportProcessor.generate_step_reports() - Generate navigation and performance reports
   └── 2.3 ReportProcessor.handle_batch_performance_reports() - Generate batch reports (if needed)

SCREEN READER ANALYSIS WORKFLOW:
- Unlike Focus Ring (immediate per-control validation), Screen Reader uses deferred analysis
- During execution: screen_reader_result remains "N/A" in TestCaseNavigateReport
- After suite completion: 
  1. model_handler.handle_screen_reader_analysis() analyzes all collected data
  2. Results stored in ScreenReaderReport table
  3. sync_screen_reader_to_navigate_report() updates TestCaseNavigateReport.screen_reader_result
- This batch approach provides comprehensive accessibility analysis across the entire suite

FLEXIBLE RETRY MECHANISM:
- Configurable retry attempts (default: 3) and delay (default: 1 second)
- Multiple retry strategies with different recovery actions:
  * stale_data: FocusListener reset for identical controls
  * corrupted_data: FocusListener reset for ?? characters
  * empty_controls: ESC key press for empty control lists
- Strategy-specific actions: different recovery methods for different failure conditions
- Configurable strategy enable/disable per strategy type

ARCHITECTURE PATTERN:
- Strategy Pattern: Flexible action execution strategies (ActionStrategyManager)
- Processor Pattern: Specialized processors for separation of concerns
- Data Classes: Type-safe data structures for all operations
"""

import os
from typing import Dict, Any, Optional
from dataclasses import asdict
# Import modularized components
from core.windows.data_models import (
    ExecutionContext, ControlStepResult
)
from core.windows.data_models.expectation_result import ExpectationResult
from core.windows.strategies import ActionStrategyManager
from core.windows.processors import (
    ControlMetadataProcessor, ControlLocatorProcessor, ControlActionProcessor,
    ControlVerificationProcessor, ReportProcessor
)

# Import required handlers and dependencies
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils import control_datasets_loader
from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.utils.control_handler import ControlHandler
from core.windows.controls.control_navigator import ControlNavigator
from rs_sdk.utils.process_handler import ProcessHandler
from rs_sdk.utils.model_handler import ModelHandler
from core.managers.report_manager import ReportManager
from rs_sdk.utils.control_recorder import ControlRecorder
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
from rs_sdk.utils.workflow_loader import WorkflowLoader



class ControlOperator:
    """Main control operator class - orchestrates the complete UI automation workflow"""
    
    def __init__(self):
        # Initialize core components
        self.current_control = ControlFactory().create_control()
        self.control_handler = ControlHandler()
        self.control_navigator = ControlNavigator()
        self.process_handler = ProcessHandler()
        self.model_handler = ModelHandler()
        self.test_case_db_handler = TestCaseDBHandler()
        self.report_manager = ReportManager(self.test_case_db_handler)
        
        # Initialize strategy manager
        self.action_strategy_manager = ActionStrategyManager(self.control_handler)
        
        # Initialize processors
        self._initialize_processors()

        # Register strategies that depend on processors (injected after init)
        from core.windows.strategies.acc_sequence_action_strategy import AccSequenceActionStrategy
        self.action_strategy_manager.register_strategy(
            'acc_sequence', AccSequenceActionStrategy(self.control_navigator)
        )

    def _initialize_processors(self):
        """Initialize all processors with their dependencies"""
        # Metadata processor
        self.metadata_processor = ControlMetadataProcessor()
        
        # Control locator processor
        self.control_locator = ControlLocatorProcessor(self.control_navigator, self.metadata_processor)
        
        # Action execution processor
        self.control_recorder = ControlRecorder()  # Initialize recorder here
        self.action_processor = ControlActionProcessor(
            self.action_strategy_manager,
            self.process_handler,
            self.control_recorder,
            self.control_handler  # Pass control_handler for UI response processor
        )
        
        # Verification processor
        self.verification_processor = ControlVerificationProcessor(
            self.model_handler,
            self.current_control
        )
        
        # Report processor
        self.report_processor = ReportProcessor(self.report_manager)

    def locate_control_by_ui_path(self, test_case, control_ui_path, navigate_report_path=None, performance_report_path=None, stress_report_path=None, test_case_execution_duration=1, test_case_execution_count=1, locate_id_flag=True, platform='windows', language='en_us', test_case_path=None, check_points=None):
        """
        Main method: Locate controls by UI path and execute complete automation workflow
        
        Args:
            test_case: Test case identifier
            control_ui_path: List of control definitions to process
            navigate_report_path: Path for navigation report output
            performance_report_path: Path for performance report output
            test_case_execution_duration: Duration of test execution
            test_case_execution_count: Number of times to execute
            locate_id_flag: Whether to use ID-based location
            platform: Target platform (windows/mac)
            language: Target language (en_us/zh_cn)
            test_case_path: Direct path to test case YAML file (optional, for intelligent backtrack)
            check_points: List of enabled check points from test suite (e.g., ['Performance', 'Focus Ring'])
        
        Returns:
            bool: Overall success status of control operations
        """
        # Initialize execution context
        execution_context = self._initialize_execution_context(
            test_case, test_case_execution_duration, test_case_execution_count, check_points
        )
        
        # Set platform for verification processor (for metadata lookup)
        self.verification_processor.set_platform(platform)
        LOGGER_DEBUG(f"[locate][ui_path][platform] Set verification platform to: {platform}", "CYAN")
        
        # Extract control names for intelligent retry mechanism
        control_names_sequence = [ctrl.get('name', '') for ctrl in control_ui_path if isinstance(ctrl, dict) and ctrl.get('name')]
        if control_names_sequence:
            LOGGER_INFO(f"[locate][ui_path][sequence] Setting control sequence for intelligent backtrack: {control_names_sequence}", "CYAN")
            self.control_locator.set_control_name_sequence(control_names_sequence)
            LOGGER_INFO(f"[locate][ui_path][sequence] Control sequence set successfully with {len(control_names_sequence)} steps", "GREEN")
        else:
            LOGGER_WARNING(f"[locate][ui_path][sequence] No valid control names found for sequence setup", "YELLOW")
        
        # Configure retry mechanism and record traversal based on test case configuration
        LOGGER_INFO(f"[locate][ui_path][test_case_path: {test_case_path}]", "CYAN")
        if test_case_path:
            try:
                # Read retry_enabled configuration from test case YAML
                workflow_loader = WorkflowLoader()
                retry_enabled = workflow_loader.get_test_case_retry_enabled(test_case_path)
                
                # Set retry configuration in control locator
                self.control_locator.set_enable_retry(retry_enabled)
                
                if retry_enabled:
                    LOGGER_INFO(f"[locate][ui_path][retry] Retry mechanism ENABLED for test case", "GREEN")
                else:
                    LOGGER_INFO(f"[locate][ui_path][retry] Retry mechanism DISABLED for test case validation", "YELLOW")
                
                # Read record_traversal configuration from test case YAML
                record_traversal = workflow_loader.get_test_case_record_traversal(test_case_path)
                
                # Set record traversal configuration in control locator
                self.control_locator.set_record_traversal(record_traversal)
                
                if record_traversal:
                    LOGGER_INFO(f"[locate][ui_path][record] Control traversal recording ENABLED", "GREEN")
                else:
                    LOGGER_INFO(f"[locate][ui_path][record] Control traversal recording DISABLED", "YELLOW")
            except Exception as e:
                LOGGER_WARNING(f"[locate][ui_path][config] Failed to read test case config, using defaults (retry enabled, record disabled): {e}", "YELLOW")
                self.control_locator.set_enable_retry(True)
                self.control_locator.set_record_traversal(False)
        else:
            # Default: retry enabled, record disabled (test validation mode)
            LOGGER_DEBUG(f"[locate][ui_path][config] No test_case_path, using defaults (retry enabled, record disabled)", "CYAN")
            self.control_locator.set_enable_retry(True)
            self.control_locator.set_record_traversal(False)
        
        # Try to build and set control_name_ui_path for intelligent backtrack
        if test_case_path:
            try:            
                # Create a workflow loader to build control name UI path
                workflow_loader = WorkflowLoader()
                
                # Build control name UI path
                control_name_ui_path_result = workflow_loader.build_control_name_ui_path(
                    test_case_path=test_case_path, 
                    platform=platform
                )
                
                if control_name_ui_path_result:
                    LOGGER_DEBUG(f"[operator][ui_path] Raw control_name_ui_path_result: {control_name_ui_path_result}", "CYAN")
                    # Extract actual control names from the result
                    control_name_ui_path = []
                    for i, step in enumerate(control_name_ui_path_result):
                        LOGGER_DEBUG(f"[operator][ui_path] Processing step {i}: {step}", "CYAN")
                        if isinstance(step, dict):
                            # First try to get control_name from control_metadata (correct structure)
                            control_name = ''
                            if 'control_metadata' in step:
                                control_name = step['control_metadata'].get('control_name', '')
                                LOGGER_DEBUG(f"[operator][ui_path] Step {i} control_name from control_metadata: '{control_name}'", "CYAN")
                            else:
                                # Fallback: try to get control_name directly from step
                                control_name = step.get('control_name', '')
                                LOGGER_DEBUG(f"[operator][ui_path] Step {i} control_name from step: '{control_name}'", "CYAN")
                            
                            if control_name:
                                # Keep original control_name for accurate intersection analysis with traverse_all_controls
                                control_name_ui_path.append(control_name)
                                LOGGER_DEBUG(f"[operator][ui_path] Added original control name: '{control_name}'", "CYAN")
                            else:
                                LOGGER_DEBUG(f"[operator][ui_path] Step {i} has no control_name field", "YELLOW")
                        else:
                            LOGGER_DEBUG(f"[operator][ui_path] Step {i} is not a dict: {type(step)}", "YELLOW")
                    
                    if control_name_ui_path:
                        LOGGER_INFO(f"[operator][ui_path] Setting control name UI path for intelligent backtrack: {control_name_ui_path}", "CYAN")
                        self.control_locator.set_control_name_ui_path(control_name_ui_path)
                        LOGGER_INFO(f"[operator][ui_path] Control name UI path set successfully with {len(control_name_ui_path)} UI controls", "GREEN")
                    else:
                        LOGGER_WARNING(f"[operator][ui_path] No valid control names found in UI path", "YELLOW")
                        LOGGER_DEBUG(f"[operator][ui_path] Total steps processed: {len(control_name_ui_path_result) if control_name_ui_path_result else 0}", "YELLOW")
                else:
                    LOGGER_WARNING(f"[operator][ui_path] Failed to build control name UI path from {test_case_path}", "YELLOW")
                    
            except Exception as e:
                LOGGER_WARNING(f"[operator][ui_path] Failed to set control name UI path: {e}", "YELLOW")
                LOGGER_DEBUG(f"[operator][ui_path] Will use fallback control sequence for intelligent backtrack", "CYAN")
        else:
            LOGGER_DEBUG(f"[operator][ui_path] No test_case_path provided, skipping intelligent backtrack UI path setup", "CYAN")
        
        result = False
        
        # Process each control
        overall_success = True  # Track overall success but continue processing all steps
        stopped_by_failure = False  # Track if execution was stopped by stop_on_failure
        
        # Use a mutable list so ai_observe can inject sub-steps at runtime
        steps_queue = list(control_ui_path)
        step_idx = 0

        while step_idx < len(steps_queue):
            ctrl = steps_queue[step_idx]

            if not self._should_process_control(ctrl, platform):
                step_idx += 1
                continue

            # ── ai_observe: take screenshot ask AI inject case_a or case_b steps ──
            if isinstance(ctrl, dict) and 'ai_observe' in ctrl:
                branch_steps = self._handle_ai_observe(ctrl, execution_context, navigate_report_path)
                if branch_steps:
                    # Insert chosen sub-steps immediately after the current ai_observe entry
                    steps_queue[step_idx + 1:step_idx + 1] = branch_steps
                    LOGGER_INFO(f"[operator][ai_observe] Injected {len(branch_steps)} branch steps at position {step_idx + 1}", "GREEN")
                step_idx += 1
                continue

            # Set current step index for intelligent retry
            self.control_locator.set_current_step_index(step_idx)
            
            step_result = self._process_single_control(
                ctrl, step_idx, execution_context, platform, language, 
                navigate_report_path, performance_report_path, stress_report_path, locate_id_flag
            )
            
            # Track individual step failures but continue processing
            is_optional = ctrl.get('optional', False)
            stop_on_failure = ctrl.get('stop_on_failure', True)  # Default: stop on failure (changed from False)
            stop_on_ai_check_failure = ctrl.get('stop_on_ai_check_failure', False)  # Default: do not stop on AI check failure
            
            # Check if AI check failed and stop_on_ai_check_failure is enabled
            if step_result.ai_check_failed and stop_on_ai_check_failure and not is_optional:
                LOGGER_ERROR(f"[operator][stop_on_ai_check_failure] Step {step_idx} '{ctrl.get('name', 'unknown')}' AI check failed. Stopping execution of remaining steps (stop_on_ai_check_failure=true).", "RED")
                overall_success = False
                stopped_by_failure = True
                break  # Exit the loop immediately
            
            if not step_result.result and not is_optional:
                LOGGER_WARNING(f"[operator][step][failed] Non-optional step {step_idx} '{ctrl.get('name', 'unknown')}' failed, marking overall test as failed", "RED")
                overall_success = False
                
                # Check if this step has stop_on_failure enabled
                if stop_on_failure:
                    LOGGER_ERROR(f"[operator][stop_on_failure] Step {step_idx} '{ctrl.get('name', 'unknown')}' failed. Stopping execution of remaining steps (stop_on_failure=true by default).", "RED")
                    stopped_by_failure = True
                    break  # Exit the loop immediately
                else:
                    LOGGER_INFO(f"[operator][stop_on_failure] Step {step_idx} '{ctrl.get('name', 'unknown')}' failed but stop_on_failure=false, continuing to next step.", "YELLOW")
            elif not step_result.result and is_optional:
                LOGGER_INFO(f"[operator][step][optional][failed] Optional step {step_idx} failed, continuing without affecting overall result", "YELLOW")

            step_idx += 1
            
        result = overall_success
            
        # Handle batch performance reports
        if test_case_execution_duration > 1 and performance_report_path:
            self.report_processor.handle_batch_performance_reports(
                performance_report_path, test_case, test_case_execution_duration, 
                execution_context, self.process_handler
            )
        
        # Return both result and whether execution was stopped by stop_on_failure
        # For backward compatibility, we return just the result if not stopped
        # Callers can check if return value is tuple to get stopped_by_failure info
        if stopped_by_failure:
            return (result, stopped_by_failure)
        return result

    def configure_retry_settings(self, max_attempts: int = 3, retry_delay: int = 1):
        """Configure simple retry settings for control location operations"""
        self.control_locator.max_retry_attempts = max_attempts
        self.control_locator.retry_delay = retry_delay
        LOGGER_INFO(f"[operator] Updated retry configuration: max_attempts={max_attempts}, "
                   f"retry_delay={retry_delay}", "CYAN")
    
    def configure_retry_strategies(self, **strategies):
        """
        Configure which retry strategies are enabled
        
        Args:
            **strategies: Dictionary of strategy_name: enabled (bool)
                Available strategies:
                - stale_data: Reset FocusListener for identical controls
                - corrupted_data: Reset FocusListener for ?? characters  
                - empty_controls: Press ESC for empty control lists
        
        Example:
            control_operator.configure_retry_strategies(
                stale_data=True,
                empty_controls=True
            )
        """
        for strategy_name, enabled in strategies.items():
            if strategy_name in self.control_locator.retry_strategies_enabled:
                self.control_locator.retry_strategies_enabled[strategy_name] = enabled
                LOGGER_INFO(f"[operator] Retry strategy '{strategy_name}' set to {enabled}", "CYAN")
            else:
                LOGGER_WARNING(f"[operator] Unknown retry strategy '{strategy_name}' ignored", "YELLOW")
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics and configuration information"""
        return {
            "retry_config": {
                "max_attempts": self.control_locator.max_retry_attempts,
                "retry_delay": self.control_locator.retry_delay,
                "enabled_strategies": {k: v for k, v in self.control_locator.retry_strategies_enabled.items() if v},
                "disabled_strategies": {k: v for k, v in self.control_locator.retry_strategies_enabled.items() if not v}
            }
        }

    # ──────────────────────────────────────────────────────────────────────────
    # AI observe support
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_ai_observe(self, ctrl: Dict[str, Any], execution_context, navigate_report_path: 'Optional[str]' = None) -> list:
        """
        Handle an ``ai_observe`` step.

        Captures the current window screenshot, calls the AI model with the
        supplied prompt, then returns the sub-steps associated with the chosen
        case (``a`` or ``b``) so the caller can inject them into the step queue.

        YAML format (inline sub-steps)::

            - name: "AI Branch: check state"
              ai_observe:
                prompt: |
                  Look at the screenshot.  Which situation applies?
                  Output format: reply with exactly 'a' or 'b'.
                case_a:
                  - name: "..."
                    action:
                      type: key
                      value: enter
                case_b:
                  - name: "..."
                    action:
                      type: key
                      value: escape

        YAML format (sub-workflow paths)::

            - name: "AI Branch: check state"
              ai_observe:
                prompt: "... Output format: reply with exactly 'a' or 'b'."
                case_a: "navigations/some/path_for_case_a"
                case_b: "navigations/some/path_for_case_b"

        Returns:
            list: Sub-steps to execute (empty list on error skips silently).
        """
        branch_config = ctrl.get('ai_observe', {})
        step_name = ctrl.get('name', 'ai_observe')
        prompt = branch_config.get('prompt', '')
        case_a_def = branch_config.get('case_a', [])
        case_b_def = branch_config.get('case_b', [])

        LOGGER_INFO(f"[operator][ai_observe] '{step_name}' capturing window screenshot", "CYAN")

        # ── 1. Capture current window screenshot ────────────────────────────────
        try:
            window_image_path, _ = self.control_recorder.record_window_image()
        except Exception as exc:
            LOGGER_ERROR(f"[operator][ai_observe] Screenshot failed: {exc} falling back to case_b", "RED")
            return self._expand_ai_observe_steps(case_b_def, navigate_report_path)

        if not window_image_path:
            LOGGER_ERROR("[operator][ai_observe] No window image captured falling back to case_b", "RED")
            return self._expand_ai_observe_steps(case_b_def, navigate_report_path)

        # ── 2. Resolve variables in prompt ──────────────────────────────────────
        if prompt and execution_context and hasattr(execution_context, 'resolve_variables'):
            prompt = execution_context.resolve_variables(prompt)

        # ── 3. Ask the AI model ─────────────────────────────────────────────────
        branch_prompt = (
            f"{prompt}\n\n"
            "IMPORTANT: Output format reply with exactly 'a' or 'b' only (no other text)."
        )
        try:
            llm_response = self.model_handler.handle_ai_check_report(
                None, window_image_path, message=branch_prompt
            )
            LOGGER_INFO(f"[operator][ai_observe] AI response: '{llm_response}'", "GREEN")
        except Exception as exc:
            LOGGER_ERROR(f"[operator][ai_observe] AI model call failed: {exc} falling back to case_b", "RED")
            return self._expand_ai_observe_steps(case_b_def, navigate_report_path)

        # ── 4. Parse AI response pick case ────────────────────────────────────
        response_stripped = (llm_response or '').strip().lower()
        # Accept 'a' if the response starts with 'a' (e.g. "a", "a.", "a:", "case a")
        if response_stripped.startswith('a'):
            chosen_case = 'a'
            chosen_def = case_a_def
        else:
            chosen_case = 'b'
            chosen_def = case_b_def

        chosen_steps = self._expand_ai_observe_steps(chosen_def, navigate_report_path)
        LOGGER_INFO(
            f"[operator][ai_observe] '{step_name}' ✅case_{chosen_case} selected "
            f"({len(chosen_steps)} steps to execute)",
            "GREEN"
        )
        return chosen_steps

    def _expand_ai_observe_steps(self, steps_or_path, base_path: 'Optional[str]' = None) -> list:
        """
        Expand the ``case_a`` / ``case_b`` value into a flat list of step dicts.

        Two supported formats:
        * ``list``  inline step dicts (used as-is; ``include`` / ``local_api``
          entries inside are **not** re-expanded here; they will be handled
          by :meth:`_process_single_control` normally).
        * ``str``   path to a sub-workflow YAML file (relative to
          ``TEST_CASES_PATH``), loaded via :class:`WorkflowLoader`.
        """
        if not steps_or_path:
            return []

        if isinstance(steps_or_path, str):
            # Sub-workflow file path
            try:
                loader = WorkflowLoader()
                included = loader._load_included_steps(steps_or_path, base_path or '')
                return loader._expand_includes(included, base_path or '')
            except Exception as exc:
                LOGGER_ERROR(f"[operator][ai_observe] Failed to load sub-workflow '{steps_or_path}': {exc}", "RED")
                return []

        if isinstance(steps_or_path, list):
            return list(steps_or_path)

        return []

    def _initialize_execution_context(self, test_case, execution_duration, execution_count, check_points=None):
        """Initialize execution context with process information and check points configuration
        
        Args:
            test_case: Test case identifier
            execution_duration: Test execution duration
            execution_count: Number of test executions
            check_points: List of enabled check points from test suite (e.g., ['Performance', 'Focus Ring'])
        """
        webex_app_pids = self.process_handler.get_cisco_collab_pid_info()
        
        LOGGER_DEBUG(f"[operator][locate] webex main [{webex_app_pids.get('main_pid', None)}], media [{webex_app_pids.get('media_pid', None)}]", "YELLOW")
        
        # Get current report ID from TestCaseDBHandler
        report_id = self.test_case_db_handler.get_current_report_id()
        
        # Log check_points configuration
        if check_points:
            LOGGER_INFO(f"[operator][check_points] Enabled check points: {check_points}", "CYAN")
        else:
            LOGGER_INFO(f"[operator][check_points] No check points specified, all features enabled by default", "CYAN")
        
        return ExecutionContext(
            test_case=test_case,
            execution_duration=execution_duration,
            execution_count=execution_count,
            report_id=report_id,
            check_points=check_points,
            webex_app_main_pid=webex_app_pids.get('main_pid', None),
            webex_app_media_pid=webex_app_pids.get('media_pid', None),
            verification_processor=self.verification_processor,  # Pass verification processor
            current_control=self.current_control  # Pass current control for backward compatibility
        )

    def _should_process_control(self, ctrl, platform):
        """Check if the control should be processed for the given platform"""
        ctrl_platform = ctrl.get("platforms", None)
        if ctrl_platform and not control_datasets_loader.is_platform_supported(ctrl_platform, platform):
            test_case_step_description = ctrl.get("name", None)
            if test_case_step_description:
                try:
                    ctrl_name, _ = control_datasets_loader.get_control_metadata_by_name(test_case_step_description, platform=platform)
                    LOGGER_DEBUG(f"[operator][locate][Skipping] control: {ctrl_name} for platform: {platform}, expected platform: {ctrl_platform}", "YELLOW")
                except:
                    LOGGER_DEBUG(f"[operator][locate][Skipping] control: {test_case_step_description} for platform: {platform}, expected platform: {ctrl_platform}", "YELLOW")
            return False
        return True

    def _process_single_control(self, ctrl, step_index, execution_context: ExecutionContext, platform, language, 
                               navigate_report_path, performance_report_path, stress_report_path, locate_id_flag):
        """Process complete workflow for a single control using specialized processors"""
        # Parse locate target - using processor
        locate_target = self.metadata_processor.parse_locate_target(ctrl, platform)
        
        # Locate control - using processor
        locate_result = self.control_locator.locate_control(locate_target, locate_id_flag, self.current_control)
        LOGGER_INFO(f"[operator][locate][result] Control '{locate_target.name}' locate_result.success: {locate_result.success}", "CYAN")
        
        # Execute action - using processor (can use ai_check_result from previous step if available)
        action_result = self.action_processor.execute_control_action(ctrl, execution_context, locate_result)
        # Check skip_report early — skip AI check, expect_state, focus ring and report generation
        skip_report = ctrl.get("skip_report", False)

        ai_result = None
        ai_check_failed = False
        expect_result = ExpectationResult(state="[SUCCESS]Success", expected="", actual="")

        if skip_report:
            LOGGER_INFO(f"[operator][skip_report] skip_report=true for '{locate_target.test_case_step_description}', skipping AI check, verification and report generation", "YELLOW")
        else:
            image_path = action_result.image_data.control_window_image_path if action_result.image_data else None

            # Resolve AI check image path based on ai_check.source
            # Supported values: "fullscreen", "control", "window" (default)
            ai_check_config = ctrl.get("ai_check", None)
            if isinstance(ai_check_config, dict):
                source = ai_check_config.get("source", "window")
                if source == "fullscreen":
                    fullscreen_path = action_result.send_value if action_result.send_value else None
                    if fullscreen_path and os.path.isfile(fullscreen_path):
                        LOGGER_INFO(f"[operator][ai_check][fullscreen] Using function-returned fullscreen: {fullscreen_path}", "CYAN")
                        image_path = fullscreen_path
                    else:
                        LOGGER_WARNING(f"[operator][ai_check][fullscreen] Fullscreen path not found: {fullscreen_path}, falling back to window image", "YELLOW")
                elif source == "control":
                    control_img_path = action_result.image_data.control_image_path if action_result.image_data else None
                    if control_img_path and os.path.isfile(control_img_path):
                        LOGGER_INFO(f"[operator][ai_check][control] Using control image: {control_img_path}", "CYAN")
                        image_path = control_img_path
                    else:
                        LOGGER_WARNING(f"[operator][ai_check][control] Control image not found: {control_img_path}, falling back to window image", "YELLOW")
                # source == "window" or unrecognised: keep default window image_path

            ai_result = self.verification_processor.perform_ai_check(ctrl, image_path, navigate_report_path, execution_context)

            # Check if AI check failed
            if ai_result.llm_response and ('❌' in ai_result.llm_response or 'Failed' in ai_result.llm_response):
                ai_check_failed = True
                LOGGER_WARNING(f"[operator][ai_check][failed] AI check failed for '{locate_target.name}': {ai_result.llm_response}", "YELLOW")

            # Verify expected state - using processor
            # If locate failed, override the expected state to ❌Failed
            if not locate_result.success:
                LOGGER_WARNING(f"[operator][locate][failed] Control location failed for '{locate_target.name}', setting state to ❌Failed", "RED")
                expect_result = ExpectationResult(
                    state="❌Failed",
                    expected="Control location",
                    actual="Failed to locate control"
                )
            else:
                expect_result = self.verification_processor.verify_expected_state(ctrl)

            LOGGER_INFO(f"[operator][expect_result] Final expect_result.state for '{locate_target.name}': {expect_result.state}", "YELLOW")
        
        # Validate focus ring - using processor (only if Focus Ring check point is enabled and skip_report is not set)
        focus_ring_status = "N/A"
        if not skip_report and execution_context.has_check_point('Focus Ring'):
            LOGGER_DEBUG(f"[operator][focus_ring] Focus Ring check point enabled, performing validation")
            control_image_path = action_result.image_data.control_image_path if action_result.image_data else None
            focus_ring_status = self.verification_processor.validate_focus_ring(control_image_path)
        elif not skip_report:
            LOGGER_DEBUG(f"[operator][focus_ring] Focus Ring check point disabled, skipping validation")
        
        # Generate reports - using processor (skip if skip_report is set)
        if not skip_report:
            self.report_processor.generate_step_reports(
                ctrl, locate_target, locate_result, action_result, ai_result, expect_result,
                step_index, execution_context, platform, language,
                navigate_report_path, performance_report_path, stress_report_path, None, focus_ring_status
            )
        
        return ControlStepResult(
            result=locate_result.success,
            expect_state=expect_result.state,
            control_metadata=asdict(locate_result.metadata) if locate_result.metadata else {},
            ai_check_failed=ai_check_failed
        )

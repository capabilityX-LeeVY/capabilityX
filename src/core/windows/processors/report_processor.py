"""
Report Processor

This module contains the ReportProcessor for handling result logging 
"""

import os
from typing import Dict, Any, Optional
from dataclasses import asdict
from core.windows.data_models.locate_target import LocateTarget
from core.windows.data_models.locate_result import LocateResult
from core.windows.data_models.action_result import ActionResult, TraverseRecord
from core.windows.data_models.ai_check_result import AICheckResult
from core.windows.data_models.expectation_result import ExpectationResult
from core.windows.data_models.execution_context import ExecutionContext
from config.paths import NAVIGATION_REPORT_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_DEBUG
from rs_sdk.utils.common_settings_loader import common_settings_loader


class ReportProcessor:
    """Report processor - handles result logging and report generation"""
    
    def __init__(self, report_manager):
        self.report_manager = report_manager
    
    @staticmethod
    def _sanitize_alt_text(text: str) -> str:
        """Sanitize text for use in HTML alt attributes (remove newlines, escape quotes)."""
        if not text:
            return ""
        return text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('"', '&quot;').strip()
    
    def generate_step_reports(self, ctrl: Dict[str, Any], locate_target: LocateTarget, 
                            locate_result: LocateResult, action_result: ActionResult, 
                            ai_result: AICheckResult, expect_result: ExpectationResult,
                            step_index: int, execution_context: ExecutionContext, 
                            platform: str, language: str,
                            navigate_report_path: str, performance_report_path: str, 
                            stress_report_path: Optional[str] = None,
                            test_case_config: Optional[dict] = None,
                            focus_ring_status: str = "N/A"):
        """Generate step reports for navigation, performance, and stress testing"""
        current_control_name = locate_result.control_name
        if execution_context.execution_count > 1:
            current_control_name = f"{execution_context.execution_count} {current_control_name}"
        
        current_control_window_image = None
        current_control_window_image_rel_path = None
        safe_alt_name = self._sanitize_alt_text(current_control_name)
        if action_result.image_data and action_result.image_data.control_window_image_path:
            # Use the actual navigation report file path as base for relative path calculation
            current_control_window_image_rel_path = os.path.relpath(action_result.image_data.control_window_image_path, os.path.dirname(navigate_report_path))
            current_control_window_image = f'<img src="{current_control_window_image_rel_path}" alt="{safe_alt_name}" style="max-width: 200px; height: auto;">'
        
        current_control_image = None
        current_control_image_rel_path = None
        if action_result.image_data and action_result.image_data.control_image_path:
            # Use the actual navigation report file path as base for relative path calculation
            current_control_image_rel_path = os.path.relpath(action_result.image_data.control_image_path, os.path.dirname(navigate_report_path))
            current_control_image = f'<img src="{current_control_image_rel_path}" alt="{safe_alt_name}_control" style="max-width: 200px; height: auto;">'
        
        # Override control image with fullscreen image when ai_check.source == "fullscreen"
        ai_check_config = ctrl.get("ai_check", None) if isinstance(ctrl, dict) else None
        if isinstance(ai_check_config, dict) and ai_check_config.get("source") == "fullscreen":
            fullscreen_path = action_result.send_value if action_result.send_value else None
            if fullscreen_path and os.path.isfile(fullscreen_path):
                current_control_image_rel_path = os.path.relpath(fullscreen_path, os.path.dirname(navigate_report_path))
                current_control_image = f'<img src="{current_control_image_rel_path}" alt="{safe_alt_name}_fullscreen" style="max-width: 200px; height: auto;">'

        expect_result = self._handle_optional_control(ctrl, locate_result, expect_result)
        
        # Generate navigation report
        # Use locate_result.control_name if available, otherwise fallback to YAML step description
        current_control_name = locate_result.control_name or locate_target.test_case_step_description or ""
        # Pass the actual image path for Focus Ring detection, and HTML for display
        control_image_path = action_result.image_data.control_image_path if action_result.image_data else ""
        self._generate_navigate_report(
            locate_target, locate_result, action_result, ai_result, expect_result,
            execution_context, platform, language, navigate_report_path,
            current_control_name, current_control_window_image, current_control_image, step_index, control_image_path,
            current_control_window_image_rel_path, current_control_image_rel_path, ctrl, test_case_config, focus_ring_status
        )

        # Expand traverse_data into individual report rows (for acc_sequence)
        if action_result.traverse_data:
            self._generate_traverse_report_rows(
                action_result.traverse_data, locate_target, execution_context,
                platform, language, navigate_report_path, step_index, test_case_config
            )

        # Generate performance report only if Performance check point is enabled
        if execution_context.has_check_point('Performance'):
            LOGGER_DEBUG(f"[report][performance] Performance check point enabled, generating performance report")
            self._generate_performance_report(
                execution_context, performance_report_path, current_control_name
            )
        else:
            LOGGER_DEBUG(f"[report][performance] Performance check point disabled, skipping performance report")

        # Generate stress report (if stress checkpoint is active and report path provided)
        if stress_report_path:
            # Pass the raw image path for stress report processing
            raw_image_path = action_result.image_data.control_window_image_path if action_result.image_data else ''
            self._generate_stress_report(
                execution_context, stress_report_path, current_control_name, raw_image_path, ai_result
            )
    
    def _handle_optional_control(self, ctrl: Dict[str, Any], locate_result: LocateResult, 
                                expect_result: ExpectationResult) -> ExpectationResult:
        """Handle optional controls when locating fails"""
        if not locate_result.success:
            ctrl_optional = ctrl.get("optional", False)
            if ctrl_optional:
                expect_result = ExpectationResult(
                    state='Optional',
                    expected=expect_result.expected,
                    actual=expect_result.actual
                )
                LOGGER_WARNING(f"[Locate][end] Optional control: {ctrl} not found, skipping.", "YELLOW")
            else:
                # Preserve the state set by control_operator if it's already ❌Failed
                # Only set to 'Failed' if the state hasn't been set to ❌Failed already
                if expect_result.state != '❌Failed':
                    expect_result = ExpectationResult(
                        state='Failed',
                        expected=expect_result.expected,
                        actual=expect_result.actual
                    )
                LOGGER_INFO(f"[Locate][end] Failed to locate control: skip [{ctrl}], start to located next control.", "RED")
        return expect_result
    
    def _generate_traverse_report_rows(self, traverse_data: list, locate_target: LocateTarget,
                                       execution_context: ExecutionContext, platform: str, language: str,
                                       navigate_report_path: str, step_index: int,
                                       test_case_config: Optional[dict] = None):
        """Expand acc_sequence traverse_data into individual report rows with focus ring analysis"""
        from rs_sdk.utils import report_handler
        from core.processor.focus_processor import FocusRingProcessor
        from config.paths import CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH
        
        focus_processor = FocusRingProcessor(
            image_output_path=CONTROL_IMAGE_PATH,
            results_output_path=FOCUS_RING_RESULT_PATH
        )
        enable_focus_ring = execution_context.has_check_point('Focus Ring')
        enable_screen_reader = execution_context.has_check_point('Screen Reader')
        
        LOGGER_INFO(
            f"[report][traverse] Expanding {len(traverse_data)} controls into report rows "
            f"[step={step_index + 1}][enable_focus_ring={enable_focus_ring}][enable_screen_reader={enable_screen_reader}]", "CYAN"
        )
        
        for record in traverse_data:
            control_name = record.control_name or ""
            safe_alt_name = self._sanitize_alt_text(control_name)
            
            # Build control image HTML
            control_image_html = ""
            control_image_rel_path = ""
            if record.control_image_path and os.path.isfile(record.control_image_path):
                control_image_rel_path = os.path.relpath(record.control_image_path, os.path.dirname(navigate_report_path))
                control_image_html = f'<img src="{control_image_rel_path}" alt="{safe_alt_name}" style="max-width: 200px; height: auto;">'
            
            # Focus ring analysis per control
            focus_ring_status = "N/A"
            if enable_focus_ring and record.control_image_path and os.path.isfile(record.control_image_path):
                try:
                    focus_ring_status = focus_processor.validate_image_focused_status(record.control_image_path)
                except Exception as e:
                    LOGGER_WARNING(f"[report][traverse] Focus ring detection failed for {control_name}: {e}")
                    focus_ring_status = "Error"
            elif not enable_focus_ring:
                focus_ring_status = "—"
            
            # Sub-step name: e.g. "2.1", "2.2" ...
            sub_step_name = f"{step_index + 1}.{record.order}"
            
            # Write report row via report_handler directly
            report_handler.write_navigate_report_body(
                navigate_report_path,
                execution_context.test_case,
                sub_step_name,
                locate_target.test_case_step_description or "",  # Step Name (scan window)
                control_name,  # Current Control Name
                "",  # reference image
                "",  # window image
                control_image_html,  # control image
                "✅Success",  # KB Navigate (traversal succeeded)
                focus_ring_status,  # Focus Ring
                "—",  # Screen Reader (placeholder, will be synced after batch analysis)
                "",  # AI check
                "N/A",  # Value Verify
                "",  # Response Time
                "—",  # CPU
                "—",  # Memory
                "—"   # GPU
            )
            
            # Insert into database for screen reader batch analysis
            if enable_screen_reader:
                try:
                    self.report_manager.test_case_db_handler.insert_navigate_report(
                        test_case=execution_context.test_case,
                        test_steps=locate_target.test_case_step_description or "",
                        locate_control_name=control_name,
                        current_control_name=control_name,
                        navigate_result="✅Success",
                        focus_ring_result=focus_ring_status,
                        platform=platform,
                        language=language,
                        control_type=record.control_type,
                        full_description=record.full_description,
                        access_key=record.access_key,
                        window_level1=record.window_level1,
                        window_level2=record.window_level2,
                        parent=record.parent_name,
                        parent_type=record.parent_type,
                        default_action=record.default_action,
                        legacy_value=record.legacy_value,
                        legacy_role=record.legacy_role,
                        legacy_state=record.legacy_state,
                        control_image_path=control_image_rel_path,
                    )
                except Exception as e:
                    LOGGER_WARNING(f"[report][traverse] Failed to insert sub-step DB record for {control_name}: {e}")
        
        LOGGER_INFO(
            f"[report][traverse] Completed writing {len(traverse_data)} traverse rows", "GREEN"
        )
    
    def _generate_navigate_report(self, locate_target: LocateTarget, locate_result: LocateResult,
                                action_result: ActionResult, ai_result: AICheckResult, 
                                expect_result: ExpectationResult, execution_context: ExecutionContext,
                                platform: str, language: str, navigate_report_path: str,
                                current_control_name: str, current_control_window_image: Optional[str], 
                                current_control_image: Optional[str], step_index: int, control_image_path: Optional[str] = None,
                                current_control_window_image_rel_path: Optional[str] = None, 
                                current_control_image_rel_path: Optional[str] = None, ctrl: Optional[dict] = None,
                                test_case_config: Optional[dict] = None, focus_ring_status: str = "N/A"):
        """Generate navigation report with control and execution details"""
        
        # Load and merge configuration settings with common settings
        final_config = test_case_config or {}
        if test_case_config:
            final_config = common_settings_loader.merge_test_case_config(test_case_config)
        
        # Extract UI response data if available
        ui_response_data = None
        if action_result.ui_response_result:
            ui_response_data = {
                'response_time_ms': action_result.ui_response_result.response_time_ms,
                'success': action_result.ui_response_result.success,
                'expected_state': action_result.ui_response_result.expected_state,
                'actual_state': action_result.ui_response_result.actual_state,
                'polling_count': action_result.ui_response_result.polling_count
            }
        
        # Extract thresholds from merged configuration
        ui_response_threshold_ms = common_settings_loader.get_ui_response_threshold(final_config, ctrl or {})
        performance_thresholds = common_settings_loader.get_performance_thresholds(final_config, ctrl or {})
        
        LOGGER_DEBUG(f"Using UI response threshold: {ui_response_threshold_ms} ms for step: {locate_target.name}")
        LOGGER_DEBUG(f"Using Performance thresholds: {performance_thresholds} for step: {locate_target.name}")
        
        # Focus ring status is now passed as parameter from ControlVerificationProcessor
        LOGGER_DEBUG(f"Focus Ring status for control '{current_control_name}': {focus_ring_status}")
        
        # Extract value verification result from action_result
        value_verify_result = action_result.value_verify_result if action_result.value_verify_result else "N/A"
        LOGGER_DEBUG(f"Value Verify result for control '{current_control_name}': {value_verify_result}")
        
        # Check if Performance check point is enabled
        enable_performance = execution_context.has_check_point('Performance')
        
        # Check if Focus Ring check point is enabled
        enable_focus_ring = execution_context.has_check_point('Focus Ring')
        
        self.report_manager.write_and_insert_navigate_report(
            navigate_report_path=navigate_report_path,
            test_case=execution_context.test_case,
            ctrl_name=locate_target.name,
            locate_control_name=current_control_name,
            ctrl_ai_check_reference_image_path=ai_result.reference_image_path or '',
            current_control_window_image=current_control_window_image if current_control_window_image else "",
            current_control_image=current_control_image if current_control_image else "",
            llm_response=ai_result.llm_response or '',
            ctrl_expect_state=expect_result.state,
            ctrl_expect=expect_result.expected,
            current_expect_state=expect_result.actual,
            platform=platform,
            language=language,
            control_metadata=asdict(locate_result.metadata) if locate_result.metadata else {},
            image_data=asdict(action_result.image_data) if action_result.image_data else {},
            step_index=step_index,
            ui_response_data=ui_response_data,
            focus_ring_status=focus_ring_status,
            window_image_path=current_control_window_image_rel_path if current_control_window_image_rel_path else "",
            control_image_path=current_control_image_rel_path if current_control_image_rel_path else "",
            step_start_time=action_result.step_start_time,
            step_end_time=action_result.step_end_time,
            step_duration_ms=action_result.step_duration_ms,
            ui_response_threshold_ms=ui_response_threshold_ms,
            performance_thresholds=performance_thresholds,
            main_cpu=execution_context.current_main_cpu if enable_performance else None,
            main_mem=execution_context.current_main_mem if enable_performance else None,
            main_gpu=execution_context.current_main_gpu if enable_performance else None,
            value_verify_result=value_verify_result,  # Value verification result
            enable_performance=enable_performance,  # Pass performance flag
            enable_focus_ring=enable_focus_ring  # Pass focus ring flag
        )
        
        # Update UI response data for the current step if available
        if ui_response_data:
            from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
            db_handler = TestCaseDBHandler()
            
            # Prepare UI response data with correct control name
            ui_response_update_data = ui_response_data.copy()
            ui_response_update_data['control_name'] = current_control_name
            ui_response_update_data['test_case'] = execution_context.test_case
            
            # Update the current step's record
            success = db_handler.update_navigate_report_ui_response(
                ui_response_data=ui_response_update_data,
                test_case=execution_context.test_case,
                step_order=None  # Will use current step counter
            )
            
            if success:
                LOGGER_INFO(f"[UI Response] Updated navigate report with UI response data for control: {current_control_name}", "GREEN")
            else:
                LOGGER_WARNING(f"[UI Response] Failed to update navigate report with UI response data for control: {current_control_name}", "YELLOW")
    
    def _generate_performance_report(self, execution_context: ExecutionContext, 
                                   performance_report_path: str, current_control_name: str):
        """Generate performance report with CPU and memory metrics"""
        self.report_manager.write_and_insert_performance_report(
            performance_report_path=performance_report_path,
            test_case=execution_context.test_case,
            current_control_name=current_control_name,
            main_cpu=execution_context.current_main_cpu,
            main_mem=execution_context.current_main_mem,
            media_cpu=execution_context.current_media_cpu,
            media_mem=execution_context.current_media_mem
        )
    
    def _generate_stress_report(self, execution_context: ExecutionContext,
                              stress_report_path: str, current_control_name: str, raw_image_path: Optional[str] = None, ai_result: Optional[AICheckResult] = None):
        """Generate stress report with comprehensive system health metrics"""
        # Use StressHandler to collect and save stress data  
        from rs_sdk.utils.stress_handler import StressHandler
        stress_handler = StressHandler()
        
        # Create modified execution context for stress reporting
        class StressExecutionContext:
            def __init__(self, base_context, control_name, image_path, ai_check_result=None, step_idx=0):
                # Copy all attributes from base context
                for attr in dir(base_context):
                    if not attr.startswith('_'):
                        try:
                            setattr(self, attr, getattr(base_context, attr))
                        except:
                            pass
                
                # Override specific attributes for stress reporting
                self.step_index = step_idx  
                self.current_control_name = control_name
                self.current_control_window_image = image_path or ''
                # Set current_control_image for stress report image display
                self.current_control_image = image_path or ''
                self.ai_check_result = ai_check_result
        
        # Create stress-specific execution context
        stress_context = StressExecutionContext(execution_context, current_control_name, raw_image_path, ai_result)
        
        # Create test case dict for stress handler
        test_case_dict = {
            'name': execution_context.test_case
        }
        
        success = stress_handler.collect_and_save_stress_data(
            stress_report_path=stress_report_path,
            test_case=test_case_dict,
            execution_context=stress_context
        )
        
        if not success:
            LOGGER_WARNING(f"Failed to generate stress report for control: {current_control_name}", "YELLOW")
    
    def handle_batch_performance_reports(self, performance_report_path: str, test_case: str, 
                                       test_case_execution_duration: int, execution_context: ExecutionContext,
                                       process_handler):
        """Handle batch performance report generation"""
        self.report_manager.batch_write_performance_reports(
            performance_report_path=performance_report_path,
            test_case=test_case,
            test_case_execution_duration=test_case_execution_duration,
            webex_app_main_pid=execution_context.webex_app_main_pid,
            webex_app_media_pid=execution_context.webex_app_media_pid,
            process_handler=process_handler
        )

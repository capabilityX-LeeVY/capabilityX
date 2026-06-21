"""
Control Action Processor

This module contains the ControlActionProcessor for handling action execution 
using the strategy pattern.
"""

import time
from datetime import datetime
from typing import Dict, Any
from core.windows.data_models.action_result import ActionResult
from core.windows.data_models.execution_context import ExecutionContext
from core.windows.data_models.locate_result import LocateResult
from core.windows.data_models.image_data import ImageData
from core.windows.strategies.action_strategy_manager import ActionStrategyManager
from core.windows.processors.ui_response_processor import UIResponseProcessor, UIResponseResult
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG


class ControlActionProcessor:
    """Control action execution processor - handles action execution using strategy pattern"""
    
    def __init__(self, action_strategy_manager: ActionStrategyManager, 
                 process_handler, control_recorder, control_handler):
        self.action_strategy_manager = action_strategy_manager
        self.process_handler = process_handler
        self.control_recorder = control_recorder
        
        # Initialize UI response processor
        self.ui_response_processor = UIResponseProcessor(control_handler)
    
    def execute_control_action(self, ctrl: Dict[str, Any], execution_context: ExecutionContext, 
                             locate_result: LocateResult) -> ActionResult:
        """Execute control action and return result with performance data and images"""
        if not locate_result.success:
            # For optional controls, still capture images and current state even if locate failed
            ctrl_optional = ctrl.get("optional", False)
            if ctrl_optional:
                LOGGER_INFO(f"[operator][action][optional][failed]: Optional control locate failed, capturing current state", "YELLOW")
                
                # Record action start time for consistency
                step_start_datetime = datetime.now()
                
                # Update performance data
                self._update_performance_data(execution_context)
                
                # Record images even though locate failed
                image_data = self._record_images()
                
                # Record end time
                step_end_datetime = datetime.now()
                step_duration_ms = int((step_end_datetime - step_start_datetime).total_seconds() * 1000)
                
                return ActionResult(
                    success=False,
                    action_type='optional_failed',
                    send_value='',
                    wait_time=1,
                    image_data=image_data,
                    ui_response_result=None,
                    step_start_time=step_start_datetime,
                    step_end_time=step_end_datetime,
                    step_duration_ms=step_duration_ms
                )
            else:
                return ActionResult(
                    success=False,
                    action_type='none',
                    send_value='',
                    wait_time=1,
                    image_path=None,
                    ui_response_result=None
                )

        ctrl_action = ctrl.get("action", "SPACE")
        ctrl_action_type = ctrl_action.get("type", "key")
        
        LOGGER_INFO(f"[operator][Locate][action] control: [{ctrl}][{ctrl_action.get('value', 'SPACE')}]!", "CYAN")
        
        # Record action start time for UI response measurement and step timing
        action_start_time = time.time()
        step_start_datetime = datetime.now()
        
        # Execute action using strategy pattern
        send_value = self._execute_action_by_type(ctrl_action_type, ctrl_action, execution_context)
        
        # Store value verification result if action type is verify
        value_verify_result = None
        if ctrl_action_type == "verify":
            value_verify_result = send_value  # VerifyActionStrategy returns verification status
        
        # Capture traverse_data from acc_sequence strategy if available
        traverse_data = None
        if ctrl_action_type == "acc_sequence":
            strategy = self.action_strategy_manager.get_strategy(ctrl_action_type)
            if hasattr(strategy, 'last_traverse_data') and strategy.last_traverse_data:
                traverse_data = strategy.last_traverse_data
        
        # Update performance data
        self._update_performance_data(execution_context)

        # When skip_report is true, skip wait, screenshots and images entirely for maximum speed
        skip_report = ctrl.get("skip_report", False)

        # Handle UI response measurement vs. normal wait
        ui_response_result = None
        if skip_report:
            # skip_report: no wait, no images — action-only mode
            LOGGER_INFO(f"[operator][skip_report] Skipping wait and image capture for '{ctrl.get('name', 'Unknown')}'", "YELLOW")
        elif ctrl.get("ui_response", False):
            # For UI response measurement, skip normal wait_time and use polling
            LOGGER_INFO(f"[operator][UI Response] Enabled for control: {ctrl.get('name', 'Unknown')}", "CYAN")
            ui_response_result = self.ui_response_processor.measure_ui_response(ctrl, action_start_time)
            
            # Note: UI response data will be saved to database in ReportProcessor
            # to ensure correct control name association
            if ui_response_result:
                LOGGER_DEBUG(f"[UI Response] Measurement completed, will be saved in report generation phase")
        else:
            # Normal wait behavior
            wait_time = ctrl_action.get("wait_time", 1)
            LOGGER_INFO(f"[operator][Locate][wait][{wait_time}s][{ctrl}]")
            time.sleep(wait_time)
        
        # Record end time and calculate duration
        step_end_datetime = datetime.now()
        step_duration_ms = int((step_end_datetime - step_start_datetime).total_seconds() * 1000)
        
        # Record images (skip entirely if skip_report, skip control screenshot if skip_screenshot)
        if skip_report:
            image_data = ImageData(
                pre_control_image_bytes=None,
                control_image_bytes=None,
                window_image_bytes=None,
                control_image_path=None,
                control_window_image_path=None
            )
        else:
            skip_screenshot = ctrl.get("skip_screenshot", False)
            image_data = self._record_images(skip_screenshot=skip_screenshot)
        
        return ActionResult(
            success=True,
            action_type=ctrl_action_type,
            send_value=send_value,
            wait_time=ctrl_action.get("wait_time", 1),
            image_data=image_data,
            ui_response_result=ui_response_result,
            step_start_time=step_start_datetime,
            step_end_time=step_end_datetime,
            step_duration_ms=step_duration_ms,
            value_verify_result=value_verify_result,  # Add value verification result
            traverse_data=traverse_data  # acc_sequence traversal records
        )
    
    def _execute_action_by_type(self, action_type: str, ctrl_action: Dict[str, Any], execution_context: ExecutionContext) -> str:
        """Execute action by type using strategy pattern"""
        return self.action_strategy_manager.execute_action(
            action_type, ctrl_action, execution_context
        )
    
    def _update_performance_data(self, execution_context: ExecutionContext):
        """Update performance data in execution context"""
        current_main_cpu, current_main_mem, current_media_cpu, current_media_mem, current_main_gpu = self.process_handler.get_performance_cisco_collab_pid_meta()
        execution_context.current_main_cpu = current_main_cpu
        execution_context.current_main_mem = current_main_mem
        execution_context.current_media_cpu = current_media_cpu
        execution_context.current_media_mem = current_media_mem
        execution_context.current_main_gpu = current_main_gpu
    
    def _record_images(self, skip_screenshot: bool = False) -> ImageData:
        """Record window and control images.
        Control image is captured first (uses focused element rect directly — always stable).
        Window image is captured second; if UIA ancestor traversal fails, falls back to
        capturing the Win32 foreground window so the report always has a window image.
        """
        if skip_screenshot:
            current_control_window_image_abs_path, current_control_window_image_bytes = self.control_recorder.record_window_image()
            if not current_control_window_image_abs_path:
                current_control_window_image_abs_path, current_control_window_image_bytes = self.control_recorder.capture_foreground_window_image()
            return ImageData(
                pre_control_image_bytes=None,
                control_image_bytes=None,
                window_image_bytes=current_control_window_image_bytes,
                control_image_path=None,
                control_window_image_path=current_control_window_image_abs_path
            )
        # Capture control image first — does not require UIA ancestor traversal
        current_control_image_abs_path, current_previous_control_image_abs_path, current_control_image_bytes, current_pre_control_image_bytes = self.control_recorder.record_control_image()
        # Capture window image second — requires ControlFirstAncestorWindow traversal,
        # which is more likely to succeed now that the UIA tree has had time to stabilize
        current_control_window_image_abs_path, current_control_window_image_bytes = self.control_recorder.record_window_image()
        # Fallback: if UIA window capture failed, capture the Win32 foreground window
        if not current_control_window_image_abs_path:
            current_control_window_image_abs_path, current_control_window_image_bytes = self.control_recorder.capture_foreground_window_image()

        return ImageData(
            pre_control_image_bytes=current_pre_control_image_bytes,
            control_image_bytes=current_control_image_bytes,
            window_image_bytes=current_control_window_image_bytes,
            control_image_path=current_control_image_abs_path,
            control_window_image_path=current_control_window_image_abs_path
        )


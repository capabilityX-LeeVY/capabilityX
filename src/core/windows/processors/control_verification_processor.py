"""
Control Verification Processor

This module contains the ControlVerificationProcessor for handling AI checks 
and expected state verification.
"""

import os
import shutil
from typing import Dict, Any, Optional, Tuple
from core.windows.data_models.ai_check_result import AICheckResult
from core.windows.data_models.expectation_result import ExpectationResult
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from config.paths import DATASET_IMG_FOLDER_PATH, NAVIGATION_REPORT_PATH, CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH
from core.processor.focus_processor import FocusRingProcessor
from rs_sdk.utils.control_datasets_loader import get_complete_control_metadata_by_name


class ControlVerificationProcessor:
    """Control verification processor - handles AI checks and expected state verification"""
    
    def __init__(self, model_handler, current_control):
        self.model_handler = model_handler
        self.current_control = current_control
        self.platform = "windows"  # Default platform
        # Initialize FocusRingProcessor for focus ring validation
        self.focus_ring_processor = FocusRingProcessor(
            image_output_path=CONTROL_IMAGE_PATH,
            results_output_path=FOCUS_RING_RESULT_PATH
        )
    
    def set_platform(self, platform: str):
        """Set the platform for metadata lookup"""
        self.platform = platform
    
    def _get_expected_control_metadata(self, expect_state_value: str) -> Optional[Tuple[str, any]]:
        """
        Get control_name and control_id from dataset based on expect_state value
        
        Args:
            expect_state_value: The expected state value from test case YAML
            
        Returns:
            Tuple of (control_name, control_id) if found and not empty, otherwise None
            Note: control_id can be either a string or a list of strings
        """
        metadata = get_complete_control_metadata_by_name(expect_state_value, platform=self.platform)
        
        if metadata:
            control_name = metadata.get('control_name', '')
            control_id = metadata.get('control_id', '')
            
            # Fix: If both control_name and control_id are empty, return None to trigger fallback
            # Handle control_id as both string and list
            control_id_is_empty = False
            if isinstance(control_id, list):
                # If it's a list, check if it's empty or contains only empty strings
                control_id_is_empty = not control_id or all(not item for item in control_id)
            else:
                # If it's a string, check if it's empty
                control_id_is_empty = not control_id
            
            if not control_name and control_id_is_empty:
                LOGGER_DEBUG(f"[verification][metadata] Metadata found but both control_name and control_id are empty for '{expect_state_value}', "
                            f"will use literal string matching", "YELLOW")
                return None
            
            LOGGER_DEBUG(f"[verification][metadata] Found metadata for '{expect_state_value}': "
                        f"control_name='{control_name}', control_id='{control_id}'", "CYAN")
            return (control_name, control_id)
        else:
            LOGGER_DEBUG(f"[verification][metadata] No metadata found for '{expect_state_value}' "
                        f"in dataset, will use literal string matching", "YELLOW")
            return None
    
    def _match_control_with_expected(self, current_control_name: str, current_control_id: str, 
                                     expected_control_name: str, expected_control_id,
                                     original_expect_value: str) -> bool:
        """
        Match current control with expected control using control_name or control_id
        
        Args:
            current_control_name: Current control's name
            current_control_id: Current control's automation ID
            expected_control_name: Expected control name from dataset
            expected_control_id: Expected control ID from dataset (can be str or list)
            original_expect_value: Original expect_state value for fallback matching
            
        Returns:
            True if match found, False otherwise
        """
        # Strategy 1: Match by control_id (most reliable)
        # Support both string and array formats for control_id
        if expected_control_id and current_control_id:
            # If expected_control_id is a list, try matching any of them
            if isinstance(expected_control_id, list):
                for control_id in expected_control_id:
                    if control_id == current_control_id:
                        LOGGER_INFO(f"[verification][match] ✅ Matched by control_id (from array): '{control_id}'", "GREEN")
                        return True
            else:
                # String format (original behavior)
                if expected_control_id == current_control_id:
                    LOGGER_INFO(f"[verification][match] ✅ Matched by control_id: '{expected_control_id}'", "GREEN")
                    return True
        
        # Strategy 2: Match by exact control_name
        if expected_control_name and current_control_name:
            if expected_control_name == current_control_name:
                LOGGER_INFO(f"[verification][match] ✅ Matched by exact control_name: '{expected_control_name}'", "GREEN")
                return True
        
        # Strategy 3: Match by control_name contains (partial match)
        if expected_control_name and current_control_name:
            if expected_control_name in current_control_name:
                LOGGER_INFO(f"[verification][match] ✅ Matched by control_name contains: '{expected_control_name}' in '{current_control_name}'", "GREEN")
                return True
        
        # Strategy 4: Fallback to original expect_state value matching (backward compatibility)
        if original_expect_value in current_control_name:
            LOGGER_INFO(f"[verification][match] ✅ Matched by original expect_state (contains): "
                       f"'{original_expect_value}' found in '{current_control_name}'", "GREEN")
            return True
        
        return False
    
    def perform_ai_check(self, ctrl: Dict[str, Any], image_path: Optional[str], navigate_report_path: Optional[str] = None, execution_context = None) -> AICheckResult:
        """Perform AI-based verification check using reference images and store result in execution_context"""
        ctrl_ai_check = ctrl.get("ai_check", None)
        llm_response = ""
        ctrl_ai_check_reference_image_path = ""
        
        # Clear previous AI check result at the start of each step
        if execution_context:
            execution_context.ai_check_result = None
        
        if ctrl_ai_check is not None and image_path:
            # Handle both string and dictionary formats for ai_check
            if isinstance(ctrl_ai_check, str):
                # Simple string format - treat as prompt only, no reference image
                ctrl_ai_check_prompt = ctrl_ai_check
                ctrl_ai_check_reference = None
            elif isinstance(ctrl_ai_check, dict):
                # Dictionary format with prompt and reference
                ctrl_ai_check_prompt = ctrl_ai_check.get("prompt", None)
                reference_name = ctrl_ai_check.get("reference", None)
                ctrl_ai_check_reference = DATASET_IMG_FOLDER_PATH / reference_name if reference_name else None
            else:
                LOGGER_WARNING(f"[Locate][AI check] Invalid ai_check format: {type(ctrl_ai_check)}", "YELLOW")
                return AICheckResult(llm_response="", reference_image_path="")
            
            # Replace dynamic variables in prompt with actual values from execution_context
            if ctrl_ai_check_prompt and execution_context:
                # Use unified variable resolution system first (supports ${var} and $var syntax)
                if hasattr(execution_context, 'resolve_variables'):
                    ctrl_ai_check_prompt = execution_context.resolve_variables(ctrl_ai_check_prompt)
                    LOGGER_INFO(f"[AI check] Applied unified variable resolution", "CYAN")
                
                # Keep backward compatibility - Replace legacy {uuid} with the actual UUID that was sent
                if "{uuid}" in ctrl_ai_check_prompt:
                    last_uuid = getattr(execution_context, 'last_uuid', None)
                    if last_uuid:
                        ctrl_ai_check_prompt = ctrl_ai_check_prompt.replace("{uuid}", last_uuid)
                        LOGGER_INFO(f"[AI check] Replaced {{uuid}} with: {last_uuid}", "CYAN")
                
                # Replace legacy {timestamp} with the actual timestamp that was sent
                if "{timestamp}" in ctrl_ai_check_prompt:
                    last_timestamp = getattr(execution_context, 'last_timestamp', None)
                    if last_timestamp:
                        ctrl_ai_check_prompt = ctrl_ai_check_prompt.replace("{timestamp}", last_timestamp)
                        LOGGER_INFO(f"[AI check] Replaced {{timestamp}} with: {last_timestamp}", "CYAN")
                
                # Replace legacy {last_sent_message} with the complete message that was sent
                if "{last_sent_message}" in ctrl_ai_check_prompt:
                    last_sent_message = getattr(execution_context, 'last_sent_message', None)
                    if last_sent_message:
                        ctrl_ai_check_prompt = ctrl_ai_check_prompt.replace("{last_sent_message}", last_sent_message)
                        LOGGER_INFO(f"[AI check] Replaced {{last_sent_message}} with: {last_sent_message}", "CYAN")
            
            if ctrl_ai_check_reference and image_path:
                reference_filename = os.path.basename(ctrl_ai_check_reference)
                target_dir = os.path.dirname(image_path)
                dst_reference_path = os.path.join(target_dir, reference_filename)
                
                if not os.path.exists(ctrl_ai_check_reference):
                    LOGGER_WARNING(f"[Locate][AI check] Reference image not found: {ctrl_ai_check_reference}", "YELLOW")
                    ctrl_ai_check_reference = None
                    ctrl_ai_check_reference_image_path = ""
                else:
                    if not os.path.exists(dst_reference_path):
                        shutil.copy(ctrl_ai_check_reference, dst_reference_path)
                    
                    # Use the actual navigation report path for relative path calculation
                    if navigate_report_path:
                        ctrl_ai_check_reference_rel = os.path.relpath(dst_reference_path, os.path.dirname(navigate_report_path))
                    else:
                        # Fallback to old method if navigate_report_path not provided
                        results_output_folder_path = NAVIGATION_REPORT_PATH
                        ctrl_ai_check_reference_rel = os.path.relpath(dst_reference_path, results_output_folder_path)
                    
                    ctrl_ai_check_reference_image_path = f'<img src="{ctrl_ai_check_reference_rel}" alt="{reference_filename}" style="max-width: 200px; height: auto;">'
                    ctrl_ai_check_reference = dst_reference_path
                
                LOGGER_DEBUG(f"[operator][Locate][AI check] reference image path: [{reference_filename}][{dst_reference_path}][{ctrl_ai_check_reference}].", "CYAN")
                llm_response = self.model_handler.handle_ai_check_report(
                    ctrl_ai_check_reference, image_path, message=ctrl_ai_check_prompt
                )
            elif ctrl_ai_check_prompt:
                # Handle prompt-only AI check (no reference image)
                LOGGER_DEBUG(f"[operator][Locate][AI check] prompt-only check: {ctrl_ai_check_prompt[:50]}...", "CYAN")
                llm_response = self.model_handler.handle_ai_check_report(
                    None, image_path, message=ctrl_ai_check_prompt
                )
                
            LOGGER_INFO(f"[operator][Locate][AI check result] control: {ctrl} with AI check: {ctrl_ai_check}, result: {llm_response}.", "CYAN")
            
            # Store AI check result in execution_context for use in subsequent actions
            if execution_context and llm_response:
                execution_context.ai_check_result = llm_response
                LOGGER_INFO(f"[operator][ai_check] Stored AI result in execution_context: {llm_response}", "GREEN")
        
        return AICheckResult(
            llm_response=llm_response,
            reference_image_path=ctrl_ai_check_reference_image_path
        )
    
    def verify_expected_state(self, ctrl: Dict[str, Any]) -> ExpectationResult:
        """
        Verify expected state by checking control properties using dataset metadata
        
        Enhanced to use control_name or control_id from dataset for matching,
        with fallback to simple string matching for backward compatibility.
        
        If optional=True and verification fails, mark as "optional" instead of "failed".
        """
        ctrl_expect = ctrl.get("expect_state", None)
        ctrl_optional = ctrl.get("optional", False)  # Check if step is optional
        ctrl_expect_state = '✅Success'
        current_expect_state = ""
        
        if ctrl_expect:
            current_control = self.current_control
            current_control.refresh()
            
            # Get both control name and control id for matching (safely)
            current_control_name = current_control.ControlName or ""
            current_control_id = current_control.ControlID
            current_expect_state = current_control_name  # For logging compatibility
            
            LOGGER_DEBUG(f"[verification][current] Control properties: "
                        f"ControlName='{current_control_name}', AutomationId='{current_control_id}'", "CYAN")
            if ctrl_optional:
                LOGGER_DEBUG(f"[verification][optional] Step is marked as optional", "YELLOW")

            # Handle both string and list formats for expect_state
            if isinstance(ctrl_expect, list):
                # Check if any of the expected states match
                matched = False
                matched_state = None
                
                for expected_state in ctrl_expect:
                    # Try to get metadata for this expected state
                    metadata_result = self._get_expected_control_metadata(expected_state)
                    
                    if metadata_result:
                        expected_control_name, expected_control_id = metadata_result
                        LOGGER_DEBUG(f"[verification][metadata] Checking '{expected_state}' with metadata: "
                                   f"control_name='{expected_control_name}', control_id='{expected_control_id}'", "CYAN")
                        
                        # Try to match using metadata
                        if self._match_control_with_expected(
                            current_control_name, current_control_id,
                            expected_control_name, expected_control_id,
                            expected_state
                        ):
                            matched = True
                            matched_state = expected_state
                            break
                    else:
                        # Fallback to simple string matching (backward compatibility)
                        LOGGER_DEBUG(f"[verification][fallback] Using literal string matching for '{expected_state}'", "YELLOW")
                        if expected_state in current_control_name:
                            matched = True
                            matched_state = expected_state
                            LOGGER_INFO(f"[verification][match] ✅ Matched by literal string (contains): "
                                       f"'{expected_state}' found in '{current_control_name}'", "GREEN")
                            break
                
                LOGGER_INFO(f"[operator][Locate][expect] [{matched}] expected any of: {ctrl_expect} current control description: {current_control_name}", "CYAN")
                if matched:
                    ctrl_expect_state = '✅Success'
                    LOGGER_INFO(f"[operator][Locate][expect] expected result: [{matched_state}] found in current control description: [{current_control_name}]", "GREEN")
                else:
                    # Check if optional - mark as optional instead of failed
                    if ctrl_optional:
                        ctrl_expect_state = '⚠️Optional'
                        LOGGER_INFO(f"[operator][Locate][expect][optional] control: {ctrl} expected any of: {ctrl_expect} NOT found, but marked as optional", "YELLOW")
                    else:
                        ctrl_expect_state = '❌Failed'
                        LOGGER_ERROR(f"[operator][Locate][expect] control: {ctrl} expected any of: {ctrl_expect} NOT found in current control description: {current_control_name}", "RED")
            else:
                # Single expect_state value
                # Try to get metadata for this expected state
                metadata_result = self._get_expected_control_metadata(ctrl_expect)
                matched = False
                
                if metadata_result:
                    expected_control_name, expected_control_id = metadata_result
                    LOGGER_DEBUG(f"[verification][metadata] Checking '{ctrl_expect}' with metadata: "
                               f"control_name='{expected_control_name}', control_id='{expected_control_id}'", "CYAN")
                    
                    # Try to match using metadata
                    matched = self._match_control_with_expected(
                        current_control_name, current_control_id,
                        expected_control_name, expected_control_id,
                        ctrl_expect
                    )
                else:
                    # Fallback to simple string matching (backward compatibility)
                    LOGGER_DEBUG(f"[verification][fallback] Using literal string matching for '{ctrl_expect}'", "YELLOW")
                    if ctrl_expect in current_control_name:
                        matched = True
                        LOGGER_INFO(f"[verification][match] ✅ Matched by literal string (contains): "
                                   f"'{ctrl_expect}' found in '{current_control_name}'", "GREEN")
                
                LOGGER_INFO(f"[operator][Locate][expect] [{matched}] expected result: [{ctrl_expect}] current control description: {current_control_name}", "CYAN")
                if matched:
                    ctrl_expect_state = '✅Success'
                    LOGGER_INFO(f"[operator][Locate][expect] expected result: [{ctrl_expect}] found in current control description: [{current_control_name}]", "GREEN")
                else:
                    # Check if optional - mark as optional instead of failed
                    if ctrl_optional:
                        ctrl_expect_state = '⚠️Optional'
                        LOGGER_INFO(f"[operator][Locate][expect][optional] control: {ctrl} expected result: {ctrl_expect} NOT found, but marked as optional", "YELLOW")
                    else:
                        ctrl_expect_state = '❌Failed'
                        LOGGER_ERROR(f"[operator][Locate][expect] control: {ctrl} expected result: {ctrl_expect} NOT found in current control description: {current_control_name}", "RED")
        
        # Convert expected to string format for ExpectationResult
        expected_str = None
        if ctrl_expect:
            if isinstance(ctrl_expect, list):
                expected_str = f"Any of: [{', '.join(ctrl_expect)}]"
            else:
                expected_str = str(ctrl_expect)
        
        return ExpectationResult(
            state=ctrl_expect_state,
            expected=expected_str,
            actual=current_expect_state
        )
    
    def validate_focus_ring(self, control_image_path: Optional[str]) -> str:
        """Validate focus ring status for the given control image"""
        focus_ring_status = "N/A"
        
        if not control_image_path:
            LOGGER_DEBUG("No control image path provided for Focus Ring detection")
            return focus_ring_status
        
        LOGGER_DEBUG(f"Checking Focus Ring for image: {control_image_path}")
        
        if not os.path.exists(control_image_path):
            LOGGER_WARNING(f"Focus Ring image not found: {control_image_path}")
            return "Image Not Found"
        
        try:
            focus_ring_status = self.focus_ring_processor.validate_image_focused_status(control_image_path)
            LOGGER_DEBUG(f"Focus Ring detection for {control_image_path}: {focus_ring_status}")
        except Exception as e:
            LOGGER_WARNING(f"Focus Ring detection failed for {control_image_path}: {str(e)}")
            focus_ring_status = "Error"
        
        return focus_ring_status
    
    def verify_control_value(self, expected_value: str) -> Dict[str, Any]:
        """
        Verify control value matches expected value
        
        Args:
            expected_value: Expected value to verify against
            
        Returns:
            Dictionary containing verification result with status, expected, and actual values
        """
        result = {
            'status': '❌Failed',
            'expected': expected_value,
            'actual': None,
            'matched': False
        }
        
        if not self.current_control:
            LOGGER_ERROR("[verification][value] No current control available", "RED")
            result['status'] = '❌Failed (No Control)'
            return result
        
        # Refresh control to get latest state
        self.current_control.refresh()
        
        # Get actual value from control
        actual_value = self.current_control.ControlValue
        result['actual'] = actual_value
        
        LOGGER_DEBUG(f"[verification][value] Expected: '{expected_value}', Actual: '{actual_value}'", "CYAN")
        
        # Handle None case
        if actual_value is None:
            LOGGER_ERROR("[verification][value] ❌ Control does not support Value pattern or value is None", "RED")
            result['status'] = '❌Failed (No Value)'
            return result
        
        # Check for match
        if actual_value == expected_value:
            # Exact match
            LOGGER_INFO(f"[verification][value] ✅ Exact match: '{actual_value}' == '{expected_value}'", "GREEN")
            result['status'] = '✅Success'
            result['matched'] = True
        elif expected_value in actual_value:
            # Partial match
            LOGGER_INFO(f"[verification][value] ✅ Partial match: '{expected_value}' in '{actual_value}'", "GREEN")
            result['status'] = '✅Success (Partial)'
            result['matched'] = True
        else:
            # Mismatch
            LOGGER_ERROR(f"[verification][value] ❌ Mismatch: expected '{expected_value}', got '{actual_value}'", "RED")
            result['status'] = f"❌Failed"
        
        return result

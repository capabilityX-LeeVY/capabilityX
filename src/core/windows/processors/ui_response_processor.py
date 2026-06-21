"""
UI Response Time Processor

This module handles UI response time measurement for controls marked with ui_response: true.
It measures the time from action execution to when the expected state is achieved.
"""

import time
import uiautomation as auto
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING
from rs_sdk.utils.control_handler import ControlHandler


@dataclass
class UIResponseResult:
    """Result of UI response time measurement"""
    success: bool
    response_time_ms: float
    start_time: float
    end_time: float
    expected_state: str
    actual_state: str
    polling_count: int
    error_message: Optional[str] = None


class UIResponseProcessor:
    """Processor for measuring UI response times"""
    
    def __init__(self, control_handler: ControlHandler):
        self.control_handler = control_handler
        self.default_timeout = 60  # Default timeout in seconds
        self.polling_interval = 1  # Poll every 1 second
        
    def measure_ui_response(self, ctrl: Dict[str, Any], action_start_time: float) -> Optional[UIResponseResult]:
        """
        Measure UI response time for controls with ui_response: true
        
        Args:
            ctrl: Control definition containing action and expect_state
            action_start_time: Timestamp when the action was executed
            
        Returns:
            UIResponseResult if ui_response is enabled, None otherwise
        """
        # Check if UI response measurement is enabled for this control
        if not ctrl.get("ui_response", False):
            return None
            
        expect_state = ctrl.get("expect_state", "")
        if not expect_state:
            LOGGER_WARNING(f"UI response enabled but no expect_state defined for control: {ctrl.get('name', 'Unknown')}")
            return None
        
        # Support both string and list formats for expect_state
        if isinstance(expect_state, str):
            expected_states = [expect_state]
        elif isinstance(expect_state, list):
            expected_states = expect_state
        else:
            LOGGER_WARNING(f"Invalid expect_state format for control: {ctrl.get('name', 'Unknown')}. Must be string or list.")
            return None
            
        LOGGER_INFO(f"[UI Response] Starting measurement for control: {ctrl.get('name', 'Unknown')}", "CYAN")
        LOGGER_INFO(f"[UI Response] Expected states: {expected_states}", "CYAN")
        
        # Start polling for expected state
        return self._poll_for_expected_state(
            expected_states=expected_states,
            action_start_time=action_start_time,
            control_name=ctrl.get('name', 'Unknown')
        )
    
    def _poll_for_expected_state(self, expected_states: List[str], action_start_time: float, 
                               control_name: str) -> UIResponseResult:
        """
        Poll the UI until one of the expected states is achieved or timeout occurs
        
        Args:
            expected_states: List of possible expected control states/text
            action_start_time: When the action was executed
            control_name: Name of the control for logging
            
        Returns:
            UIResponseResult with measurement details
        """
        polling_count = 0
        timeout_time = action_start_time + self.default_timeout
        matched_state = None
        
        LOGGER_DEBUG(f"[UI Response] Starting polling with {self.polling_interval}s interval, {self.default_timeout}s timeout")
        
        while time.time() < timeout_time:
            polling_count += 1
            current_time = time.time()
            
            # Get current focused control state
            current_state = self._get_current_control_state()
            
            LOGGER_DEBUG(f"[UI Response] Poll #{polling_count}: Current state = '{current_state}'")
            LOGGER_DEBUG(f"[UI Response] Checking against expected states: {expected_states}")
            
            # Check if any expected state is achieved
            for expected_state in expected_states:
                if self._is_state_matched(current_state, expected_state):
                    matched_state = expected_state
                    response_time_ms = (current_time - action_start_time) * 1000
                    
                    LOGGER_INFO(f"[UI Response] ✅ SUCCESS! Expected state achieved", "GREEN")
                    LOGGER_INFO(f"[UI Response] Control: {control_name}", "GREEN")
                    LOGGER_INFO(f"[UI Response] Matched state: '{matched_state}'", "GREEN")
                    LOGGER_INFO(f"[UI Response] Response time: {response_time_ms:.1f}ms ({response_time_ms/1000:.2f}s)", "GREEN")
                    LOGGER_INFO(f"[UI Response] Polling attempts: {polling_count}", "GREEN")
                    
                    return UIResponseResult(
                        success=True,
                        response_time_ms=response_time_ms,
                        start_time=action_start_time,
                        end_time=current_time,
                        expected_state=matched_state,  # Store the matched state
                        actual_state=current_state,
                        polling_count=polling_count
                    )
            
            # Wait before next poll
            time.sleep(self.polling_interval)
        
        # Timeout occurred
        final_state = self._get_current_control_state()
        response_time_ms = (time.time() - action_start_time) * 1000
        expected_states_str = "', '".join(expected_states)
        
        LOGGER_WARNING(f"[UI Response] ❌ TIMEOUT after {self.default_timeout}s", "RED")
        LOGGER_WARNING(f"[UI Response] Control: {control_name}", "RED")
        LOGGER_WARNING(f"[UI Response] Expected any of: ['{expected_states_str}'], Final state: '{final_state}'", "RED")
        LOGGER_WARNING(f"[UI Response] Polling attempts: {polling_count}", "RED")
        
        return UIResponseResult(
            success=False,
            response_time_ms=response_time_ms,
            start_time=action_start_time,
            end_time=time.time(),
            expected_state=f"Any of: [{expected_states_str}]",  # Store all expected states for logging
            actual_state=final_state,
            polling_count=polling_count,
            error_message=f"Timeout after {self.default_timeout}s"
        )
    
    def _get_current_control_state(self) -> str:
        """
        Get the current focused control's state/text
        
        Returns:
            String representation of current control state
        """
        try:
            current_control = auto.GetFocusedControl()
            if current_control:
                # Get control name/text - this is what we typically match against
                control_name = current_control.Name or ""
                
                # Also include accessible description if available
                try:
                    control_desc = getattr(current_control, 'HelpText', '') or ""
                    if control_desc and control_desc != control_name:
                        return f"{control_name}. {control_desc}".strip()
                except:
                    pass
                    
                return control_name.strip()
            else:
                return ""
        except Exception as e:
            LOGGER_DEBUG(f"[UI Response] Error getting current control state: {e}")
            return ""
    
    def _is_state_matched(self, current_state: str, expected_state: str) -> bool:
        """
        Check if current state matches expected state
        
        Args:
            current_state: Current control state
            expected_state: Expected control state
            
        Returns:
            True if states match, False otherwise
        """
        if not current_state or not expected_state:
            return False
            
        # Clean up strings for comparison
        current_clean = current_state.strip().replace('\n', ' ').replace('\r', ' ')
        expected_clean = expected_state.strip().replace('\n', ' ').replace('\r', ' ')
        
        # Exact match
        if current_clean == expected_clean:
            return True
            
        # Contains match (current state contains expected state)
        if expected_clean.lower() in current_clean.lower():
            return True
            
        return False
    
    def save_ui_response_to_db(self, ui_response_result: UIResponseResult, 
                             test_case: str, control_name: str, report_id: str) -> bool:
        """
        Save UI response measurement to database
        
        Args:
            ui_response_result: Result of UI response measurement
            test_case: Test case name
            control_name: Control name
            report_id: Report ID for linking
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
            
            db_handler = TestCaseDBHandler()
            
            # Prepare data for insertion
            ui_response_data = {
                'report_id': report_id,
                'test_case': test_case,
                'control_name': control_name,
                'response_time_ms': round(ui_response_result.response_time_ms, 1),
                'success': ui_response_result.success,
                'expected_state': ui_response_result.expected_state,
                'actual_state': ui_response_result.actual_state,
                'polling_count': ui_response_result.polling_count,
                'timeout_occurred': not ui_response_result.success,
                'error_message': ui_response_result.error_message
            }
            
            # Insert into database
            success = db_handler.insert_ui_response_record(ui_response_data)
            
            if success:
                LOGGER_INFO(f"[UI Response] Saved to database: {control_name} = {ui_response_result.response_time_ms:.1f}ms", "GREEN")
            else:
                LOGGER_WARNING(f"[UI Response] Failed to save to database: {control_name}", "YELLOW")
                
            return success
            
        except Exception as e:
            LOGGER_WARNING(f"[UI Response] Error saving to database: {e}", "YELLOW")
            return False

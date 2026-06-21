"""
Direct Input Action Strategy

This module contains the DirectInputActionStrategy for direct text input without locating a control.
Similar to direct_key but for inputting text strings directly.
"""

from typing import Dict, Any
from datetime import datetime
import uuid
from core.windows.strategies.action_strategy import ActionStrategy
from common.utils.logger import LOGGER_INFO
import uiautomation as auto


class DirectInputActionStrategy(ActionStrategy):
    """Direct input action strategy (handles 'direct_input') - input text without locating a control"""

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "")
        
        if not value:
            LOGGER_INFO("[operator][Locate][action][direct_input] No value provided!", "YELLOW")
            return ""
        
        # Handle special clear input command
        if value == "clear_input":
            auto.SendKeys("{Ctrl}a{Delete}")
            LOGGER_INFO("[operator][Locate][action][direct_input][clear_input]!", "CYAN")
            return "clear_input"
        
        # Handle dynamic value replacement (e.g., {ai_check_result})
        if "{ai_check_result}" in str(value):
            ai_check_result = getattr(execution_context, 'ai_check_result', None)
            if ai_check_result:
                value = value.replace("{ai_check_result}", str(ai_check_result))
            else:
                value = value.replace("{ai_check_result}", "")
        
        # Handle UUID replacement {uuid} -> unique 8-char identifier
        # This ensures each message is unique and can be verified
        if "{uuid}" in str(value):
            unique_id = uuid.uuid4().hex[:8]  # 8-char unique ID like "a1b2c3d4"
            value = value.replace("{uuid}", unique_id)
            # Store UUID in execution_context for later AI verification
            if execution_context is not None:
                execution_context.last_uuid = unique_id
                LOGGER_INFO(f"[direct_input] UUID stored: {unique_id}", "CYAN")
        
        # Handle timestamp replacement {timestamp} -> current time HH:MM:SS
        if "{timestamp}" in str(value):
            timestamp = datetime.now().strftime("%H:%M:%S")
            value = value.replace("{timestamp}", timestamp)
            # Store timestamp in execution_context for later AI verification
            if execution_context is not None:
                execution_context.last_timestamp = timestamp
                LOGGER_INFO(f"[direct_input] Timestamp stored: {timestamp}", "CYAN")
        
        # Handle date replacement {date} -> current date YYYY-MM-DD
        if "{date}" in str(value):
            date_str = datetime.now().strftime("%Y-%m-%d")
            value = value.replace("{date}", date_str)
        
        # Handle datetime replacement {datetime} -> YYYY-MM-DD HH:MM:SS
        if "{datetime}" in str(value):
            datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            value = value.replace("{datetime}", datetime_str)
        
        # Store the final sent value for AI verification
        if execution_context is not None:
            execution_context.last_sent_message = value
            LOGGER_INFO(f"[direct_input] Message stored for verification: {value}", "CYAN")
        
        # Send the text directly without locating any control
        auto.SendKeys(value)
        LOGGER_INFO(f"[operator][Locate][action][direct_input][{value}]!", "CYAN")
        return value

    def get_action_type(self) -> str:
        return "direct_input"

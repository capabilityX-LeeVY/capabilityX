"""
Input Action Strategy

This module contains the InputActionStrategy for text and image inputs.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from common.utils.logger import LOGGER_INFO
from config.paths import DATASET_IMG_FOLDER_PATH
from common.handler.fileHandler import is_image_file
import uiautomation as auto


class InputActionStrategy(ActionStrategy):
    """Input action strategy for text and image inputs"""
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "{None}")
        
        if value == "clear_input":
            auto.SendKeys("{Ctrl}a{Delete}")
            return "clear_input"
        
        # Resolve variables from ExecutionContext (e.g., ${var_name} or $var_name)
        if execution_context and hasattr(execution_context, 'resolve_variables'):
            value = execution_context.resolve_variables(value)
        
        if "{ai_check_result}" in str(value):
            ai_check_result = getattr(execution_context, 'ai_check_result', None)
            if ai_check_result:
                value = value.replace("{ai_check_result}", str(ai_check_result))
            else:
                value = value.replace("{ai_check_result}", "")
        
        if is_image_file(value):
            image_path = DATASET_IMG_FOLDER_PATH / value
            send_value = str(image_path)
            LOGGER_INFO(f"[operator][Locate][action][input][image] Image path: {send_value}", "CYAN")
        else:
            send_value = value
            LOGGER_INFO(f"[operator][Locate][action][input][text] Text input: {send_value}", "CYAN")

        auto.SendKeys(send_value)
        LOGGER_INFO(f"[operator][Locate][action][input][{send_value}]!", "CYAN")
        return send_value
    
    def get_action_type(self) -> str:
        return "input"

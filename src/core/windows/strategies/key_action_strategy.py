"""
Key Action Strategy

This module contains the KeyActionStrategy for keyboard key actions.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from config.key_map import KEY_MAP
from common.utils.logger import LOGGER_INFO
import uiautomation as auto


class KeyActionStrategy(ActionStrategy):
    """Keyboard key action strategy (handles 'key')"""

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "{SPACE}")
        
        # Resolve variables from ExecutionContext (e.g., ${var_name} or $var_name)
        if execution_context and hasattr(execution_context, 'resolve_variables'):
            value = execution_context.resolve_variables(value)
        
        send_value = KEY_MAP.get(value.lower(), "{SPACE}")
        auto.SendKeys(send_value)
        LOGGER_INFO(f"[operator][Locate][action][key][{send_value}]!", "CYAN")
        return send_value

    def get_action_type(self) -> str:
        return "key"

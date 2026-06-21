"""
Direct Key Action Strategy

This module contains the DirectKeyActionStrategy for direct keyboard key actions.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from config.key_map import KEY_MAP
from common.utils.logger import LOGGER_INFO
import uiautomation as auto


class DirectKeyActionStrategy(ActionStrategy):
    """Direct keyboard key action strategy (handles 'direct_key')"""

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "{SPACE}")
        send_value = KEY_MAP.get(value.lower(), "{SPACE}")
        auto.SendKeys(send_value)
        LOGGER_INFO(f"[operator][Locate][action][direct_key][{send_value}]!", "CYAN")
        return send_value

    def get_action_type(self) -> str:
        return "direct_key"

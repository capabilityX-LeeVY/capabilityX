"""
Shortcut Action Strategy

This module contains the ShortcutActionStrategy for keyboard shortcuts.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from config.shortcut_map import SHORTCUT_MAP
from common.utils.logger import LOGGER_INFO
import pyautogui as autogui
import uiautomation as auto


# Arrow keys that pyautogui doesn't handle well with Webex - use uiautomation instead
ARROW_KEYS = {'up', 'down', 'left', 'right'}

# Mapping from pyautogui key names to uiautomation SendKeys format
UIAUTOMATION_KEY_MAP = {
    'shift': '{Shift}',
    'ctrl': '{Ctrl}',
    'alt': '{Alt}',
    'up': '{UP}',
    'down': '{DOWN}',
    'left': '{LEFT}',
    'right': '{RIGHT}',
    'enter': '{Enter}',
    'tab': '{Tab}',
    'escape': '{Escape}',
    'space': '{Space}',
}


class ShortcutActionStrategy(ActionStrategy):
    """Keyboard shortcut action strategy"""
    
    def _contains_arrow_key(self, keys: list) -> bool:
        """Check if the key combination contains arrow keys"""
        return any(key.lower() in ARROW_KEYS for key in keys)
    
    def _send_via_uiautomation(self, keys: list) -> None:
        """Send key combination using uiautomation SendKeys"""
        sendkeys_str = ''.join(
            UIAUTOMATION_KEY_MAP.get(key.lower(), key) for key in keys
        )
        LOGGER_INFO(f"[operator][shortcut] Using uiautomation SendKeys: {sendkeys_str}", "CYAN")
        auto.SendKeys(sendkeys_str)
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "{None}")
        send_value = SHORTCUT_MAP.get(value, "{None}")
        LOGGER_INFO(f"[operator][Locate][check][shortcut] send_value: {send_value}")
        if send_value:
            # Use uiautomation for shortcuts containing arrow keys (pyautogui doesn't work well with Webex)
            if isinstance(send_value, list) and self._contains_arrow_key(send_value):
                self._send_via_uiautomation(send_value)
            else:
                autogui.hotkey(*send_value)
            LOGGER_INFO(f"[operator][Locate][action][shortcut][{send_value}]!", "CYAN")
        return str(send_value) if send_value else "{None}"
    
    def get_action_type(self) -> str:
        return "shortcut"

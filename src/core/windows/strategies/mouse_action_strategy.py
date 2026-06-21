"""
Mouse Action Strategy

This module contains the MouseActionStrategy for mouse-based UI actions.
It locates a control via UI Automation AutomationId (from the control dataset)
and clicks its centre using pyautogui, bypassing keyboard focus entirely.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from rs_sdk.utils.control_datasets_loader import get_complete_control_metadata_by_name
from common.utils.logger import LOGGER_INFO
import uiautomation as auto
import pyautogui


class MouseActionStrategy(ActionStrategy):
    """Mouse action strategy (handles 'mouse')

    YAML usage::

        - name: "Agree"
          action:
            type: mouse
            value: click          # click | double_click | right_click
            target: "Agree"       # dataset key (optional, defaults to step name)
    """

    # Supported mouse actions mapped to pyautogui functions
    _ACTIONS = {
        "click": pyautogui.click,
        "double_click": pyautogui.doubleClick,
        "right_click": pyautogui.rightClick,
    }

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "click")
        target = ctrl_action.get("target", "")

        if not target:
            LOGGER_INFO("[operator][mouse] No target specified in action", "RED")
            return ""

        # 1. Lookup control metadata from dataset
        metadata = get_complete_control_metadata_by_name(target, platform="windows")
        if not metadata or not metadata.get("control_id"):
            LOGGER_INFO(f"[operator][mouse] No metadata/control_id for target '{target}'", "RED")
            return ""

        control_id = metadata["control_id"]

        # 2. Find control via UI Automation AutomationId
        control = auto.Control(AutomationId=control_id)
        control.SetFocus()

        # 3. Get bounding rectangle and compute centre
        rect = control.BoundingRectangle
        cx = int((rect.left + rect.right) / 2)
        cy = int((rect.top + rect.bottom) / 2)

        # 4. Execute the requested mouse action
        action_func = self._ACTIONS.get(value, pyautogui.click)
        action_func(cx, cy)

        LOGGER_INFO(f"[operator][mouse][{value}] target='{target}' id='{control_id}' at ({cx},{cy})", "CYAN")
        return f"mouse_{value}({cx},{cy})"

    def get_action_type(self) -> str:
        return "mouse"

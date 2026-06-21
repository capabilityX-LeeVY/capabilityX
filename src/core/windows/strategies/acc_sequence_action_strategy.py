"""
Acc Sequence Action Strategy

Handles `acc_sequence` action type — traverses all UI controls in one full circle
using TAB (forward) or SHIFT+TAB (backward), stopping when focus returns to the
starting control.

YAML usage:
    # Forward: TAB one full circle
    - name: "forward navigation"
      action:
        type: acc_sequence
        value: tab

    # Backward: SHIFT+TAB one full circle
    - name: "backward navigation"
      action:
        type: acc_sequence
        value: shift+tab
"""

from typing import Dict, Any, List
from core.windows.strategies.action_strategy import ActionStrategy
from core.windows.controls.control_traverse import ControlTraverser
from core.windows.data_models.action_result import TraverseRecord
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING


_VALUE_MAP = {
    "tab":       "tab",
    "shift+tab": "shift_tab",
    "shift_tab": "shift_tab",
}


class AccSequenceActionStrategy(ActionStrategy):
    """Accessibility full-circle traversal strategy (handles 'acc_sequence')"""

    def __init__(self, control_navigator):
        self.control_navigator = control_navigator  # kept for interface compatibility
        self._traverser = ControlTraverser()
        self.last_traverse_data: List[TraverseRecord] = []  # expose traverse records

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "tab").strip().lower()
        traverse_direction = _VALUE_MAP.get(value)

        if traverse_direction is None:
            LOGGER_WARNING(
                f"[acc_sequence] Unknown value '{value}'. "
                f"Supported: {list(_VALUE_MAP.keys())}. Defaulting to 'tab'."
            )
            traverse_direction = "tab"

        LOGGER_INFO(
            f"[acc_sequence] Starting full-circle traversal "
            f"[direction={traverse_direction}]", "CYAN"
        )

        traverse_all_controls = self._traverser.traverse(direction=traverse_direction)

        self.last_traverse_data = traverse_all_controls
        control_count = len(traverse_all_controls)
        LOGGER_INFO(
            f"[acc_sequence] Full-circle traversal completed "
            f"[direction={traverse_direction}][controls visited={control_count}]", "GREEN"
        )

        return traverse_direction

    def get_action_type(self) -> str:
        return "acc_sequence"

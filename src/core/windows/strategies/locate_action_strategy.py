"""
Locate Action Strategy

Locate-only strategy: the framework still navigates to the control by name
(via the dataset lookup), but no UI action is performed on it.

Use when you want to verify a control exists / can be focused without
clicking, typing, or sending any key to it.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from common.utils.logger import LOGGER_INFO


class LocateActionStrategy(ActionStrategy):
    """Locate-only action strategy (handles 'locate')."""

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        LOGGER_INFO("[operator][Locate][action][locate] Locate only, no action performed", "CYAN")
        return ""

    def get_action_type(self) -> str:
        return "locate"

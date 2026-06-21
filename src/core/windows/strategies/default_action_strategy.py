"""
Default Action Strategy

This module contains the DefaultActionStrategy for default actions.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy


class DefaultActionStrategy(ActionStrategy):
    """Default action strategy"""
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        return "{SPACE}"
    
    def get_action_type(self) -> str:
        return "default"

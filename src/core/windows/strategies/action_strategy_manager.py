"""
Action Strategy Manager

This module contains the ActionStrategyManager for managing action strategies.
"""

from typing import Dict, Optional, Any
from core.windows.strategies.action_strategy import ActionStrategy
from core.windows.strategies.key_action_strategy import KeyActionStrategy
from core.windows.strategies.direct_key_action_strategy import DirectKeyActionStrategy
from core.windows.strategies.direct_input_action_strategy import DirectInputActionStrategy
from core.windows.strategies.input_action_strategy import InputActionStrategy
from core.windows.strategies.shortcut_action_strategy import ShortcutActionStrategy
from core.windows.strategies.api_action_strategy import ApiActionStrategy
from core.windows.strategies.function_action_strategy import FunctionActionStrategy
from core.windows.strategies.verify_action_strategy import VerifyActionStrategy
from core.windows.strategies.default_action_strategy import DefaultActionStrategy
from core.windows.strategies.acc_sequence_action_strategy import AccSequenceActionStrategy
from core.windows.strategies.locate_action_strategy import LocateActionStrategy
from core.windows.strategies.mouse_action_strategy import MouseActionStrategy


class ActionStrategyManager:
    """Action strategy manager - manages and executes different action strategies"""
    
    def __init__(self, control_handler):
        self._strategies: Dict[str, ActionStrategy] = {}
        self._register_default_strategies(control_handler)
    
    def _register_default_strategies(self, control_handler):
        """Register default action strategies"""
        strategies = [
            KeyActionStrategy(),
            DirectKeyActionStrategy(),
            DirectInputActionStrategy(),
            InputActionStrategy(),
            ShortcutActionStrategy(),
            ApiActionStrategy(),
            FunctionActionStrategy(control_handler),
            VerifyActionStrategy(),
            DefaultActionStrategy(),
            LocateActionStrategy(),
            MouseActionStrategy()
        ]

        for strategy in strategies:
            self.register_strategy(strategy.get_action_type(), strategy)
    
    def register_strategy(self, action_type: str, strategy: ActionStrategy):
        """Register a strategy for specific action type"""
        self._strategies[action_type] = strategy
    
    def get_strategy(self, action_type: str) -> ActionStrategy:
        """Get strategy by action type, return default if not found"""
        return self._strategies.get(action_type, self._strategies["default"])
    
    def execute_action(self, action_type: str, ctrl_action: Dict[str, Any], 
                      execution_context, dependencies: Optional[Dict[str, Any]] = None) -> Any:
        """Execute action using appropriate strategy"""
        strategy = self.get_strategy(action_type)
        return strategy.execute(ctrl_action, execution_context, dependencies or {})

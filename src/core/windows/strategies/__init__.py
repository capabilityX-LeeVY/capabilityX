"""
Action Strategy Module - Strategy Pattern Implementation for Control Actions

This module contains all action execution strategies following the Strategy pattern.
"""

from core.windows.strategies.action_strategy import ActionStrategy
from core.windows.strategies.key_action_strategy import KeyActionStrategy
from core.windows.strategies.direct_key_action_strategy import DirectKeyActionStrategy
from core.windows.strategies.direct_input_action_strategy import DirectInputActionStrategy
from core.windows.strategies.input_action_strategy import InputActionStrategy
from core.windows.strategies.shortcut_action_strategy import ShortcutActionStrategy
from core.windows.strategies.api_action_strategy import ApiActionStrategy
from core.windows.strategies.function_action_strategy import FunctionActionStrategy
from core.windows.strategies.default_action_strategy import DefaultActionStrategy
from core.windows.strategies.action_strategy_manager import ActionStrategyManager

__all__ = [
    'ActionStrategy',
    'KeyActionStrategy',
    'DirectKeyActionStrategy',
    'DirectInputActionStrategy',
    'InputActionStrategy', 
    'ShortcutActionStrategy',
    'ApiActionStrategy',
    'FunctionActionStrategy',
    'DefaultActionStrategy',
    'ActionStrategyManager'
]

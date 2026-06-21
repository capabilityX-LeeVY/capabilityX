"""
Shared Action Strategy Module - Cross-platform strategy base classes and implementations.

Platform-independent strategies live here. Platform-specific strategies remain
in their respective platform directories (e.g. core/windows/strategies/).
"""

from core.strategies.action_strategy import ActionStrategy
from core.strategies.api_action_strategy import ApiActionStrategy

__all__ = [
    'ActionStrategy',
    'ApiActionStrategy',
]

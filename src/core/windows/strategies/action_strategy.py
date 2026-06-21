"""
Abstract Action Strategy Base Class

Backward-compatible re-export. The canonical definition now lives in
core.strategies.action_strategy so it can be used cross-platform.
"""

from core.strategies.action_strategy import ActionStrategy

__all__ = ['ActionStrategy']

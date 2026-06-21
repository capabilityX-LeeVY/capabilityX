"""
Data Classes Module - Type-safe data structures for Control Operations

This module contains all dataclass definitions used across the control automation system.
"""

from core.windows.data_models.locate_target import LocateTarget
from core.windows.data_models.focused_control_metadata import FocusedControlMetadata
from core.windows.data_models.image_data import ImageData
from core.windows.data_models.action_result import ActionResult
from core.windows.data_models.expectation_result import ExpectationResult
from core.windows.data_models.ai_check_result import AICheckResult
from core.windows.data_models.locate_result import LocateResult
from core.windows.data_models.execution_context import ExecutionContext
from core.windows.data_models.control_step_result import ControlStepResult

__all__ = [
    'LocateTarget',
    'FocusedControlMetadata',
    'ImageData', 
    'ActionResult',
    'ExpectationResult',
    'AICheckResult',
    'LocateResult',
    'ExecutionContext',
    'ControlStepResult'
]

"""
Locate Result Data Model

This module contains the LocateResult dataclass for control location results.
"""

from dataclasses import dataclass
from typing import Optional
from core.windows.data_models.focused_control_metadata import FocusedControlMetadata


@dataclass
class LocateResult:
    """Control location result data class"""
    success: bool = False
    metadata: Optional[FocusedControlMetadata] = None
    control_name: Optional[str] = None

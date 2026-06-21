"""
Control Step Result Data Model

This module contains the ControlStepResult dataclass for control step processing results.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ControlStepResult:
    """Control step processing result data class"""
    result: bool
    expect_state: str
    control_metadata: Optional[Dict[str, Any]] = None
    ai_check_failed: bool = False  # Indicates if AI check failed for this step

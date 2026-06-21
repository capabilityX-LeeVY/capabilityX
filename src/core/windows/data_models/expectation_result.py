"""
Expectation Result Data Model

This module contains the ExpectationResult dataclass for expected state verification.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExpectationResult:
    """Expected state verification result data class"""
    state: str = "Success"
    expected: Optional[str] = None
    actual: Optional[str] = None

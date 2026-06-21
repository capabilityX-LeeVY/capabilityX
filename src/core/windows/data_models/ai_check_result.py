"""
AI Check Result Data Model

This module contains the AICheckResult dataclass for AI check results.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AICheckResult:
    """AI check result data class"""
    llm_response: Optional[str] = ""
    reference_image_path: Optional[str] = ""

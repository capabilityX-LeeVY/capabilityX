"""Locate Target Data Model

This module contains the LocateTarget dataclass for target control information to locate.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LocateTarget:
    """Locate target data class - contains target control information to locate from YAML"""
    name: Optional[str] = None
    id: Optional[str] = None
    test_case_step_description: Optional[str] = None
    action: Optional[Dict[str, Any]] = None
    action_type: str = "key"
    expect_state: Optional[str] = None
    ai_check: Optional[Dict[str, Any]] = None
    platform: Optional[str] = None
    optional: bool = False
    navigated: bool = True  # If False, skip locate and directly execute action
    match_mode: str = "dataset"  # "dataset" | "semantic"
    similarity_threshold: float = 0.55
    
    def __post_init__(self):
        if self.action is None:
            self.action = {"type": "key", "value": "SPACE"}

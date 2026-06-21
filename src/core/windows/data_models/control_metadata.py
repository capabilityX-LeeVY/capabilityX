"""
Control Metadata Data Model

This module contains the ControlMetadata dataclass for basic control information.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ControlMetadata:
    """Control metadata data class - contains basic control information"""
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
    
    def __post_init__(self):
        if self.action is None:
            self.action = {"type": "key", "value": "SPACE"}

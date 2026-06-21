"""
Extracted Control Metadata Data Model

This module contains the ExtractedControlMetadata dataclass for detailed control information.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractedControlMetadata:
    """Extracted control detailed information data class"""
    current_control_type_name: Optional[str] = None
    full_description: Optional[str] = None
    control_accesskey: Optional[str] = None
    current_control_level1_window_name: Optional[str] = None
    current_control_level2_window_name: Optional[str] = None
    parent_name: Optional[str] = None
    parent_type: Optional[str] = None
    default_action: Optional[str] = None
    legacy_value: Optional[str] = None
    legacy_role: Optional[str] = None
    legacy_state: Optional[str] = None
    control_pid: Optional[int] = None

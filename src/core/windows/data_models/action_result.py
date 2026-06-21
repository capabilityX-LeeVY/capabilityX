"""
Action Result Data Model

This module contains the ActionResult dataclass for action execution results.
"""

from dataclasses import dataclass
from typing import Optional, Any, List
from datetime import datetime
from core.windows.data_models.image_data import ImageData


@dataclass
class TraverseRecord:
    """Single control record from acc_sequence traversal"""
    order: int                          # Tab order (1-based)
    control_name: str                   # Control name
    control_id: str                     # AutomationId
    control_image_path: Optional[str] = None   # Screenshot absolute path
    window_image_path: Optional[str] = None    # Window screenshot path (optional)
    # UIA metadata for screen reader analysis
    control_type: Optional[str] = None         # Localized control type name (e.g. "button")
    full_description: Optional[str] = None     # Full description attribute
    access_key: Optional[str] = None           # Access key
    legacy_value: Optional[str] = None         # Legacy value attribute
    legacy_role: Optional[str] = None          # Legacy role attribute
    legacy_state: Optional[str] = None         # Legacy state attribute
    parent_name: Optional[str] = None          # Parent control name
    parent_type: Optional[str] = None          # Parent control type
    window_level1: Optional[str] = None        # Window level 1 hierarchy
    window_level2: Optional[str] = None        # Window level 2 hierarchy
    default_action: Optional[str] = None       # Default action attribute


@dataclass
class ActionResult:
    """Action execution result data class"""
    success: bool = False
    action_type: str = "none"
    send_value: Optional[Any] = None  # Allow str, list or other types
    wait_time: int = 1
    image_path: Optional[str] = None  # Deprecated: use image_data.control_window_image_path instead
    image_data: Optional[ImageData] = None
    ui_response_result: Optional[Any] = None  # UI response measurement result
    step_start_time: Optional[datetime] = None
    step_end_time: Optional[datetime] = None
    step_duration_ms: Optional[int] = None
    value_verify_result: Optional[str] = None  # Value verification result (✅Success / ❌Failed / N/A)
    traverse_data: Optional[List[TraverseRecord]] = None  # acc_sequence traversal records
    
    @property
    def control_image_path(self) -> Optional[str]:
        """Get control image path from image_data"""
        return self.image_data.control_image_path if self.image_data else None
    
    @property 
    def control_window_image_path(self) -> Optional[str]:
        """Get control window image path from image_data"""
        return self.image_data.control_window_image_path if self.image_data else None

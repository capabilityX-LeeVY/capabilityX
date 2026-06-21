"""
Image Data Model

This module contains the ImageData dataclass for image data containers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageData:
    """Image data container class"""
    pre_control_image_bytes: Optional[bytes] = None
    control_image_bytes: Optional[bytes] = None
    window_image_bytes: Optional[bytes] = None
    control_image_path: Optional[str] = None
    control_window_image_path: Optional[str] = None
    # Deprecated: use control_window_image_path instead
    image_path: Optional[str] = None

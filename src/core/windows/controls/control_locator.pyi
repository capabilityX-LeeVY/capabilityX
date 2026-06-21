"""
Type stub file for control_locator.py

This file provides type hints and interface definitions for classes in control_locator.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import uiautomation as auto

class ControlLocator:
    """
    Class for locating specific UI controls based on metadata.
    """

    current_control: Any

    control_handler: Any

    control_navigator: Any

    def __init__(self: Any) -> None: ...

    def locate_control(self: Any, control_meta: Any, control_index: Any) -> Any: ...

    def advanced_locate_control(self: Any, current_level: Any, target_level: Any, control_name: Any, control_meta: Any = ..., control_visited: Any = ..., control_index: Any = ...) -> Any: ...

    def _optimize_ui_path(self: Any, control_path: Any) -> Any: ...

    def _locate_by_window(self: Any, control_meta: Any) -> Any: ...

    def _locate_by_path(self: Any, start_level: Any, control_name: Any, control_meta: Any = ..., control_index: Any = ..., full_path_flag: Any = ...) -> Any: ...

    def _update_control_level_from_prefix(self: Any, control_name: Any) -> Any: ...

    def locate_control_handler(self: Any, control_meta: Any, close_flag: Any = ..., locate_id_flag: Any = ...) -> Any: ...

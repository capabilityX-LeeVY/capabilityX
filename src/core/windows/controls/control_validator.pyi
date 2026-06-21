"""
Type stub file for control_validator.py

This file provides type hints and interface definitions for classes in control_validator.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import uiautomation as auto

class ValidationResult:
    """
    ValidationResult class for WRS automation.
    """

    SUCCESS: int

    NO_TRAVERSE: int

    LOSS_FOCUS: Any

    NOT_FOUND: Any

    INVALID_TYPE: Any

    TIMEOUT: Any

    LOOP: Any

    UNKNOWN_ERROR: Any

    CANNOT_ESC: Any

    NO_CONTROL_NAME: Any

    OUT_SIDE_PROCESS: Any

class ControlValidator:
    """
    Class for validating UI controls and their properties.
    """

    current_control: Any

    control_validator_handler: Any

    control_locator: Any

    control_handler: Any

    workflow_config: Any

    def __init__(self: Any) -> None: ...

    def validate_control(self: Any, control_meta: Any, from_control_name: Any, CURRENT_APP_PID: Any, control_index: Any) -> ValidationResult: ...

    def generate_control_path_hash(self: Any, control_name: Any, from_control: Any) -> Any: ...

    def validate_default_button(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_list_items(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_menu_items(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_item(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_menu_button(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_tree(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_radio_button(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_checkbox(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_combo_box(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_tab(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_edit(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

    def validate_custom(self: Any, control_name: Any, CURRENT_APP_PID: Any) -> ValidationResult: ...

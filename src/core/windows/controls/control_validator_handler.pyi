"""
Type stub file for control_validator_handler.py

This file provides type hints and interface definitions for classes in control_validator_handler.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import uiautomation as auto

class ControlValidatorHandler:
    """
    Handler class for control validation operations.
    """

    current_control: Any

    control_handler: Any

    control_db: Any

    def __init__(self: Any) -> None: ...

    def handle_control_focus_loss(self: Any, proccess_id: Any) -> Any: ...

    def is_validated_all_controls_in_window(self: Any, control_id_hash: Any) -> Any: ...

    def handle_control_focus_outside_process(self: Any, proccess_id: Any) -> Any: ...

    def handle_control_infinite_loop(self: Any, traverse_controls: Any, control_name: Any) -> Any: ...

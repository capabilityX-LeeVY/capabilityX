"""
Type stub file for control_navigator.py

This file provides type hints and interface definitions for classes in control_navigator.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import uiautomation as auto

# Type aliases
ControlMetadataDict = Dict[str, Any]
TraversalResult = Tuple[List[str], List[str], bool, List[ControlMetadataDict]]
ValidationStatus = int
ControlType = int
ControlLevel = int

class ControlNavigator:
    """
    Main class for navigating and traversing UI controls in automated testing.
    """

    workflow_config: Any

    control_factory: Any

    current_control: Any

    control_recorder: Any

    navigator_handler: Any

    control_handler: Any

    control_metadata: Any

    validator_handler: Any

    control_db: Any

    order: int

    pre_control_name_up: Optional[Any]

    pre_control_name_down: Optional[Any]

    pre_control_name_left: Optional[Any]

    pre_control_name_right: Optional[Any]

    pre_control_custom_accesskey_left: Optional[Any]

    pre_control_custom_accesskey_right: Optional[Any]

    pre_control_custom_utbadge_up: Optional[Any]

    pre_control_custom_utbadge_down: Optional[Any]

    pre_control_combox_down: Optional[Any]

    pre_control_combox_up: Optional[Any]

    pre_control_list_down: Optional[Any]

    pre_control_list_up: Optional[Any]

    pre_control_group_button_left: Optional[Any]

    pre_control_group_button_right: Optional[Any]

    pre_control_full_description_left: Optional[Any]

    pre_control_full_description_right: Optional[Any]

    pre_control_menu_item_up: Optional[Any]

    pre_control_menu_item_down: Optional[Any]

    flag_tree: str

    flag_tab: str

    flag_combox: str

    flag_custom_accesskey: str

    flag_list: str

    flag_group_button: str

    flag_full_description: str

    flag_custom_utbadge: str

    flag_radio: str

    flag_menu_item: str

    prefix_current_control_name: Optional[Any]

    cropped_image: Any

    def _id_matches(current_id: Any, locate_id: Any) -> bool: ...

    def __init__(self: Any) -> None: ...

    def control_navigator(self: Any, level: Any = ..., from_control: Any = ..., process_id: Any = ..., is_validated: Any = ..., is_recorded: Any = ..., is_located: Any = ..., locate_control_meta: Any = ..., close_flag: Any = ..., locate_id_flag: Any = ..., locate_optimized_by_window_flag: Any = ..., test_case_flag: Any = ...) -> TraversalResult: ...

    def _process_control_metadata_recording(self: Any, control_metadata: Any, traverse_all_controls: Any, from_control: Any, is_recorded: Any, is_validated: Any, level: Any, flag_back: Any) -> Any: ...

    def get_keyboard_action(self: Any, flag_control_type: Any, current_control_name: Any, current_control_id: Any, flag_parent_type: Any, flag_accesskey: Any = ..., pre_control_class_name: Any = ..., pre_control_parent_type: Any = ...) -> Any: ...

    def handle_control_traversal(self: Any, flag_control_type: Any, current_control_name: Any, current_control_id: Any, flag_parent_type: Any, init_control_name: Any, init_control_id_hash: Any, is_located: Any, from_control: Any, visited_controls: Any, tree_visited: Any, tab_visited: Any, radio_visited: Any, menu_item_visited: Any, text_visited: Any, combox_visited: Any, button_list_visited: Any, custom_visited: Any, list_visited: Any, group_button_visited: Any, full_description_button_visited: Any = ...) -> Union[str, ControlMetadataDict]: ...

    def set_control_validated_status(self: Any, control_name: Any, control_type: Any, control_path_hash: Any, control_id: Any, control_class_name: Any) -> ValidationStatus: ...

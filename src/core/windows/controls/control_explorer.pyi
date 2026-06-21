"""
Type stub file for control_explorer.py

This file provides type hints and interface definitions for classes in control_explorer.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union

class ControlExplorer:
    """
    Class for exploring and discovering UI controls in the application.
    """

    order: int

    process_id: int

    control_recorder: Any

    VALIDATEDBEFORECONTROLS: List[Any]

    post_validation_controls: List[Any]

    control_metadata: List[Any]

    new_controls: List[Any]

    settings: Any

    workflow_config: Any

    conf_language: Any

    skipfromcontrol: Optional[Any]

    is_temporary: int

    is_validated: int

    navigator: Any

    validator: Any

    validator_handler: Any

    control_handler: Any

    current_control: Any

    control_db: Any

    window_handler: Any

    terminate_traversal: int

    cropped_image: Any

    apply_language: Any

    SkipValidation: Any

    def __init__(self: Any) -> None: ...

    def control_explorer(self: Any) -> Any: ...

    def walk_for_explorer(self: Any, new_controls: Any = ..., control_metadata: Any = ..., from_control: Any = ..., deeplevel: Any = ..., index_prefix: Any = ...) -> Any: ...

    def handle_control_skip(self: Any, control: Any, control_id: Any, from_control: Any, control_type: Any, is_validated_control_path_hash_status: Any, is_validated_status: Any, control_id_hash: Any, current_index: Any) -> Any: ...

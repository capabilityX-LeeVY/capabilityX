"""
Control Metadata Processor

This module contains the ControlMetadataProcessor for handling control metadata 
preparation and extraction.
"""

from typing import Dict, Any
from core.windows.data_models.locate_target import LocateTarget
from core.windows.data_models.focused_control_metadata import FocusedControlMetadata
from rs_sdk.utils import control_datasets_loader
from rs_sdk.factory.control_factory import ControlFactory


class ControlMetadataProcessor:
    """Control metadata processor - handles target parsing and focused control extraction"""
    
    def __init__(self):
        self.current_control = ControlFactory().create_control()
    
    def parse_locate_target(self, ctrl: Dict[str, Any], platform: str) -> LocateTarget:
        """Parse locate target from raw control definition (from YAML)"""
        test_case_step_description = ctrl.get("name", None)
        action = ctrl.get("action", {}) if isinstance(ctrl.get("action", {}), dict) else {}

        match_mode = str(ctrl.get("match_mode", action.get("match_mode", "dataset"))).strip().lower()
        if match_mode not in {"dataset", "semantic"}:
            match_mode = "dataset"

        raw_threshold = ctrl.get("similarity_threshold", action.get("similarity_threshold", 0.55))
        try:
            similarity_threshold = float(raw_threshold)
        except (TypeError, ValueError):
            similarity_threshold = 0.55

        # Keep the threshold in a safe range to reduce false positives.
        similarity_threshold = max(0.0, min(1.0, similarity_threshold))

        ctrl_name, ctrl_id = control_datasets_loader.get_control_metadata_by_name(test_case_step_description, platform=platform)

        if match_mode == "semantic" and test_case_step_description:
            # Semantic mode uses the step description as the primary locate target
            # and does not rely on exact dataset ID/name mapping.
            ctrl_name = test_case_step_description
            ctrl_id = None
        
        return LocateTarget(
            name=ctrl_name,
            id=ctrl_id,
            test_case_step_description=test_case_step_description,
            action=ctrl.get("action", {"type": "key", "value": "SPACE"}),
            action_type=ctrl.get("action", {}).get("type", "key"),
            expect_state=ctrl.get("expect_state", None),
            ai_check=ctrl.get("ai_check", None),
            platform=ctrl.get("platforms", None),
            optional=ctrl.get("optional", False),
            navigated=ctrl.get("navigated", True),  # Default to True (normal locate behavior)
            match_mode=match_mode,
            similarity_threshold=similarity_threshold
        )
    
    def extract_focused_control(self) -> FocusedControlMetadata:
        """Extract detailed metadata from currently focused control (from UI)
        
        Gets the current focused control internally using ControlFactory,
        eliminating the need to pass control object through multiple layers.
        """
        # Get current focused control
        self.current_control.refresh()
        
        current_control_type_name = self.current_control.ControlTypeName
        current_control_name = self.current_control.ControlName
        full_description = self.current_control.ControlFullDescription
        control_accesskey = self.current_control.ControlAccessKey
        parent_control = self.current_control.ControlParent
        parent_name = parent_control.get("name", "None")
        parent_type = parent_control.get("type", "None")
        reassigned_ancestors = self.current_control.ControlAncestorLevelsElements
        current_control_level1_window_name = reassigned_ancestors["level1"]["name"]
        current_control_level2_window_name = reassigned_ancestors["level2"]["name"]
        
        # Get control process ID
        control_pid = getattr(self.current_control, 'ControlProcessID', None)
        
        # Get legacy properties
        default_action, legacy_value, legacy_role, legacy_state = self.current_control.ControlLegacyProperties
        
        return FocusedControlMetadata(
            current_control_type_name=current_control_type_name,
            current_control_name=current_control_name,
            full_description=full_description,
            control_accesskey=control_accesskey,
            current_control_level1_window_name=current_control_level1_window_name,
            current_control_level2_window_name=current_control_level2_window_name,
            parent_name=parent_name,
            parent_type=parent_type,
            default_action=default_action,
            legacy_value=legacy_value,
            legacy_role=legacy_role,
            legacy_state=legacy_state,
            control_pid=control_pid
        )

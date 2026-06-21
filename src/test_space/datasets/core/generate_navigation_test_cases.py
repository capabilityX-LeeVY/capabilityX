#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Navigation Test Cases from Core Controls Dataset with Hierarchical Slicing

This tool reads the go_to_core_controls.json dataset and generates YAML test cases
for each control based on its control_ui_path navigation steps. It supports the
hierarchical slicing design where child test cases can include parent test cases
as pre-conditions.

Features:
- Filter by hierarchical depth (e.g., depth <= 5)
- Auto-generate test case names from control names
- Create YAML files with navigation steps
- Support for different action types (key, input)
- Hierarchical slicing with pre_conditions support
- Automatic parent control detection and pre-condition generation
- Support for meeting_ui_path (sliced path) and control_ui_path (full path)

Usage:
    python generate_navigation_test_cases.py --max-depth 5
    python generate_navigation_test_cases.py --max-depth 5 --output-dir custom_dir
"""

import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any


class NavigationTestCaseGenerator:
    """Generate navigation test cases from core controls dataset."""
    
    def __init__(self, input_file: str = None, output_dir: str = None, max_depth: int = None, 
                 slice_points: List[int] = None, custom_dataset: str = None, 
                 pre_conditions_prefix: str = None, check_points: List[str] = None,
                 config_file: str = None):
        """
        Initialize the generator.
        
        Args:
            input_file: Path to go_to_core_controls.json (default: from config)
            output_dir: Directory to save generated test cases (default: from config)
            max_depth: Maximum hierarchical depth to include (default: from config)
            slice_points: List of depths where to create slices (default: from config)
            custom_dataset: Custom dataset reference for YAML files (default: from config)
            pre_conditions_prefix: Path prefix for pre_conditions (default: from config)
            check_points: List of test validation checkpoints (default: from config)
            config_file: Path to configuration file (default: test_case_generation_config.json)
        """
        # Load configuration file
        config_path = Path(config_file) if config_file else Path(__file__).parent / "config" / "test_case_generation_config.json"
        config = self._load_config(config_path)
        
        # Set base directory for relative paths
        self.base_dir = Path(__file__).parent
        
        # Use parameters if provided, otherwise use config values
        self.input_file = Path(input_file) if input_file else self.base_dir / config['dataset']['input_file']
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / config['generation']['output_dir']
        self.max_depth = max_depth if max_depth is not None else config['generation']['max_depth']
        self.slice_points = slice_points if slice_points else config['generation']['slice_points']
        self.optional_steps = config['generation'].get('optional_steps', [])
        self.step_display_names = config['generation'].get('step_display_names', {})
        self.custom_dataset = custom_dataset if custom_dataset else config['dataset']['custom_dataset_reference']
        self.pre_conditions_prefix = pre_conditions_prefix if pre_conditions_prefix else config['test_case_template']['pre_conditions_path_prefix']
        self.check_points = check_points if check_points is not None else config['test_case_template'].get('check_points', [])
        
        # Load categorization configuration
        self.categorization_enabled = config['generation'].get('categorization', {}).get('enabled', False)
        self.categories = config['generation'].get('categorization', {}).get('categories', [])
        self.category_overrides = config['generation'].get('categorization', {}).get('category_overrides', {})
        
        # Load functional categories (explicit control name -> directory mappings)
        functional_config = config['generation'].get('categorization', {}).get('functional_categories', {})
        self.functional_categories_enabled = functional_config.get('enabled', False)
        self.functional_mappings = functional_config.get('mappings', {})
        
        # Load exclusion list for manually maintained test cases
        self.exclusion_list = self._load_exclusion_list()
        
        # Print configuration info
        if self.optional_steps:
            print(f"[i] Loaded {len(self.optional_steps)} optional step name(s): {', '.join(self.optional_steps[:3])}")
        if self.step_display_names:
            print(f"[i] Loaded {len(self.step_display_names)} step display name override(s)")
        if self.category_overrides:
            print(f"[i] Loaded {len(self.category_overrides)} category override(s)")
        if self.functional_mappings:
            print(f"[i] Loaded {len(self.functional_mappings)} functional category mapping(s)")
        if self.exclusion_list:
            print(f"[i] Loaded {len(self.exclusion_list)} excluded test case(s) (manual)")
        
        # Load raw dataset for looking up optional attributes and UI name mappings
        # Use the FULL raw dataset (go_to_core_controls_raw.json) to ensure all controls
        # in UI paths can be found, not just the filtered selected controls
        # This enables proper mapping from UI names like " Accept" to dataset keys like "Accept"
        raw_dataset_path = self.base_dir / 'data' / 'go_to_core_controls_raw.json'
        if not raw_dataset_path.exists():
            # Fallback to input_file if raw file doesn't exist
            raw_dataset_path = self.input_file
        self.raw_controls = self._load_raw_controls(raw_dataset_path)
    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Failed to load config from {config_path}: {e}")
            print("[i] Using default values")
            return {
                'dataset': {'input_file': 'data/go_to_core_controls.json', 'custom_dataset_reference': 'core/data/go_to_core_controls_raw'},
                'generation': {'output_dir': '../../test_cases/navigations/preconditions', 'max_depth': 10, 'slice_points': [4, 7]},
                'test_case_template': {'pre_conditions_path_prefix': 'navigations/preconditions', 'check_points': ['Keyboard Navigation']}
            }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_exclusion_list(self) -> set:
        """Load list of manually maintained test cases to exclude from generation."""
        exclusion_file = Path(__file__).parent / 'config' / 'manual_test_cases_exclusion.json'
        try:
            if exclusion_file.exists():
                with open(exclusion_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('exclusion_list', []))
        except Exception as e:
            print(f"[!] Failed to load exclusion list: {e}")
        return set()
    
    def _load_raw_controls(self, raw_dataset_path: Path) -> List[Dict[str, Any]]:
        """Load raw controls dataset for optional attribute lookup."""
        try:
            if raw_dataset_path.exists():
                with open(raw_dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert dict format to list format if needed
                if isinstance(data, dict):
                    controls_list = []
                    for name, control_data in data.items():
                        if 'name' not in control_data:
                            control_data['name'] = name
                        controls_list.append(control_data)
                    return controls_list
                else:
                    return data
        except Exception as e:
            print(f"[!] Warning: Could not load raw controls from {raw_dataset_path}: {e}")
        return []
    
    def load_controls_data(self) -> List[Dict[str, Any]]:
        """Load controls from JSON file."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert dict format to list format if needed
        if isinstance(data, dict):
            # New format: {"control_name": {"metadata": ...}}
            controls_list = []
            for name, control_data in data.items():
                if 'name' not in control_data:
                    control_data['name'] = name
                controls_list.append(control_data)
            return controls_list
        else:
            # Old format: [{"name": ..., "metadata": ...}, ...]
            return data
    
    def find_control_key_by_ui_name(self, ui_name: str) -> str:
        """
        Find dataset key for a given UI name from control_ui_path.
        This ensures test case steps use dataset keys, not intermediate UI names.
        
        Args:
            ui_name: Name from control_ui_path or meeting_ui_path
            
        Returns:
            Dataset key (control['name']) if found, otherwise original ui_name
        """
        # First, check if ui_name is already a dataset key
        for ctrl in self.raw_controls:
            if ctrl.get('name') == ui_name:
                return ui_name
        
        # If not, search for control where this ui_name appears as the LAST step in control_ui_path
        # This matches controls where ui_name is the final action
        for ctrl in self.raw_controls:
            ctrl_metadata = ctrl.get('metadata', {}).get('windows', {})
            ui_path = ctrl_metadata.get('control_ui_path', [])
            if ui_path and ui_path[-1] == ui_name:
                # Found a control that ends with this UI name
                return ctrl.get('name', ui_name)
        
        # If still not found, search for control_name match
        for ctrl in self.raw_controls:
            ctrl_metadata = ctrl.get('metadata', {}).get('windows', {})
            control_name = ctrl_metadata.get('control_name', '')
            if control_name == ui_name:
                return ctrl.get('name', ui_name)
        
        # Fallback: return original name
        return ui_name
    
    def filter_by_depth(self, controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter controls by hierarchical depth.
        
        Args:
            controls: List of control dictionaries
            
        Returns:
            Filtered list of controls with depth <= max_depth
        """
        filtered = []
        for control in controls:
            metadata = control.get('metadata', {}).get('windows', {})
            depth_str = metadata.get('shortest_hierarchical_level', '999')
            
            # Parse depth (e.g., "2.1.1.2" -> depth 4)
            depth = len(depth_str.split('.'))
            
            if depth <= self.max_depth:
                filtered.append(control)
        
        return filtered
    
    def get_category_for_control(self, control_name: str, depth: int) -> str:
        """Get category directory name for a control, considering overrides.
        
        Args:
            control_name: Name of the control
            depth: Hierarchical depth
            
        Returns:
            Category directory name or empty string if categorization disabled
        """
        # Priority 1: Check functional_categories mappings (explicit control name -> directory)
        if self.functional_categories_enabled and control_name in self.functional_mappings:
            return self.functional_mappings[control_name]
        
        if not self.categorization_enabled or not self.categories:
            return ""
        
        # Priority 2: Check category_overrides (manual overrides for depth-based categories)
        if control_name in self.category_overrides:
            return self.category_overrides[control_name]
        
        # Priority 3: Fall back to depth-based categorization
        return self.get_category_for_depth(depth)
    
    def get_category_for_depth(self, depth: int) -> str:
        """Get category directory name for given depth.
        
        Args:
            depth: Hierarchical depth
            
        Returns:
            Category directory name or empty string if categorization disabled
        """
        if not self.categorization_enabled or not self.categories:
            return ""
        
        for category in self.categories:
            depth_range = category.get('depth_range', [])
            if len(depth_range) == 2:
                min_depth, max_depth = depth_range
                if min_depth <= depth <= max_depth:
                    return category['name']
        
        return ""
    
    def sanitize_filename(self, name: str, max_length: int = 100) -> str:
        """
        Convert control name to valid filename with length limit.
        
        Args:
            name: Control name (e.g., " Join a meeting")
            max_length: Maximum filename length (default: 100, to avoid Windows path limits)
            
        Returns:
            Sanitized filename (e.g., "join_a_meeting")
        """
        # Remove leading/trailing whitespace
        name = name.strip()
        # Convert to lowercase
        name = name.lower()
        # Replace spaces and special characters with underscores
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        
        # Limit length (reserve space for .yaml extension and depth prefix)
        if len(name) > max_length:
            name = name[:max_length].rstrip('_')
        
        return name
    
    def determine_action_type(self, control_name: str) -> str:
        """
        Determine action type based on control name.
        
        Args:
            control_name: Name of the control
            
        Returns:
            Action type: 'input' for input fields, 'key' for buttons/other
        """
        input_keywords = ['email', 'password', 'username', 'address', 'name', 'code', 'number']
        control_lower = control_name.lower()
        
        for keyword in input_keywords:
            if keyword in control_lower:
                return 'input'
        
        return 'key'
    
    def get_variable_name(self, control_name: str) -> str:
        """
        Get standardized variable name for input controls.
        
        Args:
            control_name: Name of the control
            
        Returns:
            Standardized variable name (e.g., 'email', 'password', 'username')
        """
        control_lower = control_name.lower()
        
        # Map common patterns to standard variable names
        if 'email' in control_lower:
            return 'email'
        elif 'password' in control_lower:
            return 'password'
        elif 'username' in control_lower or 'user name' in control_lower:
            return 'username'
        elif 'phone' in control_lower or 'mobile' in control_lower:
            return 'phone'
        elif 'code' in control_lower or 'verification' in control_lower:
            return 'code'
        else:
            # For other cases, use sanitized name
            return self.sanitize_filename(control_name)
    
    def find_parent_control(self, controls: List[Dict[str, Any]], hierarchical_level: str, current_ui_path: List[str] = None) -> tuple:
        """
        Find parent control based on UI path prefix matching (with key mapping) and slice points.
        
        Args:
            controls: List of all controls
            hierarchical_level: Current control's hierarchical level (e.g., "2.1.1.2.30.3.1")
            current_ui_path: Current control's UI path (for prefix matching)
            
        Returns:
            Tuple of (parent_control, matched_by_ui_path: bool)
            - parent_control: Parent control dictionary or None
            - matched_by_ui_path: True if matched by UI path prefix, False if matched by hierarchical level
        """
        # Parse hierarchical level
        parts = hierarchical_level.split('.')
        current_depth = len(parts)
        
        # Find the appropriate parent slice point
        # Use the largest slice point that is less than current depth
        parent_depth = None
        for slice_point in sorted(self.slice_points, reverse=True):
            if current_depth > slice_point:
                parent_depth = slice_point
                break
        
        if parent_depth is None:
            return (None, False)
        
        # Strategy 1: If we have UI path, find control whose UI path is a prefix of current UI path
        # Map UI names to dataset keys for accurate matching
        best_match = None
        best_match_depth = 0
        best_match_length = 0
        
        if current_ui_path:
            
            # Pre-map current UI path elements to dataset keys for comparison
            current_ui_path_keys = []
            for ui_name in current_ui_path:
                # Try to find the dataset key for this UI name
                dataset_key = self.find_control_key_by_ui_name(ui_name)
                # Use dataset key if found, otherwise use original UI name
                current_ui_path_keys.append(dataset_key if dataset_key else ui_name)
            
            for control in controls:
                metadata = control.get('metadata', {}).get('windows', {})
                ctrl_level = metadata.get('shortest_hierarchical_level', '')
                ctrl_depth = len(ctrl_level.split('.'))
                
                # Skip if depth exceeds parent_depth
                if ctrl_depth > parent_depth:
                    continue
                
                ctrl_ui_path = metadata.get('control_ui_path', [])
                ctrl_name = control.get('name', '')
                
                # Check if this control's UI path is a prefix of current UI path
                if ctrl_ui_path and len(ctrl_ui_path) < len(current_ui_path):
                    # Map control's UI path elements to keys
                    ctrl_ui_path_keys = []
                    for ui_name in ctrl_ui_path:
                        dataset_key = self.find_control_key_by_ui_name(ui_name)
                        ctrl_ui_path_keys.append(dataset_key if dataset_key else ui_name)
                    
                    # Compare mapped UI paths
                    if current_ui_path_keys[:len(ctrl_ui_path_keys)] == ctrl_ui_path_keys:
                        # This is a valid parent (mapped UI path prefix match)
                        # Pick the one with highest depth (closest to parent_depth) and longest UI path
                        if (ctrl_depth > best_match_depth or 
                            (ctrl_depth == best_match_depth and len(ctrl_ui_path) > best_match_length)):
                            best_match = control
                            best_match_depth = ctrl_depth
                            best_match_length = len(ctrl_ui_path)
            
            # Don't return immediately - we might find a better match via hierarchical level
            # if best_match:
            #     return (best_match, True)  # Found by UI path prefix
        
        # Strategy 2: Try hierarchical level matching
        # Parent is the first parent_depth parts (e.g., "2.1.1.2" for depth 4)
        parent_level = '.'.join(parts[:parent_depth])
        
        # Find parent control by hierarchical level
        hierarchical_match = None
        for control in controls:
            metadata = control.get('metadata', {}).get('windows', {})
            if metadata.get('shortest_hierarchical_level') == parent_level:
                hierarchical_match = control
                break
        
        # Choose the best match: prefer the one closer to parent_depth
        # If both exist, compare their depths
        if best_match and hierarchical_match:
            best_match_depth_val = len(best_match['metadata']['windows'].get('shortest_hierarchical_level', '').split('.'))
            hierarchical_depth_val = len(hierarchical_match['metadata']['windows'].get('shortest_hierarchical_level', '').split('.'))
            
            # Prefer the one with depth closer to parent_depth
            if hierarchical_depth_val == parent_depth:
                # Hierarchical match is exactly at parent_depth - prefer it
                return (hierarchical_match, False)
            elif best_match_depth_val >= hierarchical_depth_val:
                # UI path match is better or equal
                return (best_match, True)
            else:
                # Hierarchical match is closer to parent_depth
                return (hierarchical_match, False)
        elif best_match:
            return (best_match, True)  # Only UI path match found
        elif hierarchical_match:
            return (hierarchical_match, False)  # Only hierarchical match found
        
        return (None, False)
    
    def collect_dependency_chain(self, controls: List[Dict[str, Any]], hierarchical_level: str, current_ui_path: List[str] = None) -> List[str]:
        """
        Collect the full dependency chain for a control.
        
        Args:
            controls: List of all controls
            hierarchical_level: Current control's hierarchical level
            current_ui_path: Current control's UI path (for prefix matching)
            
        Returns:
            List of parent test case paths in order (from root to immediate parent)
            Paths include category directory if categorization is enabled
            
        Example:
            For "2.1.1.2.30.3.1" with slice_points=[4, 7] and categorization:
            - Returns ["navigations/basic/sign_in_after_entering_your_password", "in_meeting/start_a_webex_meeting"]
            - First parent at depth 7 (in app_core category), then its parent at depth 4 (in in_meeting category)
        """
        dependencies = []
        current_level = hierarchical_level
        current_path = current_ui_path
        
        # Recursively find all parents up the chain
        while True:
            parent, _ = self.find_parent_control(controls, current_level, current_path)
            if parent is None:
                break
            
            parent_name = self.sanitize_filename(parent['name'])
            
            # Add category prefix if categorization is enabled (with override support)
            if self.categorization_enabled:
                parent_level = parent.get('metadata', {}).get('windows', {}).get('shortest_hierarchical_level', '')
                parent_depth = len(parent_level.split('.'))
                parent_original_name = parent['name']
                category = self.get_category_for_control(parent_original_name, parent_depth)
                if category:
                    parent_name = f"{category}/{parent_name}"
            
            dependencies.insert(0, parent_name)  # Insert at beginning to maintain order
            
            # Move up to parent's level and UI path for next iteration
            parent_level = parent.get('metadata', {}).get('windows', {}).get('shortest_hierarchical_level')
            parent_ui_path = parent.get('metadata', {}).get('windows', {}).get('control_ui_path', [])
            if not parent_level:
                break
            current_level = parent_level
            current_path = parent_ui_path
        
        return dependencies
    
    def generate_yaml_content(self, control: Dict[str, Any], all_controls: List[Dict[str, Any]] = None) -> str:
        """
        Generate YAML test case content for a control with hierarchical slicing support.
        
        Args:
            control: Control dictionary with metadata
            all_controls: List of all controls (for finding parent controls)
            
        Returns:
            YAML formatted string
        """
        name = control['name']
        metadata = control['metadata']['windows']
        ui_path = metadata['control_ui_path']
        test_case_name = self.sanitize_filename(name)
        hierarchical_level = metadata.get('shortest_hierarchical_level', '')
        
        # Check if control has meeting_ui_path (sliced path)
        meeting_ui_path = metadata.get('meeting_ui_path')
        sliced_hierarchical_level = metadata.get('sliced_hierarchical_level')
        start_index = metadata.get('start_index')
        
        # Determine if this control should be sliced based on depth and slice points
        depth = len(hierarchical_level.split('.'))
        
        # Should slice if depth is greater than any slice point
        # This ensures controls right after a slice point reference that slice point
        should_slice = any(depth > slice_point for slice_point in self.slice_points)
        
        # Find parent control for slicing (pass UI path for prefix matching)
        parent_control = None
        matched_by_ui_path = False
        if should_slice and all_controls:
            parent_control, matched_by_ui_path = self.find_parent_control(all_controls, hierarchical_level, ui_path)
        
        # Calculate start_index for slicing
        if should_slice and parent_control and not start_index:
            if matched_by_ui_path:
                # UI path match: use parent's UI path length
                parent_ui_path = parent_control['metadata']['windows'].get('control_ui_path', [])
                start_index = len(parent_ui_path)
            else:
                # Hierarchical level match: use parent's depth (different UI branch)
                parent_level = parent_control['metadata']['windows'].get('shortest_hierarchical_level', '')
                parent_depth = len(parent_level.split('.'))
                start_index = parent_depth
        
        # Build YAML header
        yaml_lines = [
            "test_case:",
            f"  name: {test_case_name}",
            f"  custom_dataset: {self.custom_dataset}",
        ]
        
        # Add check_points if configured
        if self.check_points:
            import json
            yaml_lines.append(f"  check_points: {json.dumps(self.check_points)}")
        
        # Add pre_conditions with full dependency chain if this should be sliced
        if should_slice and parent_control and all_controls:
            dependency_chain = self.collect_dependency_chain(all_controls, hierarchical_level, ui_path)
            if dependency_chain:
                yaml_lines.append("")
                yaml_lines.append("  pre_conditions:")
                for dep_name in dependency_chain:
                    # dep_name already includes category path (e.g., "preconditions/app_entry/sign_in_to_app")
                    # Only add prefix if dep_name doesn't already start with a path
                    if '/' in dep_name:
                        # dep_name has category, add only base prefix
                        yaml_lines.append(f"    - navigations/{dep_name}")
                    else:
                        # dep_name has no category, use full prefix
                        yaml_lines.append(f"    - {self.pre_conditions_prefix}/{dep_name}")
        
        yaml_lines.append("")
        yaml_lines.append("  steps:")
        
        # Use meeting_ui_path if available, otherwise calculate sliced path
        if meeting_ui_path:
            steps_to_use = meeting_ui_path
        elif should_slice and parent_control and start_index:
            # Slice the UI path starting from parent's end
            steps_to_use = ui_path[start_index:]
            
            # Safety check: if slicing results in empty array, keep at least the last step
            # This happens when the control's UI path length equals the parent's
            if not steps_to_use and ui_path:
                steps_to_use = [ui_path[-1]]
        else:
            # Use full path
            steps_to_use = ui_path
        
        # Generate steps
        for idx, step_name in enumerate(steps_to_use):
            # Map UI name to dataset key to ensure consistency
            dataset_key = self.find_control_key_by_ui_name(step_name)
            
            action_type = self.determine_action_type(dataset_key)
            
            # Default: use dataset key (simplified name) for better readability
            # Unless there's a specific display name override configured
            display_name = dataset_key
            
            # Check if there's a display name override for this step
            if step_name in self.step_display_names:
                display_name = self.step_display_names[step_name]
            elif dataset_key in self.step_display_names:
                display_name = self.step_display_names[dataset_key]
            
            is_optional = False
            
            # Check if this step name is in the optional_steps list
            if dataset_key in self.optional_steps or step_name in self.optional_steps:
                is_optional = True
            
            if idx == len(steps_to_use) - 1 and not should_slice:
                # This is the last step and not sliced
                # Use the control's dataset key (which is control['name'])
                # But respect step_display_names if already set
                if step_name not in self.step_display_names and dataset_key not in self.step_display_names:
                    display_name = control.get('name', dataset_key)
                
                # Check if this step should be optional (only for the last step)
                if not is_optional:  # Don't override if already set by optional_steps
                    is_optional = metadata.get('optional', False)
            else:
                # For non-last steps, check if there's a control in the raw dataset with this key
                # that has optional=true in its metadata
                if not is_optional:  # Don't override if already set by optional_steps
                    for ctrl in self.raw_controls:
                        # Match by dataset key (ctrl['name'])
                        if ctrl.get('name') == dataset_key and ctrl.get('metadata', {}).get('windows', {}).get('optional', False):
                            is_optional = True
                            break
            
            yaml_lines.append(f'    - name: "{display_name}"')
            yaml_lines.append(f'      action:')
            yaml_lines.append(f'        type: {action_type}')
            
            if action_type == 'input':
                # Generate placeholder variable name based on control type
                var_name = self.get_variable_name(dataset_key)
                yaml_lines.append(f'        value: ${{{var_name}}}')
            else:
                yaml_lines.append(f'        value: default')
            
            # Check for test behavior properties from raw_controls (for last step or matching control)
            test_properties = {}
            if idx == len(steps_to_use) - 1:
                # Last step: check current control's metadata first
                # This is the target control itself, so use its metadata
                test_properties = {
                    'expect_state': metadata.get('expect_state'),
                    'ui_response': metadata.get('ui_response'),
                    'ui_response_threshold_ms': metadata.get('ui_response_threshold_ms'),
                    'wait_time': metadata.get('wait_time'),
                    'performance_cpu_threshold': metadata.get('performance_cpu_threshold'),
                    'performance_mem_threshold_mb': metadata.get('performance_mem_threshold_mb'),
                    'performance_gpu_threshold': metadata.get('performance_gpu_threshold')
                }
            else:
                # Non-last step: search in raw_controls by dataset key
                for ctrl in self.raw_controls:
                    if ctrl.get('name') == dataset_key:
                        ctrl_metadata = ctrl.get('metadata', {}).get('windows', {})
                        test_properties = {
                            'expect_state': ctrl_metadata.get('expect_state'),
                            'ui_response': ctrl_metadata.get('ui_response'),
                            'ui_response_threshold_ms': ctrl_metadata.get('ui_response_threshold_ms'),
                            'wait_time': ctrl_metadata.get('wait_time'),
                            'performance_cpu_threshold': ctrl_metadata.get('performance_cpu_threshold'),
                            'performance_mem_threshold_mb': ctrl_metadata.get('performance_mem_threshold_mb'),
                            'performance_gpu_threshold': ctrl_metadata.get('performance_gpu_threshold')
                        }
                        break
            
            # Output expect_state if present
            if test_properties.get('expect_state') is not None:
                import json
                yaml_lines.append(f'      expect_state: {json.dumps(test_properties["expect_state"])}')
            
            # Output ui_response if true
            if test_properties.get('ui_response'):
                yaml_lines.append(f'      ui_response: true')
            
            # Output ui_response_threshold_ms if present
            if test_properties.get('ui_response_threshold_ms') is not None:
                yaml_lines.append(f'      ui_response_threshold_ms: {test_properties["ui_response_threshold_ms"]}')
            
            # Output wait_time if present
            if test_properties.get('wait_time') is not None:
                yaml_lines.append(f'      wait_time: {test_properties["wait_time"]}')
            
            # Output performance thresholds if present
            if test_properties.get('performance_cpu_threshold') is not None:
                yaml_lines.append(f'      performance_cpu_threshold: {test_properties["performance_cpu_threshold"]}')
            if test_properties.get('performance_mem_threshold_mb') is not None:
                yaml_lines.append(f'      performance_mem_threshold_mb: {test_properties["performance_mem_threshold_mb"]}')
            if test_properties.get('performance_gpu_threshold') is not None:
                yaml_lines.append(f'      performance_gpu_threshold: {test_properties["performance_gpu_threshold"]}')
            
            # Only output optional: true (don't output optional: false)
            if is_optional:
                yaml_lines.append(f'      optional: true')
            
            yaml_lines.append('')
        
        return '\n'.join(yaml_lines)
    
    def generate_test_cases(self) -> Dict[str, int]:
        """
        Generate all test case YAML files with hierarchical slicing support.
        
        Returns:
            Dictionary with statistics (depth -> count)
        """
        # Load and filter controls
        controls = self.load_controls_data()
        filtered_controls = self.filter_by_depth(controls)
        
        print(f"[i] Loaded {len(controls)} controls from {self.input_file}")
        print(f"[i] Filtered to {len(filtered_controls)} controls (depth <= {self.max_depth})")
        print()
        
        # Track statistics
        stats = {}
        generated_files = []
        sliced_count = 0
        
        # Generate test cases
        for control in filtered_controls:
            metadata = control['metadata']['windows']
            depth_str = metadata['shortest_hierarchical_level']
            depth = len(depth_str.split('.'))
            control_name = control['name']
            
            # Note: Input dataset (go_to_core_controls.json) is already filtered by:
            # - selected=true in core_controls_config.json
            # - Plus functional_mappings from test_case_generation_config.json
            # So no additional filtering needed here
            
            # Update stats
            stats[depth] = stats.get(depth, 0) + 1
            
            # Check if control will use slicing (depth >= 5 and has parent)
            if depth >= 5:
                parent_control, _ = self.find_parent_control(controls, depth_str)
                if parent_control:
                    sliced_count += 1
            
            # Generate YAML content with all_controls for parent lookup
            yaml_content = self.generate_yaml_content(control, all_controls=controls)
            
            # Determine output directory based on categorization (with override support)
            control_name = control['name']
            category = self.get_category_for_control(control_name, depth)
            if category:
                category_dir = self.output_dir / category
                category_dir.mkdir(parents=True, exist_ok=True)
                output_dir = category_dir
            else:
                output_dir = self.output_dir
            
            # Save to file
            test_case_name = self.sanitize_filename(control['name'])
            output_file = output_dir / f"{test_case_name}.yaml"
            
            # Check if this file is in the exclusion list (manually maintained)
            relative_path = output_file.relative_to(self.output_dir.parent)
            relative_path_str = str(relative_path).replace('\\', '/')
            
            if relative_path_str in self.exclusion_list:
                print(f"[i] Skipping excluded file: {relative_path_str}")
                continue
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            generated_files.append(str(output_file))
        
        # Print summary
        print(f"[+] Generated {len(generated_files)} test case files")
        print(f"[+] Test cases with slicing: {sliced_count}")
        print()
        
        if self.categorization_enabled:
            print("Distribution by category and depth:")
            for category in self.categories:
                category_name = category['name']
                depth_range = category.get('depth_range', [])
                if len(depth_range) == 2:
                    min_d, max_d = depth_range
                    category_depths = {d: stats[d] for d in sorted(stats.keys()) if min_d <= d <= max_d}
                    total = sum(category_depths.values())
                    if total > 0:
                        print(f"  {category_name}/ (depth {min_d}-{max_d}): {total} test cases")
                        for depth, count in category_depths.items():
                            print(f"    Depth {depth}: {count} test cases")
        else:
            print("Distribution by depth:")
            for depth in sorted(stats.keys()):
                print(f"  Depth {depth}: {stats[depth]} test cases")
        
        print()
        print(f"[+] Output directory: {self.output_dir.absolute()}")
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate navigation test cases from core controls dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test cases for depth 1-5 (default)
  python generate_navigation_test_cases.py
  
  # Generate test cases for depth 1-3 only
  python generate_navigation_test_cases.py --max-depth 3
  
  # Specify custom input file
  python generate_navigation_test_cases.py --input custom_controls.json
  
  # Specify custom output directory
  python generate_navigation_test_cases.py --output-dir ../custom_test_cases
"""
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Configuration file path (default: test_case_generation_config.json)'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Input JSON file path (overrides config)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for test cases (overrides config)'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=None,
        help='Maximum hierarchical depth to include (overrides config)'
    )
    
    parser.add_argument(
        '--slice-points',
        type=str,
        default=None,
        help='Comma-separated slice points for hierarchical slicing (overrides config). Controls at depths greater than these will reference the nearest slice point as parent.'
    )
    
    parser.add_argument(
        '--custom-dataset',
        type=str,
        default=None,
        help='Custom dataset reference for YAML files (overrides config, e.g., core/go_to_core_controls_raw)'
    )
    
    args = parser.parse_args()
    
    # Parse slice points if provided
    slice_points = [int(x.strip()) for x in args.slice_points.split(',')] if args.slice_points else None
    
    # Create generator and run
    generator = NavigationTestCaseGenerator(
        config_file=args.config,
        input_file=args.input,
        output_dir=args.output_dir,
        max_depth=args.max_depth,
        slice_points=slice_points,
        custom_dataset=args.custom_dataset
    )
    
    generator.generate_test_cases()


if __name__ == '__main__':
    main()

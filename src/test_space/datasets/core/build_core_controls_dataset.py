"""
Build Core Controls Dataset Tool
Build go_to_core_controls_datasets based on shortest_hierarchical_level
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class CoreControlsDatasetBuilder:
    """Core Controls Dataset Builder"""
    
    def __init__(self, input_file: str):
        """
        Initialize builder
        
        Args:
            input_file: Input JSON file path
        """
        self.input_file = Path(input_file)
        self.controls_data = []
        self.load_data()
    
    def load_data(self):
        """Load input data"""
        if not self.input_file.exists():
            raise FileNotFoundError(f"File not found: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert dict format to list format if needed
        if isinstance(data, dict):
            # New format: {"control_name": {"metadata": ...}}
            self.controls_data = []
            for name, control_data in data.items():
                # Add name field if not present
                if 'name' not in control_data:
                    control_data['name'] = name
                self.controls_data.append(control_data)
            print(f"Loaded {len(self.controls_data)} controls (converted from dict format)")
        else:
            # Old format: [{"name": ..., "metadata": ...}, ...]
            self.controls_data = data
            print(f"Loaded {len(self.controls_data)} controls")
    
    def filter_empty_names(self, controls: List[Dict]) -> List[Dict]:
        """
        Filter controls with empty names
        
        Args:
            controls: Control list
            
        Returns:
            Filtered control list
        """
        filtered = []
        for control in controls:
            name = control.get('name', '').strip()
            if name:  # Keep only non-empty names
                filtered.append(control)
        
        print(f"After empty name filter: {len(filtered)} controls")
        return filtered
    
    def filter_by_depth(self, controls: List[Dict], max_depth: int = None) -> List[Dict]:
        """
        Filter controls by hierarchical depth
        
        Args:
            controls: Control list
            max_depth: Maximum depth (None means no limit)
            
        Returns:
            Filtered control list
        """
        if max_depth is None:
            return controls
        
        filtered = []
        for control in controls:
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            
            if shortest_level:
                # Calculate hierarchical depth
                depth = len(shortest_level.split('.'))
                if depth <= max_depth:
                    filtered.append(control)
        
        print(f"After depth <= {max_depth} filter: {len(filtered)} controls")
        return filtered
    
    def is_main_control(self, hierarchical_level: str) -> bool:
        """
        Determine if it is a main control (main path control at each level)
        Main control definition: For each unique path prefix, keep only the first control
        For example, path "2.1.1.2.30.3.1.4.3.2":
        - 2 is main control (first level)
        - 2.1 is main control (first under 2)
        - 2.1.1 is main control (first under 2.1)
        - 2.1.1.2 is main control (first under 2.1.1)
        And so on, the first node under each prefix path is a main control
        
        Args:
            hierarchical_level: Hierarchical path string
            
        Returns:
            Whether it is a main control
        """
        if not hierarchical_level or hierarchical_level == 'None':
            return False
        
        parts = hierarchical_level.split('.')
        
        # Check if all levels except the first are 1
        for i, part in enumerate(parts):
            if i > 0 and part != '1':
                return False
        
        return True
    
    def extract_main_controls_by_path(self, controls: List[Dict]) -> List[Dict]:
        """
        Extract main path controls for each path
        For each unique path prefix, keep all nodes on that path
        
        For example: if there is path "2.1.1.2.30.3.1.4.3.2"
        Will extract: 2, 2.1, 2.1.1, 2.1.1.2, 2.1.1.2.30, 2.1.1.2.30.3, 2.1.1.2.30.3.1, 
                     2.1.1.2.30.3.1.4, 2.1.1.2.30.3.1.4.3, 2.1.1.2.30.3.1.4.3.2
        
        Args:
            controls: Control list
            
        Returns:
            Main path control list
        """
        from collections import defaultdict
        
        # Collect all path prefixes and corresponding controls
        path_controls = defaultdict(list)
        
        for control in controls:
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            
            if not shortest_level or shortest_level == 'None':
                continue
            
            parts = shortest_level.split('.')
            
            # Create entries for each prefix of this complete path
            for i in range(1, len(parts) + 1):
                prefix = '.'.join(parts[:i])
                path_controls[prefix].append(control)
        
        # For each path prefix, keep only one control (prefer exact path match)
        main_controls = []
        seen_paths = set()
        
        for path_prefix in sorted(path_controls.keys(), key=lambda x: [int(p) for p in x.split('.')]):
            if path_prefix in seen_paths:
                continue
            
            # Find control that exactly matches this path
            exact_match = None
            for control in path_controls[path_prefix]:
                level = control.get('metadata', {}).get('windows', {}).get('shortest_hierarchical_level', '')
                if level == path_prefix:
                    exact_match = control
                    break
            
            if exact_match:
                main_controls.append(exact_match)
                seen_paths.add(path_prefix)
        
        print(f"After main path extraction: {len(main_controls)} controls")
        return main_controls
    
    def filter_first_control_per_depth(self, controls: List[Dict]) -> List[Dict]:
        """
        Keep only the first control at each depth
        
        Args:
            controls: Control list
            
        Returns:
            First control list for each depth
        """
        from collections import defaultdict
        
        # Group by depth
        depth_controls = defaultdict(list)
        
        for control in controls:
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            
            if shortest_level and shortest_level != 'None':
                depth = len(shortest_level.split('.'))
                depth_controls[depth].append(control)
        
        # For each depth, keep only the first control (first after sorting by hierarchical path)
        first_controls = []
        for depth in sorted(depth_controls.keys()):
            # Sort by hierarchical path
            sorted_controls = sorted(
                depth_controls[depth],
                key=lambda c: [
                    int(x) for x in 
                    c.get('metadata', {})
                    .get('windows', {})
                    .get('shortest_hierarchical_level', '0')
                    .split('.')
                ]
            )
            if sorted_controls:
                first_controls.append(sorted_controls[0])
        
        print(f"After first control per depth: {len(first_controls)} controls")
        return first_controls
    
    def filter_main_controls(self, controls: List[Dict]) -> List[Dict]:
        """
        Keep only main controls
        
        Args:
            controls: Control list
            
        Returns:
            Filtered main control list
        """
        filtered = []
        for control in controls:
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            
            if self.is_main_control(shortest_level):
                filtered.append(control)
        
        print(f"After main controls filter: {len(filtered)} controls")
        return filtered
    
    def deduplicate_by_name_and_shortest_level(self, controls: List[Dict]) -> List[Dict]:
        """
        Deduplicate by name and shortest_hierarchical_level
        If there are multiple controls with same name, choose the one with shortest hierarchical level
        
        Args:
            controls: Control list
            
        Returns:
            Deduplicated control list
        """
        # Group by name
        name_groups = defaultdict(list)
        for control in controls:
            name = control.get('name', '').strip()
            if name:
                name_groups[name].append(control)
        
        # For each name, choose the one with shortest hierarchical level
        deduplicated = []
        for name, group in name_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Find control with shortest level
                shortest_control = min(
                    group,
                    key=lambda c: len(
                        c.get('metadata', {})
                        .get('windows', {})
                        .get('shortest_hierarchical_level', '9999.9999.9999')
                        .split('.')
                    )
                )
                deduplicated.append(shortest_control)
        
        print(f"After deduplication: {len(deduplicated)} controls (from {len(controls)})")
        return deduplicated
    
    def build_dataset(
        self,
        max_depth: int = None,
        only_main_controls: bool = False,
        first_per_depth: bool = False,
        output_file: str = None
    ) -> List[Dict]:
        """
        Build core controls dataset
        
        Args:
            max_depth: Maximum hierarchical depth (None means no limit)
            only_main_controls: Whether to keep only main controls
            first_per_depth: Whether to keep only the first control at each depth
            output_file: Output file path (None means don't save)
            
        Returns:
            Core controls dataset list
        """
        print("\nStarting to build core controls dataset...")
        print(f"Parameters: max_depth={max_depth}, only_main_controls={only_main_controls}, first_per_depth={first_per_depth}")
        print("=" * 60)
        
        # 1. Filter empty names
        filtered_controls = self.filter_empty_names(self.controls_data)
        
        # 2. Filter by depth
        if max_depth is not None:
            filtered_controls = self.filter_by_depth(filtered_controls, max_depth)
        
        # 3. Deduplicate by name and shortest_hierarchical_level
        filtered_controls = self.deduplicate_by_name_and_shortest_level(filtered_controls)
        
        # 4. Keep only main controls (if needed)
        if only_main_controls:
            # Extract main path controls for each path
            filtered_controls = self.extract_main_controls_by_path(filtered_controls)
        
        # 5. Keep only first control per depth (if needed)
        if first_per_depth:
            filtered_controls = self.filter_first_control_per_depth(filtered_controls)
        
        # 6. Sort by shortest_hierarchical_level
        def sort_key(control):
            level = control.get('metadata', {}).get('windows', {}).get('shortest_hierarchical_level', '0')
            try:
                return [int(x) for x in level.split('.') if x and x != 'None']
            except (ValueError, AttributeError):
                return [0]
        
        filtered_controls.sort(key=sort_key)
        
        print("=" * 60)
        print(f"Final generated {len(filtered_controls)} core controls")
        
        # 7. Save to file (if specified)
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert list to dict format with simplified key names
            controls_dict = {}
            for control in filtered_controls:
                key = control.get('name', control.get('metadata', {}).get('windows', {}).get('control_name', 'unknown'))
                controls_dict[key] = {
                    'metadata': control.get('metadata', {})
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(controls_dict, f, indent=4, ensure_ascii=False)
            
            print(f"\nSaved to: {output_path} (dict format with {len(controls_dict)} keys)")
        
        return filtered_controls
    
    def print_statistics(self, controls: List[Dict]):
        """
        Print statistics
        
        Args:
            controls: Control list
        """
        if not controls:
            print("\nNo control data")
            return
        
        print("\n" + "=" * 60)
        print("Statistics:")
        print("=" * 60)
        
        # Statistics by depth
        depth_stats = defaultdict(int)
        main_control_count = 0
        
        for control in controls:
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            
            if shortest_level:
                depth = len(shortest_level.split('.'))
                depth_stats[depth] += 1
                
                if self.is_main_control(shortest_level):
                    main_control_count += 1
        
        print(f"Total controls: {len(controls)}")
        print(f"Main controls: {main_control_count}")
        print("\nDistribution by depth:")
        for depth in sorted(depth_stats.keys()):
            print(f"  Depth {depth}: {depth_stats[depth]} controls")
        
        # Show first 10 controls as examples
        print("\nFirst 10 controls example:")
        for i, control in enumerate(controls[:10], 1):
            name = control.get('name', '')
            windows_data = control.get('metadata', {}).get('windows', {})
            shortest_level = windows_data.get('shortest_hierarchical_level', '')
            is_main = "★" if self.is_main_control(shortest_level) else " "
            print(f"  {i}. {is_main} [{shortest_level}] {name}")
        
        if len(controls) > 10:
            print(f"  ... and {len(controls) - 10} more controls")


def load_workflow_config():
    """Load workflow configuration file"""
    config_file = Path(__file__).parent / "config" / "build_workflow_config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def main():
    """Main function"""
    # Load config file for defaults
    workflow_config = load_workflow_config()
    phase1_config = workflow_config.get('phase1_filter', {}) if workflow_config else {}
    
    default_input = phase1_config.get('input_file', 'data/control_datasets_with_ui_path.json')
    default_output = phase1_config.get('output_file', 'data/go_to_core_controls_raw.json')
    default_max_depth = phase1_config.get('max_depth', None)
    default_only_main = phase1_config.get('only_main_controls', False)
    
    parser = argparse.ArgumentParser(
        description='Build Core Controls Dataset Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  # Build dataset using config/build_workflow_config.json defaults
  python build_core_controls_dataset.py
  
  # Build only depth 1 controls
  python src/test_space/datasets/build_core_controls_dataset.py --max-depth 1
  
  # Build only depth 2 controls
  python src/test_space/datasets/build_core_controls_dataset.py --max-depth 2
  
  # Build only main controls (first at each level)
  python src/test_space/datasets/build_core_controls_dataset.py --only-main-controls
  
  # Build main controls with max depth 3
  python src/test_space/datasets/build_core_controls_dataset.py --max-depth 3 --only-main-controls
  
  # Keep only first control per depth
  python src/test_space/datasets/build_core_controls_dataset.py --first-per-depth
  
  # Combined: depth 8, first control per depth
  python src/test_space/datasets/build_core_controls_dataset.py --max-depth 8 --first-per-depth
  
  # Specify output file
  python src/test_space/datasets/build_core_controls_dataset.py --output my_core_controls.json
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default=default_input,
        help=f'Input JSON file path (default: {default_input})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=default_output,
        help=f'Output JSON file path (default: {default_output})'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=default_max_depth,
        help=f'Maximum hierarchical depth (default: {default_max_depth} from config, None = no limit)'
    )
    
    parser.add_argument(
        '--only-main-controls',
        action='store_true',
        default=default_only_main,
        help='Keep only main controls (extract main path controls for each path, e.g., path 2.1.1.2.30.3 will extract 2, 2.1, 2.1.1, 2.1.1.2, 2.1.1.2.30, 2.1.1.2.30.3)'
    )
    
    parser.add_argument(
        '--first-per-depth',
        action='store_true',
        help='Keep only the first control at each depth (e.g., first at depth 1, first at depth 2, etc.)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save to file, only show statistics'
    )
    
    args = parser.parse_args()
    
    try:
        # Create builder
        builder = CoreControlsDatasetBuilder(args.input)
        
        # Build dataset
        output_file = None if args.no_save else args.output
        core_controls = builder.build_dataset(
            max_depth=args.max_depth,
            only_main_controls=args.only_main_controls,
            first_per_depth=args.first_per_depth,
            output_file=output_file
        )
        
        # Print statistics
        builder.print_statistics(core_controls)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

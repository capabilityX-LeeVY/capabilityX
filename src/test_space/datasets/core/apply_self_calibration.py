"""
Self-Calibration System - Apply Control Property Adjustments
Apply control-level calibrations (UI paths, control names, IDs, types, etc.) from configuration file

Usage:
    python apply_self_calibration.py --input go_to_core_controls.json --output go_to_core_controls.json --config config/self_calibration.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class CoreControlsOverrideApplier:
    """Apply control-level overrides from configuration file to dataset"""
    
    # Supported override properties in metadata.windows
    SUPPORTED_PROPERTIES = [
        'control_ui_path',
        'control_name',
        'control_id',
        'control_type',
        'control_type_name',
        'window_name',
        'window_id',
        'all_hierarchical_levels',
        'shortest_hierarchical_level',
        'optional',  # Mark step as optional (can fail without stopping execution)
        # Test step behavior properties
        'expect_state',  # Expected state after executing this step
        'ui_response',  # Whether to check UI response time
        'ui_response_threshold_ms',  # UI response threshold in milliseconds
        'wait_time',  # Time to wait after executing this step
        'performance_cpu_threshold',  # CPU usage threshold
        'performance_mem_threshold_mb',  # Memory usage threshold in MB
        'performance_gpu_threshold'  # GPU usage threshold
    ]
    
    # Top-level properties (outside metadata)
    TOP_LEVEL_PROPERTIES = [
        'display_name'  # Override the top-level "name" field for display purposes
    ]
    
    def __init__(self, config_path: str):
        """
        Initialize override applier
        
        Args:
            config_path: Path to configuration file (config/self_calibration.json)
        """
        self.config_path = Path(config_path)
        self.stats = {
            'total_controls': 0,
            'applied_overrides': 0,
            'disabled_overrides': 0,
            'override_details': {}
        }
        self.overrides = self._load_overrides()
    
    def _load_overrides(self) -> Dict[str, Dict[str, Any]]:
        """Load override configuration"""
        if not self.config_path.exists():
            print(f"⚠️  Configuration file not found: {self.config_path}")
            return {}
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        all_overrides = config.get('overrides', {})
        
        # Filter only enabled overrides
        enabled_overrides = {
            name: cfg for name, cfg in all_overrides.items() 
            if cfg.get('enabled', True)
        }
        
        disabled_count = len(all_overrides) - len(enabled_overrides)
        
        print(f"✅ Loaded {len(enabled_overrides)} control override(s)")
        if disabled_count > 0:
            print(f"⚠️  Skipped {disabled_count} disabled override(s)")
        
        # Display configuration details
        for control_name, override_config in enabled_overrides.items():
            override_props = []
            
            if override_config.get('control_ui_path'):
                path_length = len(override_config['control_ui_path'])
                override_props.append(f"ui_path({path_length} steps)")
            
            for prop in ['control_name', 'control_id', 'control_type', 'window_name', 'window_id', 'optional', 
                         'expect_state', 'ui_response', 'ui_response_threshold_ms', 'wait_time']:
                if override_config.get(prop) is not None:
                    override_props.append(prop)
            
            # Check for top-level properties
            if override_config.get('display_name') is not None:
                override_props.append('display_name')
            
            props_str = ", ".join(override_props) if override_props else "no properties"
            reason = override_config.get('reason', 'No reason specified')
            print(f"   - {control_name}: [{props_str}] - {reason}")
        
        self.stats['disabled_overrides'] = disabled_count
        return enabled_overrides
    
    def apply_overrides(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply override configuration to dataset
        
        Args:
            dataset: List of control data dictionaries
            
        Returns:
            Updated dataset with overrides applied
        """
        self.stats['total_controls'] = len(dataset)
        
        for control in dataset:
            control_name = control.get('name', '')
            control_name_metadata = control.get('metadata', {}).get('windows', {}).get('control_name', '')
            
            # Check if there's an override configuration for this control
            # Try to match by top-level name first, then by metadata.control_name
            matched_key = None
            if control_name in self.overrides:
                matched_key = control_name
            elif control_name_metadata in self.overrides:
                matched_key = control_name_metadata
            
            if matched_key:
                override_config = self.overrides[matched_key]
                reason = override_config.get('reason', 'No reason specified')
                
                applied_properties = []
                metadata_windows = control['metadata']['windows']
                
                # Apply metadata.windows properties
                for prop in self.SUPPORTED_PROPERTIES:
                    override_value = override_config.get(prop)
                    
                    # Skip if value is None (keep original)
                    if override_value is None:
                        continue
                    
                    # Store old value for logging
                    old_value = metadata_windows.get(prop)
                    
                    # Apply override
                    metadata_windows[prop] = override_value
                    applied_properties.append(prop)
                    
                    # Special logging for control_ui_path
                    if prop == 'control_ui_path' and isinstance(old_value, list) and isinstance(override_value, list):
                        self._log_ui_path_change(control_name, old_value, override_value)
                
                # Apply top-level properties
                for prop in self.TOP_LEVEL_PROPERTIES:
                    override_value = override_config.get(prop)
                    
                    # Skip if value is None (keep original)
                    if override_value is None:
                        continue
                    
                    # Handle display_name (maps to top-level "name" field)
                    if prop == 'display_name':
                        old_name = control.get('name', '')
                        control['name'] = override_value
                        applied_properties.append(prop)
                        print(f"   Name: {old_name!r} → {override_value!r}")
                        
                        # Also update UI paths to use the new display name
                        metadata = control.get('metadata', {}).get('windows', {})
                        
                        # Update control_ui_path
                        control_ui_path = metadata.get('control_ui_path', [])
                        if control_ui_path and control_ui_path[-1] == old_name:
                            control_ui_path[-1] = override_value
                            print(f"   Updated control_ui_path[-1]: {old_name!r} → {override_value!r}")
                        
                        # Update meeting_ui_path
                        meeting_ui_path = metadata.get('meeting_ui_path', [])
                        if meeting_ui_path and meeting_ui_path[-1] == old_name:
                            meeting_ui_path[-1] = override_value
                            print(f"   Updated meeting_ui_path[-1]: {old_name!r} → {override_value!r}")
                
                if applied_properties:
                    self.stats['applied_overrides'] += 1
                    self.stats['override_details'][matched_key] = {
                        'properties': applied_properties,
                        'reason': reason
                    }
                    
                    print(f"\n✅ Applied override: {matched_key}")
                    print(f"   Properties: {', '.join(applied_properties)}")
                    print(f"   Reason: {reason}")
        
        return dataset
    
    def _log_ui_path_change(self, control_name: str, old_path: List[str], new_path: List[str]):
        """Log UI path changes with detailed comparison"""
        if len(old_path) != len(new_path):
            print(f"   UI Path: {len(old_path)} steps → {len(new_path)} steps")
    
    def process_file(self, input_path: str, output_path: str, backup: bool = True):
        """
        Process dataset file with overrides
        
        Args:
            input_path: Input file path
            output_path: Output file path
            backup: Whether to backup original file
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Backup original file
        if backup and input_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = input_path.parent / f"{input_path.stem}_backup_{timestamp}{input_path.suffix}"
            with open(input_path, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"📦 Backup created: {backup_path.name}")
        
        # Read dataset
        print(f"\n📖 Reading dataset: {input_path.name}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert dict format to list format if needed for processing
        is_dict_format = isinstance(data, dict)
        if is_dict_format:
            dataset = []
            for name, control_data in data.items():
                if 'name' not in control_data:
                    control_data['name'] = name
                dataset.append(control_data)
            print(f"  [i] Converted from dict format: {len(dataset)} controls")
        else:
            dataset = data
        
        # Apply overrides
        print(f"\n🔧 Applying control overrides...")
        dataset = self.apply_overrides(dataset)
        
        # Save results
        print(f"\n💾 Saving to: {output_path.name}")
        # Convert back to dict format if input was dict format
        if is_dict_format:
            output_data = {}
            for control in dataset:
                control_name = control.get('name', '')
                control_copy = {k: v for k, v in control.items() if k != 'name'}
                output_data[control_name] = control_copy
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
            print(f"  [i] Saved as dict format: {len(output_data)} controls")
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=4, ensure_ascii=False)
        
        # Display statistics
        self._print_statistics()
    
    def _print_statistics(self):
        """Print application statistics"""
        print(f"\n{'='*60}")
        print("📊 Override Statistics:")
        print(f"{'='*60}")
        print(f"Total controls:        {self.stats['total_controls']}")
        print(f"Applied overrides:     {self.stats['applied_overrides']}")
        print(f"Disabled overrides:    {self.stats['disabled_overrides']}")
        print(f"Override ratio:        {self.stats['applied_overrides']/max(self.stats['total_controls'],1)*100:.1f}%")
        
        if self.stats['override_details']:
            print(f"\nOverridden controls:")
            for i, (name, details) in enumerate(self.stats['override_details'].items(), 1):
                props = ', '.join(details['properties'])
                print(f"  {i}. {name}")
                print(f"     Properties: {props}")
                print(f"     Reason: {details['reason']}")
        
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Apply control-level overrides to core controls dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Apply self-calibration to dataset
    python apply_self_calibration.py --input go_to_core_controls.json --output go_to_core_controls.json
    
    # Use custom configuration file
    python apply_self_calibration.py --input data.json --output data_fixed.json --config my_calibration.json
    
    # Don't backup original file
    python apply_self_calibration.py --input data.json --output data.json --no-backup
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                        help='Input dataset file path')
    parser.add_argument('--output', '-o', required=True,
                        help='Output dataset file path')
    parser.add_argument('--config', '-c', default='config/self_calibration.json',
                        help='Self-calibration configuration file path (default: config/self_calibration.json)')
    parser.add_argument('--no-backup', action='store_true',
                        help='Do not backup original file')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("🔧 Core Controls Overrides Applier")
    print(f"{'='*60}\n")
    
    # Create applier
    applier = CoreControlsOverrideApplier(args.config)
    
    # Process file
    applier.process_file(
        input_path=args.input,
        output_path=args.output,
        backup=not args.no_backup
    )
    
    print("✅ Complete!\n")


if __name__ == '__main__':
    main()

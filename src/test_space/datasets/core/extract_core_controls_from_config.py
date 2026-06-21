"""
Extract core controls based on configuration file
Reads user-selected controls from core_controls_config.json and generates final core controls dataset
"""

import json
from pathlib import Path

def load_config(config_file):
    """Load configuration file"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data(input_file):
    """Load complete dataset"""
    with open(input_file, 'r', encoding='utf-8') as f:
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

def extract_selected_controls(config, all_controls, test_gen_config=None):
    """Extract selected controls based on configuration
    
    Args:
        config: core_controls_config.json content
        all_controls: List of all controls from raw dataset
        test_gen_config: Optional test_case_generation_config.json content for functional mappings
    """
    
    selected_names = set()
    
    # Add controls marked as selected in core_controls_config.json
    for depth_key, depth_data in config.get("depths", {}).items():
        for control_config in depth_data.get("controls", []):
            if control_config.get("selected", False):
                selected_names.add(control_config["name"])
    
    # Also add controls from functional_categories mappings
    if test_gen_config:
        functional_mappings = (test_gen_config.get("generation", {})
                              .get("categorization", {})
                              .get("functional_categories", {})
                              .get("mappings", {}))
        selected_names.update(functional_mappings.keys())
        print(f"  [i] Added {len(functional_mappings)} functional category mappings")
    
    selected_controls = []
    for control in all_controls:
        if control["name"] in selected_names:
            selected_controls.append(control)
    
    return selected_controls

def print_summary(controls):
    """Print extraction results summary"""
    from collections import defaultdict
    
    by_depth = defaultdict(list)
    for control in controls:
        level = control['metadata']['windows']['shortest_hierarchical_level']
        depth = len(level.split('.'))
        by_depth[depth].append(control)
    
    print("\n" + "="*70)
    print("Core Controls Extraction Results")
    print("="*70)
    
    for depth in sorted(by_depth.keys()):
        print(f"\nDepth {depth} ({len(by_depth[depth])} controls):")
        for control in by_depth[depth]:
            name = control['name']
            control_type = control['metadata']['windows']['control_type_name']
            # Handle Unicode characters in control names
            try:
                print(f"  [+] {name} ({control_type})")
            except UnicodeEncodeError:
                # Remove non-ASCII characters if printing fails
                name_ascii = name.encode('ascii', 'ignore').decode('ascii')
                print(f"  [+] {name_ascii} ({control_type})")
    
    print(f"\n{'='*70}")
    print(f"Total: {len(controls)} core controls")
    print(f"Depth coverage: {min(by_depth.keys())} to {max(by_depth.keys())}")
    print("="*70)

def main():
    config_file = Path(__file__).parent / "config" / "core_controls_config.json"
    test_gen_config_file = Path(__file__).parent / "config" / "test_case_generation_config.json"
    input_file = Path(__file__).parent / "data" / "go_to_core_controls_raw.json"
    output_file = Path(__file__).parent / "data" / "go_to_core_controls.json"
    
    print(f"Loading configuration: {config_file}")
    config = load_config(config_file)
    
    # Load test generation config for functional mappings
    test_gen_config = None
    if test_gen_config_file.exists():
        print(f"Loading test generation config: {test_gen_config_file}")
        test_gen_config = load_config(test_gen_config_file)
    
    print(f"Loading complete dataset: {input_file}")
    all_controls = load_data(input_file)
    
    print("\nExtracting selected core controls...")
    selected_controls = extract_selected_controls(config, all_controls, test_gen_config)
    
    if not selected_controls:
        print("\n⚠ Warning: No controls selected!")
        print("Please edit config/core_controls_config.json and set 'selected': true for desired controls")
        return
    
    print_summary(selected_controls)
    
    # Convert to dict format with simplified key names
    controls_dict = {}
    for control in selected_controls:
        key = control.get('name')
        controls_dict[key] = {
            'metadata': control.get('metadata', {})
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(controls_dict, f, indent=4, ensure_ascii=False, sort_keys=False)
    
    print(f"\n[+] Core controls saved to: {output_file} (dict format with {len(controls_dict)} keys)")

if __name__ == "__main__":
    main()

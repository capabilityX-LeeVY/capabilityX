"""
Generate core controls configuration file
This script reads go_to_core_controls_raw.json, lists all controls by depth,
and generates a configuration file for users to select core controls to extract
"""

import json
from pathlib import Path
from collections import defaultdict

def load_data(input_file):
    """Load input dataset"""
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

def get_depth(control):
    """Get control depth"""
    level = control['metadata']['windows']['shortest_hierarchical_level']
    return len(level.split('.'))

def load_existing_selections(config_file):
    """Load existing user selections from config file"""
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            existing_config = json.load(f)
        
        # Build a map: (depth, name, ui_path_str) -> selected
        selections = {}
        for depth_key, depth_data in existing_config.get("depths", {}).items():
            for control in depth_data.get("controls", []):
                name = control.get("name", "")
                ui_path = control.get("ui_path", [])
                # Use tuple of (depth, name, ui_path_tuple) as key for uniqueness
                ui_path_str = "->".join(ui_path) if isinstance(ui_path, list) else ui_path
                key = (depth_key, name, ui_path_str)
                selections[key] = control.get("selected", False)
        
        print(f"  [i] Loaded {len(selections)} existing control selections")
        return selections
    except Exception as e:
        print(f"  [!] Warning: Could not load existing selections: {e}")
        return {}

def generate_config_file(controls, existing_selections=None):
    """Generate configuration file, listing all controls by depth
    
    Args:
        controls: List of control data
        existing_selections: Dict of existing user selections to preserve
    """
    if existing_selections is None:
        existing_selections = {}
    
    # Group by depth
    by_depth = defaultdict(list)
    for control in controls:
        depth = get_depth(control)
        by_depth[depth].append(control)
    
    config = {
        "_comment": "Core controls configuration file. Set 'selected': true for controls you want to extract",
        "_instructions": [
            "1. Set 'selected': true for controls you want to include",
            "2. Or delete unwanted control entries",
            "3. After saving, run: python extract_core_controls_from_config.py",
            "4. Recommended: select 3-10 core controls per depth",
            "5. Re-running this script will preserve your existing selections"
        ],
        "depths": {}
    }
    
    preserved_count = 0
    for depth in sorted(by_depth.keys()):
        depth_controls = []
        
        for control in by_depth[depth]:
            name = control['name']
            control_type = control['metadata']['windows']['control_type_name']
            ui_path = control['metadata']['windows']['control_ui_path']  # Keep original UI path
            
            # Check if this control was previously selected
            ui_path_str = "->".join(ui_path) if isinstance(ui_path, list) else ui_path
            key = (str(depth), name, ui_path_str)
            selected = existing_selections.get(key, False)
            
            if selected:
                preserved_count += 1
            
            depth_controls.append({
                "name": name,
                "control_type": control_type,
                "ui_path": ui_path,  # Keep original control names for matching
                "selected": selected  # Preserve existing selection or default to False
            })
        
        config["depths"][str(depth)] = {
            "total_controls": len(depth_controls),
            "description": f"All controls at depth {depth}",
            "controls": depth_controls
        }
    
    if preserved_count > 0:
        print(f"  [*] Preserved {preserved_count} existing selections")
    
    return config

def generate_readable_config(controls):
    """Generate human-readable text format configuration file"""
    
    # Group by depth
    by_depth = defaultdict(list)
    for control in controls:
        depth = get_depth(control)
        by_depth[depth].append(control)
    
    lines = []
    lines.append("# Core Controls Configuration File")
    lines.append("# " + "="*70)
    lines.append("# Instructions:")
    lines.append("#   1. Mark controls to extract with 'selected': true in JSON config")
    lines.append("#   2. Or delete unwanted control entries")
    lines.append("#   3. After saving, run: python extract_core_controls_from_config.py")
    lines.append("#   4. Recommended: select 3-10 core controls per depth")
    lines.append("# " + "="*70)
    lines.append("")
    
    for depth in sorted(by_depth.keys()):
        lines.append(f"\n{'='*70}")
        lines.append(f"Depth {depth} - Total {len(by_depth[depth])} controls")
        lines.append(f"{'='*70}")
        lines.append("")
        
        for i, control in enumerate(by_depth[depth], 1):
            name = control['name']
            control_type = control['metadata']['windows']['control_type_name']
            ui_path = " -> ".join(control['metadata']['windows']['control_ui_path'])
            
            lines.append(f"  {name}")
            lines.append(f"    Type: {control_type}")
            lines.append(f"    Path: {ui_path}")
            lines.append("")
    
    return "\n".join(lines)

def main():
    input_file = Path(__file__).parent / "data" / "go_to_core_controls_raw.json"
    json_config_file = Path(__file__).parent / "config" / "core_controls_config.json"
    text_config_file = Path(__file__).parent / "core_controls_selection.txt"
    
    print(f"Loading data: {input_file}")
    controls = load_data(input_file)
    print(f"Loaded {len(controls)} controls")
    
    # Load existing selections before regenerating
    print(f"\nChecking for existing selections: {json_config_file}")
    existing_selections = load_existing_selections(json_config_file)
    
    # Generate JSON configuration file (preserving selections)
    print(f"\nGenerating JSON config file: {json_config_file}")
    config = generate_config_file(controls, existing_selections)
    with open(json_config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False, sort_keys=False)
    print(f"[+] JSON config saved")
    
    # Skip generating text configuration file (not needed)
    # print(f"\nGenerating text config file: {text_config_file}")
    # readable_config = generate_readable_config(controls)
    # with open(text_config_file, 'w', encoding='utf-8') as f:
    #     f.write(readable_config)
    # print(f"[+] Text config saved")
    
    # Print statistics
    print("\n" + "="*70)
    print("Statistics by depth:")
    print("="*70)
    
    by_depth = defaultdict(int)
    for control in controls:
        depth = get_depth(control)
        by_depth[depth] += 1
    
    for depth in sorted(by_depth.keys()):
        print(f"  Depth {depth}: {by_depth[depth]} controls")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("  1. Edit config/core_controls_config.json file")
    print("  2. Set 'selected': true for controls you want")
    print("  3. Run: python extract_core_controls_from_config.py")
    print("="*70)

if __name__ == "__main__":
    main()

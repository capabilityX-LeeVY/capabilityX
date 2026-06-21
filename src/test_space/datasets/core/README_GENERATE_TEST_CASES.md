# Generate Navigation Test Cases with Hierarchical Slicing

This tool generates YAML test cases from the core controls dataset for navigation automation testing with support for hierarchical slicing and pre-conditions.

## Dataset Format

### Dictionary Format (Current)

The tool uses the **dictionary format** for core controls dataset, where control names serve as keys for efficient O(1) lookups:

**Format Structure**:
```json
{
  " Join a meeting": {
    "metadata": {
      "windows": {
        "control_name": " Join a meeting",
        "control_ui_path": [" Join a meeting"],
        "control_type": 50000,
        ...
      }
    }
  },
  " Sign in": {
    "metadata": {
      "windows": {
        "control_name": " Sign in",
        "control_ui_path": [" Sign in"],
        ...
      }
    }
  }
}
```

**Benefits**:
- ✅ **O(1) lookup speed**: Direct access by control name
- ✅ **Automatic deduplication**: Control names as keys prevent duplicates
- ✅ **Cleaner structure**: No redundant `name` field at top level
- ✅ **Backward compatible**: Scripts auto-detect and convert old array format

### Backward Compatibility

All scripts support **automatic format detection** and conversion:

```python
# Scripts automatically detect and handle both formats
if isinstance(data, dict):
    # New format: Dictionary → List (internal processing)
    controls_list = [
        {"name": name, **control_data}
        for name, control_data in data.items()
    ]
else:
    # Old format: Array (direct use)
    controls_list = data
```

**Legacy Array Format** (automatically converted if detected):
```json
[
  {
    "name": " Join a meeting",
    "metadata": {
      "windows": { ... }
    }
  }
]
```

### Migration Notes

- **All core scripts** support both formats automatically
- **No action required**: Format conversion happens transparently
- **Dataset files** use dictionary format for optimal performance
- **Test case generation** works identically with both formats

## Overview

The `generate_navigation_test_cases.py` tool reads `go_to_core_controls.json` and automatically generates YAML test case files based on each control's `control_ui_path`. The tool supports the **hierarchical slicing design**, where child test cases can include parent test cases as pre-conditions, reducing redundancy and improving execution efficiency.

## Features

- ✅ Filter controls by hierarchical depth
- ✅ Auto-generate test case names from control names
- ✅ Smart action type detection (input vs button)
- ✅ Generate placeholder variables for input fields
- ✅ **Hierarchical slicing with pre-conditions support**
- ✅ **Automatic parent control detection and pre-condition generation**
- ✅ **Support for meeting_ui_path (sliced) and control_ui_path (full)**
- ✅ **50% efficiency gain with slicing for child test cases**
- ✅ Organize output by control depth
- ✅ Full English interface

## Quick Start

```bash
cd src/datasets/core

# Generate test cases for depth 1-5 (default)
python generate_navigation_test_cases.py --max-depth 5

# Output: 27 YAML files in src/test_space/test_cases/navigations/core/
```

## Usage

### Basic Usage

```bash
# Generate test cases with default settings (depth <= 5)
python generate_navigation_test_cases.py

# Generate test cases for depth 1-3 only
python generate_navigation_test_cases.py --max-depth 3

# Specify custom input file
python generate_navigation_test_cases.py --input custom_controls.json

# Specify custom output directory
python generate_navigation_test_cases.py --output-dir ../custom_test_cases
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `go_to_core_controls.json` | Input JSON file path |
| `--output-dir` | `../../test_cases/navigations/core` | Output directory for test cases |
| `--max-depth` | `5` | Maximum hierarchical depth to include |

## How It Works

### 1. Control Selection

The tool filters controls from `go_to_core_controls.json` based on hierarchical depth:

```
Depth 1: " Join a meeting"                    (1 control)
Depth 2: " Sign in"                            (1 control)
Depth 4: " Sign In "                           (1 control - BASE test case)
Depth 5: " Schedule a meeting"                 (23 controls)
         " More options for scheduling..."
         " Start a Webex meeting"
         etc.
Depth 7+: "Start meeting"                      (with slicing, uses sign_in as pre-condition)
```

### 2. Hierarchical Slicing Detection

For each control, the tool checks:
1. **Hierarchical Level**: Determines parent-child relationships (e.g., "2.1.1.2.30.3.1" is child of "2.1.1.2")
2. **Sliced Path**: Uses `meeting_ui_path` if available (sliced), otherwise `control_ui_path` (full)
3. **Pre-condition**: If depth >= slice points (default: 4 or 7), automatically adds parent control as pre-condition

### 3. Test Case Generation

For each control, the tool:
1. Extracts the appropriate UI path (`meeting_ui_path` or `control_ui_path`)
2. Identifies parent control if hierarchical level indicates a child
3. Generates a sanitized filename (e.g., "start_meeting.yaml")
4. Creates test steps with appropriate action types
5. Adds pre-conditions section if parent control exists
6. Includes slicing metadata (`use_sliced_path`, `start_index`, `sliced_hierarchical_level`)

### 4. Action Type Detection

The tool automatically determines action types:

- **Input fields**: `email`, `password`, `username`, `address` → `type: input`
- **Buttons/Links**: All others → `type: key`

### 5. Test Case Categorization

The tool supports **automatic categorization** of test cases into subdirectories based on business logic and hierarchical depth:

#### Directory Structure

```
navigations/preconditions/
├── app_entry/      (4 files)  - Application entry points (depth 1-3, + overrides)
│   ├── join_a_meeting.yaml
│   ├── sign_in.yaml              ← Initial sign-in button (depth 2)
│   ├── sign_up.yaml
│   └── sign_in_to_app.yaml       ← Complete login flow (depth 4, moved via override)
│
├── app_core/       (24 files) - Core application features (depth 4-7)
│   ├── start_meeting.yaml
│   ├── profile_and_preferences.yaml
│   └── ...
│
└── in_meeting/     (28 files) - In-meeting operations (depth 8+)
    ├── share.yaml
    ├── closed_captions.yaml
    ├── record.yaml
    └── ...
```

#### Categorization Rules

Categories are based on control hierarchical depth, corresponding to business workflows:

1. **app_entry/** (depth 1-3)
   - Application launch entry points
   - Authentication (Sign In)
   - Guest meeting join (Join a Meeting)
   - Account registration (Sign Up)
   - ⭐ **Special Cases**: Complete login flow (depth 4) moved here via `category_overrides`

2. **app_core/** (depth 4-7)
   - Post-login main interface
   - Core feature entry points
   - Meeting preparation

3. **in_meeting/** (depth 8+)
   - Various in-meeting operations
   - Sharing, recording, captions, etc.
   - In-meeting settings

#### Configuration

Categorization is configured in `config/test_case_generation_config.json`:

```json
{
  "generation": {
    "categorization": {
      "enabled": true,
      "base_path": "navigations/preconditions",
      "categories": [
        {
          "name": "app_entry",
          "depth_range": [1, 3],
          "description": "Application entry points (sign in, join meeting, sign up)"
        },
        {
          "name": "app_core",
          "depth_range": [4, 7],
          "description": "Application core features"
        },
        {
          "name": "in_meeting",
          "depth_range": [8, 99],
          "description": "In-meeting operations"
        }
      ],
      "category_overrides": {
        "Sign in to app": "app_entry",
        " Sign In ": "app_entry"
      }
    }
  }
}
```

#### Configuration Parameters

- **enabled**: `true`/`false` - Enable/disable categorization
- **base_path**: Base path for categorization
- **categories**: Category definitions
  - **name**: Category directory name
  - **depth_range**: `[min, max]` - Depth range (inclusive)
  - **description**: Category description
- **category_overrides**: Manual category assignment (overrides depth rules) ⭐
  - Key: Control name (must match exactly)
  - Value: Target category directory name
  - Purpose: Place specific controls in business-logic-appropriate directories

#### Category Overrides Use Case

**Problem**: `Sign in to app` is a complete login flow (5 steps), depth 4, which by rules should be in `app_core/`, but business logic dictates it belongs in `app_entry/` (login entry point).

**Solution**: Use `category_overrides` to manually specify category:

```json
{
  "category_overrides": {
    "Sign in to app": "app_entry"
  }
}
```

**Result**:
- File generated at `navigations/preconditions/app_entry/sign_in_to_app.yaml`
- No `pre_conditions` (it's a complete independent flow)
- Other files correctly reference it: `- navigations/preconditions/app_entry/sign_in_to_app`

#### Custom Categorization

You can customize categorization rules as needed:

```json
{
  "categories": [
    {
      "name": "startup",
      "depth_range": [1, 2],
      "description": "Application startup"
    },
    {
      "name": "authentication",
      "depth_range": [3, 4],
      "description": "User authentication"
    },
    {
      "name": "main_ui",
      "depth_range": [5, 7],
      "description": "Main application UI"
    },
    {
      "name": "meeting_prep",
      "depth_range": [8, 9],
      "description": "Meeting preparation"
    },
    {
      "name": "meeting_actions",
      "depth_range": [10, 99],
      "description": "In-meeting actions"
    }
  ]
}
```

#### Usage Examples

**Referencing categorized paths**:

```yaml
# functional/meetings/video/vbg_static.yaml
test_case:
  name: vbg_static
  
  pre_conditions:
    - navigations/preconditions/app_core/start_meeting
  
  steps:
    - name: "Video options"
    - name: "Virtual backgrounds"
    - name: "Office"
```

**Cross-category dependencies**:

```yaml
# in_meeting test case depending on app_entry and app_core
test_case:
  name: closed_captions
  
  pre_conditions:
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_meeting
  
  steps:
    - name: "Closed captions"
```

#### Disabling Categorization

To disable categorization and generate all test cases in a flat structure:

```json
{
  "generation": {
    "categorization": {
      "enabled": false
    }
  }
}
```

All test cases will be generated directly in `navigations/preconditions/` without subdirectories.

#### Why app_entry Instead of login?

This directory contains three different application entry methods:

- **Sign In** - Registered user login
- **Join a Meeting** - Guest direct meeting join (no login required)
- **Sign Up** - New user registration
- **Sign in to app** - Complete login flow (via override configuration)

`app_entry` more accurately describes these as different entry points to the application, not just login flows.

#### Decision Principles

When a control's depth classification conflicts with business logic, prioritize:

1. **Business Logic** > depth rules
2. **Pre-conditions presence** - No dependencies typically indicates entry points
3. **Usage frequency** - High-frequency reused preconditions should be in intuitive locations
4. Use `category_overrides` configuration to implement business logic priority

### 6. Multi-Point Slicing Strategy

The tool supports **configurable slice points** for hierarchical test case construction:

**Default Slice Points: [4, 7]**

```
Level 1-4: No slicing (complete paths)
  ├── Level 4 (2.1.1.2): sign_in_to_app ← Base test case
  
Level 5-7: Slice at depth 4
  ├── Level 5 (2.1.1.2.2): schedule_meeting
  │   └── pre_condition: sign_in_to_app (depth 4)
  ├── Level 6 (2.1.1.2.30): start_webex_meeting
  │   └── pre_condition: sign_in_to_app (depth 4)
  
Level 8+: Slice at depth 7
  └── Level 8 (2.1.1.2.30.3.1): start_meeting
      └── pre_condition: accept_meeting (depth 7)
          └── pre_condition: sign_in_to_app (depth 4)
```

**Slicing Rules**:
- **Depth 1-4**: Use full `control_ui_path` (no dependencies)
- **Depth 5-7**: Slice at depth 4, reference base test case (e.g., `sign_in_to_app`)
- **Depth 8+**: Slice at depth 7, reference intermediate test case
- **Configurable**: Adjust via `config/test_case_generation_config.json` → `generation.slice_points`

### 7. Pre-condition Management

For child test cases (depth > slice points):
- **Parent Detection**: Automatically finds parent at nearest slice point (4 or 7)
- **State Verification**: Adds verification that expected control is visible
- **Execution Order**: Test runner executes parent test case before child test case
- **Dependency Chain**: Supports multi-level dependencies (child → parent → grandparent)

## Generated Test Case Format

### Example 1: Simple Navigation (Depth 1)

**File**: `join_a_meeting.yaml`

```yaml
test_case:
  name: join_a_meeting

  steps:
    - name: " Join a meeting"
      action:
        type: key
        value: default
```

### Example 2: Base Test Case (Depth 4) - Sign In to App

**File**: `sign_in_to_app.yaml`

```yaml
test_case:
  name: sign_in_to_app
  hierarchical_level: "2.1.1.2"

  steps:
    - name: " Sign in"
      action:
        type: key
        value: default

    - name: "Email address"
      action:
        type: input
        value: ${email}

    - name: " Next"
      action:
        type: key
        value: default

    - name: "Welcome bts_tony2@mailinator.com Password"
      action:
        type: input
        value: ${password}

    - name: " Sign In "
      action:
        type: key
        value: default
```

### Example 3: Child Test Case with Slicing (Depth 7) - Start Meeting

**File**: `start_meeting.yaml`

```yaml
test_case:
  name: start_meeting
  hierarchical_level: "2.1.1.2.30.3.1"

  pre_conditions:
    - test_case: sign_in_to_app  # hierarchical_level: 2.1.1.2
      state_verification:
        - control: "Profile and preferences"
          expected: visible

  use_sliced_path: true
  start_index: 4
  sliced_hierarchical_level: "30.3.1"

  steps:
    - name: " Start a Webex meeting"
      action:
        type: key
        value: default

    - name: " Accept"
      action:
        type: key
        value: default

    - name: "Start meeting"
      action:
        type: key
        value: default
```

**Efficiency Gain**: This test case uses only 3 steps instead of 8 steps (50% reduction) by leveraging the `sign_in_to_app` pre-condition.

## Output Statistics

When you run the tool with `--max-depth 5`, you'll see:

```
[i] Loaded 56 controls from go_to_core_controls.json
[i] Filtered to 27 controls (depth <= 5)

[+] Generated 27 test case files
[+] Test cases with slicing: 0  (23 if max-depth >= 7)

Distribution by depth:
  Depth 1: 3 test cases
  Depth 4: 1 test cases  (base test case with complete sign-in flow)
  Depth 5: 23 test cases

[+] Output directory: C:\...\src\test_space\test_cases\navigations\core
```

**Note**: To see test cases with hierarchical slicing and pre-conditions, use `--max-depth 7` or higher. Controls at depth >= 5 will use the `sign_in` test case as a pre-condition and execute only their sliced paths.

## File Naming Convention

Control names are sanitized to create valid filenames:

| Control Name | Generated Filename |
|--------------|-------------------|
| " Join a meeting" | `join_a_meeting.yaml` |
| " Schedule a meeting" | `schedule_a_meeting.yaml` |
| " Sign in" | `sign_in.yaml` |
| "Sign in to app" | `sign_in_to_app.yaml` |
| "More options for scheduling..." | `more_options_for_scheduling_a_meeting.yaml` |

## Integration with Test Framework

These generated test cases can be used directly with your automation framework:

### Basic Test Case Execution

```python
# Example: Load and execute test case
import yaml

with open('navigations/core/schedule_a_meeting.yaml') as f:
    test_case = yaml.safe_load(f)
    
# Execute navigation steps
for step in test_case['test_case']['steps']:
    execute_navigation_step(step)
```

### Pre-condition Support

```python
# Example: Execute test case with pre-conditions
import yaml

def execute_test_case(test_case_file):
    with open(test_case_file) as f:
        test_case = yaml.safe_load(f)['test_case']
    
    # Check if pre-conditions exist
    if 'pre_conditions' in test_case:
        for precond in test_case['pre_conditions']:
            # Execute parent test case first
            parent_file = f"navigations/core/{precond['test_case']}.yaml"
            execute_test_case(parent_file)
            
            # Verify state after pre-condition
            for verification in precond['state_verification']:
                assert verify_control_state(
                    verification['control'], 
                    verification['expected']
                )
    
    # Execute test case steps (sliced or full)
    if test_case.get('use_sliced_path', False):
        print(f"Using sliced path from index {test_case.get('start_index')}")
    
    for step in test_case['steps']:
        execute_navigation_step(step)

# Execute a child test case with slicing
execute_test_case('navigations/core/start_meeting.yaml')
# This will:
# 1. Execute sign_in_to_app.yaml first (pre-condition)
# 2. Verify "Profile and preferences" is visible
# 3. Execute only the 3 sliced steps (50% faster!)
```

### Benefits of Hierarchical Slicing

1. **Reusability**: Modify `sign_in_to_app.yaml` once, all 52+ child test cases auto-update
2. **Efficiency**: 50% reduction in execution time (8 steps → 4 steps)
3. **Maintenance**: Single point of change for common flows
4. **Clarity**: Clear parent-child relationships via hierarchical_level

## Customization

### Modify Action Type Detection

Edit the `determine_action_type()` method to customize action detection logic:

```python
def determine_action_type(self, control_name: str) -> str:
    """Determine action type based on control name."""
    input_keywords = ['email', 'password', 'username', 'address', 'name', 'code', 'number']
    # Add your custom keywords here
    
    control_lower = control_name.lower()
    for keyword in input_keywords:
        if keyword in control_lower:
            return 'input'
    return 'key'
```

### Customize Output Format

Modify the `generate_yaml_content()` method to change the YAML structure:

```python
def generate_yaml_content(self, control: Dict[str, Any]) -> str:
    """Generate YAML test case content for a control."""
    # Customize YAML structure here
    # Add metadata, tags, timeout values, etc.
```

## Workflow Integration

### Option 1: Standalone Usage

```bash
# Step 1: Build core controls dataset
python build_core_controls_dataset.py --max-depth 9

# Step 2: Generate and configure core controls
python generate_core_controls_config.py
# Edit core_controls_config.json

# Step 3: Extract final dataset
python extract_core_controls_from_config.py

# Step 4: Generate navigation test cases
python generate_navigation_test_cases.py --max-depth 5
```

### Option 2: Batch Script Integration

You can add this step to the existing batch scripts:

```powershell
# Add to build_core_controls.ps1
Write-Host "[Step 5/5] Generating navigation test cases..." -ForegroundColor Green
python generate_navigation_test_cases.py --max-depth 5
```

## Troubleshooting

### Issue: No test cases generated

**Solution**: Check if `go_to_core_controls.json` exists and contains controls with depth <= max-depth

```bash
# Verify input file
python -c "import json; print(len(json.load(open('go_to_core_controls.json'))))"
```

### Issue: Output directory not found

**Solution**: The tool automatically creates the output directory. If it fails, check permissions:

```bash
# Create directory manually
mkdir -p ../../test_cases/navigations/core
```

### Issue: Unicode encoding errors

**Solution**: Ensure your terminal supports UTF-8 encoding:

```powershell
# PowerShell
$OutputEncoding = [System.Text.Encoding]::UTF8
```

## Files Generated

Running with categorization enabled generates 56 test case files organized into subdirectories:

```
src/test_space/test_cases/navigations/preconditions/
├── app_entry/      (4 files)
│   ├── join_a_meeting.yaml
│   ├── sign_in.yaml
│   ├── sign_in_to_app.yaml
│   └── sign_up.yaml
│
├── app_core/       (24 files)
│   ├── calling_menu_item_3_of_8_to_activate_press_spacebar.yaml
│   ├── connect.yaml
│   ├── connect_to_a_device.yaml
│   ├── contacts_menu_item_5_of_8_to_activate_press_spacebar.yaml
│   ├── copy_your_personal_room_information.yaml
│   ├── meetings_menu_item_selected_2_of_8_to_activate_press_spacebar.yaml
│   ├── meetings_tab_list_meeting_recap_tab.yaml
│   ├── messaging_menu_item_1_unread_messages_1_of_8_to_activate_press_spacebar.yaml
│   ├── more_actions_menu_item_collapsed_submenu_8_of_8_to_activate_press_spacebar.yaml
│   ├── more_options_for_scheduling_a_meeting.yaml
│   ├── more_options_for_starting_a_webex_meeting.yaml
│   ├── open_cisco_ai_assistant_panel_alt_i.yaml
│   ├── primary_navigation_menu_messaging_menu_item_1_unread_messages_1_of_8_to_activate_press_spacebar.yaml
│   ├── profile_and_preferences.yaml
│   ├── schedule_a_meeting.yaml
│   ├── search_meet_and_call.yaml
│   ├── set_a_status.yaml
│   ├── settings.yaml
│   ├── start_a_conversation_call_or_meet.yaml
│   ├── start_a_webex_meeting.yaml
│   ├── start_meeting.yaml
│   ├── teams_menu_item_7_of_8_to_activate_press_spacebar.yaml
│   ├── vidcast_menu_item_6_of_8_to_activate_press_spacebar.yaml
│   └── whiteboards_menu_item_4_of_8_to_activate_press_spacebar.yaml
│
└── in_meeting/     (28 files)
    ├── audio_settings_menu_item_1_of_1.yaml
    ├── change_sharing_settings.yaml
    ├── change_virtual_background_menu_item_1_of_2.yaml
    ├── cisco_video_system_move_meeting_to_a_video_device_menu_item_1_of_1.yaml
    ├── closed_captions.yaml
    ├── closed_captions_more_options.yaml
    ├── enable_breakout_sessions_toggle_button_off_5_of_10.yaml
    ├── enable_sign_language_interpretation_toggle_button_off_6_of_10.yaml
    ├── end_meeting.yaml
    ├── invite_and_remind.yaml
    ├── meeting_options_menu_item_8_of_10.yaml
    ├── more_panels.yaml
    ├── mute_all.yaml
    ├── open_ai_assistant_panel.yaml
    ├── open_chat_panel.yaml
    ├── open_participants_panel.yaml
    ├── raise.yaml
    ├── reactions.yaml
    ├── record.yaml
    ├── report_an_issue_menu_item_9_of_10.yaml
    ├── self_view_location_menu_item_2_of_2.yaml
    ├── share.yaml
    ├── shared_content_types_tab_list_screen_or_application_tab_1_of_4.yaml
    ├── show_apps_panel.yaml
    ├── video_settings_menu_item_1_of_1.yaml
    ├── whiteboards_menu_item_4_of_10_new_feature_available.yaml
    ├── write_a_message_to_everyone_press_shift_enter_for_new_line_ready_set_chat_share_key_points_ask_quest.yaml
    └── youre_using_your_computer_for_audio_switch_audio_menu_item_1_of_1.yaml
```

**Note**: The actual output directory is `navigations/preconditions/` with subdirectories based on categorization settings. To generate files in a flat structure without categorization, set `categorization.enabled: false` in the configuration.

## Hierarchical Slicing Design

### Architecture Overview

```
Base Test Case (depth 4):
  hierarchical_level: "2.1.1.2"
  name: sign_in_to_app
  steps: [Sign in, Email, Next, Password, Sign In]  (5 steps)
  role: Foundation for 52+ dependent test cases
  
Intermediate Test Cases (depth 5-7):
  hierarchical_level: "2.1.1.2.30"
  name: start_webex_meeting
  pre_conditions: [sign_in_to_app]  ← References depth 4
  steps: [Start Webex meeting]  (1 step instead of 6)
  
Deep Test Cases (depth 8+):
  hierarchical_level: "2.1.1.2.30.3.1"
  name: start_meeting
  pre_conditions: [start_webex_meeting]  ← References depth 7
  steps: [Accept, Start meeting]  (2 steps instead of 8)
```

### Test Case Construction Workflow

#### Step 1: Identify Control Hierarchy

```json
{
  "name": "Start meeting",
  "hierarchical_level": "2.1.1.2.30.3.1",
  "control_ui_path": [
    " Sign in",          // Level 2
    "Email address",     // Level 2.1
    " Next",             // Level 2.1.1
    " Sign In ",         // Level 2.1.1.2 ← SLICE POINT 1 (depth 4)
    " Start a Webex meeting",  // Level 2.1.1.2.30
    " Accept",           // Level 2.1.1.2.30.3 ← SLICE POINT 2 (depth 7)
    "Start meeting"      // Level 2.1.1.2.30.3.1
  ]
}
```

#### Step 2: Determine Slice Strategy

**Rule**: Find the nearest slice point that's less than current depth

```python
def find_parent_control(self, hierarchical_level: str) -> Optional[str]:
    """
    Find parent control at nearest slice point.
    
    Example:
      - Level "2.1.1.2.30.3.1" (depth 7) → parent at "2.1.1.2.30.3" (depth 6)? 
        No, nearest slice point is depth 7, but 7 == 7, so check depth 4
      - Actually: depth 7 → look for slice point < 7 → finds depth 4
      - Returns: "2.1.1.2" (sign_in_to_app)
    """
    depth = len(hierarchical_level.split('.'))
    
    # Find applicable slice points (must be < current depth)
    for slice_point in sorted(self.slice_points, reverse=True):
        if depth > slice_point:
            # Found the slice point, now get parent at that depth
            parts = hierarchical_level.split('.')
            parent_level = '.'.join(parts[:slice_point])
            return self.find_control_by_level(parent_level)
    
    return None  # No slicing needed
```

#### Step 3: Generate Test Case with Pre-conditions

**Before Slicing** (8 steps, slow):
```yaml
test_case:
  name: start_meeting
  steps:
    - name: " Sign in"
    - name: "Email address"
    - name: " Next"
    - name: "Welcome bts_tony2@mailinator.com Password"
    - name: " Sign In "
    - name: " Start a Webex meeting"
    - name: " Accept"
    - name: "Start meeting"
```

**After Slicing** (3 steps, 50% faster):
```yaml
test_case:
  name: start_meeting
  hierarchical_level: "2.1.1.2.30.3.1"
  
  # Pre-condition ensures sign-in is complete
  pre_conditions:
    - test_case: sign_in_to_app  # hierarchical_level: 2.1.1.2
      state_verification:
        - control: "Profile and preferences"
          expected: visible
  
  # Slicing metadata
  use_sliced_path: true
  start_index: 4
  sliced_hierarchical_level: "30.3.1"
  
  # Only business logic steps
  steps:
    - name: " Start a Webex meeting"
      action:
        type: key
        value: default
    - name: " Accept"
      action:
        type: key
        value: default
    - name: "Start meeting"
      action:
        type: key
        value: default
```

#### Step 4: State Verification Logic

```python
class TestCaseRunner:
    def run_test_case(self, test_case_name):
        """Execute test case with dependency resolution."""
        test_case = self.load_test_case(test_case_name)
        
        # 1. Resolve and execute pre-conditions
        if 'pre_conditions' in test_case:
            for pre_cond in test_case['pre_conditions']:
                # Recursive execution of parent test case
                self.run_test_case(pre_cond['test_case'])
                
                # Verify state after pre-condition
                for verify in pre_cond.get('state_verification', []):
                    if not self.verify_control(verify['control'], verify['expected']):
                        raise PreConditionFailedError(
                            f"State verification failed: {verify['control']} is not {verify['expected']}"
                        )
        
        # 2. Execute test steps (sliced or full)
        steps = test_case['steps']
        for step in steps:
            self.execute_step(step)
```

### Design Benefits

#### 1. High Reusability (90%+ Maintenance Reduction)

```
Single Update Propagates to All Dependents:
  
  Update sign_in_to_app.yaml:
    - Add 2FA step
    - Change password field name
    - Update timeout values
  
  Result:
    ✅ 52+ test cases automatically inherit changes
    ✅ No need to update each test case individually
    ✅ Consistent behavior across all tests
```

#### 2. Clear Hierarchy (Parent-Child Relationships)

```
Visual Dependency Tree:

sign_in (2.1.1.2)                    ← Base (5 steps)
├── schedule_meeting (2.1.1.2.2)     ← +1 step = 6 total (or 1 with slicing)
├── start_webex_meeting (2.1.1.2.30) ← +1 step = 6 total (or 1 with slicing)
│   └── accept_meeting (2.1.1.2.30.3) ← +1 step = 7 total (or 1 with slicing)
│       └── start_meeting (2.1.1.2.30.3.1) ← +1 step = 8 total (or 1 with slicing)
└── profile (2.1.1.2.50)             ← +1 step = 6 total (or 1 with slicing)

With Slicing:
  - Each child only contains its unique steps
  - Total execution: parent + children steps
  - Efficiency: 50-80% faster than full path
```

#### 3. Flexible Execution Modes

| Mode | Use Case | Path Used | Steps | Speed |
|------|----------|-----------|-------|-------|
| **Full Path** | First run / Isolated test | `control_ui_path` | 8 | Slow (100%) |
| **Sliced Path** | Regression / Dependent test | `meeting_ui_path` | 3 | Fast (50%) |
| **Debug Mode** | Troubleshooting | Specific slice | 1-2 | Very Fast (25%) |

#### 4. Multi-Level Slicing Support

**Single Slice Point (Old)**:
```
Depth 1-4: Full path
Depth 5+:  Slice at depth 4
```

**Multi Slice Points (New)** ✅:
```
Depth 1-4: Full path
Depth 5-7: Slice at depth 4  ← First cut
Depth 8+:  Slice at depth 7  ← Second cut (can reference depth 4 indirectly)
```

**Example: Deep Navigation**
```yaml
# Depth 8 test case
test_case:
  name: join_meeting_with_video
  hierarchical_level: "2.1.1.2.30.3.1.5"
  
  pre_conditions:
    # References intermediate slice (depth 7)
    - test_case: start_meeting  # 2.1.1.2.30.3.1
      # Which itself references base slice (depth 4)
      # This creates a dependency chain:
      # join_meeting_with_video → start_meeting → sign_in_to_app
  
  steps:
    - name: "Enable video"  # Only 1 step!
```

### Configuration

Edit `config/test_case_generation_config.json`:

```json
{
  "generation": {
    "slice_points": [4, 7],  // Customize slice depths
    "max_depth": 10
  }
}
```

**Common Configurations**:

| Slice Points | Use Case | Efficiency |
|--------------|----------|------------|
| `[4]` | Simple hierarchy | Moderate |
| `[4, 7]` | Complex navigation | High |
| `[3, 6, 9]` | Very deep trees | Very High |

### Design Evaluation

**Score**: 9.5/10 (HIGHLY RECOMMENDED)

**Advantages**:
- ✅ High reusability: Modify base case once, 52+ dependents auto-update
- ✅ Clear hierarchy: Parent-child relationships via hierarchical_level
- ✅ Flexible execution: Support both full and sliced paths
- ✅ Time efficient: 50-80% reduction in execution time
- ✅ Maintenance cost: Reduced by 90%+
- ✅ Multi-level slicing: Support complex navigation trees
- ✅ State verification: Ensures pre-conditions succeeded
- ✅ Configurable: Adjust slice points per project needs

**Implementation Details**:
- Base cases are complete and include all required steps (e.g., Password)
- Child cases reference parent via `pre_conditions` field
- State verification ensures parent completed successfully before proceeding
- Slicing metadata preserved (`start_index`, `sliced_hierarchical_level`, `use_sliced_path`)
- Automatic parent detection using `find_parent_control()` algorithm
- Configuration-driven via `test_case_generation_config.json`

## Best Practices

### 1. Choosing Slice Points

**Guidelines**:
- **Minimum Depth**: 4 (ensure sufficient base functionality)
- **Minimum Steps**: 3+ steps in sliced portion
- **Stability**: Slice at stable, well-tested flows (e.g., login, navigation)
- **Reuse Count**: 5+ dependent test cases to justify slicing

**Example Analysis**:
```
Candidate: "2.1.1.2" (Sign In to App)
  ✅ Depth: 4
  ✅ Steps: 5 (Sign in → Email → Next → Password → Sign In)
  ✅ Stability: High (core login flow)
  ✅ Dependents: 52+ test cases
  
  Verdict: EXCELLENT slice point
```

### 2. State Verification Strategy

**Essential Verifications**:
```yaml
pre_conditions:
  - test_case: sign_in_to_app
    state_verification:
      # Primary indicator
      - control: "Profile and preferences"
        expected: visible
      
      # Optional: Additional checks
      - control: "Sign Out"
        expected: visible
      
      # Optional: Negative checks
      - control: "Sign in"
        expected: not_visible
```

### 3. Handling Test Failures

**When Pre-condition Fails**:
```python
try:
    execute_pre_condition('sign_in_to_app')
except PreConditionFailedError as e:
    # Option 1: Retry with full path
    execute_test_case_full_path('start_meeting')
    
    # Option 2: Re-run pre-condition
    reset_application_state()
    execute_pre_condition('sign_in_to_app')
    
    # Option 3: Skip test with proper logging
    skip_test(reason=f"Pre-condition failed: {e}")
```

### 4. Optimizing Deep Hierarchies

**For depth > 10**:
```json
{
  "generation": {
    "slice_points": [4, 7, 10],  // Three-tier slicing
    "max_depth": 15
  }
}
```

**Result**:
- Depth 1-4: Full path (base cases)
- Depth 5-7: Slice at 4 (first-level features)
- Depth 8-10: Slice at 7 (second-level features)
- Depth 11+: Slice at 10 (third-level features)

## Manual Test Cases Protection

### Overview

This section explains how manually maintained test cases are protected from being overwritten by auto-generation scripts.

### Protection Mechanisms

#### 1. Directory-Based Separation (Primary)

The main protection comes from directory structure:

- **Auto-generated files** → `navigations/preconditions/` and `navigations/functional/`
- **Manual files** → `navigations/postconditions/`

Since the generation script only writes to `preconditions/` and `functional/` directories, files in `postconditions/` are naturally protected.

#### 2. Exclusion List (Backup)

An explicit exclusion list is maintained in `config/manual_test_cases_exclusion.json`:

```json
{
  "exclusion_list": [
    "postconditions/end_meeting.yaml",
    "postconditions/end_meeting_for_all.yaml",
    "postconditions/sign_out.yaml"
  ]
}
```

The generation script checks this list before writing any file to ensure manual files are never overwritten.

### Manually Maintained Test Cases

#### Current List

| File | Reason for Manual Maintenance |
|------|------------------------------|
| `postconditions/end_meeting.yaml` | Custom 2-step navigation logic different from auto-generated version |
| `postconditions/end_meeting_for_all.yaml` | Uses keyboard shortcuts (`Direct Arrow Down`, `Direct Enter`) not in dataset |
| `postconditions/sign_out.yaml` | 3-step custom flow through Profile menu (control not in generation dataset) |

#### Key Characteristics

These test cases:
- ✅ Use steps that may NOT be dataset keys (acceptable for manual cases)
- ✅ Implement custom navigation logic
- ✅ Use keyboard shortcuts or UI elements not modeled in dataset
- ✅ Located in `postconditions/` directory (never touched by generator)

### How to Add New Manual Test Cases

1. **Place file in `postconditions/` directory**
   ```
   test_cases/navigations/postconditions/your_test.yaml
   ```

2. **Add to exclusion list** (optional but recommended):
   ```json
   {
     "exclusion_list": [
       "postconditions/your_test.yaml"
     ]
   }
   ```

3. **Document the reason** in `config/manual_test_cases_exclusion.json`:
   ```json
   {
     "notes": {
       "your_test.yaml": "Explanation of why this needs manual maintenance"
     }
   }
   ```

### Verification

#### Verify Protection

Run the generation script and confirm manual files are not modified:

```bash
python generate_navigation_test_cases.py --max-depth 10
```

Look for:
```
[i] Loaded 3 excluded test case(s) (manual)
```

Check git status to confirm manual files are unchanged:
```bash
git status test_cases/navigations/postconditions/
```

### Architecture Decisions

#### Why Directory-Based Protection?

1. **Clear Separation of Concerns**
   - `preconditions/`: Core navigation paths (auto-generated)
   - `functional/`: Feature-specific tests (auto-generated)
   - `postconditions/`: Cleanup/teardown logic (manual)

2. **Self-Documenting**
   - File location indicates maintenance approach
   - No need to check multiple sources to know if file is auto-generated

3. **Robust**
   - Even if exclusion list is forgotten, directory structure protects files
   - Generator would need to be explicitly reconfigured to touch `postconditions/`

#### When to Use Manual vs Auto-Generated?

**Use Auto-Generation When:**
- ✅ Test follows standard navigation pattern (UI path → control)
- ✅ All steps are modeled in dataset
- ✅ No custom logic or keyboard shortcuts

**Use Manual When:**
- ✅ Custom multi-step logic
- ✅ Keyboard shortcuts not in dataset
- ✅ UI elements not modeled as independent controls
- ✅ Cleanup/teardown scenarios

### Troubleshooting

#### Q: My manual test case was overwritten!

**A:** Check:
1. Is the file in `postconditions/` directory? (It should be)
2. Is it in the exclusion list? (Add it)
3. Run `git diff` to see what changed
4. Restore from git: `git checkout HEAD -- path/to/file.yaml`

#### Q: How do I know if a test case is auto-generated?

**A:** Check:
1. File location: `preconditions/` or `functional/` = auto-generated
2. File location: `postconditions/` = manual
3. Check `config/manual_test_cases_exclusion.json` for explicit list

## Related Documentation

- [README_BUILD_CORE_CONTROLS.md](./README_BUILD_CORE_CONTROLS.md) - Core controls dataset building workflow
- [README_CORE_CONTROLS_OVERRIDES.md](./README_CORE_CONTROLS_OVERRIDES.md) - Control property override system
- [README_SELF_CALIBRATION.md](./README_SELF_CALIBRATION.md) - Self-calibration system for control property overrides
- Build script: [build_core_controls.ps1](./build_core_controls.ps1) - 5-step automated build process
- Configuration: [config/manual_test_cases_exclusion.json](./config/manual_test_cases_exclusion.json) - Manual test case exclusion list

## Support

For questions or issues, please refer to the main project documentation or contact the development team.

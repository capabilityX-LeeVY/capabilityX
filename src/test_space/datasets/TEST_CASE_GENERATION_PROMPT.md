# Test Case Generation Prompt Template

## Purpose
This prompt template guides the generation of keyboard navigation test cases based on control datasets for accessibility testing in Webex applications.

## Input Requirements

### 1. Control Dataset
- **Location**: `src/test_space/datasets/control_specific_metadata.json`
- **Format**: JSON array containing control metadata in sequential order
- **Required Fields**:
  - `name`: Control name/label
  - `metadata.windows.control_name`: Windows accessibility name
  - `metadata.windows.control_id`: Unique control identifier

### 2. Reference Test Case
- **Location**: `src/test_space/test_cases/accessibility/sequence/`
- **Example**: `whiteboards.yaml`
- **Purpose**: Provides formatting template and structure

### 3. Output File
- **Location**: `src/test_space/test_cases/accessibility/sequence/`
- **Format**: YAML file
- **Naming Convention**: `{feature_name}.yaml`

## Control Sequence Definition

The `control_specific_metadata.json` file contains controls in the exact Tab navigation order for a specific feature.

**Standard Sequence:**
- **First Control**: The first object in the JSON array (e.g., "Personal Room" for meetings)
- **Last Control**: The last object in the JSON array (e.g., "Resize navigation menu to show labels")
- **Complete Sequence**: All controls from first to last in the order they appear in the file

**Example for Meetings Feature:**
```json
[
    {"name": "Personal Room", ...},           // First control - START HERE
    {"name": "Copy my personal room link", ...},
    {"name": "Start a Webex meeting", ...},
    // ... more controls in navigation order ...
    {"name": "Settings", ...},
    {"name": "Help menu", ...},
    {"name": "Resize navigation menu to show labels", ...}  // Last control - END HERE
]
```

## Task Instructions

### Step 1: Identify Control Sequence
1. Open the control dataset file `control_specific_metadata.json`
2. **Starting Control**: First object in the JSON array
3. **Ending Control**: Last object in the JSON array
4. Extract ALL controls in sequence from first to last (the complete array)

### Step 2: Generate Tab Sequence (Forward Navigation)
Create test steps for forward keyboard navigation:

```yaml
# Tab sequence for {feature_name}
- name: "{Control Name 1}"
  action:
    type: key
    value: tab  # or 'down' for menu items
  expect_state: "{Control Name 2}"
  ui_response: true  # Optional: only for first step

- name: "{Control Name 2}"
  action:
    type: key
    value: tab  # or 'down' for menu items
  expect_state: "{Control Name 3}"
```

**Key Rules for Tab Sequence:**
- **Regular controls**: Use `value: tab`
- **Menu items** (controls containing "menu item"): Use `value: down`
- **First step**: Add `ui_response: true` for performance measurement
- **First step action**: Use `value: default` instead of `tab` if starting from a menu selection
- **Sequence**: Each step's `expect_state` must match the next step's `name`

### Step 3: Generate Shift+Tab Sequence (Reverse Navigation)
Create test steps for reverse keyboard navigation:

```yaml
# Shift + Tab sequence for {feature_name}
- name: "{Last Control Name}"
  action:
    type: key
    value: shift+tab  # or 'up' for menu items
  expect_state: "{Second-to-Last Control Name}"

- name: "{Second-to-Last Control Name}"
  action:
    type: key
    value: shift+tab  # or 'up' for menu items
  expect_state: "{Third-to-Last Control Name}"
```

**Key Rules for Shift+Tab Sequence:**
- **Regular controls**: Use `value: shift+tab`
- **Menu items** (controls containing "menu item"): Use `value: up`
- **Order**: Reverse of Tab sequence
- **Consistency**: Must mirror the Tab sequence exactly in reverse

### Step 4: Complete YAML Structure
Wrap the sequences in the full test case structure:

```yaml
test_case:
  name: app_core_{feature_name}
  description: Verify app core {feature_name} navigation and all controls are accessible with keyboard.
  expect_result: App core {feature_name} is verified successfully and all controls are accessible.
  pre_conditions:
    - navigations/basic/sign_in
  steps:
    # Tab sequence for {feature_name}
    [Insert Tab sequence steps here]

    # Shift + Tab sequence for {feature_name}
    [Insert Shift+Tab sequence steps here]

  post_conditions: null
  retry_enabled: false
  record_traversal: true
  check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Untranslated&Truncated, Performance]
```

## Special Cases

### Menu Navigation
When navigating through menu items:
- **Forward (Tab sequence)**: Use `down` key instead of `tab`
- **Reverse (Shift+Tab sequence)**: Use `up` key instead of `shift+tab`
- **Pattern**: Applies to all controls with "menu item" in the name

**Example:**
```yaml
- name: "Primary navigation menu Messaging menu item"
  action:
    type: key
    value: down  # Not tab!
  expect_state: "Meetings menu item"

- name: "Meetings menu item"
  action:
    type: key
    value: down  # Not tab!
  expect_state: "Calling menu item"
```

### Creating Loops
To create a complete navigation loop:
1. Last control in Tab sequence should navigate back to first control
2. This creates a circular navigation path
3. Example: `"You're not signed in to phone services. Open Settings"` → `"Profile and preferences, Available"`

### Missing Controls
If a control appears to be missing between two steps:
1. Search the dataset for intermediate controls
2. Insert the missing control(s) in the sequence
3. Update both Tab and Shift+Tab sequences accordingly

## Example Prompt for Claude

```
I need to create a test case for keyboard navigation testing based on the control dataset.

**Control Dataset**: src/test_space/datasets/control_specific_metadata.json

**Scope**: Generate test case for ALL controls in the dataset
- **Starting Control**: First control in the JSON array (e.g., "Personal Room")
- **Ending Control**: Last control in the JSON array (e.g., "Resize navigation menu to show labels")
- **Include**: Every control from start to end in the exact order they appear

**Reference Format**: src/test_space/test_cases/accessibility/sequence/whiteboards.yaml

**Output File**: src/test_space/test_cases/accessibility/sequence/{feature_name}.yaml

**Instructions**:
1. Extract the COMPLETE control sequence from the dataset (all controls from first to last)
2. Generate Tab sequence (forward navigation):
   - Start from the first control in the JSON array
   - Use 'tab' for regular controls
   - Use 'down' for menu items (controls containing "menu item")
   - First step: Use `value: default` if starting from a menu selection
   - Set `ui_response: true` for the first step only
   - End at the last control in the JSON array
3. Generate Shift+Tab sequence (reverse navigation):
   - Start from the last control in the JSON array
   - Use 'shift+tab' for regular controls
   - Use 'up' for menu items (controls containing "menu item")
   - Reverse the exact order of Tab sequence
   - End at the first control in the JSON array
4. Optional: Create a complete loop by adding one more step where the last control navigates back to the first
5. Write the complete test case to the output file following the YAML structure

Please ensure:
- ALL controls from the dataset are included (no skipping)
- Controls are in the exact sequential order as they appear in the JSON array
- Menu items use down/up keys instead of tab/shift+tab
- The Shift+Tab sequence exactly mirrors the Tab sequence in reverse
- Each step's `expect_state` matches the next step's `name`
- The test case forms a complete navigation loop (optional)
```

## Quality Checklist

Before finalizing the test case, verify:

- [ ] All controls from dataset are included in order
- [ ] Tab sequence uses correct key values (tab/down)
- [ ] Shift+Tab sequence is exact reverse of Tab sequence
- [ ] Shift+Tab sequence uses correct key values (shift+tab/up)
- [ ] Menu items use down/up instead of tab/shift+tab
- [ ] First step has `ui_response: true`
- [ ] Each step's `expect_state` matches next step's `name`
- [ ] Navigation forms a complete loop (optional)
- [ ] YAML syntax is valid
- [ ] Test case metadata is complete

## Common Errors to Avoid

1. **Inconsistent sequences**: Shift+Tab must be exact reverse of Tab
2. **Wrong keys for menus**: Using tab/shift+tab instead of down/up for menu items
3. **Broken chain**: expect_state doesn't match next step's name
4. **Missing controls**: Skipping intermediate controls from the dataset
5. **Invalid YAML**: Incorrect indentation or syntax errors

## Validation

After generation, validate by:
1. Running the test case: `uv run python src/run_test_case_job.py --test_suite "{feature_name}"`
2. Checking that all controls are reached in order
3. Verifying the loop completes successfully
4. Reviewing the test report for any failures

## Additional Resources

- **Test Case Documentation**: `src/docs/TEST_CASE.md`
- **Control Dataset README**: `src/test_space/datasets/README.md`
- **Example Test Cases**: `src/test_space/test_cases/accessibility/sequence/`
- **Framework Documentation**: `src/docs/CLAUDE.md`

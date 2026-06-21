# Build Core Controls Dataset - Complete Workflow

## 📋 Overview

This guide provides a complete workflow for building a core controls dataset from the raw control data. The core controls dataset contains only the most essential UI controls needed for automation testing, filtering out auxiliary and less frequently used controls.

## 🎯 Purpose

**Why build a core controls dataset?**
- **Reduce complexity**: From 1182+ controls to a focused set of 20-50 core controls
- **Improve test reliability**: Focus on the most important user workflows
- **Faster test execution**: Less navigation, more efficient automation
- **Easier maintenance**: Fewer controls to update when UI changes

## 📁 Directory Structure

```
src/datasets/core/
├── config/                                         # Configuration files
│   ├── core_controls_config.json                  # Control selection config
│   ├── self_calibration.json                      # Self-calibration configuration
│   └── test_case_generation_config.json           # Test case generation settings
├── data/                                          # Dataset files
│   ├── control_datasets_with_ui_path.json         # Source dataset (1182+ controls)
│   ├── go_to_core_controls_raw.json               # Intermediate (211 controls)
│   └── go_to_core_controls.json                   # Final output (20-50 controls)
├── README_BUILD_CORE_CONTROLS.md                  # This file - Complete workflow
├── README_CORE_CONTROLS_OVERRIDES.md              # Overrides system guide
├── README_GENERATE_TEST_CASES.md                  # Test case generation guide
├── build_core_controls_dataset.py                 # Phase 1: Initial filtering
├── generate_core_controls_config.py               # Phase 2: Config generation
├── extract_core_controls_from_config.py           # Phase 3: Final extraction
├── apply_self_calibration.py                      # Phase 5: Apply self-calibration
├── generate_navigation_test_cases.py              # Phase 5: Generate test cases
├── build_core_controls.ps1                        # Automated build script
└── core_controls_selection.txt                    # Human-readable reference
```

### Core Workflow Files

- **build_core_controls_dataset.py** - Phase 1: Filter controls by depth and deduplicate
- **generate_core_controls_config.py** - Phase 2: Generate editable configuration with selection flags
- **extract_core_controls_from_config.py** - Phase 3: Extract final dataset from selections
- **apply_self_calibration.py** - Phase 4: Apply self-calibration to control properties
- **generate_navigation_test_cases.py** - Phase 5: Generate YAML test cases from core controls
- **build_core_controls.ps1** - Automated 6-step workflow script

### Configuration Files (config/)

- **build_workflow_config.json** - Build workflow default paths and settings (Phases 1-5)
- **core_controls_config.json** - Control selection configuration (Phase 2 output, Phase 3 input)
- **self_calibration.json** - Self-calibration configuration (Phase 4)
- **test_case_generation_config.json** - Test case generation settings (Phase 5)

### Dataset Files (data/)

- **control_datasets_with_ui_path.json** - Source dataset with 1182+ controls (Phase 1 input)
- **go_to_core_controls_raw.json** - Intermediate filtered dataset with 211 controls (Phase 1 output)
- **go_to_core_controls.json** - Final core controls dataset with 20-50 controls (Phase 3 output, Phase 4 input/output)

**Note**: All dataset files use **dictionary format** (control names as keys) for O(1) lookup performance. Legacy array format is automatically converted by all scripts.

### Dataset Format

**Current Dictionary Format**:
```json
{
  " Join a meeting": {
    "metadata": {
      "windows": {
        "control_name": " Join a meeting",
        "control_ui_path": [" Join a meeting"],
        ...
      }
    }
  }
}
```

**Benefits**:
- ✅ O(1) lookup speed vs O(n) array search
- ✅ Automatic deduplication (keys must be unique)
- ✅ Cleaner structure without redundant `name` field
- ✅ Backward compatible - all scripts auto-convert legacy array format

### Documentation

- **README_BUILD_CORE_CONTROLS.md** - This file: Complete 6-step workflow guide
- **README_SELF_CALIBRATION.md** - Detailed guide for Phase 4 (self-calibration system)
- **README_GENERATE_TEST_CASES.md** - Detailed guide for Phase 5 (test case generation)

## 🚀 Quick Start (TL;DR)

```bash
cd src/datasets/core

# Option 1: Use automated batch script (Recommended)
# PowerShell (Windows/Linux/Mac)
.\build_core_controls.ps1              # Manual mode (pause for editing)
.\build_core_controls.ps1 -Mode auto   # Auto mode (use existing config)

# Option 2: Run steps manually
# Step 1: Build filtered dataset (1182 → 211 controls)
python build_core_controls_dataset.py --max-depth 9 --only-main-controls

# Step 2: Generate configuration files
python generate_core_controls_config.py

# Step 3: Edit core_controls_config.json
#   - Set "selected": true for controls you want to include
#   - Or refer to core_controls_selection.txt for browsing

# Step 4: Extract final dataset (20-50 core controls)
python extract_core_controls_from_config.py

# Step 5 (Optional): Apply self-calibration for fine-tuning
python apply_self_calibration.py \
    --input data/go_to_core_controls.json \
    --output data/go_to_core_controls.json \
    --config config/self_calibration.json

# Step 6: Generate navigation test cases
python generate_navigation_test_cases.py --max-depth 10

# Result: YAML test cases in ../../test_cases/navigations/core/
# Note: Includes full dependency chains for hierarchical test execution
```

> **💡 Tip**: For detailed test case generation documentation, see [README_GENERATE_TEST_CASES.md](./README_GENERATE_TEST_CASES.md)

## 🔄 Complete Workflow

### Phase 1: Initial Filtering (Automated)

**Goal**: Filter from 1182 controls → ~211 controls (depth 1-9 with main paths)

**Input**: `control_datasets_with_ui_path.json` (located in parent directory)

**Script**: `build_core_controls_dataset.py`

**Command**:
```bash
python build_core_controls_dataset.py --max-depth 9 --only-main-controls
```

**What it does**:
1. Loads all controls from source file
2. Filters controls with empty names
3. Filters by hierarchical depth (≤9)
4. Deduplicates by keeping shortest path for same name
5. Extracts all main path controls (all prefixes of complete paths)

**Parameters**:
- `--input`: Input JSON file path (default: `../control_datasets_with_ui_path.json`)
- `--output`: Output file (default: `go_to_core_controls_raw.json`)
- `--max-depth`: Maximum hierarchical depth (default: 10, recommended: 8-9)
- `--only-main-controls`: Extract main path controls (all path prefixes)
- `--first-per-depth`: Keep only first control per depth (optional)
- `--no-save`: Show statistics without saving (for testing)

**Output**: `go_to_core_controls_raw.json`

**Statistics Example**:
```
Loaded 1182 controls
After empty name filter: 1181
After depth filter: 235
After deduplication: 216
After main path extraction: 211

Distribution by depth:
  Depth 1: 6 controls
  Depth 2: 2 controls
  Depth 3: 1 control
  Depth 4: 7 controls
  Depth 5: 30 controls
  Depth 6: 5 controls
  Depth 7: 5 controls
  Depth 8: 23 controls
  Depth 9: 132 controls
```

---

### Phase 2: Configuration Generation (Automated)

**Goal**: Generate editable configuration listing all 211 controls

**Input**: `go_to_core_controls_raw.json`

**Script**: `generate_core_controls_config.py`

**Command**:
```bash
python generate_core_controls_config.py
```

**What it does**:
1. Reads the filtered dataset
2. Groups controls by depth
3. Generates JSON configuration with all controls marked as `"selected": false`
4. Creates human-readable text reference file

**Outputs**:
- `core_controls_config.json` - JSON configuration (for editing)
- `core_controls_selection.txt` - Text reference (for browsing)

**Configuration Format**:
```json
{
    "_comment": "Core controls configuration file...",
    "_instructions": [...],
    "depths": {
        "4": {
            "total_controls": 7,
            "description": "All controls at depth 4",
            "controls": [
                {
                    "name": "Welcome bts_tony2@mailinator.com Password",
                    "control_type": "edit",
                    "ui_path": [
                        " Sign in",
                        "Email address",
                        " Next",
                        "Welcome bts_tony2@mailinator.com Password"
                    ],
                    "selected": false  // ← Change to true to select
                }
            ]
        }
    }
}
```

---

### Phase 3: Manual Selection (Manual)

**Goal**: Select 20-50 most important controls for your use case

**File to Edit**: `core_controls_config.json`

**How to Select Controls**:

1. **Open** `core_controls_config.json` in an editor
2. **Review** each depth section
3. **Set** `"selected": true` for controls you want to include
4. **Save** the file

**Selection Strategy**:

#### By User Scenario:
- **Sign-in Flow** (Depth 1-4): Essential for authentication
  - Join a meeting, Sign in, Email address, Next, Password, Sign In button
  
- **Main Navigation** (Depth 5): Core app features
  - Start/Schedule meeting, Settings, Search, Navigation tabs (Meetings, Messaging, Calling, Contacts)
  
- **Meeting Join** (Depth 7): Enter meeting
  - Start meeting button, Accept disclaimer
  
- **In-Meeting Controls** (Depth 9): Meeting interactions
  - Mute/Unmute, Start/Stop video, Share, Leave, Participants, Chat, Record

#### Selection Principles:
- ✅ **Must-have**: Controls in critical user paths
- ✅ **Frequently used**: Daily operations (mute, video, share)
- ✅ **Decision points**: Buttons that advance workflow
- ❌ **Skip**: Help links, auxiliary options, advanced settings
- ❌ **Skip**: Decorative text, status indicators (unless critical)

**Recommended Count by Depth**:
```
Depth 1: 2-3 controls  (Join meeting, Sign in)
Depth 2: 1 control     (Email address)
Depth 3: 1 control     (Next button)
Depth 4: 2-3 controls  (Password, Sign In, Forgot password)
Depth 5: 6-10 controls (Main navigation + key actions)
Depth 6: 0-2 controls  (Optional: Personal room, Connect)
Depth 7: 1-2 controls  (Start meeting, Accept)
Depth 8: 0-3 controls  (Optional: Pre-meeting controls)
Depth 9: 8-15 controls (Core meeting controls)

Total: 20-50 controls recommended
```

**Example Selection** (Minimal Set):
```json
// Depth 1
{"name": " Join a meeting", "selected": true}
{"name": " Sign in", "selected": true}

// Depth 2
{"name": "Email address", "selected": true}

// Depth 3
{"name": " Next", "selected": true}

// Depth 4
{"name": "Welcome bts_tony2@mailinator.com Password", "selected": true}
{"name": " Sign In ", "selected": true}

// Depth 5
{"name": " Start a Webex meeting", "selected": true}
{"name": " Meetings menu item", "selected": true}
{"name": " Settings", "selected": true}

// Depth 7
{"name": "Start meeting", "selected": true}

// Depth 9
{"name": "Mute", "selected": true}
{"name": "Unmute", "selected": true}
{"name": "Start video", "selected": true}
{"name": "Stop video", "selected": true}
{"name": "Share", "selected": true}
{"name": " Leave", "selected": true}
```

---

### Phase 4: Final Extraction (Automated)

**Goal**: Extract selected controls into final dataset

**Input**: `core_controls_config.json` (with selections)

**Script**: `extract_core_controls_from_config.py`

**Command**:
```bash
python extract_core_controls_from_config.py
```

**What it does**:
1. Reads configuration file
2. Collects all controls where `"selected": true`
3. Extracts full control data from intermediate dataset
4. Displays summary statistics
5. Saves final core controls dataset

**Output**: `go_to_core_controls.json`

**Example Output**:
```
Loading configuration: core_controls_config.json
Loading complete dataset: go_to_core_controls_raw.json

Extracting selected core controls...

======================================================================
Core Controls Extraction Results
======================================================================

Depth 1 (2 controls):
  ✓  Join a meeting (button)
  ✓  Sign in (button)

Depth 2 (1 controls):
  ✓ Email address (edit)

Depth 3 (1 controls):
  ✓  Next (button)

...

======================================================================
Total: 19 core controls
Depth coverage: 1 to 9
======================================================================

✓ Core controls saved to: go_to_core_controls.json
```

---

### Phase 5: Apply Control Overrides (Optional)

**Goal**: Fine-tune individual control properties (UI paths, names, IDs, etc.)

**Input**: 
- `go_to_core_controls.json` (from Phase 4)
- `config/self_calibration.json` (editable configuration)

**Script**: `apply_self_calibration.py`

**When to Use**:
- Fix missing steps in UI paths (e.g., missing Password field)
- Customize control display names for clarity
- Override control IDs, types, or window information
- Standardize control properties across dataset

**Quick Example**:

Edit `config/self_calibration.json`:
```json
{
  "overrides": {
    " Sign In ": {
      "control_ui_path": [
        " Sign in",
        "Email address",
        " Next",
        "Welcome bts_tony2@mailinator.com Password",  // <- Added missing step
        " Sign In "
      ],
      "control_name": null,
      "reason": "Add missing Password step to sign-in flow",
      "updated": "2025-12-13",
      "enabled": true
    }
  }
}
```

**Apply Self-Calibration**:
```bash
python apply_self_calibration.py \
    --input data/go_to_core_controls.json \
    --output data/go_to_core_controls.json \
    --config config/self_calibration.json
```

**What it does**:
1. Loads override configuration
2. Creates backup of original dataset
3. Applies enabled overrides to matching controls
4. Preserves original values for `null` properties
5. Saves updated dataset with override statistics

**Output Example**:
```
============================================================
🔧 Core Controls Overrides Applier
============================================================

✅ Loaded 2 control override(s)
⚠️  Skipped 0 disabled override(s)

📦 Backup created: go_to_core_controls_backup_20251213_154302.json

🔧 Applying control overrides...

✅ Applied override:  Sign In 
   Properties: control_ui_path
   UI Path: 4 steps → 5 steps
   Reason: Add missing Password step to sign-in flow

============================================================
📊 Override Statistics:
============================================================
Total controls:        19
Applied overrides:     1
Disabled overrides:    0
Override ratio:        5.3%
============================================================

✅ Complete!
```

**Available Override Properties**:
- `control_ui_path` - Navigation steps (array)
- `control_name` - Display name (string)
- `control_id` - Automation ID (string)
- `control_type` - UI element type code (integer)
- `control_type_name` - Type name like "button", "edit" (string)
- `window_name` - Parent window name (string)
- `window_id` - Window identifier (string)

**📖 For complete self-calibration system documentation, patterns, and examples, see:**
[README_SELF_CALIBRATION.md](./README_SELF_CALIBRATION.md)

---

## 🔧 Advanced Usage

### Re-run with Different Depths

Test different depth levels to find optimal balance:

```bash
# Conservative (fewer controls)
python build_core_controls_dataset.py --max-depth 7 --only-main-controls

# Standard (recommended)
python build_core_controls_dataset.py --max-depth 9 --only-main-controls

# Comprehensive (more controls)
python build_core_controls_dataset.py --max-depth 10 --only-main-controls
```

### Test Without Saving

Preview results before committing:

```bash
python build_core_controls_dataset.py --max-depth 8 --only-main-controls --no-save
```

### Get First Control Per Depth

Quick sample for initial exploration:

```bash
python build_core_controls_dataset.py --max-depth 9 --first-per-depth
```

### Regenerate Configuration

If you need to start fresh:

```bash
# This will overwrite existing config (all selections will be lost)
python generate_core_controls_config.py
```

---

## 📊 Quality Checks

### Before Selection (Phase 3)

1. **Review all depths**: Check `core_controls_selection.txt` for readable overview
2. **Understand paths**: Look at `ui_path` to understand control hierarchy
3. **Check control types**: Ensure buttons, edits, and navigation items are present

### After Extraction (Phase 4)

1. **Verify count**: Should have 20-50 controls for most use cases
2. **Check coverage**: All critical depths should be represented (1-7 minimum)
3. **Validate paths**: Ensure complete navigation paths from start to target
4. **Test completeness**: Can you navigate from sign-in to meeting controls?

### Validation Checklist

- [ ] Can sign in to application (Depth 1-4 controls)
- [ ] Can access main features (Depth 5 navigation)
- [ ] Can start/join a meeting (Depth 5-7 controls)
- [ ] Can use meeting controls (Depth 9 controls)
- [ ] Total count is reasonable (20-50 controls)
- [ ] No broken paths (each step leads to next)

---

## 🚀 Quick Start (TL;DR)

```bash
# Navigate to core directory
cd src/datasets/core

# Step 1: Build filtered dataset (depth 1-9)
python build_core_controls_dataset.py --max-depth 9 --only-main-controls

# Step 2: Generate configuration
python generate_core_controls_config.py

# Step 3: Edit core_controls_config.json
# Set "selected": true for controls you want

# Step 4: Extract final dataset
python extract_core_controls_from_config.py

# Result: go_to_core_controls.json is ready to use!
```

---

## 📝 File Descriptions

### Python Scripts

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `build_core_controls_dataset.py` | Initial filtering and main path extraction | `control_datasets_with_ui_path.json` | `go_to_core_controls_raw.json` |
| `generate_core_controls_config.py` | Generate editable configuration | `go_to_core_controls_raw.json` | `core_controls_config.json`, `core_controls_selection.txt` |
| `extract_core_controls_from_config.py` | Extract selected controls | `core_controls_config.json`, `go_to_core_controls_raw.json` | `go_to_core_controls.json` |

### Data Files

| File | Description | Format | Editable |
|------|-------------|--------|----------|
| `go_to_core_controls_raw.json` | Intermediate filtered dataset (211 controls) | JSON | No |
| `core_controls_config.json` | Configuration with all controls and selection flags | JSON | **Yes** |
| `core_controls_selection.txt` | Human-readable control list | Text | No |
| `go_to_core_controls.json` | **Final output** with selected core controls | JSON | No |

---

## 🔍 Troubleshooting

### Issue: Too many controls in intermediate dataset

**Problem**: `go_to_core_controls_raw.json` has too many controls (>250)

**Solution**:
```bash
# Reduce max depth
python build_core_controls_dataset.py --max-depth 8 --only-main-controls

# Or get only first per depth as sample
python build_core_controls_dataset.py --max-depth 9 --first-per-depth
```

### Issue: No controls extracted in final dataset

**Problem**: `extract_core_controls_from_config.py` shows "No controls selected"

**Solution**:
1. Open `core_controls_config.json`
2. Find controls you want
3. Change `"selected": false` to `"selected": true`
4. Save and run extraction again

### Issue: Missing critical path controls

**Problem**: Can't complete workflow (e.g., can't reach meeting from sign-in)

**Solution**:
1. Check `core_controls_selection.txt` for available controls
2. Trace the path: Sign in → Email → Next → Password → Sign In → Start Meeting
3. Select all controls in the path chain
4. Re-run extraction

### Issue: Configuration file corrupted

**Problem**: JSON syntax error or formatting issues

**Solution**:
```bash
# Regenerate from scratch (will lose current selections)
python generate_core_controls_config.py
```

---

## 💡 Best Practices

### 1. Start Conservative
- Begin with minimum controls (20-30)
- Add more if needed after testing
- Easier to add than remove

### 2. Document Your Selections
Keep notes on why you selected specific controls:
```json
{
    "name": "Unmute",
    "selected": true,
    // NOTE: Critical for accessibility testing
}
```

### 3. Version Control Your Config
- Commit `core_controls_config.json` with selections
- Track changes when updating control selections
- Document reason for changes in commit messages

### 4. Test Your Dataset
After extraction, verify the dataset works:
```python
import json

with open('data/go_to_core_controls.json') as f:
    controls = json.load(f)
    
# Dictionary format: keys are control names
print(f"Total controls: {len(controls)}")

# Check each depth is represented
from collections import Counter
depths = Counter()
for name, control in controls.items():
    depth = len(control['metadata']['windows']['shortest_hierarchical_level'].split('.'))
    depths[depth] += 1
    
print("Controls by depth:", dict(depths))
```

**Note**: Dataset uses dictionary format where control names are keys. All scripts automatically handle format detection and conversion.

### 5. Periodic Updates
- Re-run workflow when UI changes
- Review selections quarterly
- Add new critical controls as product evolves

---

## 🔄 Dataset Format Migration

### Current Format: Dictionary (Key-Value)

All dataset files have been migrated to **dictionary format** for optimal performance:

**Format Structure**:
```json
{
  "Control Name": {
    "metadata": {
      "windows": {
        "control_name": "Control Name",
        "control_ui_path": [...],
        ...
      }
    }
  }
}
```

**Key Advantages**:
1. **Performance**: O(1) lookup vs O(n) array iteration
2. **Data Quality**: Automatic deduplication (unique keys)
3. **Maintainability**: No redundant `name` field at top level
4. **Compatibility**: All scripts auto-detect and convert legacy formats

### Backward Compatibility

All workflow scripts support **automatic format detection**:

```python
# Automatic conversion in all scripts
if isinstance(data, dict):
    # Dictionary format → convert to list for processing
    controls_list = [
        {**control_data, "name": name}
        for name, control_data in data.items()
    ]
else:
    # Legacy array format → use directly
    controls_list = data
```

**No manual intervention needed** - scripts transparently handle both formats.

### Migration Status

| File | Format | Controls | Status |
|------|--------|----------|--------|
| `control_datasets_with_ui_path.json` | Dictionary | 1182 | ✅ Migrated |
| `go_to_core_controls_raw.json` | Dictionary | 211 | ✅ Migrated |
| `go_to_core_controls.json` | Dictionary | 56 | ✅ Migrated |

### Modified Scripts (All Backward Compatible)

| Script | Changes | Compatibility |
|--------|---------|---------------|
| `build_core_controls_dataset.py` | Auto-detect format in `load_data()` | ✅ Both formats |
| `generate_navigation_test_cases.py` | Auto-convert in `load_controls_data()` | ✅ Both formats |
| `extract_core_controls_from_config.py` | Dict→List→Dict conversion | ✅ Both formats |
| `apply_self_calibration.py` | Format detection on load/save | ✅ Both formats |
| `generate_core_controls_config.py` | Auto-detect in `load_data()` | ✅ Both formats |

**Result**: ✅ All workflows function identically with improved performance

---

## 📚 Related Documentation

- `README_UI_PATH.md` - Documentation for UI path generation and data structure
- `README_GENERATE_TEST_CASES.md` - Test case generation with hierarchical slicing
- `README_SELF_CALIBRATION.md` - Control property override system
- `WORKFLOW_DIAGRAM.txt` - Visual representation of the workflow
- Parent directory `src/test_space/datasets/` - Contains other control datasets

---

## 🤝 Contributing

When adding new controls or updating the workflow:

1. **Test thoroughly**: Run through complete workflow
2. **Update this README**: Document any new parameters or options
3. **Provide examples**: Add real-world use cases
4. **Version appropriately**: Track changes to scripts

---

## 📞 Support

For questions or issues:
1. Check this README for solutions
2. Review `core_controls_selection.txt` for available controls
3. Run with `--no-save` flag to test parameters
4. Check console output for detailed error messages

---

## 📄 License & Usage

This workflow is part of the Webex Regression Shield project.
Use these scripts to generate core control datasets for automation testing purposes.

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Maintainer**: Webex Test Automation Team


# Self-Calibration System - Complete Guide

## Overview

The **Self-Calibration System** is a core feature that allows you to dynamically adjust control properties through configuration files, without modifying code. This enables rapid adaptation to UI changes and maintains test suite accuracy over time.

`config/self_calibration.json` is the **configuration-driven tuning mechanism** that allows you to fine-tune any property of core controls for test case generation, including:

- **UI Paths** - Navigation steps to reach a control
- **Control Names** - Display names and identifiers
- **Control IDs** - Automation IDs for UI interaction
- **Control Types** - UI element types (button, edit, etc.)
- **Window Information** - Parent window names and IDs
- **And more...** - Any property in `metadata.windows`

## Key Features

✅ **Control-Level Tuning** - Override any control property  
✅ **Configuration-Based** - All rules in JSON, zero code changes  
✅ **Flexible** - Override single or multiple properties per control  
✅ **Granular Control** - Enable/disable individual overrides  
✅ **Traceable** - Each override has reason and timestamp  
✅ **Team-Friendly** - Anyone can edit JSON configuration

---

## ⚡ Quick Start

### 1. Edit Configuration
```bash
code config/self_calibration.json
```

### 2. Add Override
```json
{
  "overrides": {
    "Your Control Name": {
      "control_ui_path": ["step1", "step2"],
      "control_name": "Custom Name",
      "control_id": null,
      "control_type": null,
      "reason": "Why this override is needed",
      "updated": "2025-12-13",
      "enabled": true
    }
  }
}
```

### 3. Apply & Generate
```powershell
.\build_core_controls.ps1
python generate_navigation_test_cases.py --max-depth 5
```

---

## 📋 Quick Reference

### Override Properties

| Property | Type | Description | Null = Keep Original |
|----------|------|-------------|---------------------|
| `control_ui_path` | Array | Navigation steps | ✅ |
| `control_name` | String | Display name | ✅ |
| `control_id` | String | Automation ID | ✅ |
| `control_type` | Integer | UI element type | ✅ |
| `window_name` | String | Parent window | ✅ |
| `window_id` | String | Window ID | ✅ |
| `reason` | String | Why override | ❌ Required |
| `updated` | String | Date (YYYY-MM-DD) | ❌ Recommended |
| `enabled` | Boolean | Enable/disable | ❌ Default: true |

### Common Patterns

**Pattern 1: Fix Missing Steps**
```json
{
  " Sign In ": {
    "control_ui_path": [
      " Sign in",
      "Email address",
      " Next",
      "Password",  // <- Added step
      " Sign In "
    ],
    "control_name": null,
    "reason": "Add missing Password step"
  }
}
```

**Pattern 2: Rename Control**
```json
{
  "Search, meet and call": {
    "control_ui_path": null,
    "control_name": "Global Search Box",
    "reason": "More descriptive name"
  }
}
```

**Pattern 3: Override Multiple Properties**
```json
{
  " Settings": {
    "control_ui_path": ["...", " Settings"],
    "control_name": "Settings Panel",
    "control_id": "Settings.Button",
    "reason": "Complete refinement"
  }
}
```

**Pattern 4: Temporarily Disable**
```json
{
  " Settings": {
    "...": "...",
    "enabled": false
  }
}
```

### Control Type Reference

| Type Code | Type Name | Description |
|-----------|-----------|-------------|
| 50000 | button | Clickable button |
| 50004 | edit | Text input field |
| 50011 | menu_item | Menu option |
| 50025 | custom | Custom control |

---

## Configuration Structure

```json
{
  "description": "Core Controls Tuning Configuration",
  "version": "2.0",
  "overrides": {
    "Control Name": {
      "control_ui_path": ["step1", "step2"],
      "control_name": "New Name",
      "control_id": "NewID",
      "control_type": 50000,
      "window_name": "Window",
      "window_id": "WindowID",
      "reason": "Why this override is needed",
      "updated": "2025-12-13",
      "enabled": true
    }
  }
}
```

### Property Rules

| Property | Description | Value |
|----------|-------------|-------|
| `control_ui_path` | Navigation steps | Array of strings or `null` |
| `control_name` | Control display name | String or `null` |
| `control_id` | Automation ID | String or `null` |
| `control_type` | UI element type code | Integer or `null` |
| `control_type_name` | Type name (button, edit) | String or `null` |
| `window_name` | Parent window name | String or `null` |
| `window_id` | Window identifier | String or `null` |
| `reason` | Override explanation | String (required) |
| `updated` | Last update date | String (YYYY-MM-DD) |
| `enabled` | Enable/disable override | Boolean (default: true) |

**Important**: Set property to `null` to keep original value.

---

## Use Cases

### Use Case 1: Fix Missing UI Path Steps

**Problem**: Sign-in flow missing Password input step

**Solution**:
```json
{
  " Sign In ": {
    "control_ui_path": [
      " Sign in",
      "Email address",
      " Next",
      "Welcome bts_tony2@mailinator.com Password",
      " Sign In "
    ],
    "control_name": null,
    "control_id": null,
    "reason": "Add missing Password step",
    "updated": "2025-12-13",
    "enabled": true
  }
}
```

### Use Case 2: Customize Control Display Name

**Problem**: Control name too generic or unclear

**Solution**:
```json
{
  "Search, meet and call": {
    "control_ui_path": null,
    "control_name": "Global Search Box",
    "control_id": null,
    "reason": "More descriptive name for test cases",
    "updated": "2025-12-13",
    "enabled": true
  }
}
```

### Use Case 3: Override Multiple Properties

**Problem**: Control needs comprehensive refinement

**Solution**:
```json
{
  " Settings": {
    "control_ui_path": [
      " Sign in",
      "...",
      " Settings"
    ],
    "control_name": "Settings Panel (Customized)",
    "control_id": "MainWindow.Settings.Button",
    "control_type": 50000,
    "window_name": "Webex Main",
    "window_id": "MainWindow",
    "reason": "Complete control tuning for consistency",
    "updated": "2025-12-13",
    "enabled": true
  }
}
```

### Use Case 4: Temporarily Disable Override

**Problem**: Want to test without certain override

**Solution**:
```json
{
  " Settings": {
    "...": "...",
    "enabled": false
  }
}
```

---

## Workflow

### Integrated Workflow (Recommended)

1. **Edit Configuration**
   ```bash
   code config/self_calibration.json
   ```

2. **Run Build Script**
   ```powershell
   .\src\test_space\datasets\core\build_core_controls.ps1
   ```
   
   The script automatically applies overrides in Step 5.

3. **Generate Test Cases**
   ```powershell
   python src\test_space\datasets\core\generate_navigation_test_cases.py --max-depth 5
   ```

4. **Review & Iterate**
   - Check generated YAML files
   - Adjust configuration if needed
   - Re-run build script

### Standalone Usage

Apply overrides without rebuilding entire dataset:

```powershell
python apply_self_calibration.py `
    --input data/go_to_core_controls.json `
    --output data/go_to_core_controls.json `
    --config config/self_calibration.json
```

**Output Example**:
```
============================================================
🔧 Core Controls Overrides Applier
============================================================

✅ Loaded 2 control override(s)
⚠️  Skipped 1 disabled override(s)
   -  Sign In : [ui_path(5 steps)] - Add missing Password step
   - Search, meet and call: [ui_path(6 steps), control_name] - Custom name

📦 Backup created: go_to_core_controls_backup_20251213_154302.json

📖 Reading dataset: go_to_core_controls.json

🔧 Applying control overrides...
   UI Path: 5 steps → 6 steps

✅ Applied override: Search, meet and call
   Properties: control_ui_path, control_name
   Reason: Custom UI path and name for clarity

💾 Saving to: go_to_core_controls.json

============================================================
📊 Override Statistics:
============================================================
Total controls:        56
Applied overrides:     1
Disabled overrides:    1
Override ratio:        1.8%

Overridden controls:
  1. Search, meet and call
     Properties: control_ui_path, control_name
     Reason: Custom UI path and name for clarity
============================================================

✅ Complete!
```

---

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input dataset file path | Required |
| `--output` | `-o` | Output dataset file path | Required |
| `--config` | `-c` | Self-calibration configuration | `config/self_calibration.json` |
| `--no-backup` | - | Don't backup original file | False (backup enabled) |

### Examples

```powershell
# Basic usage
python apply_self_calibration.py -i data.json -o data.json

# Custom config file
python apply_self_calibration.py -i data.json -o data.json -c my_calibration.json

# No backup
python apply_self_calibration.py -i data.json -o data.json --no-backup

# Different input/output
python apply_self_calibration.py -i original.json -o modified.json
```

---

## Best Practices

### 1. Start Small

Begin with single-property overrides:

```json
{
  " Sign In ": {
    "control_ui_path": ["..."],
    "control_name": null,
    "control_id": null,
    "reason": "Fix UI path only"
  }
}
```

Validate, then add more properties if needed.

### 2. Use Descriptive Reasons

Always explain why an override is needed:

```json
{
  "reason": "Add missing Password step between Next and Sign In buttons"
}
```

Not just:
```json
{
  "reason": "Fix"
}
```

### 3. Document Update Dates

Track when overrides were added/modified:

```json
{
  "updated": "2025-12-13"
}
```

### 4. Use Disabled Overrides for Testing

Don't delete overrides - disable them temporarily:

```json
{
  " Settings": {
    "...": "...",
    "enabled": false,
    "reason": "Temporarily disabled for A/B testing"
  }
}
```

### 5. Version Control

Commit configuration changes:

```bash
git add config/self_calibration.json
git commit -m "Add override for Settings control UI path"
```

### 6. Group Related Overrides

Organize overrides by feature or issue:

```json
{
  "overrides": {
    // Sign-in flow fixes
    " Sign In ": { ... },
    "Email address": { ... },
    
    // Meeting controls
    " Start a Webex meeting": { ... },
    " Schedule a meeting": { ... }
  }
}
```

---

## Troubleshooting

### Override Not Applied

**Possible Causes**:
1. Control name mismatch (check spaces)
2. Override disabled (`enabled: false`)
3. Property set to `null`
4. JSON syntax error

**Solutions**:
```powershell
# Check control name in dataset
$json = Get-Content go_to_core_controls.json | ConvertFrom-Json
$json | Where-Object { $_.name -like "*Sign*" } | Select-Object name

# Validate JSON syntax
python -m json.tool config/self_calibration.json

# Check enabled status
Get-Content config/self_calibration.json | Select-String "enabled"
```

### Wrong Property Overridden

**Problem**: Accidentally overrode wrong property

**Solution**: Set it back to `null` to restore original:

```json
{
  " Sign In ": {
    "control_name": null,  // Restore original name
    "control_ui_path": ["..."]  // Keep UI path override
  }
}
```

### Backup Files Accumulating

**Problem**: Too many backup files

**Solution**:
```powershell
# Clean old backups (keep last 3)
Get-ChildItem src\test_space\datasets\core\*_backup_*.json | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -Skip 3 | 
    Remove-Item

# Or disable backup
python apply_self_calibration.py -i data.json -o data.json --no-backup
```

---

## Comparison with Old Approach

| Feature | Old (ui_path_fixer.py) | New (self_calibration.json) |
|---------|------------------------|-----------------------------------|
| **Scope** | ❌ UI paths only | ✅ All control properties |
| **Flexibility** | ❌ Hardcoded Password fix | ✅ Any property, any control |
| **Extensibility** | ❌ Requires code changes | ✅ Edit JSON only |
| **Dependencies** | ❌ Requires rs_sdk module | ✅ Zero dependencies |
| **Maintainability** | ❌ Complex Python code | ✅ Simple JSON config |
| **Traceability** | ❌ No change tracking | ✅ Reason + date per override |
| **Team Collaboration** | ❌ Requires Python knowledge | ✅ Anyone can edit JSON |
| **Granular Control** | ❌ All or nothing | ✅ Enable/disable individual overrides |

**Recommendation**: Use `config/self_calibration.json` for all future control calibration needs.

---

## Advanced Examples

### Example 1: Fix All Depth-5 Controls

If multiple controls at depth 5 need Password step:

```json
{
  "overrides": {
    " Settings": {
      "control_ui_path": [" Sign in", "Email address", " Next", "Welcome bts_tony2@mailinator.com Password", " Sign In ", " Settings"],
      "control_name": null,
      "reason": "Add Password step to parent path"
    },
    "Profile and preferences": {
      "control_ui_path": [" Sign in", "Email address", " Next", "Welcome bts_tony2@mailinator.com Password", " Sign In ", "Profile and preferences"],
      "control_name": null,
      "reason": "Add Password step to parent path"
    },
    " Start a Webex meeting": {
      "control_ui_path": [" Sign in", "Email address", " Next", "Welcome bts_tony2@mailinator.com Password", " Sign In ", " Start a Webex meeting"],
      "control_name": null,
      "reason": "Add Password step to parent path"
    }
  }
}
```

### Example 2: Standardize Window Names

```json
{
  "overrides": {
    " Settings": {
      "control_ui_path": null,
      "control_name": null,
      "window_name": "Webex Main Window",
      "window_id": "MainWindow",
      "reason": "Standardize window naming convention"
    },
    "Search, meet and call": {
      "control_ui_path": null,
      "control_name": null,
      "window_name": "Webex Main Window",
      "window_id": "MainWindow",
      "reason": "Standardize window naming convention"
    }
  }
}
```

### Example 3: Control Type Corrections

```json
{
  "overrides": {
    "Custom Button": {
      "control_ui_path": null,
      "control_name": null,
      "control_type": 50000,
      "control_type_name": "button",
      "reason": "Correct misidentified control type from custom to button"
    }
  }
}
```

---

## Dataset Format Compatibility

### Dictionary Format Support

The self-calibration system fully supports the **dictionary format** used by all dataset files:

**Dataset Structure**:
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

### Automatic Format Detection

The `apply_self_calibration.py` script automatically detects and handles both dictionary and legacy array formats:

```python
# Automatic conversion on load
if isinstance(data, dict):
    # Dictionary format → convert to list for processing
    controls_list = [
        {**control_data, "name": name}
        for name, control_data in data.items()
    ]
else:
    # Legacy array format → use directly
    controls_list = data

# Apply overrides to list...

# Convert back to dictionary on save
output_data = {
    control["name"]: {k: v for k, v in control.items() if k != "name"}
    for control in controls_list
}
```

### Migration Benefits

- ✅ **Backward Compatible**: Works with both old and new formats
- ✅ **Performance**: Dictionary format provides O(1) lookups
- ✅ **Automatic**: No manual intervention needed
- ✅ **Consistent**: Output format matches input format

### Usage Example

```bash
# Works with dictionary format datasets
python apply_self_calibration.py \
    --input data/go_to_core_controls.json \
    --output data/go_to_core_controls.json \
    --config config/self_calibration.json
```

**Result**: Dataset maintains dictionary format with overrides applied.

---

## Files & Scripts

| File | Purpose |
|------|---------|
| `config/self_calibration.json` | Main configuration file |
| `core_controls_overrides.example.json` | Complete example with all features |
| `apply_self_calibration.py` | Python tool to apply calibrations (supports both formats) |
| `build_core_controls.ps1` | PowerShell build script (includes Step 5) |
| `generate_navigation_test_cases.py` | Generate YAML test cases from dataset |

---

## Summary

**Core Controls Overrides** provides a powerful, flexible, and maintainable way to tune control properties for test case generation:

1. ✅ **Control-Level** - Override any property in metadata.windows
2. ✅ **Configuration-Based** - All rules in JSON, no code changes
3. ✅ **Flexible** - Single or multiple properties per control
4. ✅ **Extensible** - Add unlimited overrides easily
5. ✅ **Traceable** - Reason and date for each override
6. ✅ **Team-Friendly** - Anyone can edit configuration
7. ✅ **Granular** - Enable/disable individual overrides
8. ✅ **Format Agnostic** - Supports both dictionary and array formats

**Next time you need to calibrate a control**, just edit `config/self_calibration.json`! 🎉

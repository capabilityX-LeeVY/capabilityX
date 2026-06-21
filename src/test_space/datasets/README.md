# Control Datasets Generator

Generate Webex control datasets from database.

## Quick Start

```bash
# Merge custom controls into control_datasets.json (JSON only, no DB)
uv run python src/test_space/datasets/datasets_generator.py --mode incremental

# Sync metadata with database (DB sync only, no custom merge)
# ✨ NEW: Automatically syncs version hierarchy after database sync
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/test_space/datasets/data/ControlINFO_guest.db" \
    --metadata-file "src/test_space/datasets/control_datasets.json"

# Sync to version directory ONLY (do NOT update root directory file)
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/test_space/datasets/data/ControlINFO_guest.db" \
    --metadata-file "src/test_space/datasets/46.2.0/control_datasets.json" \
    --version-dir-only
    
# sync qt6.8 dataset
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db --db-path "src/test_space/datasets/data/ControlINFOarm_meeting_chat.db" --metadata-file "src/test_space/datasets/46.5.0/control_datasets_qt6.8.json"

# Generate new metadata from database
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/test_space/datasets/data/ControlINFO.db" \
    --output "src/test_space/datasets/control_metadata.json"

# Add images to existing metadata
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "src/test_space/datasets/data/ControlINFO.db" \
    --metadata-file "src/test_space/datasets/control_metadata.json"

# Add UI path information to control datasets
uv run python src/test_space/datasets/datasets_generator.py --add-ui-path \
    --ui-path-input "src/test_space/datasets/control_datasets.json" \
    --ui-path-output "src/test_space/datasets/core/data/control_datasets_with_ui_path.json"

# Specify project and platform: control_datasets_webex_app_windows.json
uv run python src/test_space/datasets/datasets_generator.py --project 'webex_app' --platform 'windows'

# Force regenerate from scratch
uv run python src/test_space/datasets/datasets_generator.py --force-reset
```

## Files

| File | Description |
|------|-------------|
| `control_datasets.json` | Final output dataset (default) |
| `control_metadata.json` | Source: Generated from main database |
| `control_specific_metadata.json` | Source: Generated from schedule database |
| `custom_control_metadata.json` | Source: Manually maintained custom data |

## Parameters

| Parameter | Description |
|-----------|-------------|
| `--project 'webex_app'` | Specify project name |
| `--platform 'windows'` | Specify platform (windows/mac/web) |
| `--skip-main-db` | Skip main DB, but still generate control_specific_metadata.json |
| `--skip-custom-metadata` | Don't merge custom_control_metadata.json |
| `--no-auto-clean` | Disable automatic cleaning of dynamic controls after generation (by default, auto-cleaning is enabled) |
| `--force-reset` | Regenerate completely (delete existing data) |
| `--generate-metadata` | Generate new metadata from database (includes images) |
| `--output` | Output file path for generated metadata (default: control_metadata.json) |
| `--use-array-format` | Use array format instead of key-value (default: key-value) |
| `--add-images` | Add images to existing metadata from database |
| `--add-images-output` | Output file path when adding images (default: update in place) |
| `--add-ui-path` | Add UI path information to control_datasets.json |
| `--ui-path-input` | Input file for UI path generation (default: control_datasets.json) |
| `--ui-path-output` | Output file for UI path generation (default: control_datasets_with_ui_path.json) |
| `--ui-path-db` | Database path for UI path generation (default: test_space/datasets/data/ControlINFO.db) |
| `--sync-from-db` | Sync metadata JSON file with latest data from database |
| `--db-path` | Database file path (e.g., `"src/datasets/ControlINFO.db"` or full path) |
| `--metadata-file` | Metadata JSON file path (e.g., `"src/datasets/control_metadata.json"`) |
| `--sync-output` | Output file path for synced metadata (default: update in place) |
| `--version-dir-only` | Save synced files ONLY to version directory (do NOT update root directory file) |
| `--dry-run` | Preview changes without modifying files |

## Common Scenarios

### Merge Custom Controls (Incremental Mode)

```bash
# Only merge JSON files: control_datasets.json + custom_control_metadata.json
# Does NOT sync with database - use --sync-from-db for database sync
uv run python src/test_space/datasets/datasets_generator.py --mode incremental
```

### Generate for Specific Project

```bash
# Output: control_datasets_webex_app_windows.json
uv run python src/test_space/datasets/datasets_generator.py --project 'webex_app' --platform 'windows'
```

### Generate Specific Metadata Only

```bash
# Skip main DB, but generate control_specific_metadata.json from schedule DB
uv run python src/test_space/datasets/datasets_generator.py --skip-main-db
```

### Complete Regeneration

```bash
# Delete existing and regenerate from scratch
uv run python src/test_space/datasets/datasets_generator.py --force-reset
```

### Generate New Metadata from Database

```bash
# Generate control_metadata.json (key-value format by default)
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/datasets/data/ControlINFO.db" \
    --output "src/datasets/control_metadata.json"

# Generate from custom database
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/test_space/datasets/data/ControlINFO_guest.db" \
    --output "src/test_space/datasets/control_metadata_guest.json"

# Generate in array format (instead of key-value)
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/datasets/ControlINFO.db" \
    --output "src/datasets/control_metadata.json" \
    --use-array-format

# Use default paths (DATASETS_PATH and CONTROL_METADATA_PATH from config)
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata
```

**Note**: 
- Generates **key-value format** by default: `{"Sign In": {"metadata": {...}}}`
- Use `--use-array-format` for array format: `[{"name": "Sign In", "metadata": {...}}]`
- Automatically includes image data from `ControlActionHistory` table when available
- **Auto-cleans dynamic controls**: After generation, automatically cleans all dynamic patterns including business-specific patterns (e.g., meeting links, participant names, menu indices, timestamps, tree states)

### Add Images to Old Metadata

```bash
# Add images from database to existing metadata (creates backup)
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/control_metadata.json"

# Using absolute path
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "C:/workspace/WebexRegressSheild/src/datasets/ControlINFO.db" \
    --metadata-file "C:/workspace/WebexRegressSheild/src/datasets/control_metadata.json"

# Save to a new file instead
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/old_metadata.json" \
    --add-images-output "src/datasets/metadata_with_images.json"
```

### Add UI Path Information

Add hierarchical UI path information to control datasets. This enriches control metadata with navigation path details from the database.

```bash
python src/test_space/datasets/datasets_generator.py --add-ui-path
```

```bash
# Add UI path to control datasets
uv run python src/test_space/datasets/datasets_generator.py --add-ui-path \
    --ui-path-input "src/test_space/datasets/control_datasets.json" \
    --ui-path-output "src/test_space/datasets/core/data/control_datasets_with_ui_path.json"

# Use default paths (control_datasets.json → control_datasets_with_ui_path.json)
uv run python src/test_space/datasets/datasets_generator.py --add-ui-path

# Specify custom database path
uv run python src/test_space/datasets/datasets_generator.py --add-ui-path \
    --ui-path-db "src/test_space/datasets/data/ControlINFO.db"

# With specific platform
uv run python src/test_space/datasets/datasets_generator.py --add-ui-path \
    --platform windows
```

**What it adds:**
- `control_ui_path`: Full navigation path array (e.g., `[" Sign in", "Email address", " Next", " Sign In "]`)
- `all_hierarchical_levels`: All possible hierarchical levels from database
- `shortest_hierarchical_level`: The shortest/optimal hierarchical level for navigation

**Output format:**
```json
{
    " Join a meeting": {
        "metadata": {
            "windows": {
                "control_name": " Join a meeting",
                "control_id": "MainWindow...joinMeetingButton",
                "control_ui_path": [" Sign in", "Email address", " Next", " Sign In ", " Join a meeting"],
                "all_hierarchical_levels": ["2.1.1.2.1"],
                "shortest_hierarchical_level": "2.1.1.2.1"
            }
        }
    }
}
```

**Use cases:**
- Generate navigation test cases based on UI paths
- Understand control hierarchy and relationships
- Create step-by-step test workflows
- Validate navigation sequences

### Sync Metadata with Database

**Note:** `--sync-from-db` is a separate command that ONLY syncs database to metadata. 
It does NOT merge custom controls - use `--mode incremental` for that.

**✨ NEW Feature:** Automatic Version Hierarchy Sync - After syncing metadata from the database, the system automatically compares the app version from the database with the JSON file and creates version-specific directories when versions differ.

**NEW Option:** `--version-dir-only` - Save synced files ONLY to version directory without updating the root directory file.

```bash
# Sync metadata with latest database (4-level matching)
# Saves to BOTH version directory and root
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/control_metadata.json"

# Sync to version directory ONLY (new option)
# Does NOT update root directory file
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/46.3/control_metadata.json" \
    --version-dir-only

# Preview changes without modifying files
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/control_metadata.json" \
    --dry-run

# Sync with GPT Vision image matching (requires images in metadata)
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/control_metadata.json" \
    --use-gpt-vision
```

**What happens during --sync-from-db:**
1. ✅ Syncs metadata from database
2. ✅ Auto-cleans dynamic content from keys
3. ✅ **NEW**: Automatically syncs version hierarchy:
   - Reads app version from database
   - Compares with control_datasets.json app_version
   - If versions match: No action needed ✓
   - If versions differ (e.g., 46.2 → 46.3):
     - Creates version directory (e.g., `46.3/`)
     - Saves control_datasets.json with new version to that directory
     - **NEW:** If `--version-dir-only` is specified: Stops here (do NOT update root)
     - **Default:** Also backs up and updates root file (e.g., `control_datasets_46.2.json`)

**Example output structure when versions change (default mode):**
```
test_space/datasets/
├── 46.3/                              # New version directory
│   └── control_datasets.json          # Updated with version 46.3.x.xxxxx
├── control_datasets_46.2.json         # Backup of previous version
├── control_datasets.json              # Main file (updated)
├── control_metadata.json
└── data/
    └── ControlINFO.db
```

**Example output structure with `--version-dir-only` (NEW):**
```
test_space/datasets/
├── 46.3/                              # New version directory
│   └── control_datasets.json          # Updated with version 46.3.x.xxxxx
├── control_datasets.json              # Remains unchanged (NOT updated)
├── control_metadata.json
└── data/
    └── ControlINFO.db
```

### Sync to Version Directory Only (NEW)

If you don't want to maintain a root directory `control_datasets.json` file and prefer to keep files only in version-specific directories:

```bash
# Sync metadata to version directory ONLY
# Root directory file will NOT be created or updated
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/control_metadata.json" \
    --version-dir-only
```

**Behavior:**
- ✅ Creates version directory (e.g., `46.3/`)
- ✅ Saves control_datasets.json inside version directory
- ❌ Does NOT update root directory file
- ❌ Does NOT create backups in root

**File structure:**
```
test_space/datasets/
├── 46.2/                          # Previous version
│   └── control_datasets.json
├── 46.3/                          # Latest version
│   └── control_datasets.json      # Primary location
├── control_datasets.json          # Unchanged (or can be removed)
└── data/
    └── ControlINFO.db
```

**When to use:**
- You want version-based file organization
- You prefer not to maintain a root directory master file
- You want each version to be self-contained
- You're managing multiple app versions independently

### Complete Workflow: Old Metadata → Add Images → Sync

```bash
# Step 1: Add images to old metadata (from old version database)
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "src/datasets/old_version/ControlINFO.db" \
    --metadata-file "src/datasets/old_metadata.json"

# Step 2: Sync with new database using image matching (includes version hierarchy sync)
uv run python src/test_space/datasets/datasets_generator.py --sync-from-db \
    --db-path "src/datasets/new_version/ControlINFO.db" \
    --metadata-file "src/datasets/old_metadata.json" \
    --use-gpt-vision
```

### Auto-Clean Dynamic Controls

**Dynamic control cleaning is now automatic!** 🎉

All commands (`--sync-from-db`, `--generate-metadata`, `--mode incremental`) automatically clean dynamic patterns:

**What it cleans:**
- **Business patterns** (32 patterns):
  - `https://converged-bts.webex.com/meet/pr1234567890, Copy` → `Meeting link, Copy`
  - `John Doe, Speaking, Video on, list item` → `Speaking, Video on, list item`
  - `Settings, Menu item, selected, 3 of 8, to activate press SPACEBAR` → `Settings, Menu item`
  - `Documents Tree item, Selected, expanded, 3 of 10, Level 2` → `Documents Tree item`
  - `Meeting Duration, 2 hours, 1 minute, 28 seconds` → `Meeting Duration`
  - `Activation Code, 1234-5678-9012, Copy activation code` → `Activation Code, Copy activation code`
  - And 26 more business-specific patterns...

- **Generic patterns** (5 patterns):
  - `Audio Tree item, Selected, collapsed, Level 1` → `Audio Tree item`
  - `Item 2 of 5` → `Item`
  - `Button, collapsed` → `Button`
  - And more generic dynamic patterns...

**No manual cleaning needed!** All keys are automatically cleaned during generation or sync.

For more details, see `ENHANCED_AUTO_CLEAN.md`

**Key Feature:** Removes all dynamic parts (numbers, states, timestamps, names) from keys while preserving the complete original value in the `name` field for reference.

**Example:** Reduces 1310 controls to ~1222 by removing 85+ duplicate variations and merging similar controls.

## Configuration

Default config: `src/test_space/test_suites/navigate.yaml`

```yaml
test_suite:
  name: navigate
  # platform: windows     # Optional: specify platform
  # project: webex_app    # Optional: specify project
```

- **No platform/project**: Generates `control_datasets.json`
- **With platform/project**: Generates `control_datasets_{project}_{platform}.json`

## FAQ

**Q: Why is `control_metadata.json` being updated?**

A: When the main database is available, it regenerates `control_metadata.json` by default. Use `--skip-main-db` to prevent this.

**Q: How to generate new metadata from database?**

A: Use the `--generate-metadata` command (generates key-value format by default):
```bash
# Key-value format (default): {"Sign In": {"metadata": {...}}}
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/datasets/ControlINFO.db" \
    --output "src/datasets/control_metadata.json"

# Array format: [{"name": "Sign In", "metadata": {...}}]
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/datasets/ControlINFO.db" \
    --output "src/datasets/control_metadata.json" \
    --use-array-format
```
This automatically includes images from the database if available.

**Q: My old metadata doesn't have images, can I still use GPT Vision matching?**

A: Yes! Two options:

1. **Add images to existing metadata** (preserves other data):
```bash
uv run python src/test_space/datasets/datasets_generator.py --add-images \
    --db-path "src/datasets/ControlINFO.db" \
    --metadata-file "src/datasets/old_metadata.json"
```

2. **Regenerate completely** (fresh start):
```bash
uv run python src/test_space/datasets/datasets_generator.py --generate-metadata \
    --db-path "src/datasets/ControlINFO.db" \
    --output "src/datasets/control_metadata.json"
```

**Q: Where is the database file located?**

A: Common locations:
- Default: `src/datasets/ControlINFO.db`
- Specific version: `src/datasets/sample/ControlINFO.db`
- Custom path: Use absolute path like `C:/path/to/ControlINFO.db`

Check your config in `config/paths.py` for `DATASETS_PATH` value.

**Q: What's the difference between `--add-images` and `--sync-from-db`?**

A: 
- `--add-images`: Adds image field to existing metadata from database (no other changes)
- `--sync-from-db`: Updates all fields (name, ID, type, image) with 4-level matching strategy

**Q: What is 4-level matching?**

A: The sync process tries these methods in order:
1. **Name match**: Exact control name match
2. **ID match**: Control ID (AutomationId) match
3. **Image match** (with `--use-gpt-vision`): GPT Vision compares control images
4. **New control**: If no match, adds as new entry

**Q: Is it safe to sync metadata?**

A: Yes! Use `--dry-run` to preview changes first. When syncing without `--sync-output`, it creates a timestamped backup automatically.

**Q: Why do I have many duplicate controls with only different numbers/states?**

A: Controls like "Meeting Duration, 2 hours, 15 minutes" vs "Meeting Duration, 3 hours, 5 minutes" are duplicates with dynamic values. **Good news: cleanup is now automatic!** 🎉

All commands (`--sync-from-db`, `--generate-metadata`, `--mode incremental`) automatically clean dynamic patterns from keys. No manual cleanup needed! The system automatically removes all dynamic information (numbers, states, timestamps, names) from keys, resulting in clean identifiers like `Meeting Duration`, `Audio Tree item`, `Whiteboards, Menu item`. The complete original value is preserved in the `name` field for reference.

**Q: What dynamic patterns are cleaned?**

A: The cleanup script removes these dynamic parts from control keys:
- **Time/Duration**: `Meeting Duration, 2 hours, 1 minute, 28 seconds` → `Meeting Duration`
- **Indices/Counts**: `Whiteboards, Menu item, 4 of 10` → `Whiteboards, Menu item`
- **States**: `Audio Tree item, Selected, collapsed, 2 of 14, Level 1` → `Audio Tree item`
- **Names**: `bts tony2, Video on, list item` → `Video on, list item`
- **Selection States**: `Off selected 1 of 3` → `Off`
- **Timestamps**: `Message, You, 9:32 AM, Has hyperlinks...` → `Message, You`
- **New Feature Badges**: Removes `, New feature available.` suffix
- **Press Instructions**: Removes `, to activate press SPACEBAR` suffix

All removed information is preserved in the `name` field within each control's data.

**Q: What's the difference between `--mode incremental` and `--sync-from-db`?**

A: These are two completely separate commands with different purposes:

| Command | Purpose | What it does | What it does NOT do |
|---------|---------|--------------|---------------------|
| `--mode incremental` | Merge custom controls into dataset | ✅ Merges JSON files only (control_datasets.json + custom_control_metadata.json)<br>✅ Preserves existing control data<br>✅ Creates backup before merge | ❌ Does NOT sync with database<br>❌ Does NOT update from DB |
| `--sync-from-db` | Sync metadata with database | ✅ Updates metadata from database<br>✅ Uses 4-level matching (name/ID/image/new)<br>✅ Creates timestamped backup | ❌ Does NOT merge custom controls<br>❌ Does NOT touch custom_control_metadata.json |

**Use cases:**
- **Incremental mode**: You have custom controls to merge into the main dataset (no DB involved)
- **Sync from DB**: You want to update metadata with latest database changes (no custom merge)

**Q: How to view help?**

```bash
uv run python src/test_space/datasets/datasets_generator.py --help
```

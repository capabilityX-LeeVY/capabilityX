import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from rs_sdk.utils.control_datasets_generator import ControlDatasetsGenerator
from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from config.paths import DATASETS_PATH, DATASETS_SPECIFIC_PATH, CONTROL_DEFAULT_DATASET_PATH, CONTROL_METADATA_PATH, CONTROL_SPECIFIC_METADATA_PATH, CUSTOM_CONTROL_METADATA_PATH, TEST_SUITE_PATH, TEST_CONTROL_DATASET_FOLDER_PATH

# Import comprehensive cleaning function for automatic key cleaning
import re

def clean_all_dynamic_patterns_from_key(text):
    """
    Remove ALL dynamic patterns from control key text.
    Combines both generic patterns and business-specific patterns from clean_dynamic_controls.py
    """
    if not text:
        return text
    
    original_text = text
    cleaned = text
    
    # Business-specific patterns (from clean_dynamic_controls.py)
    # These are applied first as they are more specific
    business_patterns = [
        # Call history item with name, date and instructions (e.g., "juntong_FN juntong_LN Canceled call 1/16/2026 Use Enter or Space keys..." → "Call history item")
        (r"^.+?\s+(Canceled|Missed|Incoming|Outgoing)\s+call\s+\d{1,2}/\d{1,2}/\d{4}\s+Use\s+.+$", r"Call history item"),
        # Call history contact avatar (e.g., "juntong_FN juntong_LN's avatar" → "Call history contact avatar")
        (r"^.+'s avatar$", r"Call history contact avatar"),
        # Audio call contact (e.g., "Audio call juntong_FN juntong_LN, Call on Webex" → "Audio call contact")
        (r"^Audio call .+, Call on Webex$", r"Audio call contact"),
        # Video call contact (e.g., "Video call juntong_FN juntong_LN, Call on Webex" → "Video call contact")
        (r"^Video call .+, Call on Webex$", r"Video call contact"),
        # Owner info (e.g., "pilan_FN pilan_LN, You, Owner, actions available" → "Owner info")
        (r"^.+, You, Owner, actions available$", r"Owner info"),
        # Contact email (e.g., "Mailto: pilan@cisco.com" → "Contact email")
        (r"^Mailto: .+$", r"Contact email"),
        # Voicemail list item with sender info and timestamp (e.g., "juntong_FN juntong_LN, received 11/17/2025, voice message, test duration: 6s" → "Voicemail list item")
        (r"^.+,\s*received\s+\d{1,2}/\d{1,2}/\d{4},\s*voice message,\s*test\s*duration:\s*\d+s$", r"Voicemail list item"),
        # Voicemail sender avatar (e.g., "juntong_FN juntong_LN, Avatar" → "Voicemail sender avatar")
        (r"^.+,\s*Avatar$", r"Voicemail sender avatar"),
        # Voicemail sender phone with dynamic number (e.g., "Work: 813289" → "Voicemail sender phone")
        (r"^(Work|Mobile|Home):\s*\d+$", r"Voicemail sender phone"),
        # Voicemail date with time (e.g., "11/17/2025" or "11/17/2025 1:49 PM" → "Voicemail date")
        (r"^\d{1,2}/\d{1,2}/\d{4}(\s+\d{1,2}:\d{2}\s*[AP]M)?$", r"Voicemail date"),
        # Voice message slider with duration (e.g., "Voice message, slide bar 0 seconds of 6 seconds" → "Voice message slider")
        (r"^Voice message,\s*slide bar\s*\d+\s*seconds of\s*\d+\s*seconds$", r"Voice message slider"),
        # Place phone call with number (e.g., "Place work phone call on: 813024" → "Place phone call")
        (r"^Place\s+(work|mobile|home)\s+phone call on:\s*\d+$", r"Place phone call"),
        # Work/Mobile/Home phone number (e.g., "Work 813024" → "Work phone number")
        (r"^(Work|Mobile|Home)\s+\d+$", r"Work phone number"),
        # Audio source with device name (e.g., "Audio source: CABLE Output (VB-Audio Virtual Cable) Audio settings" → "Audio source settings")
        (r"^Audio source:.+Audio settings$", r"Audio source settings"),
        # Dynamic meeting names in keys (e.g., "Invite and remind-bts tony2's meeting" → "Invite and remind-Meeting window")
        (r"^(.+)-[^-]+'s meeting$", r"\1-Meeting window"),
        (r"^(.+)-[^-]+ meeting$", r"\1-Meeting window"),
        # Participants panel with count in suffix (e.g., "Invite and remind-Participants (1) panel" → "Invite and remind-Participants panel")
        (r"^(.+)-Participants \(\d+\) panel$", r"\1-Participants panel"),
        # Date patterns - remove dates, keep action words
        (r"^(Today),\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*\w+\s+\d{1,2},\s*\d{4}$", r"\1"),
        (r"^\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*\w+\s+\d{1,2},\s*\d{4}\s+(choose date)$", r"\1"),
        # Date with "choose date" suffix - remove date, keep suffix
        (r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d{1,2},\s+\d{4}\s+(choose date)$", r"\1"),
        # "Today" with date - remove date, keep "Today"
        (r"^(Today),\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d{1,2},\s+\d{4}$", r"\1"),
        # Meeting Link with Copy
        (r"^https?://[^,]+, (Copy)$", r"Meeting link, \1"),
        # Meeting Link with Full URL
        (r"^Meeting link\s+https?://\S+\s+(Copy meeting link)$", r"Meeting link, \1"),
        # Personal Room Number with Copy
        (r"^(Personal Room number), [\d\s]+,\s*(Copy)$", r"\1, \2"),
        # Video Address with More Info
        (r"^(Video address), [^,]+\s*,\s*(More information for Host PIN)$", r"\1, \2"),
        # Activation Code - Copy Button
        (r"^(Activation Code), [\d-]+, (Copy activation code)$", r"\1, \2"),
        # Activation Code - Copied
        (r"^(Activation Code), [\d-]+, (copied)$", r"\1, \2"),
        # Meeting Duration
        (r"^(Meeting Duration), .*$", r"\1"),
        # Elapsed Time
        (r"^Elapsed time: .+$", "Elapsed time"),
        # Participant List Item (Speaking)
        (r"^.+, (Speaking, Video on, list item)$", r"\1"),
        # Participant List Item (Away)
        (r"^.+, (Muted, Video off, Stepped away, list item)$", r"\1"),
        # Participant List Item (Video on)
        (r"^.+, (Video on, list item)$", r"\1"),
        # Chat Message
        (r"^(Message, You), \d+:\d+ [AP]M, Has hyperlinks\..+$", r"\1"),
        # Menu Item with Selected Flag and Press
        (r"^(.+, Menu item), selected, \d+ of \d+, to activate press SPACEBAR$", r"\1"),
        # Menu Item with Index and Press
        (r"^(.+, Menu item), \d+ of \d+, to activate press SPACEBAR$", r"\1"),
        # Menu Item with Index and New Feature
        (r"^(.+, Menu item), \d+ of \d+, New feature available\.$", r"\1"),
        # Menu Item with Index Only
        (r"^(.+, Menu item), \d+ of \d+$", r"\1"),
        # Tree Item with States
        (r"^(.+ Tree item), (Selected, )?(collapsed|expanded), \d+ of \d+, Level \d+$", r"\1"),
        # Tree Item Selected Only
        (r"^(.+ Tree item), Selected, \d+ of \d+, Level \d+$", r"\1"),
        # Tree Item with Index Only
        (r"^(.+ Tree item), \d+ of \d+, Level \d+$", r"\1"),
        # Tree Item with Instructions
        (r"^(.+, tree item), Level \d+, \d+ of \d+.+$", r"\1"),
        # Emoji List Item (keep emoji, remove extras)
        (r"^(.+ emoji), list item, \d+ of \d+, .+$", r"\1"),
        # Combobox with Selection
        (r"^(.+, combobox), .+, Selected, \d+ of \d+$", r"\1"),
        # Calendar Date Item
        (r"^\d{1,2}:\d{2} [AP]M, \d+ of \d+, not selected$", "Time Slot"),
        # Number Selector (must be before "Menu Item Collapsed/Expanded" to match correctly)
        (r"^\d+ (selected|Not selected) \d+ of \d+$", "Number Option"),
        # Menu Item Collapsed/Expanded with Index
        (r"^(.+), (collapsed|expanded), \d+ of \d+$", r"\1"),
        # Menu Item with State Only
        (r"^(.+), (collapsed|expanded),$", r"\1"),
        # Emoji/Option Selector (keep the text before state)
        (r"^(.+) (selected|Disabled|Not selected) \d+ of \d+$", r"\1"),
        # Participants Group with Details
        (r"^(Participants group), \d+ participants?, (Expanded|Collapsed), \d+ of \d+ level \d+$", r"\1"),
        # Close Panel with Count
        (r"^(Close .+) \(\d+\) (panel)$", r"\1 \2"),
        # Participant Status with Details
        (r"^.+?, (Host|Co-host|Presenter|Guest|Panelist)(.+?), \d+ of \d+ level \d+, Tab for more options$", r"\1\2"),
        # Primary Navigation Menu Item
        (r"^(?:Primary navigation menu )?(.+?) menu item.*, \d+ of \d+, to activate press SPACEBAR$", r"\1 menu item"),
    ]
    
    # Try to apply business-specific patterns first
    for pattern, replacement in business_patterns:
        match = re.match(pattern, cleaned)
        if match:
            cleaned = re.sub(pattern, replacement, cleaned)
            # If pattern was applied, skip generic cleaning for this specific case
            if cleaned != original_text:
                return cleaned
    
    # Generic patterns (apply if no business pattern matched)
    # Pattern 1: Remove "X of Y" patterns
    cleaned = re.sub(r',?\s*\d+\s+of\s+\d+', '', cleaned)
    
    # Pattern 2: Remove state keywords (order matters - longer patterns first!)
    state_patterns = [
        r',?\s*not\s+selected\s*,?',
        r',?\s*Selected\s*,?',
        r',?\s*collapsed\s*,?',
        r',?\s*expanded\s*,?',
        r',?\s*checked\s*,?',
    ]
    for pattern in state_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Pattern 3: Remove "Level X" patterns
    cleaned = re.sub(r',?\s*Level\s+\d+', '', cleaned, flags=re.IGNORECASE)
    
    # Pattern 4: Remove "to activate press SPACEBAR" instructions
    cleaned = re.sub(r',?\s*to activate press SPACEBAR', '', cleaned, flags=re.IGNORECASE)
    
    # Pattern 5: Remove time patterns (HH:MM AM/PM)
    cleaned = re.sub(r',?\s*\d{1,2}:\d{2}\s*[AP]M', '', cleaned)
    
    # Clean up resulting formatting issues
    cleaned = re.sub(r'\s+,', ',', cleaned)  # Remove space before comma
    cleaned = re.sub(r',\s*,+', ',', cleaned)  # Remove multiple commas
    cleaned = re.sub(r',\s*$', '', cleaned)  # Remove trailing comma
    cleaned = re.sub(r'^\s*,', '', cleaned)  # Remove leading comma
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
    cleaned = cleaned.strip(' ,')  # Remove leading/trailing spaces and commas
    
    return cleaned

def clean_dataset_keys(input_file, output_file=None, verbose=True):
    """
    Comprehensively clean dynamic patterns from control datasets JSON keys.
    Only modifies keys, keeps all values unchanged.
    Also removes entries with empty keys.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file (if None, updates in place)
        verbose: If True, print progress information
    
    Returns:
        Tuple of (keys_changed, keys_removed)
    """
    if output_file is None:
        output_file = input_file
    
    if verbose:
        LOGGER_INFO(f"🧹 Cleaning dynamic content from keys: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_data = {}
    changes_count = 0
    removed_count = 0
    
    for key, value in data.items():
        # Skip entries with empty keys
        if not key or key.strip() == "":
            removed_count += 1
            if verbose:
                control_name = value.get("metadata", {}).get("windows", {}).get("control_name", "unknown")
                LOGGER_WARNING(f"   🗑️  Removed entry with empty key (control_name: '{control_name}')")
            continue
        
        # Clean the key comprehensively
        cleaned_key = clean_all_dynamic_patterns_from_key(key)
        
        # Skip if cleaned key becomes empty
        if not cleaned_key or cleaned_key.strip() == "":
            removed_count += 1
            if verbose:
                LOGGER_WARNING(f"   🗑️  Removed entry: key '{key}' became empty after cleaning")
            continue
        
        # Track if key changed
        if cleaned_key != key:
            changes_count += 1
            if verbose and changes_count <= 10:
                LOGGER_INFO(f"   [{changes_count}] '{key}' -> '{cleaned_key}'")
        
        # Keep the value completely unchanged
        new_data[cleaned_key] = value
    
    if verbose:
        if changes_count > 10:
            LOGGER_INFO(f"   ... and {changes_count - 10} more key changes")
        LOGGER_INFO(f"   Total keys cleaned: {changes_count}")
        if removed_count > 0:
            LOGGER_INFO(f"   Total entries removed (empty keys): {removed_count}")
    
    # Write cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    if verbose:
        LOGGER_INFO(f"   ✅ Keys cleaned successfully!")
    
    return (changes_count, removed_count)
import os
import json
import yaml
from pathlib import Path


def get_platform_from_config(config_file=None):
    """
    Get platform from YAML configuration file
    
    Args:
        config_file (str or Path): Path to YAML config file (e.g., test suite YAML)
                                   If None, searches for navigate.yaml in test_suites directory
        
    Returns:
        str: Platform name (windows, mac, or web), defaults to 'windows' if not found
    """
    # Default platform
    default_platform = "windows"
    
    # If no config file specified, try to find navigate.yaml
    if config_file is None:
        config_file = TEST_SUITE_PATH / "navigate.yaml"
    else:
        config_file = Path(config_file)
    
    # Check if config file exists
    if not config_file.exists():
        LOGGER_WARNING(f"Config file not found: {config_file}, using default platform: {default_platform}")
        return default_platform
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Try to get platform from test_suite section
        platform = config_data.get('test_suite', {}).get('platform', default_platform)
        
        # Validate platform
        valid_platforms = ['windows', 'mac', 'web']
        if platform.lower() not in valid_platforms:
            LOGGER_WARNING(f"Invalid platform '{platform}' in config file, using default: {default_platform}")
            return default_platform
        
        LOGGER_INFO(f"Platform from config file ({config_file.name}): {platform}")
        return platform.lower()
        
    except Exception as e:
        LOGGER_ERROR(f"Error reading config file {config_file}: {str(e)}, using default platform: {default_platform}")
        return default_platform

def get_project_from_config(config_file=None):
    """
    Get project from YAML configuration file
    
    Args:
        config_file (str or Path): Path to YAML config file (e.g., test suite YAML)
                                   If None, searches for navigate.yaml in test_suites directory
        
    Returns:
        str: Project name (e.g., 'webex_app', 'webex_web'), defaults to None if not found
    """
    # If no config file specified, try to find navigate.yaml
    if config_file is None:
        config_file = TEST_SUITE_PATH / "navigate.yaml"
    else:
        config_file = Path(config_file)
    
    # Check if config file exists
    if not config_file.exists():
        LOGGER_WARNING(f"Config file not found: {config_file}, no project specified")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Try to get project from test_suite section
        project = config_data.get('test_suite', {}).get('project', None)
        
        if project:
            LOGGER_INFO(f"Project from config file ({config_file.name}): {project}")
        else:
            LOGGER_INFO(f"No project specified in config file ({config_file.name})")
        
        return project
        
    except Exception as e:
        LOGGER_ERROR(f"Error reading config file {config_file}: {str(e)}, no project specified")
        return None

def check_db_availability(DATASETS_PATH):
    """
    Check if database file exists and has data
    
    Args:
        DATASETS_PATH (str): Path to database file
        
    Returns:
        bool: True if database is available and has data, False otherwise
    """
    if not os.path.exists(DATASETS_PATH):
        LOGGER_WARNING(f"Database file not found: {DATASETS_PATH}")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect(DATASETS_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ControlINFO WHERE Description IS NOT NULL AND TRIM(Description) != ''")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            LOGGER_INFO(f"Database {DATASETS_PATH} is available with {count} records")
            return True
        else:
            LOGGER_WARNING(f"Database {DATASETS_PATH} exists but has no valid data")
            return False
    except Exception as e:
        LOGGER_ERROR(f"Error checking database {DATASETS_PATH}: {str(e)}")
        return False

def load_existing_metadata(file_path):
    """
    Load existing metadata from JSON file
    Supports both formats:
    - Array format: [{name: "...", metadata: {...}}, ...]
    - Key-Value format: {name: {metadata: {...}}, ...}
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        list: Existing metadata in array format (for compatibility with merge functions)
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if data is dict (Key-Value format) or list (Array format)
                if isinstance(data, dict):
                    # Convert Key-Value format to Array format
                    array_data = []
                    for name, value in data.items():
                        entry = {"name": name}
                        entry.update(value)
                        array_data.append(entry)
                    LOGGER_INFO(f"✅ Loaded existing metadata (Key-Value format) from {file_path}: {len(array_data)} records")
                    return array_data
                elif isinstance(data, list):
                    # Already in Array format
                    LOGGER_INFO(f"✅ Loaded existing metadata (Array format) from {file_path}: {len(data)} records")
                    return data
                else:
                    LOGGER_ERROR(f"Unexpected data format in {file_path}: {type(data)}")
                    return []
        except Exception as e:
            LOGGER_ERROR(f"Error loading existing metadata from {file_path}: {str(e)}")
            return []
    else:
        LOGGER_INFO(f"No existing metadata file found at {file_path}")
        return []

def filter_metadata_by_platform(metadata, platform_filter=None):
    """
    Filter metadata by specified platform
    
    Args:
        metadata (dict): Metadata dict with platform keys (e.g., {'windows': {...}, 'mac': {...}})
        platform_filter (str): Platform to filter (windows, mac, web). If None, return all
        
    Returns:
        dict: Filtered metadata dict
    """
    if not metadata or not platform_filter:
        return metadata
    
    # Filter metadata by platform
    filtered = {}
    for platform, platform_data in metadata.items():
        if platform.lower() == platform_filter.lower():
            filtered[platform] = platform_data
    
    return filtered

def smart_merge_metadata(existing_metadata, new_metadata, source_priority):
    """
    Smart merge metadata by platform with priority rules
    
    Args:
        existing_metadata (dict): Existing metadata dict
        new_metadata (dict): New metadata dict to merge
        source_priority (int): Priority level (1=base, 2=specific, 3=custom)
        
    Returns:
        dict: Merged metadata dict
    """
    if not existing_metadata:
        return new_metadata.copy() if new_metadata else {}
    
    if not new_metadata:
        return existing_metadata.copy()
    
    merged = existing_metadata.copy()
    
    # Merge each platform separately (windows, mac, web)
    for platform, platform_data in new_metadata.items():
        if platform in merged:
            # Update existing platform data with higher priority
            merged[platform].update(platform_data)
            LOGGER_DEBUG(f"Updated {platform} metadata (priority: {source_priority})")
        else:
            # Add new platform data
            merged[platform] = platform_data.copy()
            LOGGER_DEBUG(f"Added new {platform} metadata (priority: {source_priority})")
    
    return merged

def ensure_name_uniqueness(dataset):
    """
    Ensure name uniqueness and report duplicates
    
    Args:
        dataset (list): Dataset to check
        
    Returns:
        list: Dataset with unique names (keeps first occurrence)
    """
    seen_names = set()
    unique_dataset = []
    duplicates = []
    
    for entry in dataset:
        name = entry.get("name", "")
        if name:
            if name in seen_names:
                duplicates.append(name)
                LOGGER_WARNING(f"Duplicate name found: '{name}' - skipping duplicate")
            else:
                seen_names.add(name)
                unique_dataset.append(entry)
        else:
            LOGGER_WARNING("Entry without name found - skipping")
    
    if duplicates:
        LOGGER_WARNING(f"Found {len(duplicates)} duplicate names: {duplicates}")
    
    LOGGER_INFO(f"Unique dataset contains {len(unique_dataset)} records")
    return unique_dataset

def incremental_merge_with_priority(existing_data, base_data, specific_data, custom_data):
    """
    Incremental merge with priority rules while preserving existing data
    Priority: existing < base < specific < custom
    
    Args:
        existing_data (list): Existing data from control_datasets.json
        base_data (list): Base metadata from control_metadata.json
        specific_data (list): Specific metadata from control_specific_metadata.json
        custom_data (list): Custom metadata from custom_control_metadata.json
        
    Returns:
        list: Merged metadata with incremental updates
    """
    # Create a dictionary for easy lookup by name
    merged_dict = {}
    
    # Step 1: Load existing data as baseline
    for entry in existing_data:
        name = entry.get("name", "")
        if name:
            merged_dict[name] = entry.copy()
    
    LOGGER_INFO(f"Step 1: Loaded {len(existing_data)} existing records as baseline")
    
    # Step 2: Update/add from base data (priority: 1)
    added_base = 0
    updated_base = 0
    for entry in base_data:
        name = entry.get("name", "")
        if name:
            if name in merged_dict:
                # Smart merge metadata with priority
                existing_metadata = merged_dict[name].get("metadata", {})
                new_metadata = entry.get("metadata", {})
                merged_metadata = smart_merge_metadata(existing_metadata, new_metadata, 1)
                merged_dict[name]["metadata"] = merged_metadata
                updated_base += 1
            else:
                # Add new entry
                merged_dict[name] = entry.copy()
                added_base += 1
    
    LOGGER_INFO(f"Step 2: Updated {updated_base} and added {added_base} base records")
    
    # Step 3: Update/add from specific data (priority: 2)
    added_specific = 0
    updated_specific = 0
    for entry in specific_data:
        name = entry.get("name", "")
        if name:
            if name in merged_dict:
                # Smart merge metadata with higher priority
                existing_metadata = merged_dict[name].get("metadata", {})
                new_metadata = entry.get("metadata", {})
                merged_metadata = smart_merge_metadata(existing_metadata, new_metadata, 2)
                merged_dict[name]["metadata"] = merged_metadata
                updated_specific += 1
            else:
                # Add new entry
                merged_dict[name] = entry.copy()
                added_specific += 1
    
    LOGGER_INFO(f"Step 3: Updated {updated_specific} and added {added_specific} specific records")
    
    # Step 4: Update/add from custom data (priority: 3 - highest)
    added_custom = 0
    updated_custom = 0
    for entry in custom_data:
        name = entry.get("name", "")
        if name:
            if name in merged_dict:
                # Smart merge metadata with highest priority
                existing_metadata = merged_dict[name].get("metadata", {})
                new_metadata = entry.get("metadata", {})
                merged_metadata = smart_merge_metadata(existing_metadata, new_metadata, 3)
                merged_dict[name]["metadata"] = merged_metadata
                updated_custom += 1
            else:
                # Add new entry
                merged_dict[name] = entry.copy()
                added_custom += 1
                added_custom += 1
    
    LOGGER_INFO(f"Step 4: Updated {updated_custom} and added {added_custom} custom records")
    
    # Convert back to list and ensure uniqueness
    merged_data = list(merged_dict.values())
    unique_data = ensure_name_uniqueness(merged_data)
    
    LOGGER_INFO(f"Final incremental dataset contains {len(unique_data)} unique records")
    
    return unique_data

def incremental_save_dataset(merged_data, output_path):
    """
    Incrementally save the control_datasets.json file (preserve existing data)
    Now saves in Key-Value format: {name: {metadata: ...}}
    
    Args:
        merged_data (list): Merged metadata (array format)
        output_path (str or Path): Path to save the final dataset
    """
    # Convert to string if it's a Path object
    output_path = str(output_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create backup of existing file
    if os.path.exists(output_path):
        backup_path = output_path + '.backup'
        import shutil
        shutil.copy2(output_path, backup_path)
        LOGGER_INFO(f"Created backup: {backup_path}")
    
    # Convert list to Key-Value format
    keyed_data = {}
    for entry in merged_data:
        name = entry.get("name", "")
        if name:
            # Remove 'name' key and use remaining data as value
            entry_copy = entry.copy()
            entry_copy.pop("name", None)
            keyed_data[name] = entry_copy
    
    # Save in Key-Value format
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(keyed_data, f, ensure_ascii=False, indent=4)
    
    LOGGER_INFO(f"✅ Incrementally saved dataset (Key-Value format) to {output_path}: {len(keyed_data)} records")

def reset_and_save_final_dataset(merged_data, output_path):
    """
    Reset and save the final control_datasets.json file (backward compatibility)
    Now saves in Key-Value format: {name: {metadata: ...}}
    
    Args:
        merged_data (list): Merged metadata (array format)
        output_path (str or Path): Path to save the final dataset
    """
    # Convert to string if it's a Path object
    output_path = str(output_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Reset (delete existing file if it exists)
    if os.path.exists(output_path):
        os.remove(output_path)
        LOGGER_INFO(f"Reset: Removed existing file {output_path}")
    
    # Convert list to Key-Value format
    keyed_data = {}
    for entry in merged_data:
        name = entry.get("name", "")
        if name:
            # Remove 'name' key and use remaining data as value
            entry_copy = entry.copy()
            entry_copy.pop("name", None)
            keyed_data[name] = entry_copy
    
    # Save in Key-Value format
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(keyed_data, f, ensure_ascii=False, indent=4)
    
    LOGGER_INFO(f"✅ Saved final dataset (Key-Value format) to {output_path}: {len(keyed_data)} records")

def filter_and_save_metadata_file(file_path, platform_filter=None):
    """
    Filter metadata file by platform and save it back
    If platform_filter is specified, converts 'windows' platform data to the target platform
    
    Args:
        file_path (str or Path): Path to the metadata file
        platform_filter (str): Platform to convert to (windows, mac, web). If None, no conversion
    """
    if not platform_filter or platform_filter.lower() == 'windows':
        # No conversion needed for windows or no filter
        return
    
    file_path = str(file_path)
    
    if not os.path.exists(file_path):
        LOGGER_WARNING(f"File not found for filtering: {file_path}")
        return
    
    try:
        # Load existing data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert platform for each entry
        converted_data = []
        for entry in data:
            name = entry.get("name", "")
            if name:
                metadata = entry.get("metadata", {})
                
                # If the entry has windows platform data, convert it to target platform
                if 'windows' in metadata:
                    converted_metadata = {
                        platform_filter.lower(): metadata['windows']
                    }
                    entry_copy = entry.copy()
                    entry_copy["metadata"] = converted_metadata
                    converted_data.append(entry_copy)
                    LOGGER_DEBUG(f"Converted '{name}' from windows to {platform_filter}")
                # If already has target platform, keep it
                elif platform_filter.lower() in metadata:
                    converted_data.append(entry)
        
        # Save converted data back
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=4)
        
        LOGGER_INFO(f"Converted {file_path} from 'windows' to '{platform_filter}' platform: {len(converted_data)} records")
        
    except Exception as e:
        LOGGER_ERROR(f"Error converting file {file_path}: {str(e)}")

def _update_control_metadata(entry, platform, control_name, automation_id, 
                            control_type, control_type_name, db_image_base64,
                            existing_platform_data, stats, window_name=None, window_id=None):
    """
    Update metadata entry with new data from database.
    
    Args:
        entry: Metadata entry to update
        platform: Platform name (windows, mac, web)
        control_name: New control name from DB
        automation_id: New automation ID from DB
        control_type: New control type from DB
        control_type_name: New control type name from DB
        db_image_base64: New image from DB (Base64)
        existing_platform_data: Existing platform metadata
        stats: Statistics dict to update
        window_name: Window name from DB (optional)
        window_id: Window automation ID from DB (optional)
        
    Returns:
        bool: True if any field was updated, False otherwise
    """
    def normalize_window_id(wid):
        """Remove SparkApp. prefix from window_id for comparison (Qt6.8 compatibility)."""
        if not wid:
            return wid
        return wid.replace('SparkApp.', '', 1)
    
    # Use database values directly without transformation
    # Prepare new values (use existing if DB value is None/empty)
    new_control_id = automation_id if automation_id else existing_platform_data.get("control_id", "")
    new_control_type = control_type if control_type else existing_platform_data.get("control_type", "")
    new_control_type_name = control_type_name if control_type_name else existing_platform_data.get("control_type_name", "")
    new_window_name = window_name if window_name else None
    new_window_id = window_id if window_id else None
    
    # Check if any field changed
    changed = False
    change_details = {"name": control_name, "changes": {}}
    
    old_control_id = existing_platform_data.get("control_id") or ""
    old_window_id = existing_platform_data.get("window_id") or ""
    
    # Check if control_id needs to be updated
    # Logic: If control_name is same, window_id (normalized) is same, but control_id is different -> UPDATE
    if old_control_id != new_control_id:
        # Normalize window_ids to check if they're from the same window
        normalized_old_window_id = normalize_window_id(old_window_id)
        normalized_new_window_id = normalize_window_id(new_window_id) if new_window_id else ""
        
        # If window_id (normalized) is the same, update control_id to keep it in sync with database
        if normalized_old_window_id == normalized_new_window_id:
            changed = True
            change_details["changes"]["control_id"] = {
                "old": old_control_id,
                "new": new_control_id
            }
        else:
            # Different window, don't update (this control belongs to a different window)
            pass
    
    if existing_platform_data.get("control_type") != new_control_type:
        changed = True
        change_details["changes"]["control_type"] = {
            "old": existing_platform_data.get("control_type"),
            "new": new_control_type
        }
    
    if existing_platform_data.get("control_type_name") != new_control_type_name:
        changed = True
        change_details["changes"]["control_type_name"] = {
            "old": existing_platform_data.get("control_type_name"),
            "new": new_control_type_name
        }
    
    # Check image changes
    if db_image_base64:
        existing_image = existing_platform_data.get("image")
        if existing_image != db_image_base64:
            changed = True
            change_details["changes"]["image"] = {
                "old": "exists" if existing_image else "none",
                "new": "updated"
            }
    
    # Check window_name changes
    old_window_name = existing_platform_data.get("window_name")
    if old_window_name != new_window_name:
        changed = True
        change_details["changes"]["window_name"] = {
            "old": old_window_name,
            "new": new_window_name
        }
    
    # Check window_id changes
    # Qt6.8 compatibility: normalize by removing SparkApp. prefix before comparison
    old_window_id = existing_platform_data.get("window_id")
    normalized_old_window_id = normalize_window_id(old_window_id)
    normalized_new_window_id = normalize_window_id(new_window_id)
    
    if normalized_old_window_id != normalized_new_window_id:
        changed = True
        change_details["changes"]["window_id"] = {
            "old": old_window_id,
            "new": new_window_id
        }
    
    if changed:
        stats["updated"] += 1
        stats["changes"].append(change_details)
        
        # Update metadata
        if platform not in entry["metadata"]:
            entry["metadata"][platform] = {}
        
        entry["metadata"][platform].update({
            "control_name": control_name,
            "control_id": new_control_id,
            "control_type": new_control_type,
            "control_type_name": new_control_type_name,
            "window_name": new_window_name,
            "window_id": new_window_id
        })
        
        # Update image if available
        if db_image_base64:
            entry["metadata"][platform]["image"] = db_image_base64
        
        return True
    else:
        stats["no_change"] += 1
        return False

def compare_images_with_gpt(image1_base64, image2_base64, control_name):
    """
    Use GPT Vision API to compare two control images and determine if they are the same control.
    
    Args:
        image1_base64 (str): Base64 encoded image from database
        image2_base64 (str): Base64 encoded image from metadata
        control_name (str): Name of the control for context
        
    Returns:
        dict: {
            "is_same": bool,  # True if images represent the same control
            "confidence": float,  # Confidence score (0-1)
            "reason": str  # Explanation from GPT
        }
    """
    try:
        from models.openai_client import OpenAIClient
        import base64
        import tempfile
        import os
        
        # Create temporary files for both images
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp1, \
             tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp2:
            
            # Decode and write images
            tmp1.write(base64.b64decode(image1_base64))
            tmp2.write(base64.b64decode(image2_base64))
            tmp1_path = tmp1.name
            tmp2_path = tmp2.name
        
        try:
            # Use OpenAI client to compare images
            client = OpenAIClient()
            
            # Prepare comparison prompt
            message = f"""Compare these two UI control images and determine if they represent the same control.
            
Control name: "{control_name}"

Analyze:
1. Visual appearance (button style, icon, color, size)
2. Text labels (if any)
3. Position and layout context
4. Focus ring or selection state

Respond in JSON format:
{{
    "is_same": true/false,
    "confidence": 0.0-1.0,
    "reason": "Brief explanation of your decision"
}}

Consider that the images might have slight differences due to:
- Different timestamps
- Hover/focus states
- Minor UI theme changes

But the core control should be identifiable as the same element."""

            # Call image comparison endpoint
            result = client.ai_analyze_image_comparison(tmp1_path, tmp2_path, message)
            
            if result:
                # Parse JSON response
                import json
                try:
                    parsed = json.loads(result)
                    return parsed
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract decision from text
                    is_same = "true" in result.lower() or "same" in result.lower()
                    return {
                        "is_same": is_same,
                        "confidence": 0.7 if is_same else 0.5,
                        "reason": result
                    }
            else:
                LOGGER_WARNING(f"No result from GPT image comparison for '{control_name}'")
                return {
                    "is_same": False,
                    "confidence": 0.0,
                    "reason": "API call failed"
                }
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(tmp1_path)
                os.unlink(tmp2_path)
            except:
                pass
                
    except Exception as e:
        LOGGER_ERROR(f"Error comparing images with GPT: {e}")
        return {
            "is_same": False,
            "confidence": 0.0,
            "reason": f"Error: {str(e)}"
        }

def sync_metadata_from_db(db_path, metadata_file_path, output_file_path=None, platform="windows", dry_run=False, use_gpt_vision=False):
    """
    Sync metadata JSON file with latest data from database.
    Supports both Array and Key-Value formats.
    ONLY matches by control name - keeps the original key unchanged.
    Updates other fields (control_id, control_type, etc.) from the database.
    
    Args:
        db_path (str or Path): Path to database file (e.g., ControlINFO.db)
        metadata_file_path (str or Path): Path to metadata JSON file to update
        output_file_path (str or Path): Path to save updated JSON. If None, updates in place
        platform (str): Platform name for metadata structure (windows, mac, web)
        dry_run (bool): If True, only report changes without saving
        use_gpt_vision (bool): Deprecated - no longer used (only name matching is performed)
    
    Returns:
        dict: Statistics of sync operation
        
    Example:
        DB Table (ControlINFO):
        Description (control_name) | AutomationId (control_id) | ControlType | ...
        "Join a meeting"           | "MainWindow...Button"      | 50000       | ...
        
        Key-Value Format:
        {"Join a meeting": {"metadata": {"windows": {"control_id": "old_id", ...}}}}
        → Updates to:
        {"Join a meeting": {"metadata": {"windows": {"control_id": "MainWindow...Button", ...}}}}
    """
    import sqlite3
    
    db_path = Path(db_path)
    metadata_file_path = Path(metadata_file_path)
    
    # Check files exist
    if not db_path.exists():
        LOGGER_ERROR(f"Database file not found: {db_path}")
        return {"error": "Database not found"}
    
    if not metadata_file_path.exists():
        LOGGER_ERROR(f"Metadata file not found: {metadata_file_path}")
        return {"error": "Metadata file not found"}
    
    try:
        # Load existing metadata (auto-detect format)
        LOGGER_INFO(f"Loading metadata from {metadata_file_path}")
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Detect format and create name-indexed dict
        is_keyed_format = isinstance(raw_data, dict)
        metadata_dict = {}
        
        if is_keyed_format:
            # Key-Value format: {name: {metadata: ...}}
            LOGGER_INFO("📋 Detected Key-Value format")
            metadata_dict = raw_data.copy()
        else:
            # Array format: [{name: ..., metadata: ...}, ...]
            LOGGER_INFO("📋 Detected Array format")
            for entry in raw_data:
                name = entry.get("name", "")
                if name:
                    metadata_dict[name] = entry
        
        LOGGER_INFO(f"Loaded {len(metadata_dict)} metadata records")
        
        # Connect to database and read latest data
        LOGGER_INFO(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get Qt version and architecture from database
        db_qtversion = get_db_qtversion(db_path)
        db_arch = get_db_arch(db_path)
        LOGGER_INFO(f"🔧 Database Qt version: {db_qtversion}, Architecture: {db_arch}")
        
        # Apply ARM64 → Qt 6.8 business rule
        if db_arch and db_arch.lower() == 'arm64':
            db_qtversion = '6.8'
            LOGGER_INFO(f"🔄 Applied ARM64 business rule: Qt version set to 6.8")
        
        # Log final values (will be None if not found in database)
        if db_qtversion or db_arch:
            LOGGER_INFO(f"✅ Target Qt version: {db_qtversion}, Architecture: {db_arch}")
        else:
            LOGGER_WARNING(f"⚠️ No Qt version/architecture info found in database")
        
        # Check if Ancestors column exists
        cursor.execute("PRAGMA table_info(ControlINFO)")
        columns = [row[1] for row in cursor.fetchall()]
        has_ancestors = "Ancestors" in columns
        
        # Query DB for control info with image data if GPT vision is enabled
        # Always include WindowName and WindowAutomationId for duplicate detection
        if use_gpt_vision:
            if has_ancestors:
                cursor.execute("""
                    SELECT ci.Description, ci.AutomationId, ci.ControlType, ci.ControlLocalizedType, ci.Ancestors, cah.Image, ci.WindowName, ci.WindowAutomationId
                    FROM ControlINFO ci
                    LEFT JOIN ControlActionHistory cah 
                        ON ci.Description = cah.Description 
                        AND ci.AutomationId = cah.AutomationId
                    WHERE ci.Description IS NOT NULL AND TRIM(ci.Description) != ''
                """)
            else:
                cursor.execute("""
                    SELECT ci.Description, ci.AutomationId, ci.ControlType, ci.ControlLocalizedType, NULL as Ancestors, cah.Image, ci.WindowName, ci.WindowAutomationId
                    FROM ControlINFO ci
                    LEFT JOIN ControlActionHistory cah 
                        ON ci.Description = cah.Description 
                        AND ci.AutomationId = cah.AutomationId
                    WHERE ci.Description IS NOT NULL AND TRIM(ci.Description) != ''
                """)
        else:
            if has_ancestors:
                cursor.execute("""
                    SELECT Description, AutomationId, ControlType, ControlLocalizedType, Ancestors, NULL as Image, WindowName, WindowAutomationId
                    FROM ControlINFO
                    WHERE Description IS NOT NULL AND TRIM(Description) != ''
                """)
            else:
                cursor.execute("""
                    SELECT Description, AutomationId, ControlType, ControlLocalizedType, NULL as Ancestors, NULL as Image, WindowName, WindowAutomationId
                    FROM ControlINFO
                    WHERE Description IS NOT NULL AND TRIM(Description) != ''
                """)
        
        db_records = cursor.fetchall()
        conn.close()
        
        LOGGER_INFO(f"Fetched {len(db_records)} records from database")
        
        # Sync statistics
        stats = {
            "total_db_records": len(db_records),
            "total_metadata_records": len(metadata_dict),
            "matched_by_name": 0,
            "new_controls_added": 0,
            "filtered_out": 0,
            "updated": 0,
            "no_change": 0,
            "not_in_db": 0,
            "changes": []
        }
        
        # Track which metadata entries have been matched
        matched_metadata_keys = set()
        
        # Only match by control name (exact match)
        # Keep the original key unchanged, only update other data
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("Syncing by Control Name (Key Unchanged)")
        LOGGER_INFO("=" * 80)
        
        db_records_unmatched = []
        for db_record in db_records:
            description, automation_id, control_type, control_type_name, ancestors_json, image_blob, window_name, window_id = db_record
            control_name = description if description else ""
            control_name_for_matching = control_name  # Keep original with spaces for exact matching
            window_name = (window_name or "").strip() if window_name else ""
            window_id = (window_id or "").strip() if window_id else ""
            
            # Skip records with empty automation_id - they are incomplete and shouldn't override existing data
            if not automation_id or not automation_id.strip():
                LOGGER_DEBUG(f"Skipping record with empty control_id: '{control_name_for_matching}'")
                continue
            
            # Convert image blob to base64 if available
            db_image_base64 = None
            if image_blob:
                import base64
                db_image_base64 = base64.b64encode(image_blob).decode('utf-8')
            
            # Try to find matching entry by control_name field (not by key)
            # Also check window_name to distinguish controls with same name in different windows
            # Skip entries that have already been matched to avoid duplicate updates
            matched_key = None
            matched_entry = None
            matched_by_window = False
            
            # First pass: try to match by control_name + control_id (exact match)
            for key, entry in metadata_dict.items():
                if key in matched_metadata_keys:
                    continue
                
                # Skip if entry is not a dictionary (e.g., app_version field)
                if not isinstance(entry, dict):
                    continue
                
                existing_platform_data = entry.get("metadata", {}).get(platform, {})
                existing_control_name = existing_platform_data.get("control_name") or ""  # Keep original with spaces
                existing_control_id_raw = existing_platform_data.get("control_id") or ""
                
                # Handle existing_control_id as both string and list
                if isinstance(existing_control_id_raw, list):
                    # If it's a list, check if automation_id matches any element
                    existing_control_ids = [str(cid).strip() for cid in existing_control_id_raw if cid]
                else:
                    # If it's a string, wrap in list for uniform processing
                    existing_control_ids = [str(existing_control_id_raw).strip()] if existing_control_id_raw else []
                
                existing_window_id = (existing_platform_data.get("window_id") or "").strip()
                
                # Perfect match: same name and same ID (exact match including spaces)
                # Remove SparkApp. prefix for comparison to handle format differences
                is_perfect_match = False
                if existing_control_name == control_name_for_matching:
                    # Debug logging
                    if "Join a meeting" in control_name_for_matching:
                        LOGGER_INFO(f"🔍 First-pass: Found name match '{key}'")
                        LOGGER_INFO(f"  existing_control_id: {existing_control_ids}")
                        LOGGER_INFO(f"  automation_id: {automation_id[:80] if automation_id else 'None'}")
                    
                    # Check if control_id matches (exact or after removing SparkApp. prefix)
                    # Try matching against any of the existing control IDs
                    for existing_control_id in existing_control_ids:
                        if existing_control_id == automation_id:
                            is_perfect_match = True
                            if "Join a meeting" in control_name_for_matching:
                                LOGGER_INFO(f"  ✅ Exact match with: {existing_control_id}")
                            break
                        elif automation_id and existing_control_id:
                            # Try removing SparkApp. prefix from automation_id for comparison
                            normalized_automation_id = automation_id.replace('SparkApp.', '', 1)
                            if "Join a meeting" in control_name_for_matching:
                                LOGGER_INFO(f"  normalized_automation_id: {normalized_automation_id[:80]}")
                            
                            if existing_control_id == normalized_automation_id:
                                is_perfect_match = True
                                LOGGER_DEBUG(f"Matched by normalized control_id: {existing_control_id} == {normalized_automation_id}")
                                if "Join a meeting" in control_name_for_matching:
                                    LOGGER_INFO(f"  ✅ Normalized match (DB -> JSON)!")
                                break
                            # Also try the reverse: remove from existing_control_id
                            else:
                                normalized_existing_id = existing_control_id.replace('SparkApp.', '', 1)
                                if "Join a meeting" in control_name_for_matching:
                                    LOGGER_INFO(f"  normalized_existing_id: {normalized_existing_id[:80]}")
                                
                                if normalized_existing_id == automation_id:
                                    is_perfect_match = True
                                    LOGGER_DEBUG(f"Matched by normalized existing_id: {normalized_existing_id} == {automation_id}")
                                    if "Join a meeting" in control_name_for_matching:
                                        LOGGER_INFO(f"  ✅ Normalized match (JSON -> DB)!")
                                    break
                
                if is_perfect_match:
                    matched_key = key
                    matched_entry = entry
                    matched_by_window = True
                    break
            
            # Second pass: if no perfect match, try matching by control_name only
            # But check if control_id is different (different window)
            if not matched_key:
                for key, entry in metadata_dict.items():
                    if key in matched_metadata_keys:
                        if control_name_for_matching in ["More options", "Join a meeting"]:
                            LOGGER_INFO(f"DEBUG [{control_name_for_matching}]: Skipping already matched key '{key}'")
                        continue
                    
                    # Skip if entry is not a dictionary (e.g., app_version field)
                    if not isinstance(entry, dict):
                        continue
                    
                    existing_platform_data = entry.get("metadata", {}).get(platform, {})
                    existing_control_name = existing_platform_data.get("control_name") or ""  # Keep original with spaces
                    existing_control_id_raw = existing_platform_data.get("control_id") or ""
                    
                    # Handle existing_control_id as both string and list
                    if isinstance(existing_control_id_raw, list):
                        # If it's a list, use the first non-empty element for similarity comparison
                        existing_control_id = next((str(cid).strip() for cid in existing_control_id_raw if cid), "")
                        existing_control_ids = [str(cid).strip() for cid in existing_control_id_raw if cid]
                    else:
                        # If it's a string, use it directly
                        existing_control_id = str(existing_control_id_raw).strip() if existing_control_id_raw else ""
                        existing_control_ids = [existing_control_id] if existing_control_id else []
                    
                    # Match by control_name field (exact match including spaces)
                    if existing_control_name == control_name_for_matching:
                        # Debug for "Join a meeting"
                        if "Join a meeting" in control_name_for_matching:
                            LOGGER_INFO(f"🔍 DEBUG [Join a meeting]: Found name match with key='{key}'")
                            LOGGER_INFO(f"  Existing control_id: {existing_control_id}")
                            LOGGER_INFO(f"  DB automation_id: {automation_id}")
                        
                        # Check if control_id is similar (not completely different window)
                        # If IDs are completely different, this is likely a different window
                        if existing_control_id and automation_id:
                            # Normalize IDs by removing SparkApp. prefix for comparison
                            normalized_existing_id = existing_control_id.replace('SparkApp.', '', 1)
                            normalized_automation_id = automation_id.replace('SparkApp.', '', 1)
                            
                            # Simple heuristic: check if they share any common path segments
                            existing_parts = set(normalized_existing_id.split('.'))
                            new_parts = set(normalized_automation_id.split('.'))
                            common_parts = existing_parts & new_parts
                            
                            # If they share less than 30% of parts, likely different windows
                            similarity = len(common_parts) / max(len(existing_parts), len(new_parts)) if existing_parts or new_parts else 0
                            
                            # Debug for "Join a meeting"
                            if "Join a meeting" in control_name_for_matching:
                                LOGGER_INFO(f"  Normalized existing_id: {normalized_existing_id}")
                                LOGGER_INFO(f"  Normalized automation_id: {normalized_automation_id}")
                                LOGGER_INFO(f"  Similarity score: {similarity:.2f}")
                                LOGGER_INFO(f"  Common parts ({len(common_parts)}): {sorted(common_parts)}")
                            
                            if similarity < 0.3:
                                # Different window - will add as new control
                                LOGGER_DEBUG(f"Skipping '{control_name_for_matching}' - different window (similarity={similarity:.2f})")
                                if "Join a meeting" in control_name_for_matching:
                                    LOGGER_INFO(f"  ❌ REJECTED - similarity too low")
                                continue
                        
                        if "Join a meeting" in control_name_for_matching:
                            LOGGER_INFO(f"  ✅ MATCHED - will update this entry")
                        
                        matched_key = key
                        matched_entry = entry
                        break
            
            if matched_key and matched_entry:
                # Found a match - update it (key remains unchanged)
                matched_metadata_keys.add(matched_key)
                stats["matched_by_name"] += 1
                
                existing_platform_data = matched_entry.get("metadata", {}).get(platform, {})
                
                # Update control info (key remains unchanged)
                updated = _update_control_metadata(
                    matched_entry, platform, control_name, automation_id, 
                    control_type, control_type_name, db_image_base64,
                    existing_platform_data, stats, window_name, window_id
                )
                
                if updated:
                    LOGGER_DEBUG(f"✅ Name match & updated: key='{matched_key}', control_name='{control_name}'")
                else:
                    LOGGER_DEBUG(f"✅ Name match (no change): key='{matched_key}', control_name='{control_name}'")
            else:
                # Save for adding as new control
                # Include window_name and window_id for generating unique keys for same-name controls in different windows
                db_records_unmatched.append((
                    control_name, automation_id, control_type, 
                    control_type_name, ancestors_json, db_image_base64, window_name, window_id
                ))
        
        LOGGER_INFO(f"Matched by name: {stats['matched_by_name']}")
        LOGGER_INFO(f"Remaining unmatched: {len(db_records_unmatched)}")
        
        # Add new controls to metadata
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("Adding New Controls")
        LOGGER_INFO("=" * 80)
        
        def normalize_window_id(window_id):
            """Remove SparkApp. prefix from window_id for comparison (Qt6.8 compatibility)."""
            if not window_id:
                return window_id
            return window_id.replace('SparkApp.', '', 1)
        
        # Prepare new controls for cleaning
        new_controls_to_add = []
        for db_record in db_records_unmatched:
            control_name, automation_id, control_type, control_type_name, ancestors_json, db_image_base64, window_name, window_id = db_record
            control_name_for_key = control_name.strip()  # Use stripped version for key comparison
            
            # Check if there's already a control with this name in metadata_dict
            # If yes and it's from a different window, create a unique key with window name
            unique_key = control_name
            if control_name_for_key in metadata_dict or control_name_for_key in [name.strip() if isinstance(name, str) else name for name, _, _, _ in new_controls_to_add]:
                # Check if this is a different window by comparing window_id only
                # Qt6.8 compatibility: Remove SparkApp. prefix before comparison
                is_different_window = False
                
                if control_name_for_key in metadata_dict:
                    existing_entry = metadata_dict[control_name_for_key]
                    existing_window_id = existing_entry.get("metadata", {}).get(platform, {}).get("window_id", "")
                    
                    # Normalize window_id by removing SparkApp. prefix for Qt6.8 compatibility
                    normalized_existing_window_id = normalize_window_id(existing_window_id)
                    normalized_new_window_id = normalize_window_id(window_id)
                    
                    # If name is same but window_id is different (after normalization), it's a different control
                    if existing_window_id and window_id:
                        if normalized_existing_window_id != normalized_new_window_id:
                            is_different_window = True
                            LOGGER_DEBUG(f"Different window detected for '{control_name}': existing_window_id='{normalized_existing_window_id}' != new_window_id='{normalized_new_window_id}'")
                
                if is_different_window and window_name:
                    # Generate unique key: "Control Name-Window Name"
                    unique_key = f"{control_name}-{window_name}"
                    LOGGER_INFO(f"🔄 Creating unique key for duplicate control: '{unique_key}'")
            
            # Create new metadata entry (Key-Value format: key is control_name, no need for "name" field)
            # Use database values directly without transformation
            new_entry = {
                "metadata": {
                    platform: {
                        "control_name": control_name,
                        "control_id": automation_id if automation_id else "",
                        "control_type": control_type if control_type else "",
                        "control_type_name": control_type_name if control_type_name else "",
                        "window_name": window_name if window_name else None,
                        "window_id": window_id if window_id else None
                    }
                }
            }
            
            # Add image if available
            if db_image_base64:
                new_entry["metadata"][platform]["image"] = db_image_base64
            
            new_controls_to_add.append((unique_key, new_entry, automation_id, window_name))
        
        # Clean new control names before adding
        if new_controls_to_add:
            LOGGER_INFO(f"🧹 Cleaning {len(new_controls_to_add)} new control names...")
            
            # Create a temporary dict with new controls
            temp_dict = {name: entry for name, entry, _, _ in new_controls_to_add}
            
            # Save to temporary file for cleaning
            import tempfile
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
                    temp_path = temp_file.name
                    json.dump(temp_dict, temp_file, ensure_ascii=False, indent=4)
                
                # Clean the temporary file
                cleaned_path = temp_path + '.cleaned'
                changes_count, removed_count = clean_dataset_keys(temp_path, output_file=cleaned_path, verbose=False)
                
                # Load cleaned data
                with open(cleaned_path, 'r', encoding='utf-8') as f:
                    cleaned_dict = json.load(f)
                
                LOGGER_INFO(f"🧹 Cleaned result: {len(cleaned_dict)} controls kept, {len(new_controls_to_add) - len(cleaned_dict)} filtered out")
                
                # Add cleaned controls to metadata
                # Only add controls that survived the cleaning process
                for unique_key, original_entry, automation_id, window_name in new_controls_to_add:
                    # Extract original control name (might be "Name" or "Name-WindowName")
                    original_name = unique_key.split('-')[0] if '-' in unique_key else unique_key
                    
                    # Find the cleaned version (key might have changed)
                    cleaned_name = None
                    cleaned_entry = None
                    
                    if original_name in cleaned_dict:
                        # Found by original name, use unique key if it has window suffix
                        cleaned_name = unique_key
                        cleaned_entry = cleaned_dict[original_name]
                    else:
                        # Name was changed during cleaning, try to find by control_id
                        for name, entry in cleaned_dict.items():
                            if entry.get("metadata", {}).get(platform, {}).get("control_id") == automation_id:
                                cleaned_name = unique_key if '-' in unique_key else name
                                cleaned_entry = entry
                                break
                    
                    if cleaned_name and cleaned_entry:
                        # Control survived cleaning, add it
                        metadata_dict[cleaned_name] = cleaned_entry
                        stats["new_controls_added"] += 1
                        
                        if unique_key != original_name:
                            LOGGER_INFO(f"➕ New control added (different window): '{cleaned_name}' (Window: {window_name}, ID: {automation_id})", "YELLOW")
                        elif cleaned_name != original_name:
                            LOGGER_INFO(f"➕ New control added (cleaned): '{original_name}' → '{cleaned_name}' (ID: {automation_id})", "YELLOW")
                        else:
                            LOGGER_INFO(f"➕ New control added: '{cleaned_name}' (ID: {automation_id})", "YELLOW")
                    else:
                        # Control was filtered out by cleaning
                        stats["filtered_out"] += 1
                        LOGGER_INFO(f"🗑️  Filtered out (dynamic content): '{original_name}' (ID: {automation_id})", "CYAN")
                
                # Clean up temporary files
                import os
                try:
                    os.unlink(temp_path)
                    os.unlink(cleaned_path)
                except:
                    pass
                        
            except Exception as e:
                LOGGER_ERROR(f"Failed to clean new control names: {str(e)}")
                LOGGER_INFO("Adding new controls without cleaning...")
                import traceback
                LOGGER_DEBUG(traceback.format_exc())
                
                # Fallback: add without cleaning
                for unique_key, new_entry, automation_id, window_name in new_controls_to_add:
                    metadata_dict[control_name] = new_entry
                    stats["new_controls_added"] += 1
                    LOGGER_INFO(f"➕ New control added: '{control_name}' (ID: {automation_id})", "YELLOW")
        else:
            # Direct add without cleaning step (cleaning is built-in now)
            for unique_key, new_entry, automation_id, window_name in new_controls_to_add:
                metadata_dict[unique_key] = new_entry
                stats["new_controls_added"] += 1
                if '-' in unique_key:
                    LOGGER_INFO(f"➕ New control added (different window): '{unique_key}' (Window: {window_name}, ID: {automation_id})", "YELLOW")
                else:
                    LOGGER_INFO(f"➕ New control added: '{unique_key}' (ID: {automation_id})", "YELLOW")
        
        LOGGER_INFO(f"New controls added: {stats['new_controls_added']}")
        
        # Check for controls in metadata but not in DB (just for reporting)
        unmatched_in_metadata = [k for k in metadata_dict.keys() if k not in matched_metadata_keys]
        stats["not_in_db"] = len(unmatched_in_metadata)
        if unmatched_in_metadata:
            LOGGER_WARNING(f"Controls in metadata but not in DB: {stats['not_in_db']}")
            for name in unmatched_in_metadata[:5]:  # Show first 5
                LOGGER_DEBUG(f"  - '{name}'")
        
        # In dry run mode, show the final metadata that would be added
        if dry_run and stats['new_controls_added'] > 0:
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("📋 Preview: New Controls That Would Be Added (Dry Run)")
            LOGGER_INFO("=" * 80)
            
            # Find all newly added controls
            new_controls = {}
            for key, entry in metadata_dict.items():
                # Skip non-dict entries (e.g., app_version)
                if isinstance(entry, dict) and key not in matched_metadata_keys:
                    new_controls[key] = entry
            
            # Display them in JSON format
            LOGGER_INFO(json.dumps(new_controls, ensure_ascii=False, indent=2))
            LOGGER_INFO("=" * 80)
        
        # Save updated metadata
        if not dry_run:
            if output_file_path is None:
                output_file_path = metadata_file_path
            else:
                output_file_path = Path(output_file_path)
            
            # Create backup
            if output_file_path.exists():
                backup_path = str(output_file_path) + '.backup'
                import shutil
                shutil.copy2(output_file_path, backup_path)
                LOGGER_INFO(f"Created backup: {backup_path}")
            
            # Save in the same format as input
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if is_keyed_format:
                # Save as Key-Value format: {name: {metadata: ...}}
                LOGGER_INFO("💾 Saving in Key-Value format")
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata_dict, f, ensure_ascii=False, indent=4)
            else:
                # Save as Array format: [{name: ..., metadata: ...}, ...]
                LOGGER_INFO("💾 Saving in Array format")
                updated_list = []
                for name, entry in metadata_dict.items():
                    # Skip non-dict entries (e.g., app_version)
                    if not isinstance(entry, dict):
                        continue
                    # Ensure 'name' field exists in array format
                    if 'name' not in entry:
                        entry['name'] = name
                    updated_list.append(entry)
                
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_list, f, ensure_ascii=False, indent=4)
            
            LOGGER_INFO(f"✅ Saved updated metadata to {output_file_path}")
            
            # Auto-fix duplicates after sync (only if not dry run)
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("🔧 Auto-fixing Duplicate Controls...")
            LOGGER_INFO("=" * 80)
            
            try:
                # Import fix function
                import sys
                fix_script_path = Path(__file__).parent / "fix_duplicate_controls.py"
                if fix_script_path.exists():
                    # Import the fix function
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("fix_duplicate_controls", fix_script_path)
                    if spec and spec.loader:
                        fix_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(fix_module)
                        
                        # Run the fix
                        LOGGER_INFO("Running duplicate control fix...")
                        fix_module.fix_duplicate_controls(
                            dataset_path=output_file_path,
                            dry_run=False
                        )
                    else:
                        LOGGER_WARNING("Failed to load fix module")
                else:
                    LOGGER_WARNING(f"Fix script not found: {fix_script_path}")
                    LOGGER_INFO("Skipping duplicate fix")
            except Exception as e:
                LOGGER_ERROR(f"Failed to auto-fix duplicates: {str(e)}")
                LOGGER_INFO("You can manually run: python fix_duplicate_controls.py --dataset-file control_datasets.json")
        else:
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("🔍 Dry Run Mode - No Files Modified")
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("💡 To apply these changes, run without --dry-run flag")
        
        # Print summary
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("🎯 Sync Summary:")
        LOGGER_INFO("=" * 80)
        LOGGER_INFO(f"  Total DB records: {stats['total_db_records']}")
        LOGGER_INFO(f"  Total metadata records: {stats['total_metadata_records']}")
        LOGGER_INFO("")
        LOGGER_INFO("  Matching Results:")
        LOGGER_INFO(f"    ✅ Matched by name (key unchanged): {stats['matched_by_name']}", "GREEN")
        LOGGER_INFO(f"    ➕ New controls added: {stats['new_controls_added']}", "YELLOW")
        LOGGER_INFO(f"    🗑️  Filtered out (dynamic content): {stats['filtered_out']}", "CYAN")
        LOGGER_INFO("")
        LOGGER_INFO(f"  Update Statistics:")
        LOGGER_INFO(f"    📝 Updated: {stats['updated']}")
        LOGGER_INFO(f"    ⏸️  No change: {stats['no_change']}")
        LOGGER_INFO(f"    ⚠️  In metadata but not in DB: {stats['not_in_db']}")
        LOGGER_INFO("=" * 80)
        
        if stats["updated"] > 0 and len(stats["changes"]) <= 10:
            LOGGER_INFO("Changes details:")
            for change in stats["changes"]:
                LOGGER_INFO(f"  '{change['name']}':")
                for field, values in change['changes'].items():
                    LOGGER_INFO(f"    {field}: '{values['old']}' -> '{values['new']}'")
        elif stats["updated"] > 10:
            LOGGER_INFO(f"({stats['updated']} changes - showing first 10)")
            for change in stats["changes"][:10]:
                LOGGER_INFO(f"  '{change['name']}': {list(change['changes'].keys())}")
        
        return stats
        
    except Exception as e:
        LOGGER_ERROR(f"Error syncing metadata from DB: {str(e)}")
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        return {"error": str(e)}

def extract_name_as_key_json(input_file_path, output_file_path=None):
    """
    Extract 'name' field as key from metadata JSON file and save as key-value JSON format.
    
    Args:
        input_file_path (str or Path): Path to input JSON file (e.g., control_metadata.json)
        output_file_path (str or Path): Path to save output JSON file. 
                                       If None, uses input_file_path with '_keyed.json' suffix
    
    Returns:
        dict: Key-value format dictionary with name as key
        
    Example:
        Input format (list):
        [
            {"name": "Join a meeting", "metadata": {...}},
            {"name": "Sign in", "metadata": {...}}
        ]
        
        Output format (dict):
        {
            "Join a meeting": {"metadata": {...}},
            "Sign in": {"metadata": {...}}
        }
    """
    input_file_path = Path(input_file_path)
    
    # Check if input file exists
    if not input_file_path.exists():
        LOGGER_ERROR(f"Input file not found: {input_file_path}")
        return {}
    
    try:
        # Load input JSON file
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        LOGGER_INFO(f"Loaded {len(data)} records from {input_file_path}")
        
        # Convert list to dict with name as key
        keyed_data = {}
        duplicate_names = []
        
        for entry in data:
            name = entry.get("name", "")
            if name:
                if name in keyed_data:
                    duplicate_names.append(name)
                    LOGGER_WARNING(f"Duplicate name found: '{name}' - keeping first occurrence")
                else:
                    # Remove 'name' key from entry and use remaining data as value
                    entry_copy = entry.copy()
                    entry_copy.pop("name", None)
                    keyed_data[name] = entry_copy
            else:
                LOGGER_WARNING("Entry without name found - skipping")
        
        if duplicate_names:
            LOGGER_WARNING(f"Found {len(duplicate_names)} duplicate names: {duplicate_names}")
        
        LOGGER_INFO(f"Converted to key-value format with {len(keyed_data)} unique names")
        
        # Determine output file path
        if output_file_path is None:
            output_file_path = input_file_path.parent / f"{input_file_path.stem}_keyed.json"
        else:
            output_file_path = Path(output_file_path)
        
        # Ensure output directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(keyed_data, f, ensure_ascii=False, indent=4)
        
        LOGGER_INFO(f"Saved key-value format JSON to {output_file_path}")
        
        return keyed_data
        
    except Exception as e:
        LOGGER_ERROR(f"Error extracting name as key from {input_file_path}: {str(e)}")
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        return {}

def control_datasets_generator(incremental_mode=True, platform=None, project=None, skip_main_db=False, skip_custom_metadata=False, auto_clean=True):
    """
    Generate control datasets with the following logic:
    1. Check if DATASETS_PATH and DATASETS_SPECIFIC_PATH are available
    2. Generate metadata from DBs if available, otherwise use existing files
    3. Apply platform conversion to generated source files (control_specific_metadata.json)
    4. Auto-clean dynamic controls (if enabled)
    5. Incremental merge with priority: existing < base < specific < custom
    6. Save final control_datasets_{project}_{platform}.json in Key-Value format
    
    Output Format (Key-Value):
        {
            "Join a meeting": {"metadata": {"windows": {...}}},
            "Sign in": {"metadata": {"windows": {...}}},
            ...
        }
    
    Args:
        incremental_mode (bool): If True, use incremental merge; if False, use reset mode
        platform (str): Platform for source file generation (windows, mac, web). 
                       Only affects newly generated source files, not the final merge.
        project (str): Project name for dataset naming (e.g., 'webex_app', 'webex_web').
                      If None, uses default naming 'control_datasets.json'
        skip_main_db (bool): If True, skip DATASETS_PATH (main DB) and only use DATASETS_SPECIFIC_PATH.
                            Default is False.
        skip_custom_metadata (bool): If True, skip custom_control_metadata.json.
                                    Default is False.
        auto_clean (bool): If True, automatically clean dynamic controls after generation.
                          Default is True.
    """
    gen = ControlDatasetsGenerator()
    
    # Log platform filter (only for source file generation)
    if platform:
        LOGGER_INFO(f"Platform for source file generation: {platform}")
    else:
        LOGGER_INFO("Platform for source file generation: windows (default)")
    
    # Log project name
    if project:
        LOGGER_INFO(f"Project name: {project}")
    else:
        LOGGER_INFO("Project name: default (no project specified)")
    
    # Determine output dataset path based on project and platform
    if project and platform:
        dataset_filename = f"control_datasets_{project}_{platform}.json"
        output_dataset_path = TEST_CONTROL_DATASET_FOLDER_PATH / dataset_filename
        LOGGER_INFO(f"Output dataset path: {output_dataset_path}")
    else:
        output_dataset_path = CONTROL_DEFAULT_DATASET_PATH
        LOGGER_INFO(f"Using default output dataset path: {output_dataset_path}")
    
    # For incremental mode, skip database sync - only merge JSON files
    # Database sync is only done with --sync-from-db parameter
    if incremental_mode:
        LOGGER_INFO("📋 Incremental mode: Merging JSON files only (skipping database sync)")
        LOGGER_INFO("   💡 Use --sync-from-db to sync with database")
        db_main_available = False
        db_specific_available = False
    else:
        # Check database availability for reset mode
        db_main_available = check_db_availability(DATASETS_PATH)
        db_specific_available = check_db_availability(DATASETS_SPECIFIC_PATH)
        
        # Log skip_main_db configuration
        if skip_main_db:
            LOGGER_INFO("⚠️  skip_main_db=True: Skipping main DB (DATASETS_PATH), only using DATASETS_SPECIFIC_PATH")
            db_main_available = False  # Force skip main DB
        
        LOGGER_INFO(f"Main DB available: {DATASETS_PATH}, Specific DB available: {DATASETS_SPECIFIC_PATH}")

    # Load existing data from output dataset for incremental mode
    if incremental_mode:
        LOGGER_INFO(f"Loading existing dataset from {output_dataset_path} for incremental update...")
        existing_data = load_existing_metadata(output_dataset_path)
    else:
        existing_data = []
    
    # Handle main database (control_metadata.json)
    # Skip in incremental mode - only merge existing + custom JSONs
    if incremental_mode:
        LOGGER_INFO("Skipping base metadata in incremental mode")
        base_data = []
    elif db_main_available:
        LOGGER_INFO("Generating control_metadata.json from main database...")
        gen.generate_control_metadata_from_dataset(DATASETS_PATH, CONTROL_METADATA_PATH)
        gen.refine_control_metadata(CONTROL_METADATA_PATH, CONTROL_METADATA_PATH)
        # Apply platform conversion to the generated file (only if platform specified)
        filter_and_save_metadata_file(CONTROL_METADATA_PATH, platform)
        
        # Auto-clean dynamic controls after generation (if enabled)
        if auto_clean:
            LOGGER_INFO("🧹 Auto-cleaning dynamic controls from control_metadata.json...")
            try:
                changes_count, removed_count = clean_dataset_keys(CONTROL_METADATA_PATH, output_file=None, verbose=False)
                LOGGER_INFO(f"✅ Auto-cleaning completed for control_metadata.json ({changes_count} keys, {removed_count} removed)")
            except Exception as e:
                LOGGER_WARNING(f"⚠️  Auto-cleaning failed: {e}, continuing with uncleaned data")
        else:
            LOGGER_INFO("⏭️  Auto-cleaning skipped (--no-auto-clean flag)")
        
        base_data = load_existing_metadata(CONTROL_METADATA_PATH)
    else:
        if skip_main_db:
            LOGGER_INFO("Skipping main database (skip_main_db=True), using empty base data")
            base_data = []
        else:
            LOGGER_INFO("Using existing control_metadata.json (database not available)")
            base_data = load_existing_metadata(CONTROL_METADATA_PATH)
    
    # Handle specific database (control_specific_metadata.json)
    # Skip in incremental mode - only merge existing + custom JSONs
    if incremental_mode:
        LOGGER_INFO("Skipping specific metadata in incremental mode")
        specific_data = []
    elif db_specific_available:
        LOGGER_INFO("Generating control_specific_metadata.json from specific database...")
        gen.generate_control_metadata_from_dataset(DATASETS_SPECIFIC_PATH, CONTROL_SPECIFIC_METADATA_PATH)
        gen.refine_control_metadata(CONTROL_SPECIFIC_METADATA_PATH, CONTROL_SPECIFIC_METADATA_PATH)
        # Apply platform conversion to the generated file (only if platform specified)
        filter_and_save_metadata_file(CONTROL_SPECIFIC_METADATA_PATH, platform)
        
        # Auto-clean dynamic controls after generation (if enabled)
        if auto_clean:
            LOGGER_INFO("🧹 Auto-cleaning dynamic controls from control_specific_metadata.json...")
            try:
                changes_count, removed_count = clean_dataset_keys(CONTROL_SPECIFIC_METADATA_PATH, output_file=None, verbose=False)
                LOGGER_INFO(f"✅ Auto-cleaning completed for control_specific_metadata.json ({changes_count} keys, {removed_count} removed)")
            except Exception as e:
                LOGGER_WARNING(f"⚠️  Auto-cleaning failed: {e}, continuing with uncleaned data")
        else:
            LOGGER_INFO("⏭️  Auto-cleaning skipped (--no-auto-clean flag)")
        
        specific_data = load_existing_metadata(CONTROL_SPECIFIC_METADATA_PATH)
    else:
        LOGGER_INFO("Using existing control_specific_metadata.json (database not available)")
        specific_data = load_existing_metadata(CONTROL_SPECIFIC_METADATA_PATH)
    
    # Load custom metadata (conditionally based on skip_custom_metadata)
    if skip_custom_metadata:
        LOGGER_INFO("⚠️  skip_custom_metadata=True: Skipping custom_control_metadata.json")
        custom_data = []
    else:
        LOGGER_INFO("Loading custom metadata from custom_control_metadata.json...")
        custom_data = load_existing_metadata(CUSTOM_CONTROL_METADATA_PATH)
    
    # Merge data with priority rules (NO platform filtering during merge)
    if incremental_mode:
        LOGGER_INFO("Incremental merge: existing + custom only (skipping base and specific)...")
        # Only merge existing data with custom data
        merged_data = incremental_merge_with_priority(existing_data, [], [], custom_data)
        
        # Save incrementally
        LOGGER_INFO(f"Incrementally saving dataset to {output_dataset_path}...")
        incremental_save_dataset(merged_data, output_dataset_path)
    else:
        LOGGER_INFO("Reset merge with priority: base < specific < custom...")
        # Use the old merge function for backward compatibility
        merged_data = []
        merged_dict = {}
        
        # Add base data
        for entry in base_data:
            name = entry.get("name", "")
            if name:
                merged_dict[name] = entry.copy()
        
        # Update from specific data
        for entry in specific_data:
            name = entry.get("name", "")
            if name:
                if name in merged_dict:
                    merged_dict[name].update(entry)
                else:
                    merged_dict[name] = entry.copy()
        
        # Update from custom data
        for entry in custom_data:
            name = entry.get("name", "")
            if name:
                if name in merged_dict:
                    merged_dict[name].update(entry)
                else:
                    merged_dict[name] = entry.copy()
        
        merged_data = list(merged_dict.values())
        
        # Reset and save final dataset
        LOGGER_INFO(f"Resetting and saving dataset to {output_dataset_path}...")
        reset_and_save_final_dataset(merged_data, output_dataset_path)
    
    LOGGER_INFO("Control datasets generation completed successfully!")


def add_images_to_existing_metadata(db_path, metadata_file_path, output_file_path=None, platform="windows"):
    import sqlite3
    import base64
    import shutil
    from datetime import datetime
    
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("🖼️  Adding Images to Existing Metadata")
    LOGGER_INFO("=" * 80)
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    if not os.path.exists(metadata_file_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_file_path}")
    
    if output_file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = metadata_file_path.replace(".json", f"_backup_{timestamp}.json")
        shutil.copy2(metadata_file_path, backup_path)
        LOGGER_INFO(f"📦 Backup created: {backup_path}")
        output_file_path = metadata_file_path
    
    LOGGER_INFO(f"📖 Loading metadata from: {metadata_file_path}")
    with open(metadata_file_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    if isinstance(metadata, list):
        metadata_dict = {item['name']: item for item in metadata}
        is_array_format = True
    else:
        metadata_dict = metadata
        is_array_format = False
    
    LOGGER_INFO(f"📊 Total metadata entries: {len(metadata_dict)}")
    
    LOGGER_INFO(f"🔌 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {
        "total": len(metadata_dict),
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    LOGGER_INFO(f"🔄 Processing {len(metadata_dict)} controls...")
    LOGGER_INFO("")
    
    for idx, (name, entry) in enumerate(metadata_dict.items(), 1):
        try:
            cursor.execute("""
                SELECT cah.Image
                FROM ControlINFO ci
                LEFT JOIN ControlActionHistory cah 
                    ON ci.ControlName = cah.ControlName
                WHERE ci.ControlName = ? 
                    AND cah.Image IS NOT NULL
                ORDER BY cah.ActionTime DESC
                LIMIT 1
            """, (name,))
            
            result = cursor.fetchone()
            
            if result and result[0]:
                image_blob = result[0]
                image_base64 = base64.b64encode(image_blob).decode('utf-8')
                
                if "metadata" not in entry:
                    entry["metadata"] = {}
                
                if platform not in entry["metadata"]:
                    entry["metadata"][platform] = {}
                
                old_image = entry["metadata"][platform].get("image")
                entry["metadata"][platform]["image"] = image_base64
                
                stats["updated"] += 1
                
                if old_image:
                    LOGGER_DEBUG(f"[{idx}/{stats['total']}] ✅ Updated image for '{name}'")
                else:
                    LOGGER_INFO(f"[{idx}/{stats['total']}] ➕ Added image for '{name}'")
            else:
                stats["skipped"] += 1
                LOGGER_DEBUG(f"[{idx}/{stats['total']}] ⏭️  Skipped '{name}' (no image in DB)")
                
        except Exception as e:
            stats["errors"] += 1
            LOGGER_ERROR(f"[{idx}/{stats['total']}] ❌ Error processing '{name}': {str(e)}")
    
    conn.close()
    
    if is_array_format:
        output_data = [{"name": k, **v} for k, v in metadata_dict.items()]
    else:
        output_data = metadata_dict
    
    LOGGER_INFO("")
    LOGGER_INFO(f"💾 Saving updated metadata to: {output_file_path}")
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    LOGGER_INFO("")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("📊 Summary:")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO(f"  Total controls: {stats['total']}")
    LOGGER_INFO(f"  ✅ Images added/updated: {stats['updated']}")
    LOGGER_INFO(f"  ⏭️  Skipped (no image in DB): {stats['skipped']}")
    LOGGER_INFO(f"  ❌ Errors: {stats['errors']}")
    LOGGER_INFO("=" * 80)
    
    if stats['updated'] > 0:
        LOGGER_INFO(f"✅ Successfully added images to {stats['updated']} controls!")
        LOGGER_INFO(f"📁 Output file: {output_file_path}")
    else:
        LOGGER_WARNING("⚠️  No images were added. Check if database has image data.")
    
    return stats


def generate_control_datasets_with_ui_path(input_file=None, output_file=None, db_path=None, start_index=None, platform="windows"):
    """
    Generate control_datasets_with_ui_path.json by adding UI path information to control_datasets.json.
    This ensures the keys are exactly the same as control_datasets.json.
    
    Args:
        input_file (str): Path to input control_datasets.json (default: CONTROL_DEFAULT_DATASET_PATH)
        output_file (str): Path to output file (default: control_datasets_with_ui_path.json)
        db_path (str): Path to database file (default: from DATASETS_SPECIFIC_PATH)
        start_index (int): Optional start index for slicing UI path
        platform (str): Platform name (default: "windows")
        
    Returns:
        dict: Statistics about the generation process
    """
    from pathlib import Path
    from rs_sdk.utils.control_db import ControlDB
    
    # Set default paths
    if input_file is None:
        input_file = CONTROL_DEFAULT_DATASET_PATH
    
    if output_file is None:
        output_file = TEST_CONTROL_DATASET_FOLDER_PATH / "control_datasets_with_ui_path.json"
    
    if db_path is None:
        # Use the database path from test_space/datasets/data
        db_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
    
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("🚀 Generating Control Datasets with UI Path")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO(f"Input file: {input_file}")
    LOGGER_INFO(f"Output file: {output_file}")
    LOGGER_INFO(f"Database: {db_path}")
    LOGGER_INFO(f"Platform: {platform}")
    if start_index:
        LOGGER_INFO(f"Start index: {start_index}")
    LOGGER_INFO("")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        LOGGER_ERROR(f"Input file not found: {input_file}")
        return {"error": "Input file not found"}
    
    # Check if database exists
    if not os.path.exists(db_path):
        LOGGER_ERROR(f"Database file not found: {db_path}")
        return {"error": "Database file not found"}
    
    # Load existing control_datasets.json
    LOGGER_INFO(f"📖 Loading control datasets from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            control_datasets = json.load(f)
        LOGGER_INFO(f"✅ Loaded {len(control_datasets)} controls")
    except Exception as e:
        LOGGER_ERROR(f"Failed to load input file: {str(e)}")
        return {"error": str(e)}
    
    # Initialize ControlDB
    control_db = ControlDB(db_path=db_path)
    
    # Statistics
    stats = {
        "total": len(control_datasets),
        "success": 0,
        "failed": 0,
        "no_hierarchy": 0,
        "errors": []
    }
    
    # Control type mapping
    control_type_map = {
        50000: "button", 50001: "calendar", 50002: "check_box", 50003: "combo_box",
        50004: "edit", 50005: "hyperlink", 50006: "image", 50007: "list_item",
        50008: "list", 50009: "menu", 50010: "menu_bar", 50011: "menu_item",
        50012: "progress_bar", 50013: "radio_button", 50014: "scroll_bar", 50015: "slider",
        50016: "spinner", 50017: "status_bar", 50018: "tab", 50019: "tab_item",
        50020: "text", 50021: "tool_bar", 50022: "tool_tip", 50023: "tree",
        50024: "tree_item", 50025: "custom", 50026: "group", 50027: "thumb",
        50028: "data_grid", 50029: "data_item", 50030: "document", 50031: "split_button",
        50032: "window", 50033: "pane", 50034: "header", 50035: "header_item",
        50036: "table", 50037: "title_bar", 50038: "separator"
    }
    
    # Create output dictionary with same keys
    output_datasets = {}
    
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("🔄 Processing controls and adding UI path information...")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("")
    
    for idx, (control_key, control_data) in enumerate(control_datasets.items(), 1):
        try:
            # Get control metadata
            if "metadata" not in control_data or platform not in control_data["metadata"]:
                LOGGER_WARNING(f"[{idx}/{stats['total']}] ⚠️  Skipped '{control_key}' (no {platform} metadata)")
                stats["failed"] += 1
                continue
            
            platform_data = control_data["metadata"][platform]
            control_name = platform_data.get("control_name", control_key)
            control_id = platform_data.get("control_id", "")
            
            # Query hierarchical levels from database
            if control_id:
                query = """
                SELECT HierarchicalLevel 
                FROM ControlINFO 
                WHERE Description = ? AND (AutomationId = ? OR (AutomationId IS NULL AND ? IS NULL))
                AND HierarchicalLevel IS NOT NULL AND HierarchicalLevel != ''
                """
                results = control_db._execute_query(query, (control_name, control_id, control_id))
            else:
                query = """
                SELECT HierarchicalLevel 
                FROM ControlINFO 
                WHERE Description = ? AND HierarchicalLevel IS NOT NULL AND HierarchicalLevel != ''
                """
                results = control_db._execute_query(query, (control_name,))
            
            hierarchical_levels = [row[0] for row in results if row[0]]
            
            if not hierarchical_levels:
                LOGGER_DEBUG(f"[{idx}/{stats['total']}] ⏭️  No hierarchical levels for '{control_key}'")
                stats["no_hierarchy"] += 1
                # Still add to output, just without UI path
                output_datasets[control_key] = control_data.copy()
                continue
            
            # Find shortest path
            min_length = min(len(x.split('.')) for x in hierarchical_levels)
            shortest_paths = [x for x in hierarchical_levels if len(x.split('.')) == min_length]
            
            if len(shortest_paths) > 1:
                def sort_key(path):
                    parts = path.split('.')
                    try:
                        return (len(parts), int(parts[-1]))
                    except (ValueError, IndexError):
                        return (len(parts), float('inf'))
                shortest_level = min(shortest_paths, key=sort_key)
            else:
                shortest_level = shortest_paths[0]
            
            # Generate UI path
            full_ui_path = control_db.fetch_ui_path_by_index(shortest_level)
            
            # Create output entry with UI path information
            output_entry = {
                "metadata": {
                    platform: {
                        **platform_data,
                        "control_ui_path": full_ui_path,
                        "all_hierarchical_levels": hierarchical_levels,
                        "shortest_hierarchical_level": shortest_level
                    }
                }
            }
            
            # Add sliced path if start_index is provided
            if start_index is not None and start_index > 0:
                if start_index <= len(full_ui_path):
                    sliced_ui_path = full_ui_path[start_index - 1:]
                    level_parts = shortest_level.split('.')
                    if start_index <= len(level_parts):
                        sliced_hierarchical_level = '.'.join(level_parts[start_index - 1:])
                        output_entry["metadata"][platform]["meeting_ui_path"] = sliced_ui_path
                        output_entry["metadata"][platform]["sliced_hierarchical_level"] = sliced_hierarchical_level
                        output_entry["metadata"][platform]["start_index"] = start_index
            
            # Copy other platform metadata if exists
            if "metadata" in control_data:
                for other_platform, other_data in control_data["metadata"].items():
                    if other_platform != platform:
                        output_entry["metadata"][other_platform] = other_data
            
            output_datasets[control_key] = output_entry
            stats["success"] += 1
            
            if idx % 100 == 0 or idx == stats["total"]:
                LOGGER_INFO(f"[{idx}/{stats['total']}] ✅ Processed '{control_key}'")
            else:
                LOGGER_DEBUG(f"[{idx}/{stats['total']}] ✅ Processed '{control_key}'")
                
        except Exception as e:
            LOGGER_ERROR(f"[{idx}/{stats['total']}] ❌ Error processing '{control_key}': {str(e)}")
            stats["failed"] += 1
            stats["errors"].append((control_key, str(e)))
            # Still add to output without UI path
            output_datasets[control_key] = control_data.copy()
    
    # Save to output file
    LOGGER_INFO("")
    LOGGER_INFO(f"💾 Saving to {output_file}...")
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_datasets, f, ensure_ascii=False, indent=4)
        
        LOGGER_INFO(f"✅ Saved {len(output_datasets)} controls to {output_file}")
    except Exception as e:
        LOGGER_ERROR(f"Failed to save output file: {str(e)}")
        return {"error": str(e)}
    
    # Print summary
    LOGGER_INFO("")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("📊 Summary:")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO(f"  Total controls: {stats['total']}")
    LOGGER_INFO(f"  ✅ Successfully added UI path: {stats['success']}")
    LOGGER_INFO(f"  ⏭️  No hierarchical levels: {stats['no_hierarchy']}")
    LOGGER_INFO(f"  ❌ Failed: {stats['failed']}")
    LOGGER_INFO("=" * 80)
    
    if stats["errors"]:
        LOGGER_WARNING(f"Errors encountered for {len(stats['errors'])} controls:")
        for control_key, error in stats["errors"][:10]:
            LOGGER_WARNING(f"  - {control_key}: {error}")
        if len(stats["errors"]) > 10:
            LOGGER_WARNING(f"  ... and {len(stats['errors']) - 10} more")
    
    LOGGER_INFO("")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("✅ Control Datasets with UI Path Generation Completed!")
    LOGGER_INFO("=" * 80)
    
    return stats

def get_major_version(version):
    """
    Extract major version (X.Y.Z) from full version string (X.Y.Z.W)
    Example: "46.3.0.33972" -> "46.3.0"
    """
    try:
        parts = version.split('.')
        if len(parts) >= 3:
            return f"{parts[0]}.{parts[1]}.{parts[2]}"
        return version
    except:
        return version


def get_db_app_version(db_path=None):
    """
    Get app version from ControlINFO database
    
    Args:
        db_path: Path to database file (default: TEST_CONTROL_DATASET_FOLDER_PATH / 'data' / 'ControlINFO.db')
    
    Returns:
        str: App version from database (e.g., "46.3.0.12345") or None if not found
    """
    if db_path is None:
        db_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
    
    if not os.path.exists(db_path):
        LOGGER_WARNING(f"⚠️ Database not found at: {db_path}")
        return None
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Try to get the latest AppVersion from ControlINFO table
        cursor.execute("SELECT DISTINCT AppVersion FROM ControlINFO WHERE AppVersion IS NOT NULL ORDER BY TabOrder DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            app_version = result[0].strip()
            LOGGER_INFO(f"✅ Found app version in DB: {app_version}")
            return app_version
        else:
            LOGGER_WARNING("⚠️ No AppVersion found in database")
            return None
    except Exception as e:
        LOGGER_ERROR(f"❌ Error reading app version from database: {e}")
        return None


def get_db_qtversion(db_path=None):
    """
    Get qtversion from ControlINFO database
    
    Args:
        db_path: Path to database file
    
    Returns:
        str: Qt version from database (e.g., "6.8") or None if not found
    """
    if db_path is None:
        db_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
    
    if not os.path.exists(db_path):
        LOGGER_DEBUG(f"Database not found at: {db_path}")
        return None
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Try to get the latest QtVersion from ControlINFO table
        # QtVersion might be stored as a column or in metadata
        cursor.execute("PRAGMA table_info(ControlINFO)")
        columns = [row[1] for row in cursor.fetchall()]
        
        qt_version = None
        
        # Check if QtVersion or similar column exists
        if 'QtVersion' in columns:
            cursor.execute("SELECT DISTINCT QtVersion FROM ControlINFO WHERE QtVersion IS NOT NULL ORDER BY TabOrder DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result[0]:
                qt_version = str(result[0]).strip()
        
        conn.close()
        
        if qt_version:
            LOGGER_INFO(f"✅ Found qtversion in DB: {qt_version}")
            return qt_version
        else:
            LOGGER_DEBUG("⚠️ No QtVersion found in database")
            return None
    except Exception as e:
        LOGGER_DEBUG(f"Could not read qtversion from database: {e}")
        return None


def get_db_arch(db_path=None):
    """
    Get architecture from ControlINFO database
    
    Args:
        db_path: Path to database file
    
    Returns:
        str: Architecture from database (e.g., "x64", "arm64") or None if not found
    """
    if db_path is None:
        db_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
    
    if not os.path.exists(db_path):
        LOGGER_DEBUG(f"Database not found at: {db_path}")
        return None
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Try to get the latest Arch from ControlINFO table
        cursor.execute("PRAGMA table_info(ControlINFO)")
        columns = [row[1] for row in cursor.fetchall()]
        
        arch = None
        
        # Check if Arch column exists
        if 'Arch' in columns:
            cursor.execute("SELECT DISTINCT Arch FROM ControlINFO WHERE Arch IS NOT NULL ORDER BY TabOrder DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result[0]:
                arch = str(result[0]).strip()
        
        conn.close()
        
        if arch:
            LOGGER_INFO(f"✅ Found arch in DB: {arch}")
            return arch
        else:
            LOGGER_DEBUG("⚠️ No Arch found in database")
            return None
    except Exception as e:
        LOGGER_DEBUG(f"Could not read arch from database: {e}")
        return None


def sync_control_datasets_with_version_hierarchy(db_path=None, input_file=None, output_base_dir=None, force_regenerate=False, version_dir_only=False):
    """
    Sync control_datasets.json with version hierarchy based on app version comparison
    
    Features:
    1. Get app version from ControlINFO.db
    2. Compare with control_datasets.json app_version
    3. If versions differ, create version-specific directory (e.g., 46.3)
    4. Generate/copy control_datasets.json for that version
    
    Args:
        db_path (str/Path): Path to ControlINFO.db (default: TEST_CONTROL_DATASET_FOLDER_PATH / 'data' / 'ControlINFO.db')
        input_file (str/Path): Path to current control_datasets.json (default: CONTROL_DEFAULT_DATASET_PATH)
        output_base_dir (str/Path): Base directory for version-specific folders (default: TEST_CONTROL_DATASET_FOLDER_PATH)
        force_regenerate (bool): If True, always create version directory even if versions match
        version_dir_only (bool): If True, save ONLY to version directory (do NOT update root directory file)
    
    Returns:
        dict: Status dict with keys: success, message, db_version, json_version, created_dir, copied_file
    """
    import json
    import shutil
    from pathlib import Path
    
    # Set default paths
    if db_path is None:
        db_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
    else:
        db_path = Path(db_path)
    
    if input_file is None:
        input_file = CONTROL_DEFAULT_DATASET_PATH
    else:
        input_file = Path(input_file)
    
    if output_base_dir is None:
        output_base_dir = TEST_CONTROL_DATASET_FOLDER_PATH
    else:
        output_base_dir = Path(output_base_dir)
    
    LOGGER_INFO("=" * 80)
    LOGGER_INFO("🔄 Syncing Control Datasets with Version Hierarchy")
    if version_dir_only:
        LOGGER_INFO("📌 Mode: Save to version directory ONLY (NOT root)")
    else:
        LOGGER_INFO("📌 Mode: Save to both version directory and root")
    LOGGER_INFO("=" * 80)
    LOGGER_INFO(f"Database path: {db_path}")
    LOGGER_INFO(f"Input file: {input_file}")
    LOGGER_INFO(f"Output base directory: {output_base_dir}")
    LOGGER_INFO("")
    
    result = {
        "success": False,
        "message": "",
        "db_version": None,
        "json_version": None,
        "created_dir": None,
        "copied_file": None
    }
    
    try:
        # 1. Get database app version
        LOGGER_INFO("📊 Step 1: Reading app version from database...")
        db_app_version = get_db_app_version(db_path)
        if not db_app_version:
            result["message"] = "Failed to read app version from database"
            LOGGER_ERROR(f"❌ {result['message']}")
            return result
        
        result["db_version"] = db_app_version
        LOGGER_INFO(f"   DB app version: {db_app_version}")
        
        # 2. Get JSON app version
        LOGGER_INFO("📊 Step 2: Reading app version from control_datasets.json...")
        if not input_file.exists():
            result["message"] = f"Input file not found: {input_file}"
            LOGGER_ERROR(f"❌ {result['message']}")
            return result
        
        with open(input_file, 'r', encoding='utf-8') as f:
            datasets = json.load(f)
        
        json_app_version = datasets.get('app_version', '')
        result["json_version"] = json_app_version
        LOGGER_INFO(f"   JSON app version: {json_app_version}")
        
        # 3. Compare versions (using X.Y.Z format)
        LOGGER_INFO("📊 Step 3: Comparing versions...")
        
        LOGGER_INFO(f"   DB version: {db_app_version}")
        LOGGER_INFO(f"   JSON version: {json_app_version}")
        
        # Extract major version (X.Y.Z) from full version (X.Y.Z.W)
        # Example: "46.3.0.33972" -> "46.3.0"
        def get_major_version(version):
            try:
                parts = version.split('.')
                if len(parts) >= 3:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}"
                return version
            except:
                return version
        
        major_version = get_major_version(db_app_version)
        LOGGER_INFO(f"   Major version (for directory): {major_version}")
        
        # 4. Check if output_base_dir is already a version directory (avoid nested version dirs)
        # Example: if output_base_dir is "46.3.0", don't create "46.3.0/46.3.0"
        output_dir_name = output_base_dir.name
        
        if output_dir_name == major_version:
            # Output directory is already the version directory
            LOGGER_INFO(f"📁 Step 4: Output directory is already the version directory: {output_base_dir}")
            version_dir = output_base_dir
        else:
            # Create version subdirectory under output_base_dir
            version_dir = output_base_dir / major_version
        
        version_dir_exists = version_dir.exists()
        
        if version_dir_exists:
            LOGGER_INFO(f"📁 Step 4a: Version directory already exists: {version_dir}")
            action = "updating"
        else:
            LOGGER_INFO(f"📁 Step 4b: Version directory does not exist, will create: {version_dir}")
            action = "creating"
        
        # 5. Create version-specific directory if it doesn't exist
        if not version_dir_exists:
            LOGGER_INFO(f"🔄 Step 5: Creating version directory...")
            version_dir.mkdir(parents=True, exist_ok=True)
            result["created_dir"] = str(version_dir)
            LOGGER_INFO(f"   ✅ Created directory: {version_dir}")
        else:
            LOGGER_INFO(f"🔄 Step 5: Skipping directory creation (already exists)")
            result["created_dir"] = str(version_dir)
        
        # 6. Create/Update version-specific control_datasets.json
        LOGGER_INFO(f"📝 Step 6: {action.capitalize()} control_datasets.json...")
        LOGGER_INFO(f"   📌 version_dir_only flag: {version_dir_only}")
        if version_dir_only:
            LOGGER_INFO(f"   📌 Saving ONLY to version directory (not root): {version_dir}")
        else:
            LOGGER_INFO(f"   📌 Will update both version directory and root directory")
        
        # Get qtversion from database if available
        db_qtversion = get_db_qtversion(db_path)
        LOGGER_INFO(f"   📊 Retrieved qtversion from DB: {db_qtversion}")
        # Get arch from database if available
        db_arch = get_db_arch(db_path)
        LOGGER_INFO(f"   📊 Retrieved architecture from DB: {db_arch}")
        
        # If architecture is arm64, force qtversion to 6.8
        if db_arch and db_arch.lower() == "arm64":
            LOGGER_INFO(f"   🔄 Architecture is arm64, setting qtversion to 6.8")
            db_qtversion = "6.8"

        # Create a new ordered dict with app_version at the top
        from collections import OrderedDict
        ordered_datasets = OrderedDict()
        ordered_datasets['app_version'] = db_app_version
        
        # Add the rest of the datasets
        for key, value in datasets.items():
            if key != 'app_version':
                ordered_datasets[key] = value
        
        datasets = ordered_datasets
        
        # Determine the filename based on qtversion
        if db_qtversion == "6.8":
            # If qtversion is 6.8, create qtversion-specific JSON file (preserve original control_datasets.json)
            version_datasets_file = version_dir / f"control_datasets_qt{db_qtversion}.json"
            LOGGER_INFO(f"   📌 Using qtversion-specific filename: control_datasets_qt{db_qtversion}.json")
            if not version_dir_only:
                LOGGER_INFO(f"   📌 Original control_datasets.json will be preserved in root")
            
            # Save to version directory
            with open(version_datasets_file, 'w', encoding='utf-8') as f:
                json.dump(datasets, f, indent=4, ensure_ascii=False)
            
            result["qtversion"] = db_qtversion
            LOGGER_INFO(f"   ✅ Created/Updated qtversion-specific file: {version_datasets_file}")
        else:
            # If qtversion is other value or not present, directly update the default control_datasets.json
            version_datasets_file = version_dir / "control_datasets.json"
            if db_qtversion:
                LOGGER_INFO(f"   📌 qtversion is {db_qtversion} (not 6.8), updating default control_datasets.json")
            else:
                LOGGER_INFO(f"   📌 Using default filename: control_datasets.json")
            
            # Save to version directory (always update)
            with open(version_datasets_file, 'w', encoding='utf-8') as f:
                json.dump(datasets, f, indent=4, ensure_ascii=False)
            LOGGER_INFO(f"   ✅ Updated file in version directory: {version_datasets_file}")
            
            # Only update root directory file if version_dir_only is False
            if not version_dir_only:
                root_file = input_file
                LOGGER_INFO(f"   📝 Also updating root directory file: {root_file}")
                with open(root_file, 'w', encoding='utf-8') as f:
                    json.dump(datasets, f, indent=4, ensure_ascii=False)
                LOGGER_INFO(f"   ✅ Updated root directory file: {root_file}")
        
        result["copied_file"] = str(version_datasets_file)
        LOGGER_INFO(f"   📂 Primary dataset file location: {version_datasets_file}")
        
        LOGGER_INFO("")
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("✅ Version Sync Completed Successfully!")
        LOGGER_INFO("=" * 80)
        LOGGER_INFO(f"Database version: {db_app_version}")
        if db_qtversion:
            LOGGER_INFO(f"Qt version: {db_qtversion}")
        LOGGER_INFO(f"Action: {action.upper()}")
        LOGGER_INFO(f"Version directory: {version_dir}")
        LOGGER_INFO(f"Dataset file: {version_datasets_file}")
        if not version_dir_only:
            LOGGER_INFO(f"Root file: {input_file}")
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("")
        
        result["success"] = True
        result["message"] = f"Successfully {action}: {db_app_version}" + (" (version dir only)" if version_dir_only else "")
        return result
        
    except json.JSONDecodeError as e:
        result["message"] = f"Failed to parse JSON: {e}"
        LOGGER_ERROR(f"❌ {result['message']}")
        return result
    except Exception as e:
        result["message"] = f"Error during sync: {e}"
        LOGGER_ERROR(f"❌ {result['message']}")
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        return result

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Control Datasets Generator')
    parser.add_argument('--mode', choices=['incremental', 'reset'], default='incremental',
                      help='Generation mode: incremental (default) or reset')
    parser.add_argument('--force-reset', action='store_true',
                      help='Force reset mode (same as --mode reset)')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to YAML config file (default: test_suites/navigate.yaml)')
    parser.add_argument('--platform', type=str, default=None,
                      help='Override platform from config (windows, mac, web)')
    parser.add_argument('--project', type=str, default=None,
                      help='Override project from config (e.g., webex_app, webex_web)')
    parser.add_argument('--skip-main-db', action='store_true',
                      help='Skip main DB (DATASETS_PATH) and only use DATASETS_SPECIFIC_PATH')
    parser.add_argument('--skip-custom-metadata', action='store_true',
                      help='Skip custom_control_metadata.json')
    parser.add_argument('--no-auto-clean', action='store_true',
                      help='Disable automatic cleaning of dynamic controls after generation')
    parser.add_argument('--extract-name-as-key', action='store_true',
                      help='Extract name as key from metadata files and save as key-value JSON format')
    parser.add_argument('--extract-input', type=str, default=None,
                      help='Input file path for name extraction (default: control_metadata.json)')
    parser.add_argument('--extract-output', type=str, default=None,
                      help='Output file path for name extraction (default: input_file_keyed.json)')
    parser.add_argument('--sync-from-db', action='store_true',
                      help='Sync metadata JSON file with latest data from database')
    parser.add_argument('--db-path', type=str, default=None,
                      help='Database path for sync operation (default: DATASETS_PATH from config)')
    parser.add_argument('--metadata-file', type=str, default=None,
                      help='Metadata file path to sync (default: control_metadata.json)')
    parser.add_argument('--sync-output', type=str, default=None,
                      help='Output file path for synced metadata (default: update in place)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Dry run mode - show changes without modifying files')
    parser.add_argument('--version-dir-only', action='store_true',
                      help='Save synced files ONLY to version directory (do NOT update root directory file)')
    parser.add_argument('--add-images', action='store_true',
                      help='Add images to existing metadata from database')
    parser.add_argument('--add-images-output', type=str, default=None,
                      help='Output file path when adding images (default: update in place with backup)')
    parser.add_argument('--generate-metadata', action='store_true',
                      help='Generate new metadata from database')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path for generated metadata')
    parser.add_argument('--add-ui-path', action='store_true',
                      help='Add UI path information to control_datasets.json')
    parser.add_argument('--ui-path-input', type=str, default=None,
                      help='Input file for UI path generation (default: control_datasets.json)')
    parser.add_argument('--ui-path-output', type=str, default=None,
                      help='Output file for UI path generation (default: control_datasets_with_ui_path.json)')
    parser.add_argument('--ui-path-db', type=str, default=None,
                      help='Database path for UI path generation (default: test_space/datasets/data/ControlINFO.db)')
    parser.add_argument('--start-index', type=int, default=None,
                      help='Start index for slicing UI path')
    args = parser.parse_args()
    
    # Handle add UI path mode
    if args.add_ui_path:
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("🛤️  Adding UI Path Information to Control Datasets")
        LOGGER_INFO("=" * 80)
        
        # Get platform from config or command line
        if args.platform:
            ui_path_platform = args.platform.lower()
        else:
            ui_path_platform = get_platform_from_config(args.config)
        
        # Generate control datasets with UI path
        try:
            stats = generate_control_datasets_with_ui_path(
                input_file=args.ui_path_input,
                output_file=args.ui_path_output,
                db_path=args.ui_path_db,
                start_index=args.start_index,
                platform=ui_path_platform
            )
            
            if "error" in stats:
                LOGGER_ERROR("=" * 80)
                LOGGER_ERROR("❌ UI Path Generation Failed!")
                LOGGER_ERROR(f"Error: {stats['error']}")
                LOGGER_ERROR("=" * 80)
                sys.exit(1)
            else:
                LOGGER_INFO("=" * 80)
                LOGGER_INFO("✅ UI Path Generation Completed Successfully!")
                LOGGER_INFO("=" * 80)
        except Exception as e:
            LOGGER_ERROR("=" * 80)
            LOGGER_ERROR("❌ UI Path Generation Failed!")
            LOGGER_ERROR(f"Error: {str(e)}")
            LOGGER_ERROR("=" * 80)
            import traceback
            LOGGER_ERROR(traceback.format_exc())
            sys.exit(1)
        
        # Exit after UI path generation
        sys.exit(0)
    
    # Handle generate metadata mode
    if args.generate_metadata:
        from rs_sdk.utils.control_datasets_generator import ControlDatasetsGenerator
        
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("📝 Generating New Metadata from Database")
        LOGGER_INFO("=" * 80)
        
        # Determine paths
        if args.db_path:
            db_path = Path(args.db_path)
        else:
            db_path = Path(DATASETS_PATH)
        
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = CONTROL_METADATA_PATH
        
        LOGGER_INFO(f"Database: {db_path}")
        LOGGER_INFO(f"Output file: {output_file}")
        LOGGER_INFO("")
        
        try:
            generator = ControlDatasetsGenerator()
            generator.generate_control_metadata_from_dataset(
                db_path=str(db_path),
                output_json_path=str(output_file),
                use_key_value_format=True  # Always use key-value format
            )
            
            LOGGER_INFO("")
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("✅ Metadata Generation Completed Successfully!")
            LOGGER_INFO("Format: Key-Value (dict)")
            LOGGER_INFO("=" * 80)
            
            # Auto-clean dynamic content from keys after generation
            LOGGER_INFO("")
            LOGGER_INFO("🧹 Auto-cleaning dynamic content from generated keys...")
            try:
                changes_count, removed_count = clean_dataset_keys(str(output_file), output_file=None, verbose=True)
                if changes_count > 0 or removed_count > 0:
                    LOGGER_INFO(f"✅ Cleaned {changes_count} keys, removed {removed_count} empty entries!")
                else:
                    LOGGER_INFO("✅ No keys needed cleaning")
            except Exception as e:
                LOGGER_WARNING(f"⚠️  Auto-cleaning failed: {e}, continuing with uncleaned data")
        except Exception as e:
            LOGGER_ERROR("=" * 80)
            LOGGER_ERROR("❌ Metadata Generation Failed!")
            LOGGER_ERROR(f"Error: {str(e)}")
            LOGGER_ERROR("=" * 80)
            import traceback
            LOGGER_ERROR(traceback.format_exc())
            sys.exit(1)
        
        # Exit after generation
        sys.exit(0)
    
    # Handle add images mode
    if args.add_images:
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("🖼️  Adding Images to Existing Metadata")
        LOGGER_INFO("=" * 80)
        
        # Determine paths
        if args.db_path:
            db_path = Path(args.db_path)
        else:
            db_path = Path(DATASETS_PATH)
        
        if args.metadata_file:
            metadata_file = Path(args.metadata_file)
        else:
            metadata_file = CONTROL_METADATA_PATH
        
        output_file = Path(args.add_images_output) if args.add_images_output else None
        
        # Get platform from config or command line
        if args.platform:
            add_images_platform = args.platform.lower()
        else:
            add_images_platform = get_platform_from_config(args.config)
        
        LOGGER_INFO(f"Database: {db_path}")
        LOGGER_INFO(f"Metadata file: {metadata_file}")
        LOGGER_INFO(f"Output file: {output_file if output_file else 'Update in place (with backup)'}")
        LOGGER_INFO(f"Platform: {add_images_platform}")
        LOGGER_INFO("")
        
        try:
            stats = add_images_to_existing_metadata(
                db_path=str(db_path),
                metadata_file_path=str(metadata_file),
                output_file_path=str(output_file) if output_file else None,
                platform=add_images_platform
            )
            
            if stats['errors'] > 0:
                LOGGER_WARNING("=" * 80)
                LOGGER_WARNING(f"⚠️  Completed with {stats['errors']} errors")
                LOGGER_WARNING("=" * 80)
            else:
                LOGGER_INFO("=" * 80)
                LOGGER_INFO("✅ Add Images Completed Successfully!")
                LOGGER_INFO("=" * 80)
        except Exception as e:
            LOGGER_ERROR("=" * 80)
            LOGGER_ERROR("❌ Add Images Failed!")
            LOGGER_ERROR(f"Error: {str(e)}")
            LOGGER_ERROR("=" * 80)
            import traceback
            LOGGER_ERROR(traceback.format_exc())
            sys.exit(1)
        
        # Exit after adding images
        sys.exit(0)
    
    # Handle DB sync mode
    if args.sync_from_db:
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("🔄 Syncing Control Datasets from Database")
        LOGGER_INFO("=" * 80)
        
        # Determine paths
        if args.db_path:
            db_path = Path(args.db_path)
        else:
            db_path = Path(DATASETS_PATH)
        
        # NEW: If metadata_file not provided, get app_version from db and construct path
        # Default to control_datasets.json (not control_metadata.json)
        if args.metadata_file:
            metadata_file = Path(args.metadata_file)
        else:
            # Read app_version from database
            LOGGER_INFO("📊 Reading app version from database to determine metadata file location...")
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT AppVersion FROM ControlINFO WHERE AppVersion IS NOT NULL ORDER BY TabOrder DESC LIMIT 1")
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    db_app_version = result[0].strip()
                    LOGGER_INFO(f"✅ Found app version in DB: {db_app_version}")
                    # Construct path to version directory
                    version_dir = Path(TEST_CONTROL_DATASET_FOLDER_PATH) / db_app_version
                    version_metadata_file = version_dir / "control_datasets.json"
                    
                    if version_metadata_file.exists():
                        metadata_file = version_metadata_file
                        LOGGER_INFO(f"✅ Found metadata file in version directory: {metadata_file}")
                    else:
                        # Fallback to root directory - use control_datasets.json for syncing dataset hierarchy
                        metadata_file = CONTROL_DEFAULT_DATASET_PATH
                        LOGGER_INFO(f"⚠️  Version metadata not found, using root directory: {metadata_file}")
                else:
                    LOGGER_WARNING("⚠️ No AppVersion found in database, using default path")
                    metadata_file = CONTROL_DEFAULT_DATASET_PATH
            except Exception as e:
                LOGGER_WARNING(f"⚠️ Error reading app version from database: {e}, using default path")
                metadata_file = CONTROL_DEFAULT_DATASET_PATH
        
        output_file = Path(args.sync_output) if args.sync_output else None
        
        # Get platform from config or command line
        if args.platform:
            sync_platform = args.platform.lower()
        else:
            sync_platform = get_platform_from_config(args.config)
        
        LOGGER_INFO(f"Database: {db_path}")
        LOGGER_INFO(f"Metadata file: {metadata_file}")
        LOGGER_INFO(f"Output file: {output_file if output_file else 'Update in place'}")
        LOGGER_INFO(f"Platform: {sync_platform}")
        LOGGER_INFO(f"Dry run: {args.dry_run}")
        LOGGER_INFO("")
        
        try:
            stats = sync_metadata_from_db(
                db_path=db_path,
                metadata_file_path=metadata_file,
                output_file_path=output_file,
                platform=sync_platform,
                dry_run=args.dry_run
            )
            
            if "error" in stats:
                LOGGER_ERROR("=" * 80)
                LOGGER_ERROR("❌ Sync Failed!")
                LOGGER_ERROR(f"Error: {stats['error']}")
                LOGGER_ERROR("=" * 80)
                sys.exit(1)
            else:
                LOGGER_INFO("=" * 80)
                LOGGER_INFO("✅ Sync Completed Successfully!")
                LOGGER_INFO("=" * 80)
                
                # Auto-clean dynamic content from keys after sync (unless dry run)
                if not args.dry_run:
                    LOGGER_INFO("")
                    LOGGER_INFO("🧹 Auto-cleaning dynamic content from synced keys...")
                    try:
                        # Clean the output file (or metadata file if no output specified)
                        file_to_clean = output_file if output_file else metadata_file
                        changes_count, removed_count = clean_dataset_keys(str(file_to_clean), output_file=None, verbose=True)
                        if changes_count > 0 or removed_count > 0:
                            LOGGER_INFO(f"✅ Cleaned {changes_count} keys, removed {removed_count} empty entries!")
                        else:
                            LOGGER_INFO("✅ No keys needed cleaning")
                    except Exception as e:
                        LOGGER_WARNING(f"⚠️  Auto-cleaning failed: {e}, continuing with uncleaned data")
                
                # NEW: Sync version hierarchy after metadata sync
                LOGGER_INFO("")
                LOGGER_INFO("=" * 80)
                LOGGER_INFO("🔄 Syncing Control Datasets Version Hierarchy")
                LOGGER_INFO("=" * 80)
                try:
                    # Use the synced metadata file as input for version hierarchy sync
                    # The file_to_clean is the one we just synced and cleaned
                    file_for_version_sync = output_file if output_file else metadata_file
                    
                    version_result = sync_control_datasets_with_version_hierarchy(
                        db_path=db_path,
                        input_file=file_for_version_sync,
                        output_base_dir=file_for_version_sync.parent if hasattr(file_for_version_sync, 'parent') else Path(file_for_version_sync).parent,
                        force_regenerate=False,
                        version_dir_only=args.version_dir_only
                    )
                    
                    if version_result['success']:
                        LOGGER_INFO("✅ Version hierarchy sync completed!")
                        LOGGER_INFO(f"   DB Version: {version_result['db_version']}")
                        LOGGER_INFO(f"   JSON Version: {version_result['json_version']}")
                        if version_result['created_dir']:
                            LOGGER_INFO(f"   Created Directory: {version_result['created_dir']}")
                            LOGGER_INFO(f"   Saved File: {version_result['copied_file']}")
                    else:
                        LOGGER_WARNING(f"⚠️  Version hierarchy sync: {version_result['message']}")
                except Exception as e:
                    LOGGER_WARNING(f"⚠️  Version hierarchy sync failed: {e}")
                    LOGGER_DEBUG(f"Details: {str(e)}")
        except Exception as e:
            LOGGER_ERROR("=" * 80)
            LOGGER_ERROR("❌ Sync Failed!")
            LOGGER_ERROR(f"Error: {str(e)}")
            LOGGER_ERROR("=" * 80)
            raise
        
        # Exit after sync
        sys.exit(0)
    
    # Handle name extraction mode
    if args.extract_name_as_key:
        LOGGER_INFO("=" * 80)
        LOGGER_INFO("🔑 Extracting Name as Key from Metadata JSON")
        LOGGER_INFO("=" * 80)
        
        # Determine input file
        if args.extract_input:
            input_file = Path(args.extract_input)
        else:
            input_file = CONTROL_METADATA_PATH
        
        # Determine output file
        output_file = Path(args.extract_output) if args.extract_output else None
        
        LOGGER_INFO(f"Input file: {input_file}")
        LOGGER_INFO(f"Output file: {output_file if output_file else 'Auto-generated'}")
        LOGGER_INFO("")
        
        try:
            extract_name_as_key_json(input_file, output_file)
            LOGGER_INFO("=" * 80)
            LOGGER_INFO("✅ Name Extraction Completed Successfully!")
            LOGGER_INFO("=" * 80)
        except Exception as e:
            LOGGER_ERROR("=" * 80)
            LOGGER_ERROR("❌ Name Extraction Failed!")
            LOGGER_ERROR(f"Error: {str(e)}")
            LOGGER_ERROR("=" * 80)
            raise
        
        # Exit after extraction
        sys.exit(0)
    
    # Determine mode
    incremental_mode = not args.force_reset and args.mode == 'incremental'
    mode_str = "Incremental" if incremental_mode else "Reset"
    
    # Get platform from config file or command line override
    if args.platform:
        # Command line override
        platform_filter = args.platform.lower()
        valid_platforms = ['windows', 'mac', 'web']
        if platform_filter not in valid_platforms:
            LOGGER_ERROR(f"Invalid platform: {platform_filter}")
            LOGGER_ERROR(f"Valid platforms are: {valid_platforms}")
            sys.exit(1)
        LOGGER_INFO(f"Using platform from command line: {platform_filter}")
    else:
        # Read from config file
        platform_filter = get_platform_from_config(args.config)
    
    # Get project from config file or command line override
    if args.project:
        # Command line override
        project_name = args.project
        LOGGER_INFO(f"Using project from command line: {project_name}")
    else:
        # Read from config file
        project_name = get_project_from_config(args.config)
    
    # Determine output dataset filename
    if project_name and platform_filter:
        output_dataset_filename = f"control_datasets_{project_name}_{platform_filter}.json"
    else:
        output_dataset_filename = "control_datasets.json"
    
    LOGGER_INFO("=" * 80)
    LOGGER_INFO(f"🚀 Starting {mode_str} Control Datasets Generation")
    LOGGER_INFO("=" * 80)
    
    LOGGER_INFO("📂 File Paths:")
    LOGGER_INFO(f"   Main DB: {DATASETS_PATH}")
    LOGGER_INFO(f"   Specific DB: {DATASETS_SPECIFIC_PATH}")
    LOGGER_INFO(f"   Control Metadata: {CONTROL_METADATA_PATH}")
    LOGGER_INFO(f"   Specific Metadata: {CONTROL_SPECIFIC_METADATA_PATH}")
    LOGGER_INFO(f"   Custom Metadata: {CUSTOM_CONTROL_METADATA_PATH}")
    LOGGER_INFO(f"   Output Dataset: {TEST_CONTROL_DATASET_FOLDER_PATH / output_dataset_filename}")
    LOGGER_INFO("")
    
    LOGGER_INFO("🔧 Configuration:")
    LOGGER_INFO(f"   Mode: {mode_str}")
    LOGGER_INFO(f"   Platform: {platform_filter}")
    LOGGER_INFO(f"   Project: {project_name if project_name else 'default'}")
    LOGGER_INFO(f"   Skip Main DB: {args.skip_main_db}")
    LOGGER_INFO(f"   Skip Custom Metadata: {args.skip_custom_metadata}")
    LOGGER_INFO(f"   Auto-clean Dynamic Controls: {not args.no_auto_clean}")
    LOGGER_INFO("")
    
    if incremental_mode:
        LOGGER_INFO("📋 Incremental Generation Rules:")
        LOGGER_INFO("   1. Load existing control_datasets.json as baseline")
        LOGGER_INFO("   2. Check DB availability and generate/use source metadata")
        LOGGER_INFO("   3. Smart merge by priority: existing < base < specific < custom")
        LOGGER_INFO("   4. Ensure name uniqueness and preserve existing data")
        LOGGER_INFO("   5. Incrementally save with backup creation")
    else:
        LOGGER_INFO("📋 Reset Generation Rules:")
        LOGGER_INFO("   1. Check DB availability and generate/use source metadata")
        LOGGER_INFO("   2. Priority merge: base < specific < custom")
        LOGGER_INFO("   3. Reset and save final control_datasets.json")
    LOGGER_INFO("")

    try:
        # Generate control metadata with platform, project, skip flags, and auto-clean setting
        control_datasets_generator(
            incremental_mode=incremental_mode, 
            platform=platform_filter, 
            project=project_name,
            skip_main_db=args.skip_main_db,
            skip_custom_metadata=args.skip_custom_metadata,
            auto_clean=not args.no_auto_clean
        )
        
        LOGGER_INFO("=" * 80)
        LOGGER_INFO(f"✅ {mode_str} Control Datasets Generation Completed Successfully!")
        LOGGER_INFO("=" * 80)
        
    except Exception as e:
        LOGGER_ERROR("=" * 80)
        LOGGER_ERROR(f"❌ {mode_str} Control Datasets Generation Failed!")
        LOGGER_ERROR(f"Error: {str(e)}")
        LOGGER_ERROR("=" * 80)
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        raise



import json
import os
from config.paths import CONTROL_DEFAULT_DATASET_PATH, TEST_CONTROL_DATASET_FOLDER_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING
from pathlib import Path

# Global variables for control datasets (will be loaded dynamically)
CONTROL_ID_JSON = []
CONTROL_NAME_MAP = {}
_current_dataset_path = None


def get_app_version_from_settings():
    """
    Read app version from settings.json file.
    
    Returns:
        str: App version string (e.g., '46.3.0.33960') or None if not found
    """
    try:
        from config.paths import SETTINGS_PATH
        
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            app_version = settings.get('appVersion')
            if app_version:
                LOGGER_DEBUG(f"Read appVersion from settings.json: {app_version}")
                return app_version
        else:
            LOGGER_DEBUG(f"settings.json not found at {SETTINGS_PATH}")
    except Exception as e:
        LOGGER_DEBUG(f"Error reading appVersion from settings.json: {e}")
    
    return None


def get_major_version_from_full_version(full_version):
    """
    Extract major version (X.Y.Z) from full version string (X.Y.Z.W).
    
    Args:
        full_version (str): Full version string (e.g., '46.3.0.33960')
        
    Returns:
        str: Major version (e.g., '46.3.0') or None if cannot extract
    """
    if not full_version:
        return None
    
    try:
        parts = full_version.split('.')
        if len(parts) >= 3:
            major_version = f"{parts[0]}.{parts[1]}.{parts[2]}"
            LOGGER_DEBUG(f"Extracted major version {major_version} from {full_version}")
            return major_version
    except Exception as e:
        LOGGER_DEBUG(f"Error extracting major version from {full_version}: {e}")
    
    return None


def get_version_directory_for_dataset():
    """
    Get version directory for loading dataset from app version in settings.json.
    
    Strategy:
    1. Read appVersion from settings.json (e.g., '46.3.0.33960')
    2. Extract major version (e.g., '46.3.0')
    3. Check if version directory exists
    4. Return version string if found, None otherwise
    
    Returns:
        str: Version string (e.g., '46.3.0') or None if not found
    """
    app_version = get_app_version_from_settings()
    if not app_version:
        return None
    
    major_version = get_major_version_from_full_version(app_version)
    if not major_version:
        return None
    
    # Check if version directory exists
    version_dir = Path(TEST_CONTROL_DATASET_FOLDER_PATH) / major_version
    if version_dir.exists():
        LOGGER_INFO(f"Found version directory for {major_version}: {version_dir}", "CYAN")
        return major_version
    else:
        LOGGER_DEBUG(f"Version directory does not exist: {version_dir}")
        return None


def get_qtversion_from_settings():
    """
    Read Qt version from settings.json file.
    
    Returns:
        str: Qt version string (e.g., '6.8') or None if not found
    """
    try:
        from config.paths import SETTINGS_PATH
        
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Try to get qtversion from installOptions
            install_options = settings.get('installOptions', {})
            qtversion = install_options.get('qtversion')
            if qtversion:
                LOGGER_DEBUG(f"Read qtversion from settings.json: {qtversion}")
                # Normalize format: "6" or "68" should be treated as Qt 6 (not 6.8 unless explicitly needed)
                # Return raw value for accurate matching
                return str(qtversion)
        else:
            LOGGER_DEBUG(f"settings.json not found at {SETTINGS_PATH}")
    except Exception as e:
        LOGGER_DEBUG(f"Error reading qtversion from settings.json: {e}")
    
    return None


def get_arch_from_settings():
    """
    Read architecture from settings.json file.
    
    Returns:
        str: Architecture string (e.g., 'x64', 'arm64') or None if not found
    """
    try:
        from config.paths import SETTINGS_PATH
        
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Try to get arch from installOptions
            install_options = settings.get('installOptions', {})
            arch = install_options.get('arch')
            if arch:
                LOGGER_DEBUG(f"Read arch from settings.json: {arch}")
                return arch
        else:
            LOGGER_DEBUG(f"settings.json not found at {SETTINGS_PATH}")
    except Exception as e:
        LOGGER_DEBUG(f"Error reading arch from settings.json: {e}")
    
    return None


def get_control_dataset_path(project=None, platform=None, custom_dataset=None, auto_detect_version=True):
    """
    Get the control dataset path based on project, platform, or custom dataset name.
    Optionally auto-detects version from settings.json.
    
    Args:
        project (str): Project name (e.g., 'webex_app', 'webex_web')
        platform (str): Platform name (e.g., 'windows', 'mac', 'web')
        custom_dataset (str): Custom dataset name (e.g., 'core/go_to_core_controls' for go_to_core_controls.json in core folder)
        auto_detect_version (bool): If True, auto-detect version from settings.json appVersion field
        
    Returns:
        Path: Path to the control dataset file. Priority:
              1. custom_dataset (if specified, with version directory if available)
              2. Version-specific control_datasets_qt6.8.json (only when arch=arm64 OR qtversion explicitly set to 6.8)
              3. Version-specific control_datasets.json (if auto_detect_version=True and version directory exists)
              4. control_datasets_{project}_{platform}.json (if project and platform specified)
              5. CONTROL_DEFAULT_DATASET_PATH (fallback)
    """
    # Get version directory if auto-detection is enabled
    version_dir = None
    if auto_detect_version:
        version = get_version_directory_for_dataset()
        if version:
            version_dir = Path(TEST_CONTROL_DATASET_FOLDER_PATH) / version
    
    # Get qtversion and arch from settings
    qtversion = get_qtversion_from_settings()
    arch = get_arch_from_settings()
    
    # Only use Qt 6.8 dataset in specific cases:
    # 1. Linux arm64 (always uses Qt 6.8)
    # 2. Architecture is arm64 (always uses Qt 6.8)
    # 3. Qt version is explicitly "6.8" (not "6" or other values)
    use_qt68_dataset = False
    normalized_platform = str(platform).lower() if platform else None
    if normalized_platform == "linux":
        LOGGER_DEBUG("Platform is linux, will use Qt 6.8 dataset")
        use_qt68_dataset = True
    elif arch and arch.lower() == "arm64":
        LOGGER_DEBUG(f"Architecture is arm64, will use Qt 6.8 dataset")
        use_qt68_dataset = True
    elif qtversion and str(qtversion) == "6.8":
        LOGGER_DEBUG(f"Qt version explicitly set to 6.8, will use Qt 6.8 dataset")
        use_qt68_dataset = True
    else:
        if qtversion:
            LOGGER_DEBUG(f"Qt version is {qtversion} (not 6.8), will use default dataset")
        if arch:
            LOGGER_DEBUG(f"Architecture is {arch} (not arm64), will use default dataset")
    
    # Priority 1: Custom dataset (with version if available)
    if custom_dataset:
        # Support both with and without .json extension
        if not custom_dataset.endswith('.json'):
            custom_dataset = f"{custom_dataset}.json"
        
        # Try version-specific custom dataset first
        if version_dir:
            versioned_dataset_path = version_dir / custom_dataset
            if versioned_dataset_path.exists():
                LOGGER_DEBUG(f"Found version-specific custom dataset: {versioned_dataset_path}")
                return versioned_dataset_path
        
        # Fall back to root directory custom dataset
        dataset_path = Path(TEST_CONTROL_DATASET_FOLDER_PATH) / custom_dataset
        if dataset_path.exists():
            LOGGER_DEBUG(f"Found custom dataset in root: {dataset_path}")
            return dataset_path
        else:
            LOGGER_WARNING(f"Custom dataset not found: {dataset_path}, falling back to default")
    
    # Priority 2: Version-specific dataset (if version directory found)
    if version_dir:
        # Priority 2a: Try Qt version-specific file only if explicitly needed
        if use_qt68_dataset:
            versioned_qt_file = version_dir / "control_datasets_qt6.8.json"
            if versioned_qt_file.exists():
                LOGGER_INFO(f"Using Qt 6.8-specific dataset from: {versioned_qt_file}", "CYAN")
                return versioned_qt_file
            else:
                LOGGER_DEBUG(f"Qt 6.8-specific dataset not found: {versioned_qt_file}, trying default")
        
        # Priority 2b: Try version-specific project/platform file if specified
        if project and platform:
            versioned_project_file = version_dir / f"control_datasets_{project}_{platform}.json"
            if versioned_project_file.exists():
                LOGGER_DEBUG(f"Found version-specific project dataset: {versioned_project_file}")
                return versioned_project_file
        
        # Priority 2c: Try default control_datasets.json in version directory
        versioned_default_file = version_dir / "control_datasets.json"
        if versioned_default_file.exists():
            LOGGER_INFO(f"Using version-specific dataset from: {versioned_default_file}", "CYAN")
            return versioned_default_file
    
    # Priority 3: Project and platform specific dataset
    if project and platform:
        dataset_filename = f"control_datasets_{project}_{platform}.json"
        dataset_path = Path(TEST_CONTROL_DATASET_FOLDER_PATH) / dataset_filename
        
        # Check if the specific dataset exists, otherwise fallback to default
        if dataset_path.exists():
            LOGGER_DEBUG(f"Found project-specific dataset: {dataset_path}")
            return dataset_path
        else:
            # Fallback to default dataset
            LOGGER_DEBUG(f"Project-specific dataset not found: {dataset_path}, using default")
            return CONTROL_DEFAULT_DATASET_PATH
    
    # Priority 4: Default dataset
    return CONTROL_DEFAULT_DATASET_PATH


def load_control_datasets(project=None, platform=None, custom_dataset=None, force_reload=False):
    """
    Load control datasets dynamically based on project, platform, or custom dataset.
    
    Automatically detects version from settings.json appVersion field and loads
    version-specific datasets if available.
    
    Args:
        project (str): Project name (e.g., 'webex_app', 'webex_web')
        platform (str): Platform name (e.g., 'windows', 'mac', 'web')
        custom_dataset (str): Custom dataset name (e.g., 'core/go_to_core_controls')
        force_reload (bool): Force reload even if already loaded
        
    Returns:
        bool: True if successfully loaded, False otherwise
        
    Note:
        Version auto-detection strategy:
        1. Reads 'appVersion' from settings.json (e.g., '46.3.0.33960')
        2. Extracts major version (e.g., '46.3.0')
        3. Checks if version directory exists (e.g., 'datasets/46.3.0/')
        4. Loads control_datasets.json from version directory if it exists
        5. Falls back to root directory if no version directory found
    """
    global CONTROL_ID_JSON, CONTROL_NAME_MAP, _current_dataset_path
    
    # Get the dataset path (with auto-detection of version from settings.json)
    dataset_path = get_control_dataset_path(project, platform, custom_dataset, auto_detect_version=True)
    
    # Check if we need to reload
    if not force_reload and _current_dataset_path == dataset_path and CONTROL_ID_JSON:
        LOGGER_DEBUG(f"Dataset already loaded from {dataset_path}")
        return True
    
    # Load the dataset
    try:
        if os.path.exists(dataset_path) and os.path.getsize(dataset_path) > 0:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Auto-detect format and build CONTROL_NAME_MAP
            if isinstance(data, dict):
                # Key-Value format: {name: {metadata: ...}}
                # Filter out non-dict values (like app_version)
                CONTROL_NAME_MAP = {k: v for k, v in data.items() if isinstance(v, dict)}
                # Build CONTROL_ID_JSON from dict values (add 'name' field back)
                CONTROL_ID_JSON = []
                for name, value in CONTROL_NAME_MAP.items():
                    entry = {"name": name}
                    entry.update(value)
                    CONTROL_ID_JSON.append(entry)
            elif isinstance(data, list):
                # Array format: [{name: ..., metadata: ...}, ...]
                CONTROL_ID_JSON = data
                CONTROL_NAME_MAP = {entry["name"]: entry for entry in CONTROL_ID_JSON if isinstance(entry, dict)}
            else:
                LOGGER_WARNING(f"Unexpected data format in {dataset_path}: {type(data)}")
                CONTROL_ID_JSON = []
                CONTROL_NAME_MAP = {}
                _current_dataset_path = None
                return False
            
            _current_dataset_path = dataset_path
            
            # Log the loaded dataset info with version info if applicable
            dataset_dir = Path(dataset_path).parent.name
            if dataset_dir and dataset_dir[0].isdigit():
                # This is a version directory
                LOGGER_INFO(f"✅ Loaded {len(CONTROL_ID_JSON)} control entries from version {dataset_dir}: {Path(dataset_path).name}")
            else:
                if custom_dataset:
                    LOGGER_INFO(f"✅ Loaded {len(CONTROL_ID_JSON)} control entries from custom dataset: {Path(dataset_path).name}")
                elif project and platform:
                    LOGGER_INFO(f"✅ Loaded {len(CONTROL_NAME_MAP)} control entries from {Path(dataset_path).name} (project: {project}, platform: {platform})")
                else:
                    LOGGER_INFO(f"✅ Loaded {len(CONTROL_NAME_MAP)} control entries from default dataset: {Path(dataset_path).name}")
            
            return True
        else:
            LOGGER_WARNING(f"Control datasets file is empty or missing: {dataset_path}")
            LOGGER_WARNING("Control metadata lookup will return None for all queries until the file is generated.")
            CONTROL_ID_JSON = []
            CONTROL_NAME_MAP = {}
            _current_dataset_path = None
            return False
    except (json.JSONDecodeError, FileNotFoundError) as e:
        LOGGER_WARNING(f"Failed to load control datasets from {dataset_path}: {e}")
        LOGGER_WARNING("Control metadata lookup will return None for all queries until the file is generated.")
        CONTROL_ID_JSON = []
        CONTROL_NAME_MAP = {}
        _current_dataset_path = None
        return False


# Initialize with default dataset on module import
try:
    if os.path.exists(CONTROL_DEFAULT_DATASET_PATH) and os.path.getsize(CONTROL_DEFAULT_DATASET_PATH) > 0:
        with open(CONTROL_DEFAULT_DATASET_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Auto-detect format and build CONTROL_NAME_MAP
        if isinstance(data, dict):
            # Key-Value format: {name: {metadata: ...}}
            CONTROL_NAME_MAP = data
            # Build CONTROL_ID_JSON from dict values (add 'name' field back)
            CONTROL_ID_JSON = []
            for name, value in data.items():
                # Skip non-dict values (e.g., "app_version" string field)
                if not isinstance(value, dict):
                    continue
                entry = {"name": name}
                entry.update(value)
                CONTROL_ID_JSON.append(entry)
            LOGGER_DEBUG(f"Loaded {len(CONTROL_NAME_MAP)} control entries (Key-Value format) from: {CONTROL_DEFAULT_DATASET_PATH}")
        elif isinstance(data, list):
            # Array format: [{name: ..., metadata: ...}, ...]
            CONTROL_ID_JSON = data
            CONTROL_NAME_MAP = {entry["name"]: entry for entry in CONTROL_ID_JSON}
            LOGGER_DEBUG(f"Loaded {len(CONTROL_ID_JSON)} control entries (Array format) from: {CONTROL_DEFAULT_DATASET_PATH}")
        else:
            LOGGER_WARNING(f"Unexpected data format in {CONTROL_DEFAULT_DATASET_PATH}: {type(data)}")
        
        _current_dataset_path = CONTROL_DEFAULT_DATASET_PATH
    else:
        LOGGER_WARNING(f"Control datasets file is empty or missing: {CONTROL_DEFAULT_DATASET_PATH}")
        LOGGER_WARNING("Control metadata lookup will return None for all queries until the file is generated.")
except (json.JSONDecodeError, FileNotFoundError) as e:
    LOGGER_WARNING(f"Failed to load control datasets from {CONTROL_DEFAULT_DATASET_PATH}: {e}")
    LOGGER_WARNING("Control metadata lookup will return None for all queries until the file is generated.")

def get_control_metadata_by_name(step_name, platform='windows'):
    entry = CONTROL_NAME_MAP.get(step_name)
    
    if entry is None:
        LOGGER_INFO(f"[metadata] No control found for step '{step_name}'")
        return None, None
    
    platform_metadata = entry["metadata"].get(platform, {})
    control_name = platform_metadata.get("control_name")
    control_id = platform_metadata.get("control_id")
    if control_name or control_id:
        LOGGER_DEBUG(f"[metadata] control_name='{control_name}', control_id='{control_id}'")
    else:
        LOGGER_INFO(f"[metadata] No control metadata for '{step_name}' on platform '{platform}'")

    return control_name, control_id

def get_all_platforms_for_step(step_name):
    entry = CONTROL_NAME_MAP.get(step_name)
    if entry is None:
        return []
    
    return list(entry["metadata"].keys())

def is_step_supported_on_platform(step_name, platform='windows'):

    entry = CONTROL_NAME_MAP.get(step_name)
    if entry is None:
        LOGGER_INFO(f"[metadata] The step '{step_name}' need not locate on {platform}.")
        return False
    
    return platform in entry["metadata"]

def is_platform_supported(ctrl_platforms, current_platform):
    if ctrl_platforms is None:
        return True
    
    if not isinstance(ctrl_platforms, list):
        LOGGER_INFO(f"Invalid ctrl_platforms type: {type(ctrl_platforms)}, expected list")
        return False
    
    if 'all' in ctrl_platforms:
        return True
    
    return current_platform in ctrl_platforms


def get_complete_control_metadata_by_name(step_name, platform='windows'):
    """Get complete control metadata including all fields for a step"""
    entry = CONTROL_NAME_MAP.get(step_name)
    
    if entry is None:
        LOGGER_INFO(f"[metadata] No control found for step '{step_name}'")
        return None
    
    platform_metadata = entry["metadata"].get(platform, {})
    
    if platform_metadata:
        complete_metadata = {
            'control_name': platform_metadata.get('control_name', ''),
            'control_id': platform_metadata.get('control_id', ''),
            'control_type': platform_metadata.get('control_type', None),
            'control_type_name': platform_metadata.get('control_type_name', ''),
            'from_control': platform_metadata.get('from_control', ''),
            'hierarchical_level': platform_metadata.get('hierarchical_level', ''),
            'platform': platform
        }
        return complete_metadata
    else:
        LOGGER_INFO(f"[metadata] No control metadata for '{step_name}' on platform '{platform}'")
        return None


def get_control_datasets():
    """Get the complete control datasets"""
    return CONTROL_ID_JSON


def get_control_count():
    """Get the total number of controls in the dataset"""
    return len(CONTROL_ID_JSON)


def search_controls_by_pattern(pattern, platform='windows'):
    """Search controls by name pattern"""
    matching_controls = []
    pattern_lower = pattern.lower()
    
    for control in CONTROL_ID_JSON:
        control_name = control.get('name', '').lower()
        if pattern_lower in control_name:
            platform_metadata = control["metadata"].get(platform, {})
            if platform_metadata:
                matching_controls.append({
                    'name': control['name'],
                    'metadata': platform_metadata
                })
    
    LOGGER_DEBUG(f"Found {len(matching_controls)} controls matching pattern '{pattern}' on platform '{platform}'")
    return matching_controls
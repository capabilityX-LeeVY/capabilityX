"""
run_datasets_generator.py

Function to run the datasets generator
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

# Import the control_datasets_generator function
import importlib.util
spec = importlib.util.spec_from_file_location(
    "datasets_generator",
    Path(__file__).parent.parent.parent / "datasets" / "datasets_generator.py"
)
if spec and spec.loader:
    datasets_generator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(datasets_generator_module)
    control_datasets_generator = datasets_generator_module.control_datasets_generator
else:
    raise ImportError("Failed to load datasets_generator module")


def run_datasets_generator(mode="incremental", platform=None, project=None, skip_main_db=False, skip_custom_metadata=False):
    """
    Run the control datasets generator
    
    Args:
        mode (str): Generation mode - 'incremental' or 'reset'. Default is 'incremental'
        platform (str): Platform filter - 'windows', 'mac', or 'web'. If None, generates for all platforms
        project (str): Project name - 'webex_app', 'control_hub', etc. If None, uses default
        skip_main_db (bool): If True, skip main DB (DATASETS_PATH) and only use DATASETS_SPECIFIC_PATH. Default is False
        skip_custom_metadata (bool): If True, skip custom_control_metadata.json. Default is False
    
    Returns:
        bool: True if generation successful, False otherwise
    """
    try:
        # Validate mode
        if mode not in ['incremental', 'reset']:
            LOGGER_ERROR(f"Invalid mode: {mode}. Must be 'incremental' or 'reset'")
            return False
        
        # Validate platform if specified
        if platform:
            valid_platforms = ['windows', 'mac', 'web']
            if platform.lower() not in valid_platforms:
                LOGGER_ERROR(f"Invalid platform: {platform}. Valid platforms are: {valid_platforms}")
                return False
            platform = platform.lower()
        
        # Convert mode to incremental_mode flag
        incremental_mode = (mode == 'incremental')
        mode_str = "Incremental" if incremental_mode else "Reset"
        
        LOGGER_INFO("=" * 80)
        LOGGER_INFO(f"🚀 Running {mode_str} Control Datasets Generation")
        LOGGER_INFO(f"   Mode: {mode_str}")
        if platform:
            LOGGER_INFO(f"   Platform: {platform}")
        if project:
            LOGGER_INFO(f"   Project: {project}")
        if skip_main_db:
            LOGGER_INFO(f"   Skip Main DB: {skip_main_db}")
        if skip_custom_metadata:
            LOGGER_INFO(f"   Skip Custom Metadata: {skip_custom_metadata}")
        LOGGER_INFO("=" * 80)
        
        # Call the control_datasets_generator function directly
        control_datasets_generator(
            incremental_mode=incremental_mode, 
            platform=platform, 
            project=project,
            skip_main_db=skip_main_db,
            skip_custom_metadata=skip_custom_metadata
        )
        
        LOGGER_INFO("=" * 80)
        LOGGER_INFO(f"✅ {mode_str} Control Datasets Generation Completed Successfully!")
        LOGGER_INFO("=" * 80)
        return True
        
    except Exception as e:
        LOGGER_ERROR("=" * 80)
        LOGGER_ERROR(f"❌ Datasets Generation Failed!")
        LOGGER_ERROR(f"Error: {str(e)}")
        LOGGER_ERROR("=" * 80)
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        return False
        LOGGER_ERROR(f"❌ Datasets Generation Failed!")
        LOGGER_ERROR(f"Error: {str(e)}")
        LOGGER_ERROR("=" * 80)
        import traceback
        LOGGER_ERROR(traceback.format_exc())
        return False


# Test the function
if __name__ == "__main__":
    # Example usage
    result = run_datasets_generator(mode="reset", platform="windows", project="webex_app")
    print(f"Generation result: {result}")

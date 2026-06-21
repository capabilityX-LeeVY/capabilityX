#!/usr/bin/env python3
"""
File Selection Manager
Handles file selection dialog operations for sending files in Webex chat.
Currently supports Windows platform with dynamic path resolution.
"""

import sys
import time
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent.parent  # test_space -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING


class FileSelectionManager:
    """
    Manages file selection for Windows test automation.
    Dynamically resolves test file paths.
    """
    
    # Default test files directory relative to test_space
    TEST_FILES_DIR = "resources/test_files"
    
    # Available test files
    TEST_FILES = {
        "document": "test_document.txt",
        "image": "test_image.png",
        "video": "test_video.mp4",
        "pdf": "test_pdf.pdf",
    }
    
    def __init__(self):
        self.test_space_dir = self._get_test_space_dir()
        
    def _get_test_space_dir(self) -> Path:
        """
        Get the absolute path to test_space directory.
        Works regardless of where the script is executed from.
        
        Returns:
            Path: Absolute path to test_space directory
        """
        # This file is in: test_space/test_functions/basic_functions/file_selection_manager.py
        # So test_space is 3 levels up
        current_file = Path(__file__).resolve()
        test_space_dir = current_file.parent.parent.parent
        
        LOGGER_DEBUG(f"Test space directory: {test_space_dir}")
        return test_space_dir
    
    def get_test_file_path(self, file_name: str) -> str:
        """
        Get the absolute path to a test file.
        
        Args:
            file_name (str): Name of the test file or alias (e.g., "document", "test_document.txt")
            
        Returns:
            str: Absolute path to the test file (platform-appropriate format)
        """
        # Check if file_name is an alias
        if file_name in self.TEST_FILES:
            file_name = self.TEST_FILES[file_name]
        
        # Build full path
        file_path = self.test_space_dir / self.TEST_FILES_DIR / file_name
        
        # Verify file exists
        if not file_path.exists():
            LOGGER_WARNING(f"Test file not found: {file_path}")
            # Return path anyway, let the test fail with clear error
        else:
            LOGGER_INFO(f"✓ Test file found: {file_path}")
        
        # Return Windows path string
        return str(file_path)
    
    def input_file_path_to_dialog(self, file_name: str, wait_time: float = 0.5) -> bool:
        """
        Input the test file path into the currently focused file selection dialog.
        
        Args:
            file_name (str): Name of the test file or alias
            wait_time (float): Time to wait after input
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = self.get_test_file_path(file_name)
            LOGGER_INFO(f"Inputting file path: {file_path}")
            
            return self._input_path_windows(file_path, wait_time)
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to input file path: {e}")
            return False
    
    def _input_path_windows(self, file_path: str, wait_time: float) -> bool:
        """
        Input file path on Windows using uiautomation SendKeys.
        Simply types the file path into the currently focused dialog.
        
        Args:
            file_path (str): Absolute file path
            wait_time (float): Time to wait after input
            
        Returns:
            bool: True if successful
        """
        try:
            import uiautomation as auto
            
            # Simply type the file path - the dialog should already be focused
            # and waiting for input after Ctrl+O
            LOGGER_INFO(f"Typing file path: {file_path}")
            
            # Use SendKeys to type the path character by character
            # waitTime controls the delay between characters
            auto.SendKeys(file_path, waitTime=0.02)
            
            LOGGER_INFO(f"✓ Input file path: {file_path}")
            time.sleep(wait_time)
            return True
                
        except Exception as e:
            LOGGER_ERROR(f"Windows file input failed: {e}")
            return False


# Singleton instance
_manager = None

def get_manager() -> FileSelectionManager:
    """Get singleton FileSelectionManager instance"""
    global _manager
    if _manager is None:
        _manager = FileSelectionManager()
    return _manager


# ============================================================
# Functions to be registered in function.json for YAML test cases
# ============================================================

def select_test_file(file_name: str = "document") -> bool:
    """
    Select a test file in the file dialog.
    Input the file path and ready for confirmation.
    
    Args:
        file_name (str): Test file name or alias ("document", "image", "pdf", or actual filename)
        
    Returns:
        bool: True if successful
    """
    manager = get_manager()
    return manager.input_file_path_to_dialog(file_name)


def get_test_file_path(file_name: str = "document") -> str:
    """
    Get the absolute path to a test file without inputting it.
    Useful for verification or other operations.
    
    Args:
        file_name (str): Test file name or alias
        
    Returns:
        str: Absolute path to the test file
    """
    manager = get_manager()
    return manager.get_test_file_path(file_name)


def confirm_file_selection() -> bool:
    """
    Confirm the file selection by pressing Enter or clicking Open button.
    
    Returns:
        bool: True if successful
    """
    try:
        import uiautomation as auto
        
        # Try to find and click "Open" button
        dialog = auto.WindowControl(ClassName='#32770', searchDepth=1)
        if dialog.Exists(timeout=2):
            open_button = dialog.ButtonControl(Name='Open')
            if open_button.Exists(timeout=1):
                open_button.Click()
                LOGGER_INFO("✓ Clicked Open button")
                return True
        
        # Fallback: press Enter
        auto.SendKeys('{Enter}')
        LOGGER_INFO("✓ Pressed Enter to confirm")
        return True
        
    except Exception as e:
        LOGGER_ERROR(f"Failed to confirm file selection: {e}")
        return False


# For testing
if __name__ == "__main__":
    manager = FileSelectionManager()
    print(f"Test space dir: {manager.test_space_dir}")
    print(f"Document path: {manager.get_test_file_path('document')}")
    print(f"Image path: {manager.get_test_file_path('image')}")

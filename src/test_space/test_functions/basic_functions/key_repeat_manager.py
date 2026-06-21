#!/usr/bin/env python3
"""
Key Repeat Manager
Handles repeated key presses for menu navigation and other operations.
"""

import sys
import time
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent.parent  # test_space -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR


# Key name to virtual key code mapping
KEY_CODES = {
    'down': 0x28,      # VK_DOWN
    'up': 0x26,        # VK_UP
    'left': 0x25,      # VK_LEFT
    'right': 0x27,     # VK_RIGHT
    'enter': 0x0D,     # VK_RETURN
    'tab': 0x09,       # VK_TAB
    'escape': 0x1B,    # VK_ESCAPE
    'space': 0x20,     # VK_SPACE
    'backspace': 0x08, # VK_BACK
    'delete': 0x2E,    # VK_DELETE
    'home': 0x24,      # VK_HOME
    'end': 0x23,       # VK_END
    'pageup': 0x21,    # VK_PRIOR
    'pagedown': 0x22,  # VK_NEXT
}


def repeat_key(key: str = "down", count: int = 1, interval: float = 0.2) -> bool:
    """
    Press a key multiple times with specified interval.
    
    Args:
        key (str): Key name to press (down, up, left, right, enter, tab, escape, space)
        count (int): Number of times to press the key
        interval (float): Time interval between key presses in seconds
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        repeat_key("down", 6, 0.2)  # Press down arrow 6 times
    """
    try:
        import ctypes
        from ctypes import wintypes
        
        # Windows API functions
        user32 = ctypes.windll.user32
        
        # Get virtual key code
        key_lower = key.lower()
        if key_lower not in KEY_CODES:
            LOGGER_ERROR(f"❌ Unknown key: {key}. Available keys: {list(KEY_CODES.keys())}")
            return False
        
        vk_code = KEY_CODES[key_lower]
        
        # Convert count to int if it's a string
        if isinstance(count, str):
            count = int(count)
        
        LOGGER_INFO(f"🔄 Pressing '{key}' key {count} times with {interval}s interval")
        
        for i in range(count):
            # Key down
            user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            # Key up
            user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
            
            LOGGER_DEBUG(f"  [{i+1}/{count}] Pressed '{key}'")
            
            # Wait interval (except after last press)
            if i < count - 1:
                time.sleep(interval)
        
        LOGGER_INFO(f"✅ Successfully pressed '{key}' {count} times")
        return True
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Failed to repeat key '{key}': {str(e)}")
        return False


def navigate_menu_down(count: int = 1, interval: float = 0.2) -> bool:
    """
    Navigate down in a menu by pressing down arrow key multiple times.
    Convenience wrapper for repeat_key("down", count, interval).
    
    Args:
        count (int): Number of times to press down
        interval (float): Time interval between presses
        
    Returns:
        bool: True if successful
    """
    return repeat_key("down", count, interval)


def navigate_menu_up(count: int = 1, interval: float = 0.2) -> bool:
    """
    Navigate up in a menu by pressing up arrow key multiple times.
    
    Args:
        count (int): Number of times to press up
        interval (float): Time interval between presses
        
    Returns:
        bool: True if successful
    """
    return repeat_key("up", count, interval)


# ============================================================
# Module-level convenience functions for direct import
# ============================================================

if __name__ == "__main__":
    # Test the functions
    print("Testing repeat_key function...")
    
    # Test with string count (as it would come from YAML params)
    result = repeat_key("down", "3", 0.3)
    print(f"Result: {result}")

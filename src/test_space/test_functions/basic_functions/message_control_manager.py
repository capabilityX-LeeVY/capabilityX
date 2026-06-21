#!/usr/bin/env python3
"""
Message Chat Control Manager
Handles message input area buttons like Screen capture, Emoji, GIF, etc.
Uses flexible control finding strategies for controls with long/dynamic AutomationIds
"""

import uiautomation as auto
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING


class MessageControlManager:
    """Tool class for managing Message Chat controls"""
    
    # Button configurations with multiple identification strategies
    # Priority: Name > AutomationId suffix > ClassName combination
    BUTTON_CONFIGS = {
        "screen_capture": {
            "names": [" Screen capture", "Screen capture", " 屏幕截图", "屏幕截图"],
            "automation_id_suffix": "screenshot_16",
            "class_name": "UTRoundButton",
        },
        "giphy": {
            "names": [" Add Giphy", "Add Giphy", " 添加Giphy", "添加Giphy"],
            "automation_id_suffix": "gif_16",
            "class_name": "UTRoundButton",
        },
        "emoji": {
            "names": [" Insert Emoji", "Insert Emoji", " 插入表情", "插入表情"],
            "automation_id_suffix": "emoticons_16",
            "class_name": "UTRoundButton",
        },
        "mention": {
            "names": [" Add mention", "Add mention", " @提及", "@提及"],
            "automation_id_suffix": "mention_16",
            "class_name": "UTRoundButton",
        },
        "pmr_url": {
            "names": [" Insert my PMR URL", "Insert my PMR URL", " 插入我的个人会议室URL", "插入我的个人会议室URL"],
            "automation_id_suffix": "pmr-bold",
            "class_name": "UTRoundButton",
        },
        "space_settings": {
            "names": [" Space settings menu", "Space settings menu", " 空间设置菜单", "空间设置菜单"],
            "automation_id_suffix": "settings",
            "class_name": "UTRoundButton",
        },
    }
    
    def __init__(self):
        self.timeout = 5
        
    def find_button_by_name(self, names, timeout=None):
        """
        Find button by Name property
        
        Args:
            names (list): List of possible button names
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, or None
        """
        timeout = timeout or self.timeout
        
        for name in names:
            try:
                LOGGER_DEBUG(f"Searching button by Name: '{name}'")
                button = auto.ButtonControl(Name=name)
                if button.Exists(timeout // len(names) or 1):
                    LOGGER_INFO(f"✓ Found button by Name: '{name}'")
                    return button
            except Exception as e:
                LOGGER_DEBUG(f"Name search failed for '{name}': {e}")
                continue
                
        return None
    
    def find_button_by_automation_id_suffix(self, suffix, timeout=None):
        """
        Find button by AutomationId suffix (partial match)
        
        Args:
            suffix (str): AutomationId suffix to match
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, or None
        """
        timeout = timeout or self.timeout
        
        try:
            LOGGER_DEBUG(f"Searching button by AutomationId suffix: '{suffix}'")
            
            # Search all buttons and filter by AutomationId suffix
            root = auto.GetRootControl()
            
            # Use a broader search first
            buttons = root.GetChildren()
            
            def find_recursive(control, depth=0, max_depth=15):
                """Recursively search for button with matching AutomationId suffix"""
                if depth > max_depth:
                    return None
                    
                try:
                    automation_id = control.AutomationId
                    if automation_id and automation_id.endswith(suffix):
                        LOGGER_INFO(f"✓ Found button by AutomationId suffix: '{suffix}', full ID: '{automation_id}'")
                        return control
                    
                    # Search children
                    for child in control.GetChildren():
                        result = find_recursive(child, depth + 1, max_depth)
                        if result:
                            return result
                except:
                    pass
                    
                return None
            
            # Start search from focused window for better performance
            focused_window = auto.GetForegroundControl()
            if focused_window:
                result = find_recursive(focused_window)
                if result:
                    return result
            
            # Fallback to root search
            return find_recursive(root)
            
        except Exception as e:
            LOGGER_DEBUG(f"AutomationId suffix search failed: {e}")
            return None
    
    def find_button_by_class_and_parent(self, class_name, parent_contains=None, timeout=None):
        """
        Find button by ClassName and optional parent AutomationId
        
        Args:
            class_name (str): Button ClassName
            parent_contains (str): Substring to match in parent AutomationId
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, or None
        """
        timeout = timeout or self.timeout
        
        try:
            LOGGER_DEBUG(f"Searching button by ClassName: '{class_name}'")
            button = auto.ButtonControl(ClassName=class_name)
            if button.Exists(timeout):
                LOGGER_INFO(f"✓ Found button by ClassName: '{class_name}'")
                return button
        except Exception as e:
            LOGGER_DEBUG(f"ClassName search failed: {e}")
            
        return None
    
    def find_message_button(self, button_key, timeout=None):
        """
        Find a message chat button using multiple strategies
        
        Args:
            button_key (str): Button key from BUTTON_CONFIGS
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, or None
        """
        timeout = timeout or self.timeout
        
        if button_key not in self.BUTTON_CONFIGS:
            LOGGER_ERROR(f"Unknown button key: {button_key}")
            LOGGER_INFO(f"Available buttons: {list(self.BUTTON_CONFIGS.keys())}")
            return None
        
        config = self.BUTTON_CONFIGS[button_key]
        LOGGER_INFO(f"🔍 Searching for '{button_key}' button...")
        
        # Strategy 1: Find by Name
        button = self.find_button_by_name(config["names"], timeout)
        if button:
            return button
        
        # Strategy 2: Find by AutomationId suffix
        if "automation_id_suffix" in config:
            button = self.find_button_by_automation_id_suffix(config["automation_id_suffix"], timeout)
            if button:
                return button
        
        # Strategy 3: Find by ClassName
        if "class_name" in config:
            button = self.find_button_by_class_and_parent(config["class_name"], timeout=timeout)
            if button:
                return button
        
        LOGGER_ERROR(f"✗ Button '{button_key}' not found with any strategy")
        return None
    
    def click_message_button(self, button_key, timeout=None):
        """
        Find and click a message chat button
        
        Args:
            button_key (str): Button key from BUTTON_CONFIGS
            timeout (int): Search timeout in seconds
            
        Returns:
            bool: Whether click was successful
        """
        button = self.find_message_button(button_key, timeout)
        
        if button is None:
            return False
        
        try:
            LOGGER_INFO(f"🖱️ Clicking '{button_key}' button...")
            button.Click()
            time.sleep(0.5)
            LOGGER_INFO(f"✅ Successfully clicked '{button_key}' button")
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to click '{button_key}' button: {e}")
            return False
    
    def is_button_enabled(self, button_key, timeout=None):
        """
        Check if a message chat button is enabled
        
        Args:
            button_key (str): Button key from BUTTON_CONFIGS
            timeout (int): Search timeout in seconds
            
        Returns:
            bool: Whether button is enabled, None if not found
        """
        button = self.find_message_button(button_key, timeout)
        
        if button is None:
            return None
        
        try:
            is_enabled = button.IsEnabled
            LOGGER_INFO(f"Button '{button_key}' enabled: {is_enabled}")
            return is_enabled
        except Exception as e:
            LOGGER_ERROR(f"Failed to check enabled state for '{button_key}': {e}")
            return None


# ============== Convenience Functions ==============

def click_screen_capture(timeout=5):
    """Click Screen capture button in message chat"""
    manager = MessageControlManager()
    return manager.click_message_button("screen_capture", timeout)


def click_giphy(timeout=5):
    """Click Add Giphy button in message chat"""
    manager = MessageControlManager()
    return manager.click_message_button("giphy", timeout)


def click_emoji(timeout=5):
    """Click Insert Emoji button in message chat"""
    manager = MessageControlManager()
    return manager.click_message_button("emoji", timeout)


def click_mention(timeout=5):
    """Click Add mention button in message chat"""
    manager = MessageControlManager()
    return manager.click_message_button("mention", timeout)


def click_pmr_url(timeout=5):
    """Click Insert my PMR URL button in message chat"""
    manager = MessageControlManager()
    return manager.click_message_button("pmr_url", timeout)


def click_space_settings(timeout=5):
    """Click Space settings menu button"""
    manager = MessageControlManager()
    return manager.click_message_button("space_settings", timeout)


def find_button(button_key, timeout=5):
    """
    Find a message button by key
    
    Args:
        button_key (str): One of: screen_capture, giphy, emoji, mention, pmr_url
        timeout (int): Search timeout
        
    Returns:
        Control: Found control or None
    """
    manager = MessageControlManager()
    return manager.find_message_button(button_key, timeout)


def click_button(button_key, timeout=5):
    """
    Click a message button by key
    
    Args:
        button_key (str): One of: screen_capture, giphy, emoji, mention, pmr_url
        timeout (int): Search timeout
        
    Returns:
        bool: Whether click was successful
    """
    manager = MessageControlManager()
    return manager.click_message_button(button_key, timeout)


# ============== Test Function ==============

def test_message_controls():
    """Test message control functionality"""
    print("=== Test Message Chat Controls ===")
    print("Make sure you have a Webex chat window open!\n")
    
    manager = MessageControlManager()
    
    # Test finding each button
    for button_key in manager.BUTTON_CONFIGS.keys():
        print(f"\n--- Testing '{button_key}' button ---")
        button = manager.find_message_button(button_key, timeout=3)
        if button:
            print(f"   ✅ Found: Name='{button.Name}'")
            print(f"   Enabled: {button.IsEnabled}")
        else:
            print(f"   ❌ Not found")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_message_controls()

#!/usr/bin/env python3
"""
Mute/Unmute state control tool
Handles buttons with the same AutomationId but different state names
"""

import uiautomation as auto
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING

class MuteControlManager:
    """Tool class for managing Mute/Unmute button states"""
    
    def __init__(self):
        # Prefer QT6.8 ids first, then fall back to legacy build ids.
        self.in_meeting_automation_ids = [
            "SparkApp.CallControlBar.Main_CallStripButton_Audio",
            "Main_CallStripButton_Audio",
        ]
        self.pre_meeting_automation_ids = [
            "SparkApp.MeetingInterstitialPageView.MeetingInterstitialPageForVdi.meetingBodyViewItem.audioButtonLeftCell",
            "audioButtonLeftCell",
        ]
        
        self.expected_mute_names = ["Mute", "静音"]  # Support multiple languages
        self.expected_unmute_names = ["Unmute", "取消静音"]  # Support multiple languages
        
    def find_mute_button(self, timeout=5, context="auto"):
        """
        Find Mute/Unmute button by AutomationId
        
        Args:
            timeout (int): Search timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            Control: Found control, returns None if not found
        """
        
        try:
            automation_ids = []
            
            if context == "auto":
                # Try both contexts automatically
                automation_ids = self.in_meeting_automation_ids + self.pre_meeting_automation_ids
            elif context == "pre_meeting":
                automation_ids = self.pre_meeting_automation_ids
            elif context == "in_meeting":
                automation_ids = self.in_meeting_automation_ids
            else:
                LOGGER_ERROR(f"Invalid context: {context}, must be 'auto', 'pre_meeting', or 'in_meeting'")
                return None
            
            start_time = time.time()

            for automation_id in automation_ids:
                LOGGER_DEBUG(f"Searching for Mute button, AutomationId: {automation_id}, context: {context}")

                elapsed = time.time() - start_time
                remaining_timeout = max(1, int(timeout - elapsed))
                LOGGER_DEBUG(
                    f"Remaining timeout for Mute button search: {remaining_timeout}s, AutomationId: {automation_id}"
                )

                # Search button using AutomationId
                button = auto.ButtonControl(AutomationId=automation_id)

                if button.Exists(remaining_timeout):
                    button_name = button.Name
                    LOGGER_INFO(f"✓ Found Mute button: '{button_name}', AutomationId: {automation_id}")
                    return button
                else:
                    LOGGER_DEBUG(f"✗ Mute button not found with AutomationId: {automation_id}")
            
            LOGGER_ERROR(f"✗ Mute button not found in any context")
            return None
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while searching for Mute button: {e}")
            return None
    
    def get_current_mute_state(self, button=None, context="auto"):
        """
        Get current mute state
        
        Args:
            button (Control): Mute button control, auto-search if None
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            str: 'muted', 'unmuted', 'unknown'
        """
        
        if button is None:
            button = self.find_mute_button(context=context)
            
        if button is None:
            LOGGER_ERROR("Cannot get mute state: button not found")
            return 'unknown'
            
        try:
            # Refresh control state
            button.Refind()
            button_name = button.Name
            LOGGER_DEBUG(f"Current button name: '{button_name}'")
            
            # Check current state
            if any(mute_name in button_name for mute_name in self.expected_mute_names):
                LOGGER_INFO(f"✓ Current state: unmuted (button shows: '{button_name}')")
                return 'unmuted'  # Button shows "Mute" means currently unmuted
            elif any(unmute_name in button_name for unmute_name in self.expected_unmute_names):
                LOGGER_INFO(f"✓ Current state: muted (button shows: '{button_name}')")
                return 'muted'    # Button shows "Unmute" means currently muted
            else:
                LOGGER_WARNING(f"⚠ Unrecognized button state: '{button_name}'")
                return 'unknown'
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while getting mute state: {e}")
            return 'unknown'
    
    def set_mute_state(self, target_state, timeout=5, context="auto"):
        """
        Set mute state
        
        Args:
            target_state (str): target state 'muted' or 'unmuted'
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        
        if target_state not in ['muted', 'unmuted']:
            LOGGER_ERROR(f"Invalid target state: {target_state}, must be 'muted' or 'unmuted'")
            return False
            
        LOGGER_INFO(f"🎯 Setting mute state target: {target_state}, context: {context}")
        
        # Find button
        button = self.find_mute_button(timeout, context)
        if button is None:
            return False
            
        # Get current state
        current_state = self.get_current_mute_state(button, context)
        if current_state == 'unknown':
            LOGGER_ERROR("Cannot determine current mute state")
            return False
            
        # Check if operation is needed
        if current_state == target_state:
            LOGGER_INFO(f"✓ Current state is already {target_state}, no operation needed")
            return True
            
        # Execute click operation
        try:
            LOGGER_INFO(f"🔄 Current state: {current_state} -> target state: {target_state}, executing click operation")
            try:
                invoke_pattern = button.GetInvokePattern()
                invoke_pattern.Invoke()
                LOGGER_DEBUG("Invoked mute button via InvokePattern")
            except Exception:
                LOGGER_DEBUG("InvokePattern not available, falling back to Click()")
                button.Click()
            
            # Wait for state update
            time.sleep(1)
            
            # Verify if state changed
            new_state = self.get_current_mute_state(button, context)
            if new_state == target_state:
                LOGGER_INFO(f"✅ Mute state set successfully: {target_state}")
                return True
            else:
                LOGGER_ERROR(f"✗ Mute state setting failed: expected {target_state}, actual {new_state}")
                return False
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while setting mute state: {e}")
            return False
    
    def ensure_muted(self, timeout=5, context="auto"):
        """
        Ensure in muted state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        return self.set_mute_state('muted', timeout, context)
    
    def ensure_unmuted(self, timeout=5, context="auto"):
        """
        Ensure in unmuted state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        return self.set_mute_state('unmuted', timeout, context)
    
    def toggle_mute_state(self, timeout=5, context="auto"):
        """
        Toggle mute state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            tuple: (Whether successful, new state)
        """
        
        LOGGER_INFO(f"🔄 Toggle mute state, context: {context}")
        
        # Find button
        button = self.find_mute_button(timeout, context)
        if button is None:
            return False, 'unknown'
            
        # Get current state
        current_state = self.get_current_mute_state(button, context)
        if current_state == 'unknown':
            LOGGER_ERROR("Cannot determine current mute state")
            return False, 'unknown'
            
        # Execute click operation
        try:
            LOGGER_INFO(f"🔄 Execute toggle operation, current state: {current_state}")
            try:
                invoke_pattern = button.GetInvokePattern()
                invoke_pattern.Invoke()
                LOGGER_DEBUG("Invoked mute button via InvokePattern")
            except Exception:
                LOGGER_DEBUG("InvokePattern not available, falling back to Click()")
                button.Click()
            
            # Wait for state update
            time.sleep(1)
            
            # Get new state
            new_state = self.get_current_mute_state(button, context)
            if new_state != 'unknown' and new_state != current_state:
                LOGGER_INFO(f"✅ Mute state toggled successfully: {current_state} -> {new_state}")
                return True, new_state
            else:
                LOGGER_ERROR(f"✗ Mute state toggle failed")
                return False, new_state
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while toggling mute state: {e}")
            return False, 'unknown'


# Utility functions for convenient use in YAML
def ensure_muted(timeout=5, context="auto"):
    """
    Convenience function to ensure muted state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        bool: Whether operation was successful
    """
    manager = MuteControlManager()
    return manager.ensure_muted(timeout, context)


def ensure_unmuted(timeout=5, context="auto"):
    """
    Convenience function to ensure unmuted state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        bool: Whether operation was successful
    """
    manager = MuteControlManager()
    return manager.ensure_unmuted(timeout, context)


def toggle_mute(timeout=5, context="auto"):
    """
    Convenience function to toggle mute state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        tuple: (Whether successful, new state)
    """
    manager = MuteControlManager()
    return manager.toggle_mute_state(timeout, context)


def get_mute_status(timeout=5, context="auto"):
    """
    Convenience function to get current mute state
    
    Args:
        timeout (int): Search timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        str: 'muted', 'unmuted', 'unknown'
    """
    manager = MuteControlManager()
    button = manager.find_mute_button(timeout, context)
    return manager.get_current_mute_state(button, context)


# Specific functions for pre-meeting settings
def ensure_muted_before_meeting(timeout=5):
    """Ensure muted state before starting meeting"""
    return ensure_muted(timeout, "pre_meeting")

def ensure_unmuted_before_meeting(timeout=5):
    """Ensure unmuted state before starting meeting"""
    return ensure_unmuted(timeout, "pre_meeting")

def toggle_mute_before_meeting(timeout=5):
    """Toggle mute state before starting meeting"""
    return toggle_mute(timeout, "pre_meeting")

def get_mute_status_before_meeting(timeout=5):
    """Get mute status before starting meeting"""
    return get_mute_status(timeout, "pre_meeting")


# Specific functions for in-meeting settings
def ensure_muted_in_meeting(timeout=5):
    """Ensure muted state during meeting"""
    return ensure_muted(timeout, "in_meeting")

def ensure_unmuted_in_meeting(timeout=5):
    """Ensure unmuted state during meeting"""
    return ensure_unmuted(timeout, "in_meeting")

def toggle_mute_in_meeting(timeout=5):
    """Toggle mute state during meeting"""
    return toggle_mute(timeout, "in_meeting")

def get_mute_status_in_meeting(timeout=5):
    """Get mute status during meeting"""
    return get_mute_status(timeout, "in_meeting")


# Test function
def test_mute_control():
    """Test mute control functionality"""
    print("=== Test mute control functionality ===")
    
    manager = MuteControlManager()
    
    # Test finding button
    print("\n1. Test finding mute button:")
    button = manager.find_mute_button()
    if button:
        print(f"   ✅ Found button: {button.Name}")
    else:
        print("   ❌ Button not found")
        return
    
    # Test getting current state
    print("\n2. Test getting current state:")
    current_state = manager.get_current_mute_state(button)
    print(f"   Current state: {current_state}")
    
    # Test setting mute
    print("\n3. Test setting mute state:")
    result = manager.ensure_muted()
    print(f"   Set mute result: {'success' if result else 'failed'}")
    
    # Test setting unmute
    print("\n4. Test setting unmute state:")
    result = manager.ensure_unmuted()
    print(f"   Set unmute result: {'success' if result else 'failed'}")
    
    # Test toggle state
    print("\n5. Test toggle state:")
    success, new_state = manager.toggle_mute_state()
    print(f"   Toggle result: {'success' if success else 'failed'}, new state: {new_state}")


if __name__ == "__main__":
    test_mute_control()

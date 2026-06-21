#!/usr/bin/env python3
"""
Video Control Manager - Video on/off state control tool
Handles video buttons with the same AutomationId but different state names
"""

import uiautomation as auto
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING

class VideoControlManager:
    """Tool class for managing Start video/Stop video button states"""
    
    def __init__(self):
        # Prefer QT6.8 ids first, then fall back to legacy build ids.
        self.in_meeting_automation_ids = [
            "SparkApp.CallControlBar.Main_CallStripButton_Video",
            "Main_CallStripButton_Video",
        ]
        self.pre_meeting_automation_ids = [
            "SparkApp.MeetingInterstitialPageView.MeetingInterstitialPageForVdi.meetingBodyViewItem.videoButtonLeftCell",
            "videoButtonLeftCell",
        ]
        
        self.expected_start_video_names = ["Start video", "开启视频"]  # Support multiple languages
        self.expected_stop_video_names = ["Stop video", "停止视频"]  # Support multiple languages
        
    def find_video_button(self, timeout=5, context="auto"):
        """
        Find Start video/Stop video button by AutomationId
        
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
                LOGGER_DEBUG(f"Searching for Video button, AutomationId: {automation_id}, context: {context}")

                elapsed = time.time() - start_time
                remaining_timeout = max(1, int(timeout - elapsed))
                LOGGER_DEBUG(
                    f"Remaining timeout for Video button search: {remaining_timeout}s, AutomationId: {automation_id}"
                )
                
                # Search button using AutomationId
                button = auto.ButtonControl(AutomationId=automation_id)
                
                if button.Exists(remaining_timeout):
                    button_name = button.Name
                    LOGGER_INFO(f"✓ Found Video button: '{button_name}', AutomationId: {automation_id}")
                    return button
                else:
                    LOGGER_DEBUG(f"✗ Video button not found with AutomationId: {automation_id}")
            
            LOGGER_ERROR(f"✗ Video button not found in any context")
            return None
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while searching for Video button: {e}")
            return None
    
    def get_current_video_state(self, button=None, context="auto"):
        """
        Get current video state
        
        Args:
            button (Control): Video button control, auto-search if None
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            str: 'video_on', 'video_off', 'unknown'
        """
        
        if button is None:
            button = self.find_video_button(context=context)
            
        if button is None:
            LOGGER_ERROR("Cannot get video state: button not found")
            return 'unknown'
            
        try:
            # Refresh control state
            button.Refind()
            button_name = button.Name
            LOGGER_DEBUG(f"Current button name: '{button_name}'")
            
            # Check current state
            if any(start_name in button_name for start_name in self.expected_start_video_names):
                LOGGER_INFO(f"✓ Current state: video off (button shows: '{button_name}')")
                return 'video_off'  # Button shows "Start video" means currently video is off
            elif any(stop_name in button_name for stop_name in self.expected_stop_video_names):
                LOGGER_INFO(f"✓ Current state: video on (button shows: '{button_name}')")
                return 'video_on'   # Button shows "Stop video" means currently video is on
            else:
                LOGGER_WARNING(f"⚠ Unrecognized button state: '{button_name}'")
                return 'unknown'
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while getting video state: {e}")
            return 'unknown'
    
    def set_video_state(self, target_state, timeout=5, context="auto"):
        """
        Set video state
        
        Args:
            target_state (str): target state 'video_on' or 'video_off'
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        
        if target_state not in ['video_on', 'video_off']:
            LOGGER_ERROR(f"Invalid target state: {target_state}, must be 'video_on' or 'video_off'")
            return False
            
        LOGGER_INFO(f"🎯 Setting video state target: {target_state}, context: {context}")
        
        # Find button
        button = self.find_video_button(timeout, context)
        if button is None:
            return False
            
        # Get current state
        current_state = self.get_current_video_state(button, context)
        if current_state == 'unknown':
            LOGGER_ERROR("Cannot determine current video state")
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
                LOGGER_DEBUG("Invoked video button via InvokePattern")
            except Exception:
                LOGGER_DEBUG("InvokePattern not available, falling back to Click()")
                button.Click()
            
            # Wait for state update
            time.sleep(1)
            
            # Verify if state changed
            new_state = self.get_current_video_state(button, context)
            if new_state == target_state:
                LOGGER_INFO(f"✅ Video state set successfully: {target_state}")
                return True
            else:
                LOGGER_ERROR(f"✗ Video state setting failed: expected {target_state}, actual {new_state}")
                return False
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while setting video state: {e}")
            return False
    
    def ensure_video_on(self, timeout=5, context="auto"):
        """
        Ensure in video on state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        return self.set_video_state('video_on', timeout, context)
    
    def ensure_video_off(self, timeout=5, context="auto"):
        """
        Ensure in video off state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            bool: Whether operation was successful
        """
        return self.set_video_state('video_off', timeout, context)
    
    def toggle_video_state(self, timeout=5, context="auto"):
        """
        Toggle video state
        
        Args:
            timeout (int): Operation timeout in seconds
            context (str): "auto", "pre_meeting", "in_meeting"
            
        Returns:
            tuple: (Whether successful, new state)
        """
        
        LOGGER_INFO(f"🔄 Toggle video state, context: {context}")
        
        # Find button
        button = self.find_video_button(timeout, context)
        if button is None:
            return False, 'unknown'
            
        # Get current state
        current_state = self.get_current_video_state(button, context)
        if current_state == 'unknown':
            LOGGER_ERROR("Cannot determine current video state")
            return False, 'unknown'
            
        # Execute click operation
        try:
            LOGGER_INFO(f"🔄 Execute toggle operation, current state: {current_state}")
            try:
                invoke_pattern = button.GetInvokePattern()
                invoke_pattern.Invoke()
                LOGGER_DEBUG("Invoked video button via InvokePattern")
            except Exception:
                LOGGER_DEBUG("InvokePattern not available, falling back to Click()")
                button.Click()
            
            # Wait for state update
            time.sleep(1)
            
            # Get new state
            new_state = self.get_current_video_state(button, context)
            if new_state != 'unknown' and new_state != current_state:
                LOGGER_INFO(f"✅ Video state toggled successfully: {current_state} -> {new_state}")
                return True, new_state
            else:
                LOGGER_ERROR(f"✗ Video state toggle failed")
                return False, new_state
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while toggling video state: {e}")
            return False, 'unknown'


# Utility functions for convenient use in YAML
def ensure_video_on(timeout=5, context="auto"):
    """
    Convenience function to ensure video on state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        bool: Whether operation was successful
    """
    manager = VideoControlManager()
    return manager.ensure_video_on(timeout, context)


def ensure_video_off(timeout=5, context="auto"):
    """
    Convenience function to ensure video off state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        bool: Whether operation was successful
    """
    manager = VideoControlManager()
    return manager.ensure_video_off(timeout, context)


def toggle_video(timeout=5, context="auto"):
    """
    Convenience function to toggle video state
    
    Args:
        timeout (int): Operation timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        tuple: (Whether successful, new state)
    """
    manager = VideoControlManager()
    return manager.toggle_video_state(timeout, context)


def get_video_status(timeout=5, context="auto"):
    """
    Convenience function to get current video state
    
    Args:
        timeout (int): Search timeout in seconds
        context (str): "auto", "pre_meeting", "in_meeting"
        
    Returns:
        str: 'video_on', 'video_off', 'unknown'
    """
    manager = VideoControlManager()
    button = manager.find_video_button(timeout, context)
    return manager.get_current_video_state(button, context)


# Specific functions for pre-meeting settings
def ensure_video_on_before_meeting(timeout=5):
    """Ensure video on state before starting meeting"""
    return ensure_video_on(timeout, "pre_meeting")

def ensure_video_off_before_meeting(timeout=5):
    """Ensure video off state before starting meeting"""
    return ensure_video_off(timeout, "pre_meeting")

def toggle_video_before_meeting(timeout=5):
    """Toggle video state before starting meeting"""
    return toggle_video(timeout, "pre_meeting")

def get_video_status_before_meeting(timeout=5):
    """Get video status before starting meeting"""
    return get_video_status(timeout, "pre_meeting")


# Specific functions for in-meeting settings
def ensure_video_on_in_meeting(timeout=5):
    """Ensure video on state during meeting"""
    return ensure_video_on(timeout, "in_meeting")

def ensure_video_off_in_meeting(timeout=5):
    """Ensure video off state during meeting"""
    return ensure_video_off(timeout, "in_meeting")

def toggle_video_in_meeting(timeout=5):
    """Toggle video state during meeting"""
    return toggle_video(timeout, "in_meeting")

def get_video_status_in_meeting(timeout=5):
    """Get video status during meeting"""
    return get_video_status(timeout, "in_meeting")


# Test function
def test_video_control():
    """Test video control functionality"""
    print("=== Test video control functionality ===")
    
    manager = VideoControlManager()
    
    # Test finding button
    print("\n1. Test finding video button:")
    button = manager.find_video_button()
    if button:
        print(f"   ✅ Found button: {button.Name}")
    else:
        print("   ❌ Button not found")
        return
    
    # Test getting current state
    print("\n2. Test getting current state:")
    current_state = manager.get_current_video_state(button)
    print(f"   Current state: {current_state}")
    
    # Test setting video on
    print("\n3. Test setting video on state:")
    result = manager.ensure_video_on()
    print(f"   Set video on result: {'success' if result else 'failed'}")
    
    # Test setting video off
    print("\n4. Test setting video off state:")
    result = manager.ensure_video_off()
    print(f"   Set video off result: {'success' if result else 'failed'}")
    
    # Test toggle state
    print("\n5. Test toggle state:")
    success, new_state = manager.toggle_video_state()
    print(f"   Toggle result: {'success' if success else 'failed'}, new state: {new_state}")


if __name__ == "__main__":
    test_video_control()

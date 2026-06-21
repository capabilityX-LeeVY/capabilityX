#!/usr/bin/env python3
"""
Layout Control Manager - Meeting layout switching tool
Handles layout switching between different view modes (side-by-side, stack, grid)
"""

import uiautomation as auto
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING

class LayoutControlManager:
    """Tool class for managing meeting layout switching operations"""
    
    def __init__(self):
        # Layout control button AutomationIds
        self.layout_main_button_id = "ScannedByVDI"
        self.layout_main_button_name = "Layout. Check and adjust layout settings."
        
        # Layout option buttons
        self.layout_options = {
            'side_by_side': {
                'id': 'RectangleToggleButton_3',
                'name': 'Side-by-side view',
                'display_name': 'Side-by-side'
            },
            'stack': {
                'id': 'RectangleToggleButton_2', 
                'name': 'Stack view',
                'display_name': 'Stack'
            },
            'grid': {
                'id': 'RectangleToggleButton_1',
                'name': 'Layout, Grid view', 
                'display_name': 'Grid'
            }
        }
        
    def find_layout_main_button(self, timeout=5):
        """
        Find main layout button
        
        Args:
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, returns None if not found
        """
        try:
            LOGGER_DEBUG(f"Searching for Layout main button, AutomationId: {self.layout_main_button_id}")
            
            # Search button using AutomationId
            button = auto.ButtonControl(AutomationId=self.layout_main_button_id)
            
            if button.Exists(timeout):
                button_name = button.Name
                LOGGER_INFO(f"✓ Found Layout main button: '{button_name}', AutomationId: {self.layout_main_button_id}")
                return button
            else:
                LOGGER_ERROR(f"✗ Layout main button not found, AutomationId: {self.layout_main_button_id}")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while searching for Layout main button: {e}")
            return None
    
    def find_layout_option_button(self, layout_type, timeout=5):
        """
        Find specific layout option button
        
        Args:
            layout_type (str): Layout type ('side_by_side', 'stack', 'grid')
            timeout (int): Search timeout in seconds
            
        Returns:
            Control: Found control, returns None if not found
        """
        if layout_type not in self.layout_options:
            LOGGER_ERROR(f"Invalid layout type: {layout_type}, must be one of {list(self.layout_options.keys())}")
            return None
            
        option = self.layout_options[layout_type]
        
        try:
            LOGGER_DEBUG(f"Searching for {option['display_name']} button, AutomationId: {option['id']}")
            
            # Search button using AutomationId
            button = auto.ButtonControl(AutomationId=option['id'])
            
            if button.Exists(timeout):
                button_name = button.Name
                LOGGER_INFO(f"✓ Found {option['display_name']} button: '{button_name}', AutomationId: {option['id']}")
                return button
            else:
                LOGGER_ERROR(f"✗ {option['display_name']} button not found, AutomationId: {option['id']}")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while searching for {option['display_name']} button: {e}")
            return None
    
    def switch_to_layout(self, layout_type, wait_time=5):
        """
        Switch to specific layout
        
        Args:
            layout_type (str): Layout type ('side_by_side', 'stack', 'grid')
            wait_time (int): Wait time after switching in seconds
            
        Returns:
            bool: Whether operation was successful
        """
        if layout_type not in self.layout_options:
            LOGGER_ERROR(f"Invalid layout type: {layout_type}, must be one of {list(self.layout_options.keys())}")
            return False
            
        option = self.layout_options[layout_type]
        LOGGER_INFO(f"🎯 Switching to {option['display_name']} layout")
        
        try:
            # Step 1: Find and click main layout button
            main_button = self.find_layout_main_button()
            if main_button is None:
                LOGGER_ERROR("Cannot find main layout button")
                return False
                
            LOGGER_INFO(f"🔄 Step 1: Clicking main layout button")
            main_button.Click()
            time.sleep(1)  # Wait for layout menu to appear
            
            # Step 2: Find and click specific layout option
            option_button = self.find_layout_option_button(layout_type)
            if option_button is None:
                LOGGER_ERROR(f"Cannot find {option['display_name']} layout option button")
                return False
                
            LOGGER_INFO(f"🔄 Step 2: Clicking {option['display_name']} layout option")
            option_button.Click()
            
            # Step 3: Wait for layout to apply
            LOGGER_INFO(f"⏳ Waiting {wait_time} seconds for layout to apply...")
            time.sleep(wait_time)
            
            LOGGER_INFO(f"✅ Successfully switched to {option['display_name']} layout")
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred while switching to {option['display_name']} layout: {e}")
            return False
    
    def close_layout_menu(self):
        """
        Close any open layout menu by pressing Escape key
        
        Returns:
            bool: Whether operation was attempted
        """
        try:
            LOGGER_DEBUG("Attempting to close any open layout menu...")
            import pyautogui
            pyautogui.press('escape')
            time.sleep(0.5)
            return True
        except Exception as e:
            LOGGER_DEBUG(f"Could not close layout menu: {e}")
            return False


# Utility functions for convenient use in YAML
def switch_to_side_by_side_layout(wait_time=5):
    """
    Convenience function to switch to side-by-side layout
    
    Args:
        wait_time (int): Wait time after switching in seconds
        
    Returns:
        bool: Whether operation was successful
    """
    manager = LayoutControlManager()
    return manager.switch_to_layout('side_by_side', wait_time)


def switch_to_stack_layout(wait_time=5):
    """
    Convenience function to switch to stack layout
    
    Args:
        wait_time (int): Wait time after switching in seconds
        
    Returns:
        bool: Whether operation was successful
    """
    manager = LayoutControlManager()
    return manager.switch_to_layout('stack', wait_time)


def switch_to_grid_layout(wait_time=5):
    """
    Convenience function to switch to grid layout
    
    Args:
        wait_time (int): Wait time after switching in seconds
        
    Returns:
        bool: Whether operation was successful
    """
    manager = LayoutControlManager()
    return manager.switch_to_layout('grid', wait_time)


if __name__ == "__main__":
    # Simple test when run directly
    manager = LayoutControlManager()
    print("Testing layout control...")
    result = manager.switch_to_layout('side_by_side', 2)
    print(f"Test result: {'success' if result else 'failed'}")

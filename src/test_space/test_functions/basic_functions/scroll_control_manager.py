#!/usr/bin/env python3
"""
Scroll Bar Control Manager - Simplified Version
Handles finding and interacting with scroll bars using arrow buttons (most reliable method)
"""

import uiautomation as auto
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING

class ScrollBarManager:
    """Simplified scroll bar manager focusing on arrow button method"""
    
    def __init__(self):
        # Common scroll bar class names
        self.scroll_class_names = [
            "ScrollBar",
            "SCROLLBAR",
            "VScrollBar", 
            "HScrollBar",
            "UTScrollBar_QMLTYPE_15",  # Qt/QML scroll bar
            "UTScrollBar_QMLTYPE_14",  # Qt/QML scroll bar
            "QScrollBar"  # Qt scroll bar
        ]
        
    def find_scroll_bar(self, container_automation_id=None, orientation="vertical", timeout=5):
        """
        Find scroll bar element in the specified container
        
        Args:
            container_automation_id (str): AutomationId of container to search in
            orientation (str): "vertical" or "horizontal"
            timeout (int): Search timeout in seconds
            
        Returns:
            auto.Control: Scroll bar control if found, None otherwise
        """
        try:
            LOGGER_DEBUG(f"Searching for {orientation} scroll bar")
            
            # Find container if specified
            if container_automation_id:
                container = auto.Control(AutomationId=container_automation_id)
                if not container.Exists(timeout):
                    LOGGER_ERROR(f"Container with AutomationId '{container_automation_id}' not found")
                    return None
            else:
                container = auto.GetRootControl()
            
            # Method 1: Search by control type
            scroll_bar = auto.ScrollBarControl(searchFromControl=container)
            if scroll_bar.Exists(timeout):
                if self._is_orientation_match(scroll_bar, orientation):
                    LOGGER_INFO(f"Found scroll bar by control type: {scroll_bar}")
                    return scroll_bar
            
            # Method 2: Search by class name patterns
            for class_name in self.scroll_class_names:
                try:
                    scroll_bar = container.Control(ClassName=class_name)
                    if scroll_bar.Exists(1):
                        if self._is_orientation_match(scroll_bar, orientation):
                            LOGGER_INFO(f"Found scroll bar by class name '{class_name}': {scroll_bar}")
                            return scroll_bar
                except:
                    continue
            
            LOGGER_WARNING(f"No {orientation} scroll bar found in container")
            return None
            
        except Exception as e:
            LOGGER_ERROR(f"Error finding scroll bar: {e}")
            return None
    
    def find_scroll_bar_buttons(self, scroll_bar):
        """
        Find arrow buttons and thumb within scroll bar
        
        Args:
            scroll_bar: Scroll bar control element
            
        Returns:
            dict: Dictionary containing found components
        """
        try:
            from typing import Union, Dict, Any
            components: Dict[str, Any] = {
                'up_button': None,
                'down_button': None,
                'thumb': None
            }
            
            # Search for child controls within the scroll bar
            for child in scroll_bar.GetChildren():
                try:
                    if hasattr(child, 'ControlType'):
                        control_type = child.ControlType
                        child_class = getattr(child, 'ClassName', '')
                        
                        LOGGER_DEBUG(f"Child control: Type={control_type}, Class={child_class}")
                        
                        # Check for button controls (arrow buttons)
                        if control_type == auto.ControlType.ButtonControl:
                            rect = child.BoundingRectangle
                            scroll_rect = scroll_bar.BoundingRectangle
                            
                            # Determine position relative to scroll bar
                            if rect.top <= scroll_rect.top + 30:  # Near top
                                components['up_button'] = child
                                LOGGER_INFO(f"Found UP button: {child}")
                            elif rect.bottom >= scroll_rect.bottom - 30:  # Near bottom
                                components['down_button'] = child
                                LOGGER_INFO(f"Found DOWN button: {child}")
                        
                        # Check for thumb/slider controls
                        elif control_type == auto.ControlType.ThumbControl:
                            components['thumb'] = child
                            LOGGER_INFO(f"Found thumb: {child}")
                            
                except Exception as e:
                    LOGGER_DEBUG(f"Error processing child control: {e}")
                    continue
            
            # Fallback: Find buttons by position if not found by control type
            if not components['up_button'] or not components['down_button']:
                fallback_buttons = self._find_buttons_by_position(scroll_bar)
                if fallback_buttons:  # Check if fallback_buttons is not None
                    up_btn = fallback_buttons.get('up_button')
                    down_btn = fallback_buttons.get('down_button')
                    if not components['up_button'] and up_btn:
                        components['up_button'] = up_btn
                    if not components['down_button'] and down_btn:
                        components['down_button'] = down_btn
            
            return components
            
        except Exception as e:
            LOGGER_ERROR(f"Error finding scroll bar buttons: {e}")
            return {'up_button': None, 'down_button': None, 'thumb': None}
    
    def _find_buttons_by_position(self, scroll_bar):
        """
        Find buttons by their position within scroll bar (fallback method)
        
        Args:
            scroll_bar: Scroll bar control element
            
        Returns:
            dict: Dictionary with up_button and down_button
        """
        try:
            rect = scroll_bar.BoundingRectangle
            button_height = 20  # Typical button height
            
            # Create virtual button areas
            up_button_area = {
                'left': rect.left,
                'top': rect.top,
                'right': rect.right,
                'bottom': rect.top + button_height
            }
            
            down_button_area = {
                'left': rect.left,
                'top': rect.bottom - button_height,
                'right': rect.right,
                'bottom': rect.bottom
            }
            
            LOGGER_INFO(f"Created virtual button areas - UP: {up_button_area}, DOWN: {down_button_area}")
            
            return {
                'up_button': up_button_area,
                'down_button': down_button_area
            }
            
        except Exception as e:
            LOGGER_ERROR(f"Error creating virtual buttons: {e}")
            return {'up_button': None, 'down_button': None}
    
    def _is_orientation_match(self, scroll_bar, orientation):
        """
        Check if scroll bar matches the desired orientation
        
        Args:
            scroll_bar: Scroll bar control
            orientation (str): "vertical" or "horizontal"
            
        Returns:
            bool: True if orientation matches
        """
        try:
            rect = scroll_bar.BoundingRectangle
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            if orientation == "vertical":
                return height > width
            elif orientation == "horizontal":
                return width > height
            else:
                return True  # Any orientation
                
        except:
            return True  # If we can't determine, assume it matches
    
    def scroll_using_arrow_buttons(self, scroll_bar, direction="down", clicks=10):
        """
        Scroll using arrow buttons (most reliable method)
        
        Args:
            scroll_bar: Scroll bar control element
            direction (str): "up" or "down"
            clicks (int): Number of button clicks
            
        Returns:
            bool: True if operation was successful
        """
        try:
            # Find arrow buttons
            components = self.find_scroll_bar_buttons(scroll_bar)
            
            if direction == "down":
                button = components['down_button']
                button_name = "DOWN"
            else:  # direction == "up"
                button = components['up_button']
                button_name = "UP"
            
            if not button:
                LOGGER_ERROR(f"No {button_name} arrow button found")
                return False
            
            LOGGER_INFO(f"Clicking {button_name} arrow button {clicks} times")
            
            # Click the button multiple times
            for i in range(clicks):
                try:
                    if isinstance(button, dict):  # Virtual button area
                        center_x = (button['left'] + button['right']) // 2
                        center_y = (button['top'] + button['bottom']) // 2
                        auto.Click(center_x, center_y)
                    else:  # Real control
                        button.Click()
                    
                    # Small delay between clicks
                    time.sleep(0.05)
                    
                except Exception as e:
                    LOGGER_WARNING(f"Click {i+1} failed: {e}")
                    continue
            
            LOGGER_INFO(f"Successfully clicked {button_name} button {clicks} times")
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Error scrolling using arrow buttons: {e}")
            return False


# Wrapper functions for YAML test cases
def scroll_using_arrow_buttons_only(container_automation_id, direction="down", click_count=10, timeout=5):
    """
    YAML interface function for arrow button scrolling
    
    Args:
        container_automation_id (str): AutomationId of container
        direction (str): "up" or "down"
        click_count (int): Number of clicks
        timeout (int): Search timeout
        
    Returns:
        bool: True if successful
    """
    try:
        manager = ScrollBarManager()
        
        # Find the scroll bar
        scroll_bar = manager.find_scroll_bar(container_automation_id, "vertical", timeout)
        if not scroll_bar:
            LOGGER_ERROR(f"Could not find scroll bar in container: {container_automation_id}")
            return False
        
        # Perform scroll using arrow buttons
        return manager.scroll_using_arrow_buttons(scroll_bar, direction, click_count)
        
    except Exception as e:
        LOGGER_ERROR(f"Error in scroll_using_arrow_buttons_only: {e}")
        return False

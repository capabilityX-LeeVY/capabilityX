"""
Linux Control - Platform-specific implementation for Linux/AT-SPI

This module provides the main control class for Linux using AT-SPI
(Assistive Technology Service Provider Interface).
"""

import hashlib
import time
import pyatspi
from gi.repository import Atspi

from rs_sdk.framework.abstract_control import BaseControl
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.platform.linux.linux_control_handler import ControlHandler
from rs_sdk.platform.linux.linux_control_singleton import Control
from rs_sdk.utils.control_db import ControlDB


class LinuxControl(BaseControl):
    """
    Linux-specific control implementation using AT-SPI.
    
    This class provides control access and manipulation for Linux applications
    using the AT-SPI accessibility framework.
    """
    
    def __init__(self):
        """Initialize and get the currently focused control."""
        self.control_handler = ControlHandler()
        self.control_db = ControlDB()
        self.control = Control()
        self.element = None
        self.pre_element = None
        
        try:
            # Check if we should use the focus listener's cached focus
            if self.control.toggle_listener:
                self.element = self.control.current_focus
                self.pre_element = self.control.previous_focus
            else:
                # Get the currently focused element via AT-SPI
                desktop = pyatspi.Registry.getDesktop(0)
                self.element = self._get_focused_element(desktop)
            
            if not self.element:
                LOGGER_ERROR("Failed to initialize: No focused element found.", "RED")
        except Exception as e:
            LOGGER_ERROR(f"Failed to initialize Linux control: {e}", "RED")
    
    def _get_focused_element(self, accessible):
        """Recursively find the focused element in the accessibility tree."""
        try:
            state_set = accessible.getState()
            if state_set.contains(pyatspi.STATE_FOCUSED):
                return accessible
            
            for i in range(accessible.childCount):
                child = accessible.getChildAtIndex(i)
                focused = self._get_focused_element(child)
                if focused:
                    return focused
        except Exception as e:
            LOGGER_DEBUG(f"Error traversing accessibility tree: {e}")
        
        return None
    
    def refresh(self, force_update=False):
        """
        Refresh the control element. If invalid, attempt to get from system.
        
        Args:
            force_update: If True, force get the focused element from system instead of cache
        """
        if force_update:
            # Force update from system
            try:
                desktop = pyatspi.Registry.getDesktop(0)
                forced_element = self._get_focused_element(desktop)
                if forced_element:
                    self.element = forced_element
                    # Update global state only if element is valid
                    self.control.current_focus = forced_element
                    LOGGER_DEBUG("[Force Refresh] Updated element")
                    return forced_element
            except Exception as e:
                LOGGER_WARNING(f"Failed to force refresh element: {e}")
        
        # Normal refresh logic
        if not self.element:
            try:
                desktop = pyatspi.Registry.getDesktop(0)
                new_element = self._get_focused_element(desktop)
                if new_element:
                    self.pre_element = self.element
                    self.element = new_element
                    self.control.current_focus = new_element
                    LOGGER_DEBUG("[Refresh] Updated focused element")
                    return new_element
            except Exception as e:
                LOGGER_WARNING(f"Failed to refresh element: {e}")
        
        return self.element
    
    def get_control_name(self):
        """Get the name of the current control."""
        if not self.element:
            return ""
        try:
            return self.element.name or ""
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control name: {e}")
            return ""
    
    def get_control_role(self):
        """Get the role of the current control."""
        if not self.element:
            return ""
        try:
            return self.element.getRoleName() or ""
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control role: {e}")
            return ""
    
    def get_control_description(self):
        """Get the description of the current control."""
        if not self.element:
            return ""
        try:
            return self.element.description or ""
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control description: {e}")
            return ""
    
    def click(self):
        """Click the current control."""
        if not self.element:
            LOGGER_WARNING("No element to click")
            return False
        
        try:
            action = self.element.queryAction()
            if action and action.nActions > 0:
                action.doAction(0)  # Perform the default action
                LOGGER_DEBUG(f"Clicked control: {self.get_control_name()}")
                return True
        except Exception as e:
            LOGGER_WARNING(f"Failed to click control: {e}")
        
        return False
    
    def get_control_hash(self):
        """Generate a hash for the current control based on its properties."""
        if not self.element:
            return ""
        
        try:
            name = self.get_control_name()
            role = self.get_control_role()
            description = self.get_control_description()
            
            control_string = f"{name}|{role}|{description}"
            return hashlib.sha256(control_string.encode()).hexdigest()
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate control hash: {e}")
            return ""
    
    def get_control_id(self):
        """Get the ID of the current control."""
        if not self.element:
            return ""
        try:
            # AT-SPI doesn't have a direct ID property, use accessible_id if available
            return getattr(self.element, 'accessible_id', '') or ""
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control ID: {e}")
            return ""
    
    def get_control_id_hash(self):
        """Get a hash-based ID for the current control."""
        return self.get_control_hash()
    
    def get_control_type(self):
        """Get the type/role number of the current control."""
        if not self.element:
            return 0
        try:
            return self.element.getRole()
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control type: {e}")
            return 0
    
    def get_control_type_name(self):
        """Get the type/role name of the current control."""
        return self.get_control_role()
    
    def get_control_help_text(self):
        """Get the help text of the current control."""
        if not self.element:
            return ""
        try:
            return self.element.description or ""
        except Exception as e:
            LOGGER_WARNING(f"Failed to get help text: {e}")
            return ""
    
    def get_fulldescription(self):
        """Get the full description of the current control."""
        if not self.element:
            return ""
        try:
            name = self.get_control_name()
            role = self.get_control_role()
            description = self.get_control_description()
            return f"{name} | {role} | {description}"
        except Exception as e:
            LOGGER_WARNING(f"Failed to get full description: {e}")
            return ""
    
    def get_control_ancestor_element(self):
        """Get the parent element of the current control."""
        return self.get_control_parent()
    
    def get_control_all_ancestor_elements(self):
        """Get all ancestor elements of the current control."""
        ancestors = []
        if not self.element:
            return ancestors
        
        try:
            current = self.element
            while current:
                parent = current.parent
                if parent:
                    ancestors.append(parent)
                    current = parent
                else:
                    break
        except Exception as e:
            LOGGER_WARNING(f"Failed to get ancestor elements: {e}")
        
        return ancestors
    
    def get_control_ancestor_levels_elements(self):
        """Get ancestor elements organized by level."""
        return self.get_control_all_ancestor_elements()
    
    def get_control_previous_sibling(self):
        """Get the previous sibling of the current control."""
        if not self.element:
            return None
        
        try:
            parent = self.element.parent
            if parent:
                index = self.element.getIndexInParent()
                if index > 0:
                    return parent.getChildAtIndex(index - 1)
        except Exception as e:
            LOGGER_WARNING(f"Failed to get previous sibling: {e}")
        
        return None
    
    def get_control_next_sibling(self):
        """Get the next sibling of the current control."""
        if not self.element:
            return None
        
        try:
            parent = self.element.parent
            if parent:
                index = self.element.getIndexInParent()
                if index < parent.childCount - 1:
                    return parent.getChildAtIndex(index + 1)
        except Exception as e:
            LOGGER_WARNING(f"Failed to get next sibling: {e}")
        
        return None
    
    def get_control_parent(self):
        """Get the parent element of the current control."""
        if not self.element:
            return None
        
        try:
            return self.element.parent
        except Exception as e:
            LOGGER_WARNING(f"Failed to get parent: {e}")
            return None
    
    def get_control_process_id(self):
        """Get the process ID of the application owning this control."""
        if not self.element:
            return 0
        
        try:
            app = self.element.getApplication()
            if app:
                return app.get_process_id() if hasattr(app, 'get_process_id') else 0
        except Exception as e:
            LOGGER_WARNING(f"Failed to get process ID: {e}")
        
        return 0
    
    def get_control_runtime_id(self):
        """Get a runtime ID for the current control."""
        # AT-SPI doesn't have runtime IDs like Windows UIA, use a hash-based approach
        return self.get_control_hash()
    
    def get_control_accesskey(self):
        """Get the access key (keyboard shortcut) for the current control."""
        if not self.element:
            return ""
        
        try:
            # Try to get keyboard shortcut from accessible attributes
            attrs = self.element.getAttributes()
            for attr in attrs:
                if 'accesskey' in attr.lower() or 'shortcut' in attr.lower():
                    return attr.split(':', 1)[1] if ':' in attr else ""
        except Exception as e:
            LOGGER_DEBUG(f"No access key found: {e}")
        
        return ""
    
    def get_control_Level(self):
        """Get the nesting level of the current control in the accessibility tree."""
        if not self.element:
            return 0
        
        level = 0
        try:
            current = self.element
            while current and current.parent:
                level += 1
                current = current.parent
        except Exception as e:
            LOGGER_WARNING(f"Failed to get control level: {e}")
        
        return level
    
    def get_control_from_name(self, name):
        """Find a control by name in the accessibility tree."""
        if not self.element:
            return None
        
        try:
            # Search from desktop root
            desktop = pyatspi.Registry.getDesktop(0)
            return self._search_by_name(desktop, name)
        except Exception as e:
            LOGGER_WARNING(f"Failed to find control by name: {e}")
            return None
    
    def _search_by_name(self, accessible, name):
        """Recursively search for a control with the given name."""
        try:
            if accessible.name == name:
                return accessible
            
            for i in range(accessible.childCount):
                child = accessible.getChildAtIndex(i)
                result = self._search_by_name(child, name)
                if result:
                    return result
        except Exception as e:
            LOGGER_DEBUG(f"Error searching by name: {e}")
        
        return None
    
    def get_control_toggle_state(self, control_name):
        """Get the toggle state of a control (for checkboxes, toggle buttons, etc.)."""
        element = self.get_control_from_name(control_name) if control_name else self.element
        if not element:
            return False
        
        try:
            state_set = element.getState()
            return state_set.contains(pyatspi.STATE_CHECKED)
        except Exception as e:
            LOGGER_WARNING(f"Failed to get toggle state: {e}")
            return False


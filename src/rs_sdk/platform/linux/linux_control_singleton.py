"""
Linux Control Singleton - Platform-specific implementation for Linux/AT-SPI

This module provides a singleton Control class for Linux that maintains
state of focused controls similar to the Windows Control class.
"""

import pyatspi
from common.utils.featureToggle import FeatureToggle


class Control:
    """
    Singleton control class for Linux platform.
    
    Maintains the current and previous focused controls in the Linux accessibility tree.
    Uses AT-SPI (Assistive Technology Service Provider Interface) instead of UIAutomation.
    """
    
    _instance = None  # Singleton instance
    _current_focus = None  # Current focused accessible element
    _previous_focus = None  # Previous focused accessible element

    handler = None
    toggle_listener = True
    PREVALIDATEDCONTROLS = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Control, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_cropped_image'):
            self._cropped_image = FeatureToggle.isEnabled('croppedImage')
    
    @property
    def current_focus(self):
        """Get the current focused accessible element."""
        return self._current_focus
    
    @current_focus.setter
    def current_focus(self, new_focus):
        """
        Set the current focused accessible element.
        
        Args:
            new_focus: pyatspi.Accessible object or None
        """
        if new_focus and new_focus != self._current_focus:
            if self._cropped_image and self._current_focus:
                self._previous_focus = self._current_focus
            self._current_focus = new_focus

    @property
    def previous_focus(self):
        """Get the previous focused accessible element."""
        return self._previous_focus

    @previous_focus.setter
    def previous_focus(self, old_focus):
        """
        Set the previous focused accessible element.
        
        Args:
            old_focus: pyatspi.Accessible object or None
        """
        self._previous_focus = old_focus

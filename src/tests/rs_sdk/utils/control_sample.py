from comtypes.gen import UIAutomationClient
from common.utils.featureToggle import FeatureToggle

class Control:
    _instance = None  # Singleton instance
    # current_focus: UIAutomationClient.IUIAutomationElement = None # type: ignore
    _current_focus: UIAutomationClient.IUIAutomationElement = None  # type: ignore
    _previous_focus: UIAutomationClient.IUIAutomationElement = None  # type: ignore

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
        return self._current_focus
    
    @current_focus.setter
    def current_focus(self, new_focus: UIAutomationClient.IUIAutomationElement):
        if new_focus and new_focus != self._current_focus:
            if self._cropped_image and self._current_focus:
                self._previous_focus = self._current_focus  # 
            self._current_focus = new_focus

    @property
    def previous_focus(self):
        return self._previous_focus

    @previous_focus.setter
    def previous_focus(self, old_focus: UIAutomationClient.IUIAutomationElement):
        self._previous_focus = old_focus


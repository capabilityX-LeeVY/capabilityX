# sdk/factory.py
import platform
from rs_sdk.platform.windows.windows_navigate import WindowsNavigate

class NavigatorFactory:
    """Factory class to create control instances based on the current platform."""

    def __init__(self):
        self.platform = platform.system()
        
    def create_navigator(self):
        """Create and return a control instance based on the current platform."""
        if self.platform == "Windows":
            return WindowsNavigate()
        else:
            raise NotImplementedError(f"{self.platform} platform is not supported yet.")

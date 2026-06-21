# sdk/factory.py
import platform

_current_platform = platform.system()

# Conditional imports for platform-specific modules
if _current_platform == "Windows":
    from rs_sdk.platform.windows.windows_control import WindowsControl as Control
elif _current_platform == "Linux":
    from rs_sdk.platform.linux.linux_control import LinuxControl as Control

class ControlFactory:
    """Factory class to create control instances based on the current platform."""

    def __init__(self):
        self.platform = _current_platform

    def create_control(self):
        """Create and return a control instance based on the current platform."""
        if self.platform in ["Windows", "Linux"]:
            return Control()
        else:
            raise NotImplementedError(f"Platform '{self.platform}' is not supported")
        
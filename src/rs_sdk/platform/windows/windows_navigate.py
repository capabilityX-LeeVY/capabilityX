from rs_sdk.platform.windows.windows_navigator_handler import WindowsNavigateHandler

class WindowsNavigate():
    """Class to traverse application menu controls using SendKeys."""

    def __init__(self):
        """Initialize the class and set up initial state."""
        self.navigator = WindowsNavigateHandler()

    def windows_navigate(self):
        """Public method to start control traversal."""
        self.navigator.traverse_control()

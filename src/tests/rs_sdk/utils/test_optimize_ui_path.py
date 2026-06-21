import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from core.windows.control_locator import ControlLocator
from rs_sdk.utils.control import Control
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

class TestOptimizeUIPath:
    def __init__(self):
        self.control_locator = ControlLocator()

    def test_specific_ui_path_optimization(self):
        LOGGER_INFO("=== Testing Specific UI Path Optimization ===", "CYAN")

        Control.PREVALIDATEDCONTROLS = ['Settings navigation, Menu, Use up and down arrow keys to navigate Level 2, Background  Menu Item, Selected. 1 of 1', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Sharing content  Menu Item, Unselected. 4 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Notifications Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 5 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Appearance  Menu Item, Unselected. 6 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Accessibility  Menu Item, Unselected. 7 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Keyboard shortcuts  Menu Item, Unselected. 8 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Privacy  Menu Item, Unselected. 9 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Messaging  Menu Item, Unselected. 10 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Meetings Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 11 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Calling  Menu Item, Unselected. 12 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Devices  Menu Item, Unselected. 13 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Accessories  Menu Item, Unselected. 14 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Accessories  Menu Item, Unselected. 14 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Devices  Menu Item, Unselected. 13 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Calling  Menu Item, Unselected. 12 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Meetings Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 11 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Messaging  Menu Item, Unselected. 10 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Privacy  Menu Item, Unselected. 9 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Keyboard shortcuts  Menu Item, Unselected. 8 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Accessibility  Menu Item, Unselected. 7 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Appearance  Menu Item, Unselected. 6 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Notifications Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 5 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Sharing content  Menu Item, Unselected. 4 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Video Menu group expanded, Unselected,  Use right arrow key to open group, use left arrow key to close group, 3 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 2, Smart audio  Menu Item, Unselected. 1 of 1', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Audio Menu group expanded, Unselected,  Use right arrow key to open group, use left arrow key to close group, 2 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, General  Menu Item, Unselected. 1 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, General  Menu Item, Unselected. 1 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Audio Menu group expanded, Unselected,  Use right arrow key to open group, use left arrow key to close group, 2 of 14', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 2, Smart audio  Menu Item, Unselected. 1 of 1', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Video Menu group expanded, Unselected,  Use right arrow key to open group, use left arrow key to close group, 3 of 14', ' None, ', ' Blur, 2 of 12, Unselected', ' Add virtual background, Button, For best results, use an image file or a video file with a resolution that is 480 x 360 pixels or higher but does not exceed 1920 x 1080 pixels., 3 of 12', ' Executive office, 4 of 12, Unselected', ' Home office, 5 of 12, Unselected', ' Lookout, 6 of 12, Unselected', ' Daylight, 7 of 12, Unselected', ' Fountain, 8 of 12, Unselected', ' Dark, 9 of 12, Unselected', ' Lava, 10 of 12, Unselected', ' Download Aurora image, Animated virtual background, 11 of 12, Unselected', ' Download Silhouette image, Animated virtual background, 12 of 12, Unselected', ' Download Silhouette image, Animated virtual background, 12 of 12, Unselected', ' Download Aurora image, Animated virtual background, 11 of 12, Unselected', ' Lava, 10 of 12, Unselected', ' Dark, 9 of 12, Unselected', ' Fountain, 8 of 12, Unselected', ' Daylight, 7 of 12, Unselected', ' Lookout, 6 of 12, Unselected', ' Home office, 5 of 12, Unselected', ' Executive office, 4 of 12, Unselected', ' Add virtual background, Button, For best results, use an image file or a video file with a resolution that is 480 x 360 pixels or higher but does not exceed 1920 x 1080 pixels., 3 of 12', ' Blur, 2 of 12, Unselected', ' None, ']

        test_control_path = ['Audio options', 'Audio Settings..., Menu item', 'Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Video Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 3 of 14', ' Rotate']

        result = self.control_locator._optimize_ui_path(test_control_path)
        
        LOGGER_INFO(f"Optimized Result: {result}", "GREEN")

        expected = ['Settings navigation, Menu, Use up and down arrow keys to navigate Level 1, Video Menu group collapsed, Unselected,  Use right arrow key to open group, use left arrow key to close group, 3 of 14', ' Rotate']

        if result == expected:
            LOGGER_INFO("✓ Test PASSED: Found matching control and returned optimized path", "GREEN")
            return True
        else:
            LOGGER_ERROR("✗ Test FAILED: Expected optimized path not returned", "RED")
            return False

    def run_test(self):
        LOGGER_INFO("Starting Specific UI Path Optimization Test...", "MAGENTA")
        LOGGER_INFO("=" * 60, "MAGENTA")
        
        try:
            success = self.test_specific_ui_path_optimization()
            print()
            
            LOGGER_INFO("=" * 60, "MAGENTA")
            if success:
                LOGGER_INFO("Test completed successfully!", "GREEN")
            else:
                LOGGER_ERROR("Test failed!", "RED")
            
        except Exception as e:
            LOGGER_ERROR(f"Test execution failed with error: {e}", "RED")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_instance = TestOptimizeUIPath()
    test_instance.run_test()

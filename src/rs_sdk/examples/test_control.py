import logging
import time
import subprocess
import uiautomation as auto

from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.factory.navigator_factory import NavigatorFactory
from tests.rs_sdk.utils.event_listener_sample import FocusListener
from tests.rs_sdk.utils.control_sample import Control
# from acc.common import accUIA


def test_notepad_navigation():
    
    if Control.toggle_listener:
        listener = FocusListener()
        listener.start()

    subprocess.Popen("notepad.exe")
    time.sleep(2)  # Wait for Notepad to launch
    auto.SendKeys("{Alt}")  # focus on menu bar if not in menu
    time.sleep(0.5)
    auto.SendKeys("{Tab}")

    navigator = NavigatorFactory().create_navigator()
    navigator.windows_navigate()

    auto.SendKeys("{Alt} + {F4}")  # Close Notepad

def test_webex_app():
    """Test and log the focused control's name and type."""
    listener = FocusListener()
    listener.start()
    Control = Control()  # 使用实例

    try:
        while True:
            try:
                previous_control = Control.previous_focus  # 获取上一个控件
                current_control = Control.current_focus  # 获取当前控件

                prev_name = previous_control.CurrentName if previous_control else "None"
                curr_name = current_control.CurrentName if current_control else "None"

                print(f"Previous Control Name: {prev_name}")
                print(f"Current Control Name: {curr_name}")

                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()

def test_get_focused_control():
    """Test and log the focused control's name and type."""
    listener = FocusListener()
    listener.start()
    control_factory = ControlFactory()

    try:
        while True:
            control = control_factory.create_control()
            if control:
                logging.info(f"Control Name: {control.get_control_name()}")
                logging.info(f"Control Id: {control.get_control_id()}")
                logging.info(f"Control Type: {control.get_control_type()}")
                logging.info(f"Control Type Name: {control.get_control_type_name()}")
                logging.info(f"Control Full Description: {control.get_fulldescription()}")
                logging.info(f"Control ancestor name: {control.get_control_ancestor_element()}")
                logging.info(f"Control all ancestors: {control.get_control_all_ancestor_elements()}")
                logging.info(f"Control ancestors level 1 to level 2: {control.get_control_ancestor_levels_elements()}")
                logging.info(f"Control previous sibling name: {control.get_control_previous_sibling()}")
                logging.info(f"Control next sibling name: {control.get_control_next_sibling()}")
                logging.info(f"Control parent name: {control.get_control_parent()}")
                logging.info(f"Control help text: {control.get_control_help_text()}")
            else:
                logging.error("Failed to create control.")

            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()


def test_focus_listener():
    """Test the focus change listener."""
    listener = FocusListener()
    listener.start()
    
    input("Press Enter to stop listening...\n")  # Wait for user input to stop the listener
    
    listener.stop()
    print("Focus listener test completed.")

import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from rs_sdk.utils.control_handler import ControlHandler
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

class TestUIPath:
    def __init__(self, control_handler):
        self.control_handler = control_handler

    def test_generate_optimal_control_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_handler.generate_optimal_control_path(current_control_level, target_control_name)
        LOGGER_INFO(f"Optimal Control Path: {optimal_control_path}", "GREEN")

    def test_generate_optimal_control_second_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_handler.generate_optimal_control_second_path(current_control_level, target_control_name)
        LOGGER_INFO(f"Optimal Control Second Path: {optimal_control_path}", "GREEN")

    def test_generate_optimal_control_all_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_handler.generate_optimal_control_all_path(current_control_level, target_control_name)
        LOGGER_INFO(f"Optimal Control all Path: {optimal_control_path}", "GREEN")

    def test_generate_optimal_control_min_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_handler.generate_optimal_control_min_path(current_control_level, target_control_name)
        LOGGER_INFO(f"Optimal Control min Path: {optimal_control_path}", "GREEN")

    def test_get_last_from_control_name(self, control_name):
        last_control_name = self.control_handler.get_last_from_control_name(control_name)
        from_control_name = self.control_handler.get_from_control_name(control_name)
        LOGGER_INFO(f"From Control Name: {from_control_name}", "GREEN")
        LOGGER_INFO(f"Last Control Name: {last_control_name}", "GREEN")

    def test_generate_ui_path_by_index(self, hierarchical_level, start_level):
        optimal_control_path = self.control_handler.generate_ui_path_by_index(hierarchical_level, start_level)
        LOGGER_INFO(f"UI Path by index: {optimal_control_path}", "GREEN")

    # def test_get_control_Level_by_prefix_name(self, prefix_name, control_id):
    #     control_level = self.control_handler.get_control_Level_by_prefix_name(prefix_name, control_id)
    #     LOGGER_INFO(f"Control Level by prefix name: {control_level}", "GREEN")

    def test_get_control_Level_by_prefix_name_and_id(self, prefix_name, control_id):
        control_level = self.control_handler.get_control_Level_by_prefix_name_and_id(prefix_name, control_id)
        LOGGER_INFO(f"Control Level by prefix name and control ID: {control_level}", "GREEN")


if __name__ == "__main__":
    # Example usage: you can replace the parameters with actual values
    test_instance = TestUIPath(ControlHandler())
    test_instance.test_generate_ui_path_by_index('2.1.1.2.3.2.1.13.1.5.2', 1)
    # test_instance.test_generate_optimal_control_path(10, " Test Speaker")
    # test_instance.test_generate_optimal_control_min_path(2, " Blur, 2 of 12, Unselected")
    # test_instance.test_generate_optimal_control_second_path(2, " Webex Menu")
    # test_instance.test_get_control_Level_by_prefix_name("Mute", "Main_CallStripButton_Audio")
    # test_instance.test_get_control_Level_by_prefix_name_and_id("Annotate", None)
    # test_instance.test_get_control_Level_by_prefix_name_and_id("Mute", "Main_CallStripButton_Audio")
    # test_instance.test_get_last_from_control_name(" Webex Menu")


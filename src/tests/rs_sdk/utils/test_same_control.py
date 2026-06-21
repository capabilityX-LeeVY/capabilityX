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

    def test_get_control_is_validated_prefix(self, control_name):
        control_name_normolize = self.control_handler.extract_prefix(control_name)
        is_validated_status = self.control_handler.get_control_is_validated_prefix(control_name_normolize)
        LOGGER_INFO(f"control name: {control_name_normolize}, is_validated_status: {is_validated_status}", "GREEN")

    def test_are_controls_same(self, control1, control2):
        """Test the enhanced are_controls_same method to verify if two controls are considered the same"""
        LOGGER_INFO(f"Testing enhanced are_controls_same method:", "CYAN")
        LOGGER_INFO(f"Control 1: {control1}", "YELLOW")
        LOGGER_INFO(f"Control 2: {control2}", "YELLOW")
        
        # Test the enhanced are_controls_same method
        result = self.control_handler.are_controls_same(control1, control2)
        
        LOGGER_INFO(f"Final Result: {result}", "GREEN" if result else "RED")
        LOGGER_INFO("-" * 80, "WHITE")
        
        return result
    
    def test_are_controls_tree_same(self, control1, control2):
        """Test the enhanced are_controls_tree_same method to verify if two controls are considered the same"""
        LOGGER_INFO(f"Testing enhanced are_controls_tree_same method:", "CYAN")
        LOGGER_INFO(f"Control 1: {control1}", "YELLOW")
        LOGGER_INFO(f"Control 2: {control2}", "YELLOW")

        # Test the enhanced are_controls_tree_same method
        result = self.control_handler.are_controls_tree_same(control1, control2)
        
        LOGGER_INFO(f"Final Result: {result}", "GREEN" if result else "RED")
        LOGGER_INFO("-" * 80, "WHITE")
        
        return result

    def test_normalize_control_tree_name(self, control_name):
        """Test the normalize_control_tree_name method to verify control name normalization"""
        LOGGER_INFO(f"Testing normalize_control_tree_name method:", "CYAN")
        LOGGER_INFO(f"Original Control: {control_name}", "YELLOW")
        
        # Test the normalize_control_tree_name method
        result = self.control_handler.normalize_control_tree_name(control_name)
        
        LOGGER_INFO(f"Normalized Result: {result}", "GREEN")
        LOGGER_INFO("-" * 80, "WHITE")
        
        return result


if __name__ == "__main__":
    # Example usage: you can replace the parameters with actual values
    test_instance = TestUIPath(ControlHandler())
    
    # Test normalize_control_tree_name method
    LOGGER_INFO("=" * 80, "CYAN")
    LOGGER_INFO("Testing normalize_control_tree_name method:", "CYAN")
    LOGGER_INFO("=" * 80, "CYAN")
    
    control1 = 'Level 1 Video Tree item Selected collapsed 3 of 14'
    control2 = 'Level 1 Videos Tree item Selected expanded 3 of 14'
    # test_instance.test_normalize_control_tree_name(control1)
    test_instance.test_are_controls_tree_same(control1, control2)
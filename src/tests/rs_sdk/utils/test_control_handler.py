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

def test_generate_optimal_control_path(control_handler):
    current_control_level = 1
    target_control_name =  "Annotate" #" Blur, 2 of 12, Unselected" # "More sharing options"

    optimal_control_path = control_handler.generate_optimal_control_path(
        current_control_level, target_control_name
    )

    LOGGER_INFO(f"Optimal Control Path: {optimal_control_path}", "GREEN")

# test_generate_optimal_control_path(ControlHandler())

def test_get_last_from_control_name(control_handler):
    control_name = "Share"
    last_control_name = control_handler.get_last_from_control_name(control_name)
    from_control_name = control_handler.get_from_control_name(control_name)
    LOGGER_INFO(f"From Control Name: {from_control_name}", "GREEN")
    LOGGER_INFO(f"Last Control Name: {last_control_name}", "GREEN")

# test_get_last_from_control_name(ControlHandler())

def test_control_is_validated_prefix(control_handler):
    control_name = "Ebene 1, Registerkarte Allgemein"
    is_validated_status =control_handler.get_control_is_validated_prefix(control_name)
    LOGGER_INFO(f"Control Name: {is_validated_status}", "GREEN")

# test_control_is_validated_prefix(ControlHandler())

def test_normalize_control_id(control_handler):
    control_id = "SparkApp.RecordControlPopupView.RecordControlView_QMLTYPE_835.recordingMenu_saveOptions"
    patterns_to_strip = ["_QML_", "_QMLTYPE_"]
    normalized_control_id = control_handler.normalize_control_id(control_id, patterns_to_strip)
    LOGGER_INFO(f"Normalized Control ID: {normalized_control_id}", "GREEN")

# test_normalize_control_id(ControlHandler())

def test_get_control_window_automation_id(control_handler):
    control_name = " Sign up"
    window_automation_id = control_handler.get_control_window_automation_id(control_name)
    LOGGER_INFO(f"Control Name: {control_name}, Window Automation ID: {window_automation_id}", "GREEN")

test_get_control_window_automation_id(ControlHandler())
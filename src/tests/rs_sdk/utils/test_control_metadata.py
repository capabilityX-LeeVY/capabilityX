"""
Test: control_metadata focus-change printer
-----------------------------------------
Run this script, then switch focus in the Webex app (Tab / click).
Each focus change prints:
  1. current_name   — CurrentName  (with force_update + ValuePattern fallbacks)
  2. current_id     — CurrentAutomationId
  3. control_value  — ValuePattern.CurrentValue
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

import time
from common.utils.logger import LOGGER_INFO
from rs_sdk.utils.event_listener import FocusListener
from rs_sdk.utils.control_metadata import ControlMetadata


def test_control_metadata_on_focus_change():
    """Print control_metadata properties on every focus change."""
    listener = FocusListener()
    listener.start()

    metadata = ControlMetadata()
    time.sleep(1)  # let listener settle

    LOGGER_INFO("=== control_metadata focus-change test started ===", "GREEN")
    LOGGER_INFO("Switch focus in Webex (Tab / click). Press Ctrl+C to stop.\n", "CYAN")

    step = 0

    try:
        while True:
            step += 1
            meta = metadata.get_control_metadata()
            ctrl = metadata.current_control

            current_name  = meta.get("name")
            current_id    = meta.get("id")
            control_value = ctrl.ControlValue

            LOGGER_INFO(f"[{step}] current_name  : {current_name!r}", "CYAN")
            LOGGER_INFO(f"[{step}] current_id    : {current_id!r}", "CYAN")
            LOGGER_INFO(f"[{step}] control_value : {control_value!r}", "CYAN")
            LOGGER_INFO("---", "CYAN")

            time.sleep(1)

    except KeyboardInterrupt:
        LOGGER_INFO("\n=== Test stopped ===", "YELLOW")
    finally:
        listener.stop()


if __name__ == "__main__":
    test_control_metadata_on_focus_change()

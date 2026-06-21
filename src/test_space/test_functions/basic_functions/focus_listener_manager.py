"""
focus_listener_manager.py

Resets the FocusListener by stopping and restarting it.
Use this after manually clicking/focusing a control before a keyboard navigation
test, to ensure the listener reflects the current focus state cleanly.
"""

import sys
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING

if sys.platform == "win32":
    from rs_sdk.utils.event_listener import FocusListener
else:
    from rs_sdk.platform.linux import FocusListener


def reset_focus_listener():
    """
    Stop and restart the FocusListener to clear any stale focus state.

    Call this after manually setting focus on a feature window, before
    running an acc_sequence traversal, so the listener picks up the
    correct initial focused element.

    Returns:
        bool: True if reset succeeded.
    """
    try:
        listener = FocusListener()
        listener.stop()
        listener.start()
        LOGGER_INFO("[reset_focus_listener] FocusListener restarted successfully.", "GREEN")
        return True
    except Exception as e:
        LOGGER_WARNING(f"[reset_focus_listener] Failed to reset FocusListener: {e}")
        return False

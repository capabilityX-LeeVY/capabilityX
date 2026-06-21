"""
sr_content_collector.py

Collects all screen-reader-accessible content from a target window by
traversing the UIA tree. Returns the text content that a screen reader
would announce for every element under the target.
"""

import sys

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

if sys.platform == "win32":
    import comtypes.client
    from comtypes.client import GetModule
    GetModule('oleacc.dll')
    GetModule('UIAutomationCore.dll')
    from comtypes.gen import UIAutomationClient
    from comtypes import GUID

    UIA_CLSID = GUID('{FF48DBA4-60EF-4201-AA87-54103EEF594E}')
    uia = comtypes.client.CreateObject(UIA_CLSID, interface=UIAutomationClient.IUIAutomation)


# UIA control type IDs that represent a window/dialog container
WINDOW_CONTROL_TYPES = {
    50032,  # Window
    50033,  # Pane
}


def collect_sr_content(window_title: str = None, max_depth: int = 25, root_element=None) -> dict:
    """
    Traverse the UIA tree of the target window and collect every element's
    accessible name (what a screen reader would announce).

    Args:
        window_title: Optional window title. Ignored if root_element provided.
        max_depth: Maximum tree traversal depth (safety guard).
        root_element: Optional UIA element to traverse from. Use this to scope
                      collection to a specific dialog/sub-window.

    Returns:
        dict with keys:
            - "items": list of {"name", "control_type", "localized_type"}
            - "all_text": newline-joined names for substring matching
            - "count": number of elements collected
    """
    if sys.platform != "win32":
        LOGGER_WARNING("[sr_content_collector] Only supported on Windows")
        return {"items": [], "all_text": "", "count": 0}

    try:
        if root_element is None:
            root_element = _get_target_window(window_title)
        if not root_element:
            LOGGER_ERROR("[sr_content_collector] Could not find target window")
            return {"items": [], "all_text": "", "count": 0}

        items = []
        _traverse_element(root_element, items, max_depth, current_depth=0)

        all_text = "\n".join(item["name"] for item in items if item["name"])

        LOGGER_INFO(f"[sr_content_collector] Collected {len(items)} elements", "GREEN")
        LOGGER_DEBUG(f"[sr_content_collector] Preview: {all_text[:300]}...")

        return {"items": items, "all_text": all_text, "count": len(items)}

    except Exception as e:
        LOGGER_ERROR(f"[sr_content_collector] Error: {e}")
        return {"items": [], "all_text": "", "count": 0}


def get_focused_dialog_element():
    """
    Return the parent dialog/window UIA element of the currently focused control.

    Walks up from the focused element to find the nearest Window (50032).
    Useful for scoping screenshot + SR collection to the active dialog
    (e.g. an Emergency Calling Notification popup) rather than the entire
    app window.

    Returns:
        UIA element of the parent dialog/window, or None on failure.
    """
    if sys.platform != "win32":
        return None
    try:
        focused = uia.GetFocusedElement()
        if not focused:
            return None

        walker = uia.ControlViewWalker
        current = focused
        depth = 0
        while current and depth < 30:
            try:
                ctrl_type = current.CurrentControlType or 0
                if ctrl_type in WINDOW_CONTROL_TYPES:
                    name = current.CurrentName or ""
                    LOGGER_INFO(
                        f"[sr_content_collector] Focused dialog element: "
                        f"[{name}] type={ctrl_type} depth={depth}",
                        "GREEN",
                    )
                    return current
            except Exception:
                pass
            try:
                current = walker.GetParentElement(current)
            except Exception:
                break
            depth += 1
        return None
    except Exception as e:
        LOGGER_ERROR(f"[sr_content_collector] get_focused_dialog_element error: {e}")
        return None


def _get_target_window(window_title: str = None):
    """Resolve the UIA element for the target window."""
    if window_title:
        root = uia.GetRootElement()
        walker = uia.ControlViewWalker
        child = walker.GetFirstChildElement(root)
        while child:
            try:
                name = child.CurrentName or ""
                if window_title.lower() in name.lower():
                    return child
            except Exception:
                pass
            child = walker.GetNextSiblingElement(child)

    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return uia.ElementFromHandle(hwnd)
    except Exception as e:
        LOGGER_WARNING(f"[sr_content_collector] Foreground window fallback failed: {e}")

    return None


def _traverse_element(element, items: list, max_depth: int, current_depth: int):
    """Recursively traverse UIA tree and collect element names."""
    if current_depth > max_depth:
        return

    try:
        name = element.CurrentName or ""
        control_type = element.CurrentControlType or 0
        localized_type = element.CurrentLocalizedControlType or ""

        if name.strip():
            items.append({
                "name": name.strip(),
                "control_type": control_type,
                "localized_type": localized_type,
            })
    except Exception as e:
        LOGGER_DEBUG(f"[sr_content_collector] Element access error at depth {current_depth}: {e}")
        return

    try:
        walker = uia.ControlViewWalker
        child = walker.GetFirstChildElement(element)
        while child:
            _traverse_element(child, items, max_depth, current_depth + 1)
            child = walker.GetNextSiblingElement(child)
    except Exception:
        pass

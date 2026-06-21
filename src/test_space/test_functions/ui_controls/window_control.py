"""
Window Control UI Utilities

This module contains UI control utility functions for window management,
including connecting to application windows, focusing windows, and basic window operations.
"""

import os
import sys
import time
from pathlib import Path
import psutil
import uiautomation as auto

# Add project root to Python path to access the control_handler
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

# Alternative path setup for development
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR
from rs_sdk.utils.control_handler import ControlHandler
from rs_sdk.utils.control_metadata import ControlMetadata


BROWSER_PROCESS_NAMES = {"msedge.exe", "chrome.exe", "firefox.exe"}
BROWSER_PROCESS_BY_HINT = {
    "edge": {"msedge.exe"},
    "microsoft edge": {"msedge.exe"},
    "chrome": {"chrome.exe"},
    "google chrome": {"chrome.exe"},
    "firefox": {"firefox.exe"},
}


def _get_process_name(control) -> str:
    """Best-effort lookup of the executable name for a UIA control."""
    try:
        process_id = getattr(control, "ProcessId", 0) or 0
        if not process_id:
            return ""
        return (psutil.Process(process_id).name() or "").strip().lower()
    except Exception:
        return ""


def _normalize_browser_hint(browser_hint: str | None) -> str:
    return (browser_hint or "edge").strip().lower()


def _get_allowed_process_names(browser_hint: str | None) -> set[str]:
    normalized = _normalize_browser_hint(browser_hint)
    return BROWSER_PROCESS_BY_HINT.get(normalized, BROWSER_PROCESS_BY_HINT["edge"])


def _find_button_control_by_name(
    button_name: str,
    timeout: int = 5,
    max_depth: int = 20,
    browser_hint: str = "edge",
):
    """
    Find a button-like control by visible name in the active browser window only.
    """
    target_window = _find_browser_window(timeout=timeout, browser_hint=browser_hint)
    if target_window is None:
        LOGGER_ERROR("[WindowControlUtils] Browser window not found before button search")
        return None

    search_names = [button_name]
    stripped_name = (button_name or "").strip()
    if stripped_name and stripped_name not in search_names:
        search_names.append(stripped_name)

    def _matches(control_name: str) -> bool:
        if not control_name:
            return False
        normalized = control_name.strip()
        return any(
            normalized == candidate or candidate in normalized or normalized in candidate
            for candidate in search_names
        )

    def _search_recursive(control, depth: int = 0):
        if control is None or depth > max_depth:
            return None

        try:
            control_type = getattr(control, "ControlType", None)
            if control_type in {auto.ControlType.ButtonControl, auto.ControlType.HyperlinkControl}:
                if _matches(getattr(control, "Name", "")):
                    return control
        except Exception:
            pass

        try:
            for child in control.GetChildren():
                result = _search_recursive(child, depth + 1)
                if result is not None:
                    return result
        except Exception:
            pass

        return None

    deadline = time.time() + max(timeout, 1)
    while time.time() < deadline:
        result = _search_recursive(target_window)
        if result is not None:
            return result
        time.sleep(0.3)

    return None


def _find_browser_window(
    window_title_contains: str = "Microsoft Edge",
    timeout: int = 5,
    browser_hint: str = "edge",
):
    """Find and activate the requested browser window."""
    deadline = time.time() + max(timeout, 1)
    allowed_process_names = _get_allowed_process_names(browser_hint)
    preferred_tokens = {
        "msedge.exe": ["microsoft edge", "edge", "webex"],
        "chrome.exe": ["google chrome", "chrome", "webex"],
        "firefox.exe": ["mozilla firefox", "firefox", "webex"],
    }
    preferred_name_tokens = []
    for process_name in allowed_process_names:
        preferred_name_tokens.extend(preferred_tokens.get(process_name, []))

    while time.time() < deadline:
        candidates = []
        try:
            for window in auto.GetRootControl().GetChildren():
                name = (getattr(window, "Name", "") or "").strip()
                class_name = (getattr(window, "ClassName", "") or "").strip()
                process_name = _get_process_name(window)
                if not name:
                    continue
                if process_name in allowed_process_names:
                    candidates.append(window)
                    continue
                lower_name = name.lower()
                if class_name == "Chrome_WidgetWin_1" and any(token in lower_name for token in preferred_name_tokens):
                    candidates.append(window)
        except Exception:
            candidates = []

        if candidates:
            candidates.sort(
                key=lambda w: (
                    _get_process_name(w) not in allowed_process_names,
                    not any(token in (getattr(w, "Name", "") or "").lower() for token in preferred_name_tokens),
                    len(getattr(w, "Name", "") or ""),
                )
            )
            target = candidates[0]
            LOGGER_INFO(
                f"[WindowControlUtils] Resolved browser window: "
                f"hint='{browser_hint}', "
                f"name='{getattr(target, 'Name', '')}', "
                f"class='{getattr(target, 'ClassName', '')}', "
                f"process='{_get_process_name(target)}'"
            )
            try:
                target.SetActive()
            except Exception:
                pass
            try:
                target.SetFocus()
            except Exception:
                pass
            return target

        time.sleep(0.3)

    return None


def _find_edit_control_by_name(
    field_name: str,
    timeout: int = 5,
    max_depth: int = 20,
    browser_hint: str = "edge",
):
    """Find an edit control by accessible name in the active browser window."""
    target_window = _find_browser_window(timeout=timeout, browser_hint=browser_hint)
    normalized_field_name = (field_name or "").strip().lower()
    search_names = [field_name, (field_name or "").strip()]
    alias_map = {
        "name": [
            "name",
            "enter your name",
            "display name",
            "guest name",
            "your name",
        ],
    }
    for alias in alias_map.get(normalized_field_name, []):
        if alias not in [name.lower() for name in search_names if name]:
            search_names.append(alias)
    search_names = [name for name in search_names if name]

    def _matches(control_name: str) -> bool:
        normalized = (control_name or "").strip().lower()
        if not normalized:
            return False
        return any(
            normalized == candidate.lower()
            or normalized.startswith(candidate.lower())
            or candidate.lower() in normalized
            for candidate in search_names
        )

    def _search_recursive(control, depth: int = 0):
        if control is None or depth > max_depth:
            return None

        try:
            if getattr(control, "ControlType", None) in {
                auto.ControlType.EditControl,
                auto.ControlType.ComboBoxControl,
            }:
                if _matches(getattr(control, "Name", "")):
                    return control
        except Exception:
            pass

        try:
            for child in control.GetChildren():
                result = _search_recursive(child, depth + 1)
                if result is not None:
                    return result
        except Exception:
            pass

        return None

    deadline = time.time() + max(timeout, 1)
    while time.time() < deadline:
        result = _search_recursive(target_window)
        if result is not None:
            return result
        time.sleep(0.3)

    return None


def _click_found_control(control, button_name: str):
    """Invoke a found control using the safest available interaction."""
    try:
        try:
            control.SetFocus()
        except Exception:
            pass

        try:
            invoke_pattern = control.GetInvokePattern()
            if invoke_pattern:
                invoke_pattern.Invoke()
                LOGGER_INFO(f"[WindowControlUtils] Invoked button: {button_name}")
                return True
        except Exception as exc:
            LOGGER_DEBUG(f"[WindowControlUtils] InvokePattern unavailable for '{button_name}': {exc}")

        control.Click()
        LOGGER_INFO(f"[WindowControlUtils] Clicked button: {button_name}")
        return True
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error clicking resolved control '{button_name}': {e}")
        return False

def connect_webex_window(webex_main_pid: int, ctrl_id: str, prefix_to_remove: str = "SparkApp.", **kwargs):
    """
    Connect to and focus on Webex application window by PID and AutoID
    
    Args:
        webex_main_pid (int): Webex main process PID
        ctrl_id (str): Control ID to focus on
        prefix_to_remove (str): Optional prefix to remove from ctrl_id before using it
        **kwargs: Additional parameters (ignored for compatibility)
        """
    try:
        if prefix_to_remove and ctrl_id.startswith(prefix_to_remove):
            ctrl_id = ctrl_id[len(prefix_to_remove):]
            ctrl_id = ctrl_id.split('.')[0]
        LOGGER_INFO(f"[WindowControlUtils] Connecting to Webex window with PID: {webex_main_pid}, Control ID: {ctrl_id}")
        
        # Create control handler instance
        control_handler = ControlHandler()
        
        # Execute the window connection/focus operation
        control_handler.focus_on_window_by_pid_autoid_contains(webex_main_pid, ctrl_id)
        
        LOGGER_INFO(f"[WindowControlUtils] Successfully connected to Webex window with PID {webex_main_pid} and control ID {ctrl_id}")
        
        return "connect_webex_window"
        
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error connecting to Webex window: {e}")
        raise

def connect_webex_app_main_window(webex_main_pid: int, ctrl_id: str = "MainWindow", prefix_to_remove: str = "SparkApp.", **kwargs):
    """
    Connect to and focus on Webex application main window by PID and AutoID
    
    Args:
        webex_main_pid (int): Webex main process PID
        ctrl_id (str): Control ID to focus on, defaults to "MainWindow"
        prefix_to_remove (str): Optional prefix to remove from ctrl_id before using it
        **kwargs: Additional parameters (ignored for compatibility)
    
    Returns:
        str: Function name indicating successful execution
    """
    try:
        if prefix_to_remove and ctrl_id.startswith(prefix_to_remove):
            ctrl_id = ctrl_id[len(prefix_to_remove):]
            ctrl_id = ctrl_id.split('.')[0]
        LOGGER_INFO(f"[WindowControlUtils] Connecting to Webex main window with PID: {webex_main_pid}, Control ID: {ctrl_id}")
        
        # Create control handler instance
        control_handler = ControlHandler()
        
        # Execute the window connection/focus operation
        control_handler.focus_on_window_by_pid_autoid_contains(webex_main_pid, ctrl_id)
        
        LOGGER_INFO(f"[WindowControlUtils] Successfully connected to Webex main window with PID {webex_main_pid} and control ID {ctrl_id}")
        
        return "connect_webex_app_main_window"
        
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error connecting to Webex main window: {e}")
        raise

def connect_webex_meeting_main_window(webex_main_pid: int, ctrl_id: str = "CallWindowDialog", prefix_to_remove: str = "SparkApp.", **kwargs):
    """
    Connect to and focus on Webex application meeting main window by PID and AutoID

    Args:
        webex_main_pid (int): Webex main process PID
        ctrl_id (str): Control ID to focus on, defaults to "CallWindowDialog"
        prefix_to_remove (str): Optional prefix to remove from ctrl_id before using it
        **kwargs: Additional parameters (ignored for compatibility)
    
    Returns:
        str: Function name indicating successful execution
    """
    try:
        if prefix_to_remove and ctrl_id.startswith(prefix_to_remove):
            ctrl_id = ctrl_id[len(prefix_to_remove):]
            ctrl_id = ctrl_id.split('.')[0]
        
        LOGGER_INFO(f"[WindowControlUtils] Connecting to Webex meeting window with PID: {webex_main_pid}, Control ID: {ctrl_id}")

        # Create control handler instance
        control_handler = ControlHandler()
        
        # Execute the window connection/focus operation
        control_handler.focus_on_window_by_pid_autoid_contains(webex_main_pid, ctrl_id)

        LOGGER_INFO(f"[WindowControlUtils] Successfully connected to Webex meeting window with PID {webex_main_pid} and control ID {ctrl_id}")

        return "connect_webex_meeting_main_window"
        
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error connecting to Webex meeting window: {e}")
        raise

def close_window_by_pid(pid: int, **kwargs):
    """
    Close window by process ID (placeholder for future implementation)
    
    Args:
        pid (int): Process ID of the window to close
        **kwargs: Additional parameters
    
    Returns:
        str: Function name indicating successful execution
    """
    try:
        LOGGER_INFO(f"[WindowControlUtils] Closing window with PID: {pid}")
        
        # TODO: Implement window closing logic
        # For now, just log the action
        LOGGER_INFO(f"[WindowControlUtils] Window closing functionality for PID {pid} - to be implemented")
        
        return "close_window_by_pid"
        
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error closing window: {e}")
        raise


def click_button_by_name(button_name: str, **kwargs):
    """
    Click button by name (placeholder for future implementation)
    
    Args:
        button_name (str): Name of the button to click
        **kwargs: Additional parameters
    
    Returns:
        str: Function name indicating successful execution
    """
    try:
        timeout = int(kwargs.get("timeout", 5) or 5)
        LOGGER_INFO(f"[WindowControlUtils] Clicking button by name: {button_name}, timeout: {timeout}s")

        button = _find_button_control_by_name(
            button_name=button_name,
            timeout=timeout,
            browser_hint=kwargs.get("browser", "edge"),
        )
        if button is None:
            LOGGER_ERROR(f"[WindowControlUtils] Button not found: {button_name}")
            return False

        return _click_found_control(button, button_name)
        
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error clicking button: {e}")
        raise


def click_browser_button_by_name(button_name: str, **kwargs):
    """
    Click a browser-hosted button or link by visible name.

    Args:
        button_name (str): Name of the browser button/link to click
        **kwargs: Optional parameters such as timeout

    Returns:
        bool: Whether click was successful
    """
    browser_hint = kwargs.get("browser", "edge")
    _find_browser_window(timeout=int(kwargs.get("timeout", 5) or 5), browser_hint=browser_hint)
    return click_button_by_name(button_name, **kwargs)


def set_focus_to_edge_browser(window_title_contains: str = "Microsoft Edge", timeout: int = 5, **kwargs):
    """
    Activate an Edge browser window so follow-up actions target the browser, not the terminal.
    """
    try:
        window = _find_browser_window(
            window_title_contains=window_title_contains,
            timeout=timeout,
            browser_hint=kwargs.get("browser", "edge"),
        )
        if window is None:
            LOGGER_ERROR(f"[WindowControlUtils] Edge browser window not found: {window_title_contains}")
            return False
        LOGGER_INFO(f"[WindowControlUtils] Focused browser window: {window.Name}")
        return True
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error focusing Edge browser: {e}")
        raise


def press_escape_key(wait_time: float = 0.2, **kwargs):
    """Press Escape after focusing the browser window."""
    try:
        _find_browser_window(
            timeout=int(kwargs.get("timeout", 5) or 5),
            browser_hint=kwargs.get("browser", "edge"),
        )
        auto.SendKeys("{Esc}")
        time.sleep(wait_time)
        LOGGER_INFO("[WindowControlUtils] Pressed Escape")
        return True
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error pressing Escape: {e}")
        raise


def set_browser_input_value(field_name: str, text: str, clear_existing: bool = True, timeout: int = 5, **kwargs):
    """
    Set a named input field value inside the active browser page.
    """
    try:
        edit = _find_edit_control_by_name(
            field_name=field_name,
            timeout=timeout,
            browser_hint=kwargs.get("browser", "edge"),
        )
        if edit is None:
            LOGGER_ERROR(f"[WindowControlUtils] Browser input field not found: {field_name}")
            return False

        try:
            edit.SetFocus()
        except Exception:
            pass

        time.sleep(0.2)
        if clear_existing:
            auto.SendKeys("{Ctrl}a{Delete}")
            time.sleep(0.1)
        auto.SendKeys(text)
        LOGGER_INFO(f"[WindowControlUtils] Set browser input '{field_name}' to '{text}'")
        return True
    except Exception as e:
        LOGGER_ERROR(f"[WindowControlUtils] Error setting browser input '{field_name}': {e}")
        raise


def get_available_ui_control_functions():
    """
    Get list of available UI control functions in this module
    
    Returns:
        dict: Dictionary of function names and descriptions
    """
    return {
        "connect_webex_app_main_window": "Connect to and focus on Webex application main window",
        "close_window_by_pid": "Close window by process ID (placeholder)",
        "click_button_by_name": "Click button by name",
        "click_browser_button_by_name": "Click browser button or link by visible name",
        "set_focus_to_edge_browser": "Focus the Edge browser window",
        "press_escape_key": "Press Escape key",
        "set_browser_input_value": "Set a named input field value in the browser"
    }

def ui_element_wait_time(seconds: int = 2):
    """
    Get default wait time for UI element operations
       
    Returns:
        int: Default wait time in seconds
    """
    time.sleep(seconds)

def get_ui_control_metadata():
    """
    Get metadata for UI control functions in this module
    
    Returns:
        ControlMetadata: Metadata object containing control function information
    """
    metadata = ControlMetadata()
    control_metadata = metadata.get_control_metadata()
    return control_metadata

def get_control_window_name():
    control_metadata = get_ui_control_metadata()
    window_name = control_metadata.get("window_name", "UnknownWindow")
    return window_name

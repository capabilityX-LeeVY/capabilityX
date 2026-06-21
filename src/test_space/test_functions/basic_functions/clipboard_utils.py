"""Utility functions for clipboard operations used by YAML test cases."""

from common.utils.logger import LOGGER_INFO
import win32clipboard


def set_clipboard_text(text: str) -> str:
    """Set plain text into the Windows clipboard for later paste operations."""
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
    finally:
        win32clipboard.CloseClipboard()

    LOGGER_INFO(f"[clipboard] Text copied to clipboard: {text}", "CYAN")
    return text
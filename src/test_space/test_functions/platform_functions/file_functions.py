"""
Local file helpers for test execution.

Provides one function.json-compatible entry point:
- replace_txt_file  Overwrite a local text file with new content.
"""

from __future__ import annotations

import os
from pathlib import Path

from common.utils.logger import LOGGER_ERROR, LOGGER_INFO


def replace_txt_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Overwrite a local text file with the given content.

    Args:
        file_path: Absolute or relative path to the file to write.
        content:   New content to write (replaces the entire file).
        encoding:  File encoding, defaults to utf-8.

    Returns:
        bool: True on success, raises on failure.
    """
    if not file_path or not file_path.strip():
        raise ValueError("Parameter 'file_path' is required")

    target = Path(os.path.expandvars(file_path)).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(content, encoding=encoding)
    LOGGER_INFO(f"[replace_txt_file] Wrote {len(content)} chars to '{target}'", "GREEN")
    return True

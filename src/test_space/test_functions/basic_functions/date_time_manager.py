import datetime
import tempfile
from pathlib import Path

_WHITEBOARD_NAME_FILE = Path(tempfile.gettempdir()) / "wrs_shared_whiteboard_name.txt"

def get_date(format="%Y-%m-%d"):
    return datetime.datetime.now().strftime(format)

def generate_whiteboard_name():
    """Generate a unique whiteboard name based on current timestamp, e.g. wb_20260313_142530"""
    return "wb_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def generate_and_save_whiteboard_name():
    """Generate a unique whiteboard name, save it to a temp file for cross-test-case sharing, and return it."""
    name = "wb_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    _WHITEBOARD_NAME_FILE.write_text(name, encoding="utf-8")
    return name

def load_whiteboard_name():
    """Load the whiteboard name saved by generate_and_save_whiteboard_name from the temp file."""
    if not _WHITEBOARD_NAME_FILE.exists():
        return "wb_"
    return _WHITEBOARD_NAME_FILE.read_text(encoding="utf-8").strip()
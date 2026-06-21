"""
log_parser.py

This module provides functionality to parse log files and extract correlation IDs.
Supports UUID v4 format extraction and general log pattern searching.
"""

import re
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING


def _get_log_dir() -> Path:
    system = platform.system()
    home_dir = Path.home()
    if system == "Windows":
        return home_dir / "AppData" / "Local" / "CiscoSpark" / "Logs"
    elif system == "Darwin":  # macOS
        return home_dir / "Library" / "Logs" / "SparkMacDesktop"
    else:
        raise RuntimeError(f"Unsupported platform: {system}. Only Windows and macOS are supported.")


def get_default_log_path() -> str:
    return str(_get_log_dir() / "current_log.txt")


def get_default_log_paths() -> List[str]:
    """Return both log file paths in chronological order (older first)."""
    log_dir = _get_log_dir()
    return [
        str(log_dir / "last_run_current_log.txt"),
        str(log_dir / "current_log.txt"),
    ]


def _read_combined_log_content(log_file_path: Optional[str] = None) -> Optional[str]:
    """Read and concatenate content from log file(s).
    
    If log_file_path is None, reads both last_run_current_log.txt and
    current_log.txt (in chronological order) and returns combined content.
    Missing files are silently skipped.
    """
    paths = [log_file_path] if log_file_path is not None else get_default_log_paths()
    combined: List[str] = []
    for p in paths:
        path = Path(p)
        if path.exists():
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                combined.append(f.read())
            LOGGER_DEBUG(f"Read log file: {p}")
        else:
            LOGGER_WARNING(f"Log file not found, skipping: {p}")
    if not combined:
        return None
    return "\n".join(combined)


def get_correlation_id_from_log(
    log_file_path: Optional[str] = None,
    search_pattern: str = "with correlation id:",
    get_last: bool = True
) -> Optional[str]:
    """
    Extract correlation ID (UUID v4 format) from log file.
    
    Searches for pattern: "with correlation id: <uuid>"
    UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    
    Args:
        log_file_path (Optional[str]): Path to the log file. If None, uses platform-specific default path.
        search_pattern (str): Pattern to search for before the UUID (default: "with correlation id:")
        get_last (bool): If True, returns the last correlation ID found; if False, returns the first (default: False)
    
    Returns:
        Optional[str]: The correlation ID (UUID) if found, None otherwise
        
    Example:
        >>> # Get first correlation ID (default)
        >>> correlation_id = get_correlation_id_from_log()
        >>> print(correlation_id)
        'e2d434ea-cbd3-487f-822b-b0a3707c77a1'
        
        >>> # Get last correlation ID
        >>> last_id = get_correlation_id_from_log(get_last=True)
        >>> print(last_id)
        'f3e545fb-dce4-498f-933c-c1b4818d88b2'
    """
    # UUID v4 regex pattern
    # Format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    # Where 'y' is one of [8, 9, a, b]
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
    
    # Combined pattern: search_pattern followed by UUID
    full_pattern = re.escape(search_pattern) + r'\s*' + uuid_pattern
    
    try:
        content = _read_combined_log_content(log_file_path)
        if content is None:
            LOGGER_ERROR(f"No readable log files found")
            return None
        
        if get_last:
            matches = list(re.finditer(full_pattern, content, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                uuid_match = re.search(uuid_pattern, last_match.group(0), re.IGNORECASE)
                if uuid_match:
                    correlation_id = uuid_match.group(0)
                    LOGGER_INFO(f"✅ Found last correlation ID: {correlation_id}")
                    return correlation_id
        else:
            # Find first match (original behavior)
            match = re.search(full_pattern, content, re.IGNORECASE)
            if match:
                uuid_match = re.search(uuid_pattern, match.group(0), re.IGNORECASE)
                if uuid_match:
                    correlation_id = uuid_match.group(0)
                    LOGGER_INFO(f"✅ Found first correlation ID: {correlation_id}")
                    return correlation_id
        
        position_text = "last" if get_last else "first"
        LOGGER_WARNING(f"⚠️ No correlation ID found in log file with pattern: '{search_pattern}'")
        return None
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error reading log file: {e}")
        return None


def get_all_correlation_ids_from_log(
    log_file_path: Optional[str] = None,
    search_pattern: str = "with correlation id:"
) -> List[str]:
    """
    Extract all correlation IDs (UUID v4 format) from log file.
    
    Args:
        log_file_path (Optional[str]): Path to the log file. If None, uses platform-specific default path.
        search_pattern (str): Pattern to search for before the UUID
    
    Returns:
        List[str]: List of all correlation IDs found (may be empty)
        
    Example:
        >>> # Use default platform-specific log path
        >>> all_ids = get_all_correlation_ids_from_log()
        >>> print(f"Found {len(all_ids)} correlation IDs")
    """
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
    full_pattern = re.escape(search_pattern) + r'\s*' + uuid_pattern
    
    try:
        content = _read_combined_log_content(log_file_path)
        if content is None:
            LOGGER_ERROR(f"No readable log files found")
            return []
        
        # Find all matches
        matches = re.finditer(full_pattern, content, re.IGNORECASE)
        correlation_ids = []
        
        for match in matches:
            uuid_match = re.search(uuid_pattern, match.group(0), re.IGNORECASE)
            if uuid_match:
                correlation_ids.append(uuid_match.group(0))
        
        if correlation_ids:
            LOGGER_INFO(f"✅ Found {len(correlation_ids)} correlation ID(s)")
            for i, cid in enumerate(correlation_ids, 1):
                LOGGER_INFO(f"   {i}. {cid}")
        else:
            LOGGER_WARNING(f"⚠️ No correlation IDs found in log file")
        
        return correlation_ids
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error reading log file: {e}")
        return []


def search_log_for_pattern(
    log_file_path: Optional[str] = None,
    pattern: str = "",
    context_lines: int = 2
) -> List[Dict[str, Any]]:
    """
    Search log file for a pattern and return matches with context.
    
    Args:
        log_file_path (Optional[str]): Path to the log file. If None, uses platform-specific default path.
        pattern (str): Regular expression pattern to search for
        context_lines (int): Number of lines before/after match to include
    
    Returns:
        List[Dict[str, Any]]: List of matches with line numbers and context
        
    Example:
        >>> # Use default platform-specific log path
        >>> matches = search_log_for_pattern(pattern="event flow id", context_lines=1)
        >>> for match in matches:
        ...     print(f"Line {match['line_number']}: {match['match']}")
    """
    try:
        content = _read_combined_log_content(log_file_path)
        if content is None:
            LOGGER_ERROR(f"No readable log files found")
            return []
        
        lines = content.splitlines(keepends=True)
        matches = []
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                # Get context lines
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                context = {
                    'line_number': i + 1,
                    'match': line.strip(),
                    'context_before': [l.strip() for l in lines[start:i]],
                    'context_after': [l.strip() for l in lines[i+1:end]]
                }
                matches.append(context)
        
        LOGGER_INFO(f"✅ Found {len(matches)} match(es) for pattern: '{pattern}'")
        return matches
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error searching log file: {e}")
        return []


def extract_uuid_from_text(text: str) -> Optional[str]:
    """
    Extract first UUID v4 from any text string.
    
    Args:
        text (str): Text to search for UUID
    
    Returns:
        Optional[str]: The UUID if found, None otherwise
        
    Example:
        >>> text = "Meeting ID is e2d434ea-cbd3-487f-822b-b0a3707c77a1"
        >>> uuid = extract_uuid_from_text(text)
        >>> print(uuid)
        'e2d434ea-cbd3-487f-822b-b0a3707c77a1'
    """
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
    match = re.search(uuid_pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def extract_all_uuids_from_text(text: str) -> List[str]:
    """
    Extract all UUID v4 occurrences from text string.
    
    Args:
        text (str): Text to search for UUIDs
    
    Returns:
        List[str]: List of all UUIDs found
        
    Example:
        >>> text = "IDs: e2d434ea-cbd3-487f-822b-b0a3707c77a1 and f3e545fb-dce4-498f-933c-c1b4818d88b2"
        >>> uuids = extract_all_uuids_from_text(text)
        >>> print(len(uuids))
        2
    """
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
    return re.findall(uuid_pattern, text, re.IGNORECASE)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Log Parser - Example Usage")
    print("=" * 60)
    
    # Example 0: Get default log path
    print("\n0️⃣ Get default log path:")
    try:
        default_path = get_default_log_path()
        print(f"   Platform: {platform.system()}")
        print(f"   Default log path: {default_path}")
    except RuntimeError as e:
        print(f"   ❌ {e}")
    
    # Example 1: Get single correlation ID (using default path)
    print("\n1️⃣ Extract single correlation ID (auto-detect platform):")
    correlation_id = get_correlation_id_from_log()  # No path needed!
    
    # Example 2: Get all correlation IDs (using default path)
    print("\n2️⃣ Extract all correlation IDs (auto-detect platform):")
    all_ids = get_all_correlation_ids_from_log()  # No path needed!
    
    # Example 3: Search for custom pattern (using default path)
    print("\n3️⃣ Search log for pattern (auto-detect platform):")
    matches = search_log_for_pattern(
        pattern="event flow id",
        context_lines=1
    )  # No path needed!
    
    if matches:
        print(f"\n📋 First match details:")
        first_match = matches[0]
        print(f"   Line: {first_match['line_number']}")
        print(f"   Content: {first_match['match']}")
    
    # Example 4: Extract UUID from text
    print("\n4️⃣ Extract UUID from text:")
    sample_text = "Meeting started with ID e2d434ea-cbd3-487f-822b-b0a3707c77a1"
    uuid = extract_uuid_from_text(sample_text)
    if uuid:
        print(f"   Found UUID: {uuid}")

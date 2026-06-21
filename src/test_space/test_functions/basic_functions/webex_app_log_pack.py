"""
webex_app_log_pack.py

Utilities for packaging Webex application log files into a ZIP archive.
Supports Windows and macOS platform-specific log directories.
"""
import os
import sys
# from dotenv import load_dotenv
# load_dotenv()
# pythonpath = os.getenv("PYTHONPATH")
# if pythonpath:
#     full_path = os.path.abspath(pythonpath)
#     if full_path not in sys.path:
#         sys.path.insert(0, full_path)
import platform
import zipfile
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING


def get_log_dir() -> Path:
    """
    Return the platform-specific Webex log directory (not a single file).

    Returns:
        Path: Directory that contains Webex log files.

    Raises:
        RuntimeError: If the platform is not Windows or macOS.
    """
    system = platform.system()
    home_dir = Path.home()

    if system == "Windows":
        log_dir = home_dir / "AppData" / "Local" / "CiscoSpark"
    elif system == "Darwin":  # macOS
        log_dir = home_dir / "Library" / "Logs" / "SparkMacDesktop"
    else:
        raise RuntimeError(f"Unsupported platform: {system}. Only Windows and macOS are supported.")

    return log_dir


def bundle_logs(
    output_dir: Optional[str] = None,
    archive_name: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    max_files: Optional[int] = None,
) -> Optional[str]:
    """
    Package Webex log files into a ZIP archive.

    Collects all files under the platform-specific log directory and writes
    them into a single ZIP file, preserving the relative directory structure.

    Args:
        output_dir (Optional[str]): Directory where the ZIP file will be saved.
            Defaults to the system temp directory.
        archive_name (Optional[str]): Base name for the ZIP file (without extension).
            Defaults to ``webex_logs_<YYYYMMDD_HHMMSS>``.
        include_patterns (Optional[List[str]]): Glob patterns to filter files,
            e.g. ``["*.txt", "*.log"]``.  When *None* all files are included.
        max_files (Optional[int]): Maximum number of files to include (newest
            files first, sorted by modification time).  ``None`` means no limit.

    Returns:
        Optional[str]: Absolute path to the created ZIP archive, or ``None``
        if the operation failed.

    Example:
        >>> # Default — pack everything, save to temp dir
        >>> zip_path = bundle_logs()
        >>> print(zip_path)
        'C:/Users/user/webex_logs/webex_logs_20260401_120000.zip'

        >>> # Save to Desktop, only .txt and .log files
        >>> zip_path = bundle_logs(
        ...     output_dir="C:/Users/user/Desktop",
        ...     include_patterns=["*.txt", "*.log"],
        ... )
    """
    try:
        log_dir = get_log_dir()
        LOGGER_DEBUG(f"Log directory: {log_dir}")

        if not log_dir.exists():
            LOGGER_ERROR(f"❌ Log directory not found: {log_dir}")
            return None

        # Collect candidate files
        if include_patterns:
            candidates: List[Path] = []
            for pat in include_patterns:
                candidates.extend(log_dir.rglob(pat))
        else:
            candidates = [p for p in log_dir.rglob("*") if p.is_file()]

        if not candidates:
            LOGGER_WARNING(f"⚠️ No log files found under: {log_dir}")
            return None

        # Sort by modification time (newest first) and optionally cap
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if max_files is not None:
            candidates = candidates[:max_files]

        LOGGER_DEBUG(f"Packaging {len(candidates)} file(s) …")

        # Resolve output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if archive_name is None:
            archive_name = f"webex_logs_{timestamp}"
        out_dir = Path(output_dir) if output_dir else Path.home() / "webex_logs"
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"{archive_name}.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in candidates:
                try:
                    arcname = file_path.relative_to(log_dir.parent)
                    zf.write(file_path, arcname)
                    LOGGER_DEBUG(f"   + {arcname}")
                except Exception as file_err:
                    LOGGER_WARNING(f"   ⚠️ Skipped {file_path.name}: {file_err}")

        LOGGER_DEBUG(f"✅ Log archive created: {zip_path}  ({zip_path.stat().st_size / 1024:.1f} KB)")
        return str(zip_path)

    except Exception as e:
        LOGGER_ERROR(f"❌ Failed to bundle logs: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Webex Log Pack - Example Usage")
    print("=" * 60)

    print(f"\nLog directory: {get_log_dir()}")

    print("\nBundling all logs to temp dir …")
    result = bundle_logs()
    if result:
        print(f"Archive: {result}")

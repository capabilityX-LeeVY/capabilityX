"""
Platform-specific terminal helpers for local test execution.

Provides function.json-compatible entry points:
- open_terminal_and_run_command
- close_terminal_session
- open_background_process_and_run_command
- close_background_process_session
"""

from __future__ import annotations

import json
import os
import platform
import shlex
import signal
import subprocess
import tempfile
import textwrap
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from common.utils.logger import LOGGER_ERROR, LOGGER_INFO, LOGGER_WARNING


_SESSION_ROOT = Path(tempfile.gettempdir()) / "wrs_terminal_sessions"
_SESSION_REGISTRY = _SESSION_ROOT / "registry.json"


def _ensure_session_root() -> None:
    _SESSION_ROOT.mkdir(parents=True, exist_ok=True)


def _load_registry() -> Dict[str, Dict[str, Any]]:
    _ensure_session_root()
    if not _SESSION_REGISTRY.exists():
        return {}

    try:
        return json.loads(_SESSION_REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER_WARNING(f"[terminal_functions] Failed to read terminal registry: {exc}")
        return {}


def _save_registry(registry: Dict[str, Dict[str, Any]]) -> None:
    _ensure_session_root()
    _SESSION_REGISTRY.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _build_session_id(session_name: Optional[str] = None) -> str:
    if session_name:
        return session_name.strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"wrs_terminal_{timestamp}_{suffix}"


def _normalize_cwd(cwd: Optional[str]) -> str:
    if not cwd:
        return str(Path.cwd())
    return str(Path(cwd).expanduser().resolve())


def _write_windows_script(session_id: str, command: str, cwd: str) -> Path:
    script_path = _SESSION_ROOT / f"{session_id}.cmd"
    script_body = "\n".join([
        "@echo off",
        f"title {session_id}",
        f'cd /d "{cwd}"',
        command,
    ]) + "\n"
    script_path.write_text(script_body, encoding="utf-8")
    return script_path


def _write_macos_script(session_id: str, command: str, cwd: str, keep_open: bool) -> Path:
    script_path = _SESSION_ROOT / f"{session_id}.command"
    reopen_statement = "exec bash" if keep_open else "exit"
    script_body = textwrap.dedent(
        f"""#!/bin/bash
        cd {json.dumps(cwd)} || exit 1
        {command}
        printf '\n[WRS] Session: {session_id}\n'
        {reopen_statement}
        """
    )
    script_path.write_text(script_body, encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def _open_windows_terminal(session_id: str, command: str, cwd: str, keep_open: bool) -> Dict[str, Any]:
    script_path = _write_windows_script(session_id, command, cwd)
    cmd_flag = "/k" if keep_open else "/c"
    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    process = subprocess.Popen(
        ["cmd.exe", cmd_flag, str(script_path)],
        cwd=cwd,
        creationflags=creation_flags,
    )

    return {
        "platform": "windows",
        "pid": process.pid,
        "script_path": str(script_path),
        "cwd": cwd,
        "command": command,
        "terminal": "cmd",
    }


def _run_osascript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _open_macos_terminal(session_id: str, command: str, cwd: str, keep_open: bool) -> Dict[str, Any]:
    script_path = _write_macos_script(session_id, command, cwd, keep_open)
    terminal_command = f"bash {shlex.quote(str(script_path))}"
    escaped_terminal_command = terminal_command.replace("\\", "\\\\").replace('"', '\\"')
    apple_script = textwrap.dedent(
        f"""
        tell application "Terminal"
            activate
            do script "{escaped_terminal_command}"
            delay 0.5
            set custom title of selected tab of front window to "{session_id}"
            return id of front window as string
        end tell
        """
    ).strip()
    window_id = _run_osascript(apple_script)

    return {
        "platform": "darwin",
        "window_id": window_id,
        "script_path": str(script_path),
        "cwd": cwd,
        "command": command,
        "terminal": "Terminal",
        "keep_open": keep_open,
    }


def _cleanup_session_artifacts(session_info: Dict[str, Any]) -> None:
    script_path = session_info.get("script_path")
    if not script_path:
        return

    try:
        Path(script_path).unlink(missing_ok=True)
    except OSError as exc:
        LOGGER_WARNING(f"[terminal_functions] Failed to remove temp terminal script '{script_path}': {exc}")


def _build_log_path(session_id: str, log_file: Optional[str] = None) -> str:
    if log_file:
        return str(Path(log_file).expanduser().resolve())

    _ensure_session_root()
    return str((_SESSION_ROOT / f"{session_id}.log").resolve())


def _open_background_process(session_id: str, command: str, cwd: str, log_path: str) -> Dict[str, Any]:
    current_platform = platform.system().lower()
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as log_handle:
        if current_platform == "windows":
            creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                shell=True,
                creationflags=creation_flags,
            )
        elif current_platform in ("darwin", "linux"):
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                shell=True,
                executable="/bin/bash",
                start_new_session=True,
            )
        else:
            raise RuntimeError(f"Unsupported platform for background process automation: {current_platform}")

    return {
        "platform": current_platform,
        "pid": process.pid,
        "cwd": cwd,
        "command": command,
        "log_path": log_path,
        "session_type": "background_process",
    }


def _is_process_alive(pid: int) -> bool:
    current_platform = platform.system().lower()
    if current_platform == "windows":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    result = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    process_state = result.stdout.strip()
    if not process_state:
        return False

    return not process_state.startswith("Z")


def _wait_for_process_exit(pid: int, timeout_seconds: float) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not _is_process_alive(pid):
            return True
        time.sleep(0.1)
    return not _is_process_alive(pid)


def _close_background_process_windows(session_info: Dict[str, Any]) -> bool:
    pid = session_info.get("pid")
    if not pid:
        raise ValueError("Missing pid for background process session")

    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _close_background_process_posix(session_info: Dict[str, Any]) -> bool:
    pid = session_info.get("pid")
    if not pid:
        raise ValueError("Missing pid for background process session")

    if not _is_process_alive(pid):
        return True

    try:
        process_group_id = os.getpgid(pid)
    except ProcessLookupError:
        return True

    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        return True

    if _wait_for_process_exit(pid, 5):
        return True

    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        return True

    return _wait_for_process_exit(pid, 2)


def open_terminal_and_run_command(
    command: str,
    cwd: Optional[str] = None,
    terminal: Optional[str] = None,
    keep_open: bool = True,
    session_name: Optional[str] = None,
) -> str:
    """
    Open a visible local terminal window and run a command.

    Returns:
        str: Session id used later by close_terminal_session.
    """
    if not command or not command.strip():
        raise ValueError("Parameter 'command' is required")

    current_platform = platform.system().lower()
    session_id = _build_session_id(session_name)
    normalized_cwd = _normalize_cwd(cwd)

    LOGGER_INFO(
        f"[open_terminal_and_run_command] Opening terminal session '{session_id}' on {current_platform} with command: {command}",
        "CYAN",
    )

    registry = _load_registry()

    try:
        if current_platform == "windows":
            session_info = _open_windows_terminal(session_id, command, normalized_cwd, keep_open)
        elif current_platform == "darwin":
            session_info = _open_macos_terminal(session_id, command, normalized_cwd, keep_open)
        else:
            raise RuntimeError(f"Unsupported platform for visible terminal automation: {current_platform}")

        session_info.update(
            {
                "created_at": datetime.now().isoformat(),
                "session_id": session_id,
                "requested_terminal": terminal,
            }
        )
        registry[session_id] = session_info
        _save_registry(registry)

        LOGGER_INFO(f"[open_terminal_and_run_command] Terminal session '{session_id}' started successfully", "GREEN")
        return session_id
    except Exception as exc:
        LOGGER_ERROR(f"[open_terminal_and_run_command] Failed to open terminal session '{session_id}': {exc}", "RED")
        raise


def open_background_process_and_run_command(
    command: str,
    cwd: Optional[str] = None,
    session_name: Optional[str] = None,
    log_file: Optional[str] = None,
) -> str:
    """
    Start a local command as a background process without opening a terminal window.

    Returns:
        str: Session id used later by close_background_process_session.
    """
    if not command or not command.strip():
        raise ValueError("Parameter 'command' is required")

    session_id = _build_session_id(session_name)
    normalized_cwd = _normalize_cwd(cwd)
    log_path = _build_log_path(session_id, log_file)

    LOGGER_INFO(
        f"[open_background_process_and_run_command] Starting background session '{session_id}' with command: {command}",
        "CYAN",
    )

    registry = _load_registry()

    try:
        session_info = _open_background_process(session_id, command, normalized_cwd, log_path)
        session_info.update(
            {
                "created_at": datetime.now().isoformat(),
                "session_id": session_id,
            }
        )
        registry[session_id] = session_info
        _save_registry(registry)

        LOGGER_INFO(
            f"[open_background_process_and_run_command] Background session '{session_id}' started successfully",
            "GREEN",
        )
        return session_id
    except Exception as exc:
        LOGGER_ERROR(
            f"[open_background_process_and_run_command] Failed to start background session '{session_id}': {exc}",
            "RED",
        )
        raise


def _close_windows_terminal(session_info: Dict[str, Any]) -> bool:
    pid = session_info.get("pid")
    if not pid:
        raise ValueError("Missing pid for Windows terminal session")

    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _close_macos_terminal(session_info: Dict[str, Any], session_id: str) -> bool:
    window_id = session_info.get("window_id", "")
    apple_script = textwrap.dedent(
        f"""
        tell application "Terminal"
            repeat with current_window in windows
                if (id of current_window as string) is equal to "{window_id}" then
                    close current_window saving no
                    return "closed"
                end if
            end repeat
            repeat with current_window in windows
                repeat with current_tab in tabs of current_window
                    if custom title of current_tab is equal to "{session_id}" then
                        close current_window saving no
                        return "closed"
                    end if
                end repeat
            end repeat
            return "not_found"
        end tell
        """
    ).strip()
    result = _run_osascript(apple_script)
    return result == "closed"


def close_terminal_session(session_id: str) -> bool:
    """
    Close a terminal session previously opened by open_terminal_and_run_command.

    Returns:
        bool: True when the session was closed or already gone.
    """
    if not session_id or not session_id.strip():
        raise ValueError("Parameter 'session_id' is required")

    registry = _load_registry()
    session_info = registry.get(session_id)
    if not session_info:
        LOGGER_WARNING(f"[close_terminal_session] Session '{session_id}' not found in registry")
        return False

    current_platform = platform.system().lower()
    session_platform = session_info.get("platform")
    if session_platform != current_platform:
        raise RuntimeError(
            f"Session '{session_id}' was created on platform '{session_platform}', current platform is '{current_platform}'"
        )

    try:
        if current_platform == "windows":
            closed = _close_windows_terminal(session_info)
        elif current_platform == "darwin":
            closed = _close_macos_terminal(session_info, session_id)
        else:
            raise RuntimeError(f"Unsupported platform for terminal close: {current_platform}")

        if not closed:
            LOGGER_WARNING(f"[close_terminal_session] Session '{session_id}' was not found when closing")
            return False

        registry.pop(session_id, None)
        _save_registry(registry)
        _cleanup_session_artifacts(session_info)
        LOGGER_INFO(f"[close_terminal_session] Terminal session '{session_id}' closed successfully", "GREEN")
        return True
    except Exception as exc:
        LOGGER_ERROR(f"[close_terminal_session] Failed to close session '{session_id}': {exc}", "RED")
        raise


def close_background_process_session(session_id: str) -> bool:
    """
    Stop a background process session previously opened by open_background_process_and_run_command.

    Returns:
        bool: True when the session was stopped or already gone.
    """
    if not session_id or not session_id.strip():
        raise ValueError("Parameter 'session_id' is required")

    registry = _load_registry()
    session_info = registry.get(session_id)
    if not session_info:
        LOGGER_WARNING(f"[close_background_process_session] Session '{session_id}' not found in registry")
        return False

    current_platform = platform.system().lower()
    session_platform = session_info.get("platform")
    if session_platform != current_platform:
        raise RuntimeError(
            f"Session '{session_id}' was created on platform '{session_platform}', current platform is '{current_platform}'"
        )

    try:
        if current_platform == "windows":
            closed = _close_background_process_windows(session_info)
        elif current_platform in ("darwin", "linux"):
            closed = _close_background_process_posix(session_info)
        else:
            raise RuntimeError(f"Unsupported platform for background process close: {current_platform}")

        if not closed:
            LOGGER_WARNING(f"[close_background_process_session] Session '{session_id}' was not stopped cleanly")
            return False

        registry.pop(session_id, None)
        _save_registry(registry)
        LOGGER_INFO(f"[close_background_process_session] Background session '{session_id}' stopped successfully", "GREEN")
        return True
    except Exception as exc:
        LOGGER_ERROR(f"[close_background_process_session] Failed to stop session '{session_id}': {exc}", "RED")
        raise
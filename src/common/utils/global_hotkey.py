"""
Global Hotkey Listener for WRS Test Process
============================================

Registers a system-wide hotkey (Ctrl+Alt+0).
When triggered, the entire process tree is terminated gracefully.

- Windows: uses the Windows API (ctypes / RegisterHotKey).
- macOS:   uses pynput.keyboard.GlobalHotKeys (requires Accessibility
           permission granted to the terminal or the Python executable in
           System Settings → Privacy & Security → Accessibility).

Usage:
    from common.utils.global_hotkey import start_hotkey_listener
    start_hotkey_listener()  # Call once at program startup

Works regardless of which window has focus.
"""

import os
import signal
import sys
import threading

_listener_started = False


# ---------------------------------------------------------------------------
# Shared termination helper
# ---------------------------------------------------------------------------

def _print_stop_banner(pid: int) -> None:
    print(flush=True)
    print("=" * 60, flush=True)
    if sys.platform == "darwin":
        print("  STOPPED by global hotkey  Ctrl+Option+0  (macOS)", flush=True)
    else:
        print("  STOPPED by global hotkey  Ctrl+Alt+0", flush=True)
    print(f"  Terminating process tree (PID {pid})...", flush=True)
    print("=" * 60, flush=True)


# ---------------------------------------------------------------------------
# Windows implementation
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

    MOD_CONTROL = 0x0002
    MOD_ALT     = 0x0001
    MOD_NOREPEAT = 0x4000
    VK_0        = 0x30
    WM_HOTKEY   = 0x0312
    HOTKEY_ID   = 9001

    def _terminate_process_win() -> None:
        pid = os.getpid()
        _print_stop_banner(pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        try:
            import subprocess
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            os._exit(1)

    def _hotkey_thread_win() -> None:
        """Background thread that listens for the global hotkey on Windows."""
        user32 = ctypes.windll.user32
        success = user32.RegisterHotKey(
            None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_0
        )
        if not success:
            print("[GlobalHotkey] Failed to register Ctrl+Alt+0 — "
                  "the hotkey may already be in use by another application.",
                  flush=True)
            return
        try:
            msg = ctypes.wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    _terminate_process_win()
                    break
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def _start_platform_listener() -> None:
        t = threading.Thread(
            target=_hotkey_thread_win, daemon=True, name="GlobalHotkeyListener"
        )
        t.start()


# ---------------------------------------------------------------------------
# macOS implementation
# ---------------------------------------------------------------------------

elif sys.platform == "darwin":

    def _terminate_process_mac() -> None:
        pid = os.getpid()
        _print_stop_banner(pid)
        # Kill the entire process group so child processes are also terminated.
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
        except OSError:
            pass
        # Fallback: kill just the main process
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        os._exit(1)

    def _hotkey_thread_mac() -> None:
        """Background thread that listens for Ctrl+Alt+0 on macOS via pynput."""
        try:
            from pynput import keyboard  # type: ignore[import-untyped]

            print("[GlobalHotkey] macOS: Ctrl+Option+0 registered "
                  "(requires Accessibility permission for Terminal in "
                  "System Settings → Privacy & Security → Accessibility)",
                  flush=True)
            with keyboard.GlobalHotKeys(
                {"<ctrl>+<alt>+0": _terminate_process_mac}
            ) as listener:
                listener.join()
        except Exception:
            # pynput not installed or Accessibility permission not granted — skip silently.
            pass

    def _start_platform_listener() -> None:
        t = threading.Thread(
            target=_hotkey_thread_mac, daemon=True, name="GlobalHotkeyListener"
        )
        t.start()


# ---------------------------------------------------------------------------
# Unsupported platforms — no-op
# ---------------------------------------------------------------------------

else:

    def _start_platform_listener() -> None:  # type: ignore[misc]
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_hotkey_listener() -> None:
    """
    Start the global hotkey listener in a daemon thread.

    Safe to call multiple times — only the first call takes effect.
    Activates on Windows and macOS; silently skipped on other platforms.
    """
    global _listener_started
    if _listener_started:
        return
    _listener_started = True
    _start_platform_listener()

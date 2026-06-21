from __future__ import annotations

"""
Web platform specific functions for browser operations
"""
from tools.webexApp import appHandler
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from config.paths import TEST_SUITE_PATH, TEST_CASES_PATH
from pathlib import Path
from PIL import ImageGrab
import io
import time
import subprocess
import os
import platform
import psutil


BROWSER_PROCESS_NAMES = {
    "edge": ["msedge.exe", "Microsoft Edge", "msedge"],
    "microsoft edge": ["msedge.exe", "Microsoft Edge", "msedge"],
    "chrome": ["chrome.exe", "Google Chrome", "chrome", "google-chrome"],
    "google chrome": ["chrome.exe", "Google Chrome", "chrome", "google-chrome"],
    "firefox": ["firefox.exe", "firefox"],
    "safari": ["Safari"],
    "all": ["msedge.exe", "chrome.exe", "firefox.exe", "Microsoft Edge", "msedge", "Google Chrome", "chrome", "google-chrome", "firefox", "Safari"],
}


def _normalize_browser_name(browser: str | None) -> str:
    return (browser or "edge").strip().lower()


def _get_browser_processes(browser: str | None = "edge") -> list[psutil.Process]:
    browser_name = _normalize_browser_name(browser)
    process_names = BROWSER_PROCESS_NAMES.get(browser_name, BROWSER_PROCESS_NAMES["edge"])
    result = []
    for process in psutil.process_iter(attrs=["name"]):
        try:
            name = (process.info.get("name") or "").strip().lower()
            if name in process_names:
                result.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return result


def _kill_browser_processes(browser: str | None = "edge", timeout: float = 5.0) -> tuple[int, list[str]]:
    browser_name = _normalize_browser_name(browser)
    processes = _get_browser_processes(browser_name)
    if not processes:
        return 0, []

    killed_names = []
    for process in processes:
        try:
            killed_names.append((process.name() or "").strip().lower())
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    deadline = time.time() + max(timeout, 0.5)
    while time.time() < deadline:
        remaining = _get_browser_processes(browser_name)
        if not remaining:
            break
        time.sleep(0.2)

    # Edge and other browsers can keep child processes alive; on Windows,
    # fall back to taskkill /T /F to tear down the remaining process tree.
    remaining_processes = _get_browser_processes(browser_name)
    if remaining_processes and platform.system().lower() == "windows":
        process_names = BROWSER_PROCESS_NAMES.get(browser_name, BROWSER_PROCESS_NAMES["edge"])
        for process_name in process_names:
            try:
                subprocess.run(
                    ["taskkill", "/IM", process_name, "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except OSError:
                continue

        deadline = time.time() + max(timeout, 0.5)
        while time.time() < deadline:
            remaining = _get_browser_processes(browser_name)
            if not remaining:
                break
            time.sleep(0.2)

    remaining = sorted({(proc.name() or "").strip().lower() for proc in _get_browser_processes(browser_name)})
    return len(killed_names), remaining


def open_browser(site_url: str = "https://web.webex.com", browser: str = "edge"):
    """
    Open a browser and navigate to the specified URL.

    Args:
        site_url (str): URL to navigate to. Default is Webex web app.
        browser (str): Browser to use. Supports: chrome, edge, firefox, safari.
                       safari is macOS-only. Defaults to edge.

    Returns:
        dict: Result with success status and message
    """
    browser_name = (browser or "edge").strip().lower()
    LOGGER_INFO(f"Opening browser '{browser_name}' with URL: {site_url}", "CYAN")

    try:
        current_os = platform.system().lower()
        if current_os == "darwin":
            # macOS: use `open -a <App>` to launch by app name.
            mac_browser_map = {
                "chrome": "Google Chrome",
                "google chrome": "Google Chrome",
                "edge": "Microsoft Edge",
                "microsoft edge": "Microsoft Edge",
                "firefox": "Firefox",
                "safari": "Safari",
            }
            app_name = mac_browser_map.get(browser_name)
            if app_name is None:
                return {
                    "status": "failed",
                    "message": f"Unsupported browser '{browser_name}' on macOS. Use chrome, edge, firefox, or safari.",
                    "url": site_url,
                    "browser": browser_name,
                }
            if browser_name == "safari":
                script = f'''
tell application "Safari"
    activate
    if not (exists front window) then
        make new document
    end if
    set URL of front document to "{site_url}"
end tell
'''
                subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            else:
                subprocess.Popen(["open", "-a", app_name, site_url])

        elif current_os == "windows":
            # Windows: resolve executable path by browser.
            win_browser_paths = {
                "edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                    os.path.join(os.path.expanduser("~"), r"AppData\Local\Microsoft\Edge\Application\msedge.exe"),
                ],
                "microsoft edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ],
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.join(os.path.expanduser("~"), r"AppData\Local\Google\Chrome\Application\chrome.exe"),
                ],
                "google chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ],
                "firefox": [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                ],
            }
            paths = win_browser_paths.get(browser_name)
            if paths is None:
                return {
                    "status": "failed",
                    "message": f"Unsupported browser '{browser_name}' on Windows. Use chrome, edge, or firefox.",
                    "url": site_url,
                    "browser": browser_name,
                }
            exe = next((p for p in paths if os.path.exists(p)), None)
            if exe is None:
                return {
                    "status": "failed",
                    "message": f"Browser '{browser_name}' not found on this system.",
                    "url": site_url,
                    "browser": browser_name,
                }
            launch_args = [exe]
            if browser_name in {"edge", "microsoft edge", "chrome", "google chrome"}:
                launch_args.append("--new-window")
            launch_args.append(site_url)
            subprocess.Popen(launch_args)

        else:
            # Linux: use command name directly.
            linux_browser_cmds = {
                "chrome": "google-chrome",
                "google chrome": "google-chrome",
                "edge": "microsoft-edge",
                "microsoft edge": "microsoft-edge",
                "firefox": "firefox",
            }
            cmd = linux_browser_cmds.get(browser_name)
            if cmd is None:
                return {
                    "status": "failed",
                    "message": f"Unsupported browser '{browser_name}' on Linux. Use chrome, edge, or firefox.",
                    "url": site_url,
                    "browser": browser_name,
                }
            subprocess.Popen([cmd, site_url])

        LOGGER_INFO(f"Browser opened successfully at: {site_url}", "GREEN")
        return {
            "status": "success",
            "message": f"Browser opened at {site_url}",
            "url": site_url,
            "browser": browser_name,
        }

    except Exception as e:
        LOGGER_ERROR(f"Error opening browser: {str(e)}", "RED")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "url": site_url,
            "browser": browser_name,
        }


def navigate_to_webex(site_url: str = None):
    """
    Navigate to Webex web application
    
    Args:
        site_url (str): Optional custom Webex URL. If not provided, uses default.
    
    Returns:
        dict: Result with success status and message
    """
    if site_url is None:
        site_url = "https://web.webex.com"
    
    return open_browser(site_url=site_url)


def close_browser(browser: str = "all"):
    """
    Close browser instances for the requested browser.
    
    Returns:
        dict: Result with success status and message
    """
    browser_name = _normalize_browser_name(browser)
    LOGGER_INFO(f"Closing browser '{browser_name}'...", "CYAN")
    
    try:
        if platform.system().lower() == "windows":
            killed_count, remaining = _kill_browser_processes(browser_name)
            if remaining:
                LOGGER_ERROR(
                    f"Browser close incomplete for '{browser_name}', remaining processes: {remaining}",
                    "RED",
                )
                return {
                    "status": "error",
                    "message": f"Remaining browser processes after close: {remaining}",
                    "browser": browser_name,
                    "killed_count": killed_count,
                }
        else:
            killed_count, remaining = _kill_browser_processes(browser_name)
            if remaining:
                LOGGER_ERROR(
                    f"Browser close incomplete for '{browser_name}', remaining processes: {remaining}",
                    "RED",
                )
                return {
                    "status": "error",
                    "message": f"Remaining browser processes after close: {remaining}",
                    "browser": browser_name,
                    "killed_count": killed_count,
                }

        LOGGER_INFO(f"Browser '{browser_name}' closed successfully", "GREEN")
        return {
            "status": "success",
            "message": f"Browser '{browser_name}' closed successfully",
            "browser": browser_name,
            "killed_count": killed_count,
        }
    except Exception as e:
        LOGGER_ERROR(f"Error closing browser: {str(e)}", "RED")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "browser": browser_name,
        }



#!/usr/bin/env python3
"""
Auto-answer incoming Webex desktop calls on Windows by UI automation.

Usage examples:
  python WebexVDIPeerRunner.py
  python WebexVDIPeerRunner.py --once --verbose
  python WebexVDIPeerRunner.py --timeout 600 --interval 0.25

Production run:
    python WebexVDIPeerRunner.py --web-server --web-host 127.0.0.1 --share-cooldown 2.5
    python WebexVDIPeerRunner.py --web-server --web-host 0.0.0.0 --share-cooldown 3.0
    # Enable only for troubleshooting; disabled by default.
    python WebexVDIPeerRunner.py --web-server --enable-share-debug-endpoint

Requirements:
    Windows: pip install pywinauto flask
    Linux (GNOME/X11): sudo apt install python3-pyatspi
    Cross-platform web server: pip install flask

Notes:
- This relies on desktop UI labels and can break after Webex UI changes.
- For non-English UI, pass localized button labels with --answer-label.
"""

from __future__ import annotations

import argparse
import atexit
import csv
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from typing import Iterable, List

try:
    from flask import Flask, jsonify, request
except Exception:
    Flask = None
    jsonify = None
    request = None

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
SCRIPT_VERSION = "1.1.0"

if IS_WINDOWS:
    try:
        from pywinauto import Desktop
        from pywinauto import findwindows
        from pywinauto.keyboard import send_keys
    except Exception as exc:
        print(
            "[ERROR] Failed to import pywinauto. Install it with: pip install pywinauto\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)


@dataclass
class Config:
    timeout: float
    interval: float
    answer_delay: float
    answer_after_rings: int
    ring_interval: float
    once: bool
    dry_run: bool
    verbose: bool
    answer_labels: List[str]
    window_title_regex: str
    auto_start_webex: bool
    webex_command: str
    webex_monitor_interval: float
    enable_web_server: bool
    enable_share_debug_endpoint: bool
    share_cooldown: float
    web_host: str
    web_port: int


@dataclass
class RuntimeState:
    incoming_since: float | None = None
    last_seen: float | None = None
    answers: int = 0
    webex_running: bool = False
    last_webex_check: float | None = None
    last_start_attempt: float | None = None
    last_start_success: bool | None = None
    last_matched_window: str = ""
    last_matched_button: str = ""
    last_share_attempt: float | None = None


STATE_LOCK = threading.Lock()
SHARE_REQUEST_LOCK = threading.Lock()


def _update_state(**kwargs) -> None:
    with STATE_LOCK:
        for key, value in kwargs.items():
            setattr(RUNTIME_STATE, key, value)


RUNTIME_STATE = RuntimeState()


def _state_snapshot() -> dict:
    with STATE_LOCK:
        snapshot = asdict(RUNTIME_STATE)
    snapshot["timestamp"] = time.time()
    return snapshot


def _get_real_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _create_app(cfg: Config) -> Flask:
    if Flask is None or jsonify is None:
        raise RuntimeError("Flask is not installed. Install it with: pip install flask")

    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            {
                "service": "webex-vdi-peer-runner",
                "routes": [
                    "/",
                    "/healthz",
                    "/version",
                    "/status",
                    "/incoming-call-visible",
                    "/restart-webex",
                    "/sharescreen",
                    "/stopshare",
                    "/sendAudio",
                    "/detectAudio",
                ],
            }
        )

    @app.get("/version")
    def version():
        return jsonify(
            {
                "service": "webex-vdi-peer-runner",
                "version": SCRIPT_VERSION,
                "platform": sys.platform,
                "python": sys.version.split()[0],
            }
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.get("/status")
    def status():
        return jsonify(
            {
                "config": {
                    "answer_delay": cfg.answer_delay,
                    "answer_after_rings": cfg.answer_after_rings,
                    "ring_interval": cfg.ring_interval,
                    "interval": cfg.interval,
                    "timeout": cfg.timeout,
                    "auto_start_webex": cfg.auto_start_webex,
                    "webex_monitor_interval": cfg.webex_monitor_interval,
                },
                "runtime": _state_snapshot(),
            }
        )

    @app.get("/incoming-call-visible")
    def incoming_call_visible():
        label_patterns = _compile_label_patterns(cfg.answer_labels)
        target = _find_incoming_call_target(cfg, label_patterns)
        visible = target is not None
        payload = {"visible": visible}
        if target:
            title, _, label = target
            payload["window"] = title
            payload["button"] = label
        return jsonify(payload)

    @app.get("/restart-webex")
    def restart_webex():
        started = _start_webex(cfg)
        return jsonify(
            {
                "started": started,
                "command": cfg.webex_command,
                "webex_running": _is_webex_running(),
            }
        )

    @app.get("/sharescreen")
    def sharescreen():
        now = time.time()
        with STATE_LOCK:
            last_attempt = RUNTIME_STATE.last_share_attempt
        if cfg.share_cooldown > 0 and last_attempt is not None:
            elapsed = now - last_attempt
            if elapsed < cfg.share_cooldown:
                return (
                    jsonify(
                        {
                            "started": False,
                            "reason": "Share cooldown active",
                            "cooldown_seconds": cfg.share_cooldown,
                            "retry_after_seconds": round(cfg.share_cooldown - elapsed, 3),
                        }
                    ),
                    429,
                )

        if not SHARE_REQUEST_LOCK.acquire(blocking=False):
            return (
                jsonify(
                    {
                        "started": False,
                        "reason": "Share request already in progress",
                    }
                ),
                429,
            )

        _update_state(last_share_attempt=now)
        try:
            return jsonify(_start_screen_share(cfg))
        finally:
            SHARE_REQUEST_LOCK.release()

    if cfg.enable_share_debug_endpoint:
        @app.get("/debug-share-controls")
        def debug_share_controls():
            return jsonify(_debug_share_controls())

    @app.get("/stopshare")
    def stopshare():
        return jsonify(_stop_screen_share())

    @app.get("/sendAudio")
    def send_audio_route():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "WebexVDITxAudio.py")
        if not os.path.isfile(script_path):
            return jsonify({"error": f"Missing script: {script_path}"}), 404

        text = request.args.get("text", "").strip()
        device_index = request.args.get("device_index", "").strip()
        channels = request.args.get("channels", "").strip()

        cmd = [sys.executable, script_path]
        if text:
            cmd.append(text)
        if device_index:
            cmd.extend(["--device-index", device_index])
        if channels:
            cmd.extend(["--channels", channels])

        result = subprocess.run(
            cmd,
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        response = {
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        status_code = 200 if result.returncode == 0 else 500
        return jsonify(response), status_code

    @app.get("/detectAudio")
    def detect_audio_route():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "WebexVDIAudioPresenceDetector.py")
        if not os.path.isfile(script_path):
            return jsonify({"error": f"Missing script: {script_path}"}), 404

        duration_seconds = request.args.get("duration_seconds", "30").strip()
        classify = request.args.get("classify", "0").strip()
        model_path = request.args.get("model_path", "").strip()
        class_labels = request.args.get("class_labels", "").strip()

        try:
            float(duration_seconds)
        except ValueError:
            return jsonify({"error": "Invalid duration_seconds"}), 400

        cmd = [
            sys.executable,
            script_path,
            "--duration-seconds",
            duration_seconds,
        ]

        if classify in {"1", "true", "yes", "y"}:
            if not model_path:
                return jsonify({"error": "model_path is required when classify=1"}), 400
            cmd.extend(["--classify", "--classifier-model", model_path])
            if class_labels:
                cmd.extend(["--class-labels", class_labels])

        result = subprocess.run(
            cmd,
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"

        present_match = re.search(r"Audio present:\s*(true|false)", output)
        class_match = re.search(r"Audio class:\s*(.+)", output)
        if present_match:
            response = {
                "audio_present": present_match.group(1) == "true",
                "return_code": result.returncode,
            }
            if class_match:
                response["audio_class"] = class_match.group(1).strip()
            print(f"Audio present (API): {response['audio_present']}")
            return jsonify(response), 200

        return jsonify({
            "error": "Unable to parse audio presence",
            "return_code": result.returncode,
            "output": output.strip(),
        }), 500

    return app


def _start_web_server(cfg: Config) -> None:
    if not cfg.enable_web_server:
        return

    if Flask is None:
        print("[ERROR] Web server requested but Flask is not installed. Install with: pip install flask")
        raise SystemExit(2)

    app = _create_app(cfg)

    def _run_server() -> None:
        app.run(host=cfg.web_host, port=cfg.web_port, debug=False, use_reloader=False)

    thread = threading.Thread(target=_run_server, name="webex-vdi-peer-runner-flask", daemon=True)
    thread.start()
    real_ip = _get_real_ip()
    print(f"[INFO] Web server started at http://{cfg.web_host}:{cfg.web_port}")
    if cfg.web_host in {"0.0.0.0", "127.0.0.1", "localhost"}:
        print(f"[INFO] Web server reachable at http://{real_ip}:{cfg.web_port}")


def _compile_label_patterns(labels: Iterable[str]) -> List[re.Pattern[str]]:
    patterns: List[re.Pattern[str]] = []
    for label in labels:
        label = label.strip()
        if not label:
            continue
        patterns.append(re.compile(rf"^{re.escape(label)}$", re.IGNORECASE))
    return patterns


def _is_webex_running() -> bool:
    if IS_WINDOWS:
        try:
            # Desktop app process name.
            for image_name in ["CiscoCollabHost.exe"]:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {image_name}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    check=False,
                )
                if image_name.lower() in (result.stdout or "").lower():
                    _update_state(webex_running=True, last_webex_check=time.time())
                    return True
            _update_state(webex_running=False, last_webex_check=time.time())
            return False
        except Exception:
            _update_state(webex_running=False, last_webex_check=time.time())
            return False

    if IS_LINUX:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "webex|CiscoCollabHost"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
            running = result.returncode == 0 and bool((result.stdout or "").strip())
            _update_state(webex_running=running, last_webex_check=time.time())
            return running
        except Exception:
            _update_state(webex_running=False, last_webex_check=time.time())
            return False

    _update_state(webex_running=False, last_webex_check=time.time())
    return False


def _default_webex_command() -> str:
    if IS_WINDOWS:
        collabhost_launcher = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "CiscoSparkLauncher",
            "CiscoCollabHost.exe",
        )
        candidates = [
            collabhost_launcher,
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Cisco Spark", "CiscoCollabHost.exe"),
            "CiscoCollabHost.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return f'"{candidate}"'
        # Prefer CiscoCollabHost fallback.
        return f'"{collabhost_launcher}"' if collabhost_launcher else "CiscoCollabHost.exe"

    if IS_LINUX:
        if shutil.which("webex"):
            return "webex"
        if os.path.isfile("/opt/Webex/bin/CiscoCollabHost"):
            return "/opt/Webex/bin/CiscoCollabHost"
        return "webex"

    return ""


def _start_webex(cfg: Config) -> bool:
    command = (cfg.webex_command or "").strip()
    if not command:
        print("[ERROR] Webex start command is empty.")
        return False

    try:
        _update_state(last_start_attempt=time.time(), last_start_success=False)
        if IS_WINDOWS:
            subprocess.Popen(command, shell=True)
        elif IS_LINUX:
            subprocess.Popen(command, shell=True)
        else:
            print("[ERROR] Unsupported platform for Webex auto-start.")
            return False
    except Exception as exc:
        print(f"[ERROR] Failed to start Webex with '{command}': {exc}")
        return False

    _update_state(last_start_success=True)
    print(f"[INFO] Webex start command executed: {command}")
    return True


def _ensure_webex_running(cfg: Config) -> None:
    if _is_webex_running():
        return

    if not cfg.auto_start_webex:
        print("[WARN] Webex is not running and auto-start is disabled.")
        return

    print("[INFO] Webex is not running; attempting to start it.")
    if not _start_webex(cfg):
        return

    deadline = time.time() + 20
    while time.time() < deadline:
        if _is_webex_running():
            print("[OK] Webex is running.")
            return
        time.sleep(1)

    print("[WARN] Webex start command was sent, but process not detected yet.")


def _iter_candidate_windows(title_regex: str):
    if not IS_WINDOWS:
        return

    # Enumerate only top-level windows first; full UIA desktop traversal can block.
    desktop = Desktop(backend="uia")
    try:
        elements = findwindows.find_elements(backend="uia", top_level_only=True)
    except Exception:
        return

    for element in elements:
        try:
            window = desktop.window(handle=element.handle)
            title = window.window_text() or ""
            if re.search(title_regex, title, re.IGNORECASE):
                yield window
        except Exception:
            continue


_PID_IMAGE_CACHE: dict[int, str] = {}


def _get_process_image_name_windows(pid: int) -> str:
    if not IS_WINDOWS or pid <= 0:
        return ""

    cached = _PID_IMAGE_CACHE.get(pid)
    if cached is not None:
        return cached

    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        line = (result.stdout or "").strip()
        if not line or line.startswith("INFO:"):
            _PID_IMAGE_CACHE[pid] = ""
            return ""
        row = next(csv.reader([line]), [])
        image_name = (row[0] if row else "").strip().lower()
        _PID_IMAGE_CACHE[pid] = image_name
        return image_name
    except Exception:
        _PID_IMAGE_CACHE[pid] = ""
        return ""


def _is_webex_window_windows(window) -> bool:
    if not IS_WINDOWS:
        return False

    try:
        pid = int(window.element_info.process_id)
    except Exception:
        pid = 0

    image_name = _get_process_image_name_windows(pid)
    if image_name in {"ciscocollabhost.exe", "webex.exe"}:
        return True

    # Fallback if process lookup fails: aggressively skip obvious non-target apps.
    title = (window.window_text() or "").strip().lower()
    if re.search(r"visual studio code|mozilla firefox|snipping tool|command prompt|powershell", title):
        return False
    return "webex" in title


def _find_answer_button(window, label_patterns: List[re.Pattern[str]]):
    try:
        descendants = window.descendants(control_type="Button")
    except Exception:
        return None

    for btn in descendants:
        text = (btn.window_text() or "").strip()
        if any(p.match(text) for p in label_patterns):
            return btn
    return None


def _find_button_in_windows(
    title_regex: str,
    label_patterns: List[re.Pattern[str]],
    webex_only: bool = False,
):
    for window in _iter_candidate_windows(title_regex):
        if webex_only and IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = (button.window_text() or "").strip()
        return title, button, label

    return None


def _find_button_in_window_title(window_title: str, label_patterns: List[re.Pattern[str]]):
    if not window_title:
        return None

    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        if title != window_title:
            continue

        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = (button.window_text() or "").strip()
        return title, button, label

    return None


def _find_clickable_control_in_windows(
    title_regex: str,
    label_patterns: List[re.Pattern[str]],
    webex_only: bool = False,
):
    control_types = ["Button", "ListItem", "Text", "Pane", "Custom"]
    for window in _iter_candidate_windows(title_regex):
        if webex_only and IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        for control_type in control_types:
            try:
                descendants = window.descendants(control_type=control_type)
            except Exception:
                continue

            for control in descendants:
                text = (control.window_text() or "").strip()
                if any(p.match(text) for p in label_patterns):
                    return title, control, text

    return None


def _find_best_share_confirm_button_windows(label_patterns: List[re.Pattern[str]]):
    candidates = []
    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        try:
            descendants = window.descendants(control_type="Button")
        except Exception:
            continue

        for button in descendants:
            label = (button.window_text() or "").strip()
            if not any(p.match(label) for p in label_patterns):
                continue

            rect = None
            try:
                rect = button.rectangle()
            except Exception:
                try:
                    rect = button.element_info.rectangle
                except Exception:
                    rect = None

            if rect is None:
                continue

            width = max(1, int(rect.right) - int(rect.left))
            height = max(1, int(rect.bottom) - int(rect.top))
            # Prefer visually large, bottom-positioned Share button in share dialog.
            score = int(rect.top) * 10 + width * height
            candidates.append((score, title, button, label))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, title, button, label = candidates[0]
    return title, button, label


def _find_share_dialog_window_title_windows() -> str:
    marker_patterns = _compile_label_patterns(["Screen 1", "Screen 2", "Application", "Sharing options"])
    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        try:
            descendants = window.descendants()
        except Exception:
            continue

        hits = 0
        for control in descendants:
            text = (control.window_text() or "").strip()
            if any(p.match(text) for p in marker_patterns):
                hits += 1
                if hits >= 2:
                    return title
    return ""


def _debug_share_controls() -> dict:
    controls = []
    if not IS_WINDOWS:
        return {"supported": False, "reason": "Debug control dump currently implemented for Windows"}

    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""
        if not title and not re.search(r"webex|share", title, re.IGNORECASE):
            # keep empty-title windows too; some Webex dialogs have blank titles
            pass

        for control_type in ["Button", "ListItem", "Text"]:
            try:
                descendants = window.descendants(control_type=control_type)
            except Exception:
                continue

            for control in descendants:
                text = (control.window_text() or "").strip()
                if not text:
                    continue
                if not re.search(r"share|screen|application|content", text, re.IGNORECASE):
                    continue

                rect = None
                try:
                    rect = control.rectangle()
                except Exception:
                    try:
                        rect = control.element_info.rectangle
                    except Exception:
                        rect = None

                controls.append(
                    {
                        "window": title,
                        "control_type": control_type,
                        "text": text,
                        "rect": {
                            "left": int(rect.left) if rect else None,
                            "top": int(rect.top) if rect else None,
                            "right": int(rect.right) if rect else None,
                            "bottom": int(rect.bottom) if rect else None,
                        },
                    }
                )

    return {
        "supported": True,
        "count": len(controls),
        "controls": controls[:200],
    }


def _iter_accessible_nodes(accessible):
    yield accessible
    try:
        count = int(accessible.childCount)
    except Exception:
        return

    for index in range(count):
        try:
            child = accessible.getChildAtIndex(index)
        except Exception:
            continue
        if child is None:
            continue
        yield from _iter_accessible_nodes(child)


def _get_accessible_window_name(accessible) -> str:
    node = accessible
    while node is not None:
        try:
            role_name = (node.getRoleName() or "").lower()
            if role_name in {"frame", "window", "dialog", "alert"}:
                return (node.name or "").strip()
            node = node.parent
        except Exception:
            return ""
    return ""


def _find_incoming_call_target_linux(cfg: Config, label_patterns: List[re.Pattern[str]]):
    if not IS_LINUX:
        return None

    try:
        import pyatspi
    except Exception as exc:
        print(
            "[ERROR] Linux backend requires pyatspi. Install with: "
            "sudo apt install python3-pyatspi\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception:
        return None

    for app in desktop:
        app_name = (getattr(app, "name", "") or "").strip()
        if not re.search(r"webex", app_name, re.IGNORECASE):
            continue

        for node in _iter_accessible_nodes(app):
            try:
                role_name = (node.getRoleName() or "").lower()
            except Exception:
                continue

            if role_name not in {"push button", "button"}:
                continue

            label = (getattr(node, "name", "") or "").strip()
            if not any(p.match(label) for p in label_patterns):
                continue

            title = _get_accessible_window_name(node) or app_name
            if not re.search(cfg.window_title_regex, title, re.IGNORECASE):
                if not re.search(cfg.window_title_regex, app_name, re.IGNORECASE):
                    continue

            return title, node, label

    return None


def _find_button_target_linux(label_patterns: List[re.Pattern[str]], title_regex: str):
    if not IS_LINUX:
        return None

    try:
        import pyatspi
    except Exception as exc:
        print(
            "[ERROR] Linux backend requires pyatspi. Install with: "
            "sudo apt install python3-pyatspi\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception:
        return None

    for app in desktop:
        app_name = (getattr(app, "name", "") or "").strip()
        if not re.search(r"webex", app_name, re.IGNORECASE):
            continue

        for node in _iter_accessible_nodes(app):
            try:
                role_name = (node.getRoleName() or "").lower()
            except Exception:
                continue

            if role_name not in {"push button", "button"}:
                continue

            label = (getattr(node, "name", "") or "").strip()
            if not any(p.match(label) for p in label_patterns):
                continue

            title = _get_accessible_window_name(node) or app_name
            if not re.search(title_regex, title, re.IGNORECASE):
                if not re.search(title_regex, app_name, re.IGNORECASE):
                    continue

            return title, node, label

    return None


def _find_clickable_target_linux(label_patterns: List[re.Pattern[str]], title_regex: str):
    if not IS_LINUX:
        return None

    try:
        import pyatspi
    except Exception as exc:
        print(
            "[ERROR] Linux backend requires pyatspi. Install with: "
            "sudo apt install python3-pyatspi\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception:
        return None

    clickable_roles = {
        "push button",
        "button",
        "list item",
        "table cell",
        "label",
        "panel",
    }

    for app in desktop:
        app_name = (getattr(app, "name", "") or "").strip()
        if not re.search(r"webex", app_name, re.IGNORECASE):
            continue

        for node in _iter_accessible_nodes(app):
            try:
                role_name = (node.getRoleName() or "").lower()
            except Exception:
                continue

            if role_name not in clickable_roles:
                continue

            label = (getattr(node, "name", "") or "").strip()
            if not any(p.match(label) for p in label_patterns):
                continue

            title = _get_accessible_window_name(node) or app_name
            if not re.search(title_regex, title, re.IGNORECASE):
                if not re.search(title_regex, app_name, re.IGNORECASE):
                    continue

            return title, node, label

    return None


def _find_incoming_call_target(cfg: Config, label_patterns: List[re.Pattern[str]]):
    if IS_LINUX:
        return _find_incoming_call_target_linux(cfg, label_patterns)

    for window in _iter_candidate_windows(cfg.window_title_regex):
        title = window.window_text() or ""
        if cfg.verbose:
            print(f"[DEBUG] Candidate window: {title}")

        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = (button.window_text() or "").strip()
        return title, button, label

    return None


def _find_button_target(label_patterns: List[re.Pattern[str]], title_regex: str):
    if IS_LINUX:
        return _find_button_target_linux(label_patterns, title_regex)
    if IS_WINDOWS:
        return _find_button_in_windows(title_regex, label_patterns)
    return None


def _find_clickable_target(label_patterns: List[re.Pattern[str]], title_regex: str):
    if IS_LINUX:
        return _find_clickable_target_linux(label_patterns, title_regex)
    if IS_WINDOWS:
        return _find_clickable_control_in_windows(title_regex, label_patterns)
    return None


def _find_share_button_target_windows(label_patterns: List[re.Pattern[str]], title_regex: str):
    target = _find_button_in_windows(title_regex, label_patterns, webex_only=True)
    if target:
        return target
    return _find_clickable_control_in_windows(title_regex, label_patterns, webex_only=True)


def _invoke_button(cfg: Config, title: str, button, label: str, action_name: str) -> bool:
    print(f"[INFO] {action_name} UI matched in window '{title}', button '{label}'")
    _update_state(last_matched_window=title, last_matched_button=label)

    if cfg.dry_run:
        print("[INFO] Dry-run enabled; not clicking the button.")
        return True

    if IS_WINDOWS:
        try:
            button.invoke()
            print(f"[OK] {action_name} button invoked.")
            return True
        except Exception as exc:
            if cfg.verbose:
                print(f"[WARN] invoke() failed: {exc}; trying click_input().")
            try:
                button.click_input()
                print(f"[OK] {action_name} button clicked with click_input().")
                return True
            except Exception as click_exc:
                print(f"[ERROR] Failed to click {action_name} button: {click_exc}")
                return False

    if IS_LINUX:
        try:
            action = button.queryAction()
            for i in range(action.nActions):
                action_label = (action.getName(i) or "").lower()
                if action_label in {"click", "press", "activate"}:
                    action.doAction(i)
                    print(f"[OK] {action_name} button action executed via AT-SPI.")
                    return True

            if action.nActions > 0:
                action.doAction(0)
                print(f"[OK] {action_name} button default action executed via AT-SPI.")
                return True
        except Exception as exc:
            print(f"[ERROR] Failed to activate {action_name} button on Linux: {exc}")
            return False

    print(f"[ERROR] Unsupported platform for {action_name} action.")
    return False


def _start_screen_share(cfg: Config) -> dict:
    primary_share_labels = _compile_label_patterns([
        "Share",
        "Share screen",
        "Start sharing",
        "Share content",
    ])
    dialog_screen_labels = _compile_label_patterns([
        "Screen",
        "Screen 1",
    ])
    dialog_share_labels = _compile_label_patterns([
        "Share",
        "Share screen",
    ])

    if IS_WINDOWS:
        target = _find_share_button_target_windows(primary_share_labels, title_regex=r"webex|meeting|call")
        if not target:
            target = _find_share_button_target_windows(primary_share_labels, title_regex=r".*")
    else:
        target = _find_button_target(primary_share_labels, title_regex=r"webex|meeting|call")
        if not target:
            target = _find_clickable_target(primary_share_labels, title_regex=r"webex|meeting|call")
        if not target:
            target = _find_button_target(primary_share_labels, title_regex=r".*")
        if not target:
            target = _find_clickable_target(primary_share_labels, title_regex=r".*")
    if not target:
        return {"started": False, "reason": "Primary Share control not found"}

    title, button, label = target
    opened = _invoke_button(cfg, title, button, label, "Open share dialog")
    if not opened:
        return {
            "started": False,
            "reason": "Failed to open share dialog",
            "window": title,
            "button": label,
        }

    time.sleep(1.0)

    screen_target = _find_clickable_target(dialog_screen_labels, title_regex=r"share|shared content|content")
    screen_label = ""
    dialog_title = ""
    if screen_target:
        screen_title, screen_control, screen_label = screen_target
        dialog_title = screen_title
        selected = _invoke_button(cfg, screen_title, screen_control, screen_label, "Select screen")
        if not selected:
            return {
                "started": False,
                "reason": "Failed to select screen option",
                "window": screen_title,
                "button": screen_label,
            }
        time.sleep(0.5)
    else:
        # In many Webex layouts Screen 1 is preselected already.
        if cfg.verbose:
            print("[WARN] Screen option not found explicitly; trying final Share button directly.")
        if IS_WINDOWS:
            dialog_title = _find_share_dialog_window_title_windows()

    confirm_target = None
    if dialog_title and IS_WINDOWS:
        confirm_target = _find_button_in_window_title(dialog_title, dialog_share_labels)
    if not confirm_target:
        confirm_target = _find_button_target(dialog_share_labels, title_regex=r"share|shared content|content")
    if not confirm_target:
        confirm_target = _find_button_target(dialog_share_labels, title_regex=r".*")
    if not confirm_target and IS_WINDOWS:
        confirm_target = _find_best_share_confirm_button_windows(dialog_share_labels)
    if not confirm_target:
        if IS_WINDOWS and not cfg.dry_run:
            # In some builds the Share button is not exposed cleanly via UIA; Enter can trigger default action.
            try:
                send_keys("{ENTER}")
                return {
                    "started": True,
                    "window": "",
                    "button": "ENTER",
                    "selection": screen_label,
                    "fallback": "keyboard_enter",
                }
            except Exception:
                pass
        return {"started": False, "reason": "Confirm Share button not found in share dialog"}

    confirm_title, confirm_button, confirm_label = confirm_target
    started = _invoke_button(cfg, confirm_title, confirm_button, confirm_label, "Start screen share")
    return {
        "started": started,
        "window": confirm_title,
        "button": confirm_label,
        "selection": screen_label,
    }


def _stop_screen_share() -> dict:
    if IS_WINDOWS:
        try:
            send_keys("^+z")
            return {
                "stopped": True,
                "method": "shortcut",
                "shortcut": "Ctrl+Shift+Z",
            }
        except Exception as exc:
            return {
                "stopped": False,
                "method": "shortcut",
                "shortcut": "Ctrl+Shift+Z",
                "reason": str(exc),
            }

    if IS_LINUX:
        try:
            result = subprocess.run(
                ["xdotool", "key", "ctrl+shift+z"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return {
                    "stopped": True,
                    "method": "shortcut",
                    "shortcut": "Ctrl+Shift+Z",
                }
            return {
                "stopped": False,
                "method": "shortcut",
                "shortcut": "Ctrl+Shift+Z",
                "reason": (result.stderr or result.stdout or "xdotool failed").strip(),
            }
        except Exception as exc:
            return {
                "stopped": False,
                "method": "shortcut",
                "shortcut": "Ctrl+Shift+Z",
                "reason": str(exc),
            }

    return {
        "stopped": False,
        "method": "shortcut",
        "shortcut": "Ctrl+Shift+Z",
        "reason": "Unsupported platform",
    }


def _is_windows_button_present(label: str) -> bool:
    if not IS_WINDOWS:
        return False

    patterns = _compile_label_patterns([label])
    return (
        _find_button_in_windows(r"webex|meeting|call", patterns, webex_only=True) is not None
        or _find_button_in_windows(r".*", patterns, webex_only=True) is not None
    )


def _post_answer_shortcuts(cfg: Config) -> None:
    if cfg.dry_run or not IS_WINDOWS:
        return

    shortcuts = [
        ("Start video", "^+v", "Ctrl+Shift+V"),
        ("Unmute", "^m", "Ctrl+M"),
    ]
    sent_labels = set()
    deadline = time.time() + 4.0

    # Retry briefly because call-stripe controls can appear after answer animation.
    while time.time() < deadline and len(sent_labels) < len(shortcuts):
        for label, keys, key_desc in shortcuts:
            if label in sent_labels:
                continue
            if not _is_windows_button_present(label):
                continue

            try:
                send_keys(keys)
                sent_labels.add(label)
                print(f"[INFO] '{label}' detected in call stripe; sent {key_desc}.")
            except Exception as exc:
                print(f"[WARN] Failed to send {key_desc} for '{label}': {exc}")

        if len(sent_labels) < len(shortcuts):
            time.sleep(0.4)


def _attempt_answer(cfg: Config, title: str, button, label: str) -> bool:
    answered = _invoke_button(cfg, title, button, label, "Answer")
    if answered:
        _post_answer_shortcuts(cfg)
    return answered


def try_answer_once(cfg: Config, label_patterns: List[re.Pattern[str]], state: RuntimeState) -> bool:
    now = time.time()
    target = _find_incoming_call_target(cfg, label_patterns)

    if not target:
        state.last_seen = None
        state.incoming_since = None
        return False

    title, button, label = target

    if state.incoming_since is None:
        state.incoming_since = now
        if cfg.verbose:
            print("[DEBUG] Incoming call detected; starting timers.")

    state.last_seen = now
    elapsed = now - state.incoming_since

    # Ring count is estimated from elapsed time while incoming call UI is visible.
    estimated_rings = int(elapsed / cfg.ring_interval) + 1
    delay_ready = cfg.answer_delay > 0 and elapsed >= cfg.answer_delay
    rings_ready = cfg.answer_after_rings > 0 and estimated_rings >= cfg.answer_after_rings

    if cfg.verbose:
        print(
            "[DEBUG] Incoming elapsed="
            + f"{elapsed:.2f}s; estimated_rings={estimated_rings}; "
            + f"delay_ready={delay_ready}; rings_ready={rings_ready}"
        )

    if cfg.answer_delay <= 0 and cfg.answer_after_rings <= 0:
        return _attempt_answer(cfg, title, button, label)

    if delay_ready or rings_ready:
        return _attempt_answer(cfg, title, button, label)

    return False


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Auto-answer incoming Webex calls (Windows/Linux)",
        epilog=(
            "Requirements:\n"
            "  Windows: pip install pywinauto flask\n"
            "  Linux (GNOME/X11): sudo apt install python3-pyatspi\n\n"
            "Optional web server dependency:\n"
            "  pip install flask\n\n"
            "Optional pre-check:\n"
            "  python -m py_compile WebexVDIPeerRunner.py"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0,
        help="Max seconds to watch for incoming call UI. 0 means run forever.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.30,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--answer-delay",
        type=float,
        default=0.0,
        help="Wait this many seconds after incoming UI appears before answering.",
    )
    parser.add_argument(
        "--answer-after-rings",
        type=int,
        default=0,
        help="Answer after this many estimated rings (0 disables).",
    )
    parser.add_argument(
        "--ring-interval",
        type=float,
        default=3.0,
        help="Estimated seconds per ring when using --answer-after-rings.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exit right after first successful answer.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect incoming call UI without clicking.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print debug logs for candidate windows.",
    )
    parser.add_argument(
        "--answer-label",
        action="append",
        default=["Answer", "Accept"],
        help=(
            "Answer button label to match; can be repeated. "
            "Default: Answer, Accept"
        ),
    )
    parser.add_argument(
        "--window-title-regex",
        default=r"webex|incoming|call",
        help="Regex used to filter candidate windows by title.",
    )
    parser.add_argument(
        "--no-auto-start-webex",
        action="store_true",
        help="Do not start Webex automatically if it is not running.",
    )
    parser.add_argument(
        "--webex-command",
        default="",
        help="Custom command to start Webex when not running.",
    )
    parser.add_argument(
        "--webex-monitor-interval",
        type=float,
        default=20.0,
        help="Seconds between Webex running checks/restart attempts.",
    )
    parser.add_argument(
        "--web-server",
        action="store_true",
        help="Run a Flask web server alongside the watcher.",
    )
    parser.add_argument(
        "--enable-share-debug-endpoint",
        action="store_true",
        help="Enable the /debug-share-controls endpoint.",
    )
    parser.add_argument(
        "--share-cooldown",
        type=float,
        default=2.5,
        help="Minimum seconds between /sharescreen requests.",
    )
    parser.add_argument(
        "--web-host",
        default="0.0.0.0",
        help="Host interface for the Flask web server.",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=5000,
        help="Port for the Flask web server.",
    )

    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be > 0")
    if args.timeout < 0:
        parser.error("--timeout must be >= 0")
    if args.answer_delay < 0:
        parser.error("--answer-delay must be >= 0")
    if args.answer_after_rings < 0:
        parser.error("--answer-after-rings must be >= 0")
    if args.ring_interval <= 0:
        parser.error("--ring-interval must be > 0")
    if args.webex_monitor_interval <= 0:
        parser.error("--webex-monitor-interval must be > 0")
    if args.share_cooldown < 0:
        parser.error("--share-cooldown must be >= 0")
    if args.web_port <= 0 or args.web_port > 65535:
        parser.error("--web-port must be between 1 and 65535")

    return Config(
        timeout=args.timeout,
        interval=args.interval,
        answer_delay=args.answer_delay,
        answer_after_rings=args.answer_after_rings,
        ring_interval=args.ring_interval,
        once=args.once,
        dry_run=args.dry_run,
        verbose=args.verbose,
        answer_labels=args.answer_label,
        window_title_regex=args.window_title_regex,
        auto_start_webex=not args.no_auto_start_webex,
        webex_command=args.webex_command.strip() or _default_webex_command(),
        webex_monitor_interval=args.webex_monitor_interval,
        enable_web_server=args.web_server,
        enable_share_debug_endpoint=args.enable_share_debug_endpoint,
        share_cooldown=args.share_cooldown,
        web_host=args.web_host,
        web_port=args.web_port,
    )


def main() -> int:
    cfg = parse_args()
    label_patterns = _compile_label_patterns(cfg.answer_labels)

    print("[INFO] Webex VDI peer runner (auto-answer watcher) started.")
    print(
        "[INFO] Labels="
        + ", ".join(cfg.answer_labels)
        + f"; interval={cfg.interval}s; timeout={cfg.timeout or 'infinite'}s"
    )
    print(
        "[INFO] Answer policy: "
        + f"delay={cfg.answer_delay}s; after_rings={cfg.answer_after_rings}; "
        + f"ring_interval={cfg.ring_interval}s"
    )
    print(
        "[INFO] Webex startup: "
        + f"auto_start={cfg.auto_start_webex}; command={cfg.webex_command}; "
        + f"monitor_interval={cfg.webex_monitor_interval}s"
    )
    if cfg.enable_web_server:
        print(f"[INFO] Web server requested on http://{cfg.web_host}:{cfg.web_port}")

    start = time.time()
    state = RUNTIME_STATE

    _start_web_server(cfg)
    _ensure_webex_running(cfg)
    next_webex_check_at = time.time() + cfg.webex_monitor_interval

    try:
        while True:
            now = time.time()
            if now >= next_webex_check_at:
                _ensure_webex_running(cfg)
                next_webex_check_at = now + cfg.webex_monitor_interval
            matched = try_answer_once(cfg, label_patterns, state)
            if matched:
                with STATE_LOCK:
                    state.answers += 1
                    state.incoming_since = None
                    state.last_seen = None
                if cfg.once:
                    return 0

            if cfg.timeout and (time.time() - start) >= cfg.timeout:
                print(f"[INFO] Timeout reached ({cfg.timeout}s). Answers sent: {state.answers}")
                return 0

            time.sleep(cfg.interval)
    except KeyboardInterrupt:
        print(f"\n[INFO] Stopped by user. Answers sent: {state.answers}")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

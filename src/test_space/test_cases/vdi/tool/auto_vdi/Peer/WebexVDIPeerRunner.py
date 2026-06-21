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
import urllib.request
import urllib.error
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

_AUTO_VDI_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_CALLING_INFO_PATH = os.path.join(_AUTO_VDI_DIR, "calling_info.txt")
_HVD_INFO_PATHS = [
    os.path.join(_AUTO_VDI_DIR, "hvd_info.txt"),
    os.path.join(_AUTO_VDI_DIR, "hvd_info-horizon.txt"),
]

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
    join_toast_title: str
    join_toast_button_label: str
    prejoin_window_title: str
    prejoin_button_label: str
    join_debug_interval: float


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
    last_join_flow_debug_at: float | None = None
    last_join_flow_debug_key: str = ""


STATE_LOCK = threading.Lock()
SHARE_REQUEST_LOCK = threading.Lock()
REACTION_LOCK = threading.Lock()
REACTION_STOP_EVENT = threading.Event()
REACTION_THREAD: threading.Thread | None = None
REACTION_INTERVAL_SECONDS = 10.0
CHECKBOX_DEBUG_VERBOSE = False


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


def _checkbox_debug(message: str) -> None:
    if CHECKBOX_DEBUG_VERBOSE:
        print(f"[DEBUG] {message}")


def _send_reaction_shortcut_once() -> tuple[bool, str]:
    if IS_WINDOWS:
        try:
            send_keys("%+6")
            return True, "Alt+Shift+6"
        except Exception as exc:
            return False, str(exc)

    if IS_LINUX:
        try:
            result = subprocess.run(
                ["xdotool", "key", "alt+shift+6"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True, "alt+shift+6"
            return False, (result.stderr or result.stdout or "xdotool failed").strip()
        except Exception as exc:
            return False, str(exc)

    return False, "Unsupported platform"


def _reaction_sender_loop(interval_seconds: float) -> None:
    while not REACTION_STOP_EVENT.is_set():
        ok, detail = _send_reaction_shortcut_once()
        if ok:
            print(f"[INFO] Sent reaction shortcut: {detail}")
        else:
            print(f"[WARN] Failed to send reaction shortcut: {detail}")

        if REACTION_STOP_EVENT.wait(interval_seconds):
            break


def _start_reaction_sender(interval_seconds: float = REACTION_INTERVAL_SECONDS) -> dict:
    global REACTION_THREAD

    with REACTION_LOCK:
        if REACTION_THREAD is not None and REACTION_THREAD.is_alive():
            return {
                "started": False,
                "already_running": True,
                "interval_seconds": interval_seconds,
                "shortcut": "Alt+Shift+6",
            }

        REACTION_STOP_EVENT.clear()
        REACTION_THREAD = threading.Thread(
            target=_reaction_sender_loop,
            args=(interval_seconds,),
            name="webex-vdi-reaction-sender",
            daemon=True,
        )
        REACTION_THREAD.start()

        return {
            "started": True,
            "already_running": False,
            "interval_seconds": interval_seconds,
            "shortcut": "Alt+Shift+6",
        }


def _stop_reaction_sender() -> dict:
    global REACTION_THREAD

    with REACTION_LOCK:
        thread = REACTION_THREAD
        if thread is None or not thread.is_alive():
            REACTION_THREAD = None
            return {
                "stopped": False,
                "was_running": False,
            }

        REACTION_STOP_EVENT.set()
        thread.join(timeout=2.0)
        still_running = thread.is_alive()
        if not still_running:
            REACTION_THREAD = None

        return {
            "stopped": not still_running,
            "was_running": True,
        }


def _get_real_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _read_kv_file(path: str) -> dict:
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    result[key.strip()] = value.strip()
    except OSError:
        pass
    return result


def _update_peer_ip_in_calling_info(path: str, real_ip: str, port: int) -> None:
    new_peer_ip = f"{real_ip}:{port}"
    lines = []
    updated = False
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if re.match(r"^\s*peer_ip\s*:", line):
                    lines.append(f"peer_ip: {new_peer_ip}\n")
                    updated = True
                else:
                    lines.append(line)
    except OSError:
        lines = []

    if not updated:
        lines.append(f"peer_ip: {new_peer_ip}\n")

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[INFO] Updated peer_ip in {path} to {new_peer_ip}")
    except OSError as exc:
        print(f"[WARN] Failed to update calling_info.txt: {exc}")


def _upload_calling_info_once(hvd_ip: str, calling_info_path: str) -> bool:
    url = f"http://{hvd_ip}/uploadCallingInfo"
    try:
        with open(calling_info_path, "rb") as f:
            data = f.read()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "text/plain")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 204)
    except Exception as exc:
        print(f"[WARN] Upload to {hvd_ip} failed: {exc}")
        return False


def _upload_calling_info_with_retry(hvd_ip: str, calling_info_path: str, retry_interval: float = 30.0) -> None:
    print(f"[INFO] Starting calling_info.txt upload task for HVD: {hvd_ip}")
    while True:
        if _upload_calling_info_once(hvd_ip, calling_info_path):
            print(f"[OK] calling_info.txt uploaded successfully to {hvd_ip}")
            return
        print(f"[WARN] Will retry upload to {hvd_ip} in {retry_interval}s")
        time.sleep(retry_interval)


def _init_calling_info_and_upload(cfg: Config) -> None:
    real_ip = _get_real_ip()
    _update_peer_ip_in_calling_info(_CALLING_INFO_PATH, real_ip, cfg.web_port)

    hvd_ips: list = []
    seen: set = set()
    for hvd_file in _HVD_INFO_PATHS:
        kv = _read_kv_file(hvd_file)
        hvd_ip = kv.get("hvd_ip", "").strip()
        if hvd_ip and hvd_ip not in seen:
            hvd_ips.append(hvd_ip)
            seen.add(hvd_ip)
            print(f"[INFO] Found HVD IP from {os.path.basename(hvd_file)}: {hvd_ip}")

    for hvd_ip in hvd_ips:
        t = threading.Thread(
            target=_upload_calling_info_with_retry,
            args=(hvd_ip, _CALLING_INFO_PATH),
            name=f"calling-info-upload-{hvd_ip}",
            daemon=True,
        )
        t.start()


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
                    "/sharefile",
                    "/immersiveshare",
                    "/stopshare",
                    "/stopfileshare",
                    "/sendReaction",
                    "/stopReaction",
                    "/recvShareStatus",
                    "/leaveMeeting",
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

    def _handle_share_request(immersive: bool = False):
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
            return jsonify(_start_screen_share(cfg, immersive=immersive))
        finally:
            SHARE_REQUEST_LOCK.release()

    @app.get("/sharescreen")
    def sharescreen():
        return _handle_share_request(immersive=False)

    @app.get("/sharefile")
    def sharefile():
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

        file_path = request.args.get("path", r"C:\WebexVDI-VC-Status.pdf").strip()
        if not file_path:
            file_path = r"C:\WebexVDI-VC-Status.pdf"

        _update_state(last_share_attempt=now)
        try:
            return jsonify(_start_file_share(cfg, file_path=file_path))
        finally:
            SHARE_REQUEST_LOCK.release()

    @app.get("/immersiveshare")
    def immersive_share():
        return _handle_share_request(immersive=True)

    if cfg.enable_share_debug_endpoint:
        @app.get("/debug-share-controls")
        def debug_share_controls():
            return jsonify(_debug_share_controls())

    @app.get("/stopshare")
    def stopshare():
        return jsonify(_stop_screen_share())

    @app.get("/stopfileshare")
    def stopfileshare():
        return jsonify(_stop_file_share(cfg))

    @app.get("/sendReaction")
    def send_reaction_route():
        return jsonify(_start_reaction_sender(REACTION_INTERVAL_SECONDS))

    @app.get("/stopReaction")
    def stop_reaction_route():
        return jsonify(_stop_reaction_sender())

    @app.get("/leaveMeeting")
    def leave_meeting_route():
        return jsonify(_leave_meeting(cfg))

    @app.get("/recvShareStatus")
    def recv_share_status():
        sharing = _is_screen_share_active()
        return jsonify({"rx_sharing": sharing})

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
        collabhost_programs = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Programs",
            "Cisco Spark",
            "CiscoCollabHost.exe",
        )
        candidates = [
            collabhost_launcher,
            collabhost_programs,
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Cisco Spark", "CiscoCollabHost.exe"),
            "CiscoCollabHost.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate
        # Prefer CiscoCollabHost fallback.
        if collabhost_launcher:
            return collabhost_launcher
        return "CiscoCollabHost.exe"

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

    def _strip_matching_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1].strip()
        return value

    def _windows_webex_candidates(raw_command: str):
        normalized = _strip_matching_quotes(raw_command)
        candidates = []

        if normalized:
            candidates.append(normalized)

        localappdata = os.environ.get("LOCALAPPDATA", "")
        programfiles = os.environ.get("PROGRAMFILES", "")
        for known in [
            os.path.join(localappdata, "CiscoSparkLauncher", "CiscoCollabHost.exe"),
            os.path.join(localappdata, "Programs", "Cisco Spark", "CiscoCollabHost.exe"),
            os.path.join(programfiles, "Cisco Spark", "CiscoCollabHost.exe"),
            "CiscoCollabHost.exe",
        ]:
            if known and known not in candidates:
                candidates.append(known)

        return candidates

    try:
        _update_state(last_start_attempt=time.time(), last_start_success=False)
        if IS_WINDOWS:
            started_with = None
            last_error = None

            for candidate in _windows_webex_candidates(command):
                try:
                    is_probably_path = ("\\" in candidate) or ("/" in candidate) or candidate.lower().endswith(".exe")
                    if is_probably_path and os.path.isfile(candidate):
                        subprocess.Popen([candidate], shell=False)
                        started_with = candidate
                        break
                    if candidate.lower().endswith(".exe") and shutil.which(candidate):
                        subprocess.Popen([candidate], shell=False)
                        started_with = candidate
                        break
                except Exception as exc:
                    last_error = exc

            if not started_with:
                if last_error is not None:
                    raise last_error
                raise RuntimeError(
                    "No valid Webex executable found. Tried: "
                    + ", ".join(_windows_webex_candidates(command))
                )

            command = started_with
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
            title = _safe_control_text(window)
            if re.search(title_regex, title, re.IGNORECASE):
                yield window
        except Exception:
            continue


_PID_IMAGE_CACHE: dict[int, str] = {}


def _safe_control_text(control) -> str:
    try:
        return (control.window_text() or "").strip()
    except Exception:
        return ""


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
    title = _safe_control_text(window).lower()
    if re.search(r"visual studio code|mozilla firefox|snipping tool|command prompt|powershell", title):
        return False
    return "webex" in title


def _find_answer_button(window, label_patterns: List[re.Pattern[str]]):
    try:
        descendants = window.descendants(control_type="Button")
    except Exception:
        return None

    for btn in descendants:
        text = _safe_control_text(btn)
        if any(p.match(text) for p in label_patterns):
            return btn
    return None


def _focus_webex_window_windows(title_regex: str = r"webex|meeting|call", exclude_exact_title: str = ""):
    if not IS_WINDOWS:
        return None

    for window in _iter_candidate_windows(title_regex):
        if not _is_webex_window_windows(window):
            continue

        title = _safe_control_text(window)
        if exclude_exact_title and title.strip().lower() == exclude_exact_title.strip().lower():
            continue

        try:
            window.set_focus()
            return title
        except Exception:
            try:
                window.restore()
                window.set_focus()
                return title
            except Exception:
                continue

    return None


def _find_button_in_windows(
    title_regex: str,
    label_patterns: List[re.Pattern[str]],
    webex_only: bool = False,
):
    for window in _iter_candidate_windows(title_regex):
        if webex_only and IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = _safe_control_text(window)
        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = _safe_control_text(button)
        return title, button, label

    return None


def _find_button_in_window_title(
    window_title: str,
    label_patterns: List[re.Pattern[str]],
    webex_only: bool = True,
    title_contains: bool = False,
):
    if not window_title:
        return None

    for window in _iter_candidate_windows(r".*"):
        if webex_only and IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = _safe_control_text(window)
        title_norm = title.strip().lower()
        window_title_norm = window_title.strip().lower()
        if title_contains:
            if window_title_norm not in title_norm:
                continue
        elif title_norm != window_title_norm:
            continue

        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = _safe_control_text(button)
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


def _find_show_me_in_front_target_windows(dialog_title: str = ""):
    label_patterns = _compile_label_patterns(["Show me in front"])
    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue

        title = _safe_control_text(window)
        if dialog_title and title.strip().lower() != dialog_title.strip().lower():
            continue

        try:
            all_descendants = window.descendants()
        except Exception:
            all_descendants = []

        matched_label_control = None
        matched_label_text = ""
        matched_label_rect = None

        # Pass 1: prefer an actual checkbox whose own text matches.
        for control in all_descendants:
            try:
                if control.element_info.control_type != "CheckBox":
                    continue
            except Exception:
                continue

            text = _safe_control_text(control)
            if any(p.match(text) for p in label_patterns):
                return title, control, (text or "Show me in front")

        # Pass 2: find any labeled control for "Show me in front".
        for control in all_descendants:
            text = _safe_control_text(control)
            if not any(p.match(text) for p in label_patterns):
                continue
            matched_label_control = control
            matched_label_text = text or "Show me in front"
            try:
                matched_label_rect = control.rectangle()
            except Exception:
                try:
                    matched_label_rect = control.element_info.rectangle
                except Exception:
                    matched_label_rect = None
            break

        if matched_label_control is None:
            continue

        # Pass 3: if label and checkbox are separate, pick nearest checkbox in same row.
        if matched_label_rect is not None:
            nearest_checkbox = None
            nearest_score = None
            label_top = int(matched_label_rect.top)
            label_bottom = int(matched_label_rect.bottom)
            label_left = int(matched_label_rect.left)

            for control in all_descendants:
                try:
                    if control.element_info.control_type != "CheckBox":
                        continue
                except Exception:
                    continue

                rect = None
                try:
                    rect = control.rectangle()
                except Exception:
                    try:
                        rect = control.element_info.rectangle
                    except Exception:
                        rect = None
                if rect is None:
                    continue

                top = int(rect.top)
                bottom = int(rect.bottom)
                left = int(rect.left)
                vertical_delta = min(abs(top - label_top), abs(bottom - label_bottom))
                horizontal_penalty = 0 if left <= label_left + 50 else (left - label_left)
                score = vertical_delta * 10 + horizontal_penalty

                if nearest_score is None or score < nearest_score:
                    nearest_score = score
                    nearest_checkbox = control

            if nearest_checkbox is not None:
                return title, nearest_checkbox, matched_label_text

        # Fallback: use the labeled control directly.
        return title, matched_label_control, matched_label_text

    return None


def _is_windows_checkbox_checked(control) -> bool | None:
    try:
        state = control.get_toggle_state()
        result = int(state) == 1
        _checkbox_debug(f"_is_windows_checkbox_checked: get_toggle_state() returned {state}, result={result}")
        return result
    except Exception as e:
        print(f"[WARN] _is_windows_checkbox_checked: get_toggle_state() failed: {e}")

    try:
        toggle_iface = getattr(control, "iface_toggle", None)
        if toggle_iface is None:
            _checkbox_debug("_is_windows_checkbox_checked: iface_toggle is None")
            return None
        state = int(toggle_iface.CurrentToggleState)
        result = state == 1
        _checkbox_debug(f"_is_windows_checkbox_checked: iface_toggle.CurrentToggleState={state}, result={result}")
        return result
    except Exception as e:
        print(f"[WARN] _is_windows_checkbox_checked: iface_toggle failed: {e}")
        return None


def _click_windows_checkbox_glyph(control) -> bool:
    """Click near the left checkbox glyph area instead of the wrapper center.

    Some custom Webex controls expose TogglePattern state but repaint only when
    the actual checkbox glyph hit area is clicked.
    """
    try:
        rect = control.rectangle()
        width = max(1, int(rect.right) - int(rect.left))
        height = max(1, int(rect.bottom) - int(rect.top))
    except Exception as e:
        print(f"[WARN] _click_windows_checkbox_glyph: failed to get rectangle: {e}")
        return False

    # Target left-side box area: x near left edge, y centered vertically.
    x = max(6, min(20, width // 5))
    y = max(4, min(height - 4, height // 2))

    try:
        _checkbox_debug(
            f"_click_windows_checkbox_glyph: clicking glyph at relative coords ({x}, {y}), "
            f"size=({width}x{height})"
        )
        control.click_input(coords=(x, y))
        return True
    except Exception as e:
        print(f"[WARN] _click_windows_checkbox_glyph: click_input(coords=...) failed: {e}")
        return False


def _set_windows_checkbox_checked(control, desired_checked: bool = True) -> bool:
    current = _is_windows_checkbox_checked(control)
    _checkbox_debug(f"_set_windows_checkbox_checked: initial state={current}, desired={desired_checked}")
    if current is desired_checked and desired_checked is False:
        _checkbox_debug("_set_windows_checkbox_checked: already in desired state=False, returning True")
        return True

    # Renderer-first strategy: prefer real input events before UIA toggle pattern.
    # This helps custom Webex controls that update UIA state but do not repaint reliably.
    for action in ("glyph_click", "click", "space", "invoke", "toggle"):
        for attempt in range(2):
            try:
                if action == "glyph_click":
                    _checkbox_debug(f"_set_windows_checkbox_checked: attempt {attempt+1}/2 glyph-targeted click")
                    if not _click_windows_checkbox_glyph(control):
                        break
                elif action == "click":
                    _checkbox_debug(f"_set_windows_checkbox_checked: attempt {attempt+1}/2 control.click_input()")
                    control.click_input()
                elif action == "space":
                    _checkbox_debug(f"_set_windows_checkbox_checked: attempt {attempt+1}/2 set_focus() + Space key")
                    control.set_focus()
                    send_keys(" ")
                elif action == "invoke":
                    _checkbox_debug(f"_set_windows_checkbox_checked: attempt {attempt+1}/2 control.invoke()")
                    control.invoke()
                else:
                    _checkbox_debug(f"_set_windows_checkbox_checked: attempt {attempt+1}/2 toggle_iface.Toggle()")
                    toggle_iface = getattr(control, "iface_toggle", None)
                    if toggle_iface is None:
                        _checkbox_debug("_set_windows_checkbox_checked: iface_toggle is None")
                        break
                    toggle_iface.Toggle()

                time.sleep(0.5)
            except Exception as e:
                print(f"[WARN] _set_windows_checkbox_checked: {action} action failed: {e}")
                break

            current = _is_windows_checkbox_checked(control)
            _checkbox_debug(f"_set_windows_checkbox_checked: after {action} attempt {attempt+1}, state={current}")
            if current is desired_checked:
                _checkbox_debug(f"_set_windows_checkbox_checked: {action} action reached desired state")
                return True

    print(f"[WARN] _set_windows_checkbox_checked: all attempts failed, final state={current}, returning False")
    return False


def _ensure_show_me_in_front_checked(cfg: Config, dialog_title: str = "") -> dict:
    if IS_WINDOWS:
        _checkbox_debug("_ensure_show_me_in_front_checked: searching for 'Show me in front' control")
        target = _find_show_me_in_front_target_windows(dialog_title=dialog_title)
        if not target:
            target = _find_show_me_in_front_target_windows()
        if not target:
            print("[WARN] _ensure_show_me_in_front_checked: control not found")
            return {
                "ok": False,
                "reason": "'Show me in front' option not found",
            }

        title, control, label = target
        _checkbox_debug(f"_ensure_show_me_in_front_checked: found control '{label}' in window '{title}'")
        _checkbox_debug(f"_ensure_show_me_in_front_checked: control object type: {type(control).__name__}")
        
        checked = _is_windows_checkbox_checked(control)
        _checkbox_debug(f"_ensure_show_me_in_front_checked: initial checked state={checked}")
        
        if checked is True:
            _checkbox_debug("_ensure_show_me_in_front_checked: control already checked, returning success")
            return {
                "ok": True,
                "window": title,
                "control": label,
                "already_checked": True,
            }

        # Prefer reliable checkbox state transitions when possible.
        is_checkbox = False
        try:
            is_checkbox = control.element_info.control_type == "CheckBox"
            _checkbox_debug(f"_ensure_show_me_in_front_checked: is_checkbox={is_checkbox}")
        except Exception as e:
            print(f"[WARN] _ensure_show_me_in_front_checked: control_type check failed: {e}")
            is_checkbox = False

        enabled = False
        if is_checkbox and not cfg.dry_run:
            _checkbox_debug("_ensure_show_me_in_front_checked: using _set_windows_checkbox_checked (is_checkbox=True)")
            enabled = _set_windows_checkbox_checked(control, desired_checked=True)
        else:
            _checkbox_debug(
                f"_ensure_show_me_in_front_checked: using _invoke_button (is_checkbox={is_checkbox}, dry_run={cfg.dry_run})"
            )
            enabled = _invoke_button(cfg, title, control, label, "Enable 'Show me in front'")

        _checkbox_debug(f"_ensure_show_me_in_front_checked: toggle enabled={enabled}")
        if not enabled:
            print("[WARN] _ensure_show_me_in_front_checked: toggle failed, returning error")
            return {
                "ok": False,
                "reason": "Failed to click 'Show me in front' option",
                "window": title,
                "control": label,
            }

        checked_after = _is_windows_checkbox_checked(control)
        _checkbox_debug(f"_ensure_show_me_in_front_checked: checked_after first attempt={checked_after}")
        
        if checked_after is False:
            _checkbox_debug("_ensure_show_me_in_front_checked: still unchecked, attempting fallback")
            # Fallback: for some builds, checkbox toggles via keyboard space on focus.
            if not cfg.dry_run:
                if is_checkbox:
                    _checkbox_debug("_ensure_show_me_in_front_checked: fallback - calling _set_windows_checkbox_checked again")
                    _set_windows_checkbox_checked(control, desired_checked=True)
                else:
                    try:
                        _checkbox_debug("_ensure_show_me_in_front_checked: fallback - set_focus + Space key")
                        control.set_focus()
                        send_keys(" ")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"[WARN] _ensure_show_me_in_front_checked: fallback failed: {e}")
                        pass
                checked_after = _is_windows_checkbox_checked(control)
                _checkbox_debug(f"_ensure_show_me_in_front_checked: checked_after fallback={checked_after}")

        if checked_after is False:
            print("[WARN] _ensure_show_me_in_front_checked: option still unchecked after all attempts")
            return {
                "ok": False,
                "reason": "'Show me in front' option did not remain checked",
                "window": title,
                "control": label,
            }

        _checkbox_debug("_ensure_show_me_in_front_checked: success - option verified as checked")
        return {
            "ok": True,
            "window": title,
            "control": label,
            "already_checked": False,
            "verified_checked": checked_after is True,
        }

    if IS_LINUX:
        label_patterns = _compile_label_patterns(["Show me in front"])
        target = _find_clickable_target(label_patterns, title_regex=r"share|shared content|content")
        if not target:
            target = _find_clickable_target(label_patterns, title_regex=r".*")
        if not target:
            return {
                "ok": False,
                "reason": "'Show me in front' option not found",
            }

        title, control, label = target
        enabled = _invoke_button(cfg, title, control, label, "Enable 'Show me in front'")
        if not enabled:
            return {
                "ok": False,
                "reason": "Failed to click 'Show me in front' option",
                "window": title,
                "control": label,
            }

        return {
            "ok": True,
            "window": title,
            "control": label,
            "already_checked": False,
            "verified_checked": None,
        }

    return {
        "ok": False,
        "reason": "Unsupported platform",
    }


def _ensure_show_me_in_front_unchecked(cfg: Config, dialog_title: str = "") -> dict:
    if IS_WINDOWS:
        _checkbox_debug("_ensure_show_me_in_front_unchecked: searching for 'Show me in front' control")
        target = _find_show_me_in_front_target_windows(dialog_title=dialog_title)
        if not target:
            target = _find_show_me_in_front_target_windows()
        if not target:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: control not found (may not be present in this layout)")
            return {
                "ok": True,
                "reason": "'Show me in front' option not found (skipping)",
            }

        title, control, label = target
        _checkbox_debug(f"_ensure_show_me_in_front_unchecked: found control '{label}' in window '{title}'")
        _checkbox_debug(f"_ensure_show_me_in_front_unchecked: control object type: {type(control).__name__}")
        
        checked = _is_windows_checkbox_checked(control)
        _checkbox_debug(f"_ensure_show_me_in_front_unchecked: initial checked state={checked}")
        
        if checked is False:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: control already unchecked, returning success")
            return {
                "ok": True,
                "window": title,
                "control": label,
                "already_unchecked": True,
            }

        # Prefer reliable checkbox state transitions when possible.
        is_checkbox = False
        try:
            is_checkbox = control.element_info.control_type == "CheckBox"
            _checkbox_debug(f"_ensure_show_me_in_front_unchecked: is_checkbox={is_checkbox}")
        except Exception as e:
            print(f"[WARN] _ensure_show_me_in_front_unchecked: control_type check failed: {e}")
            is_checkbox = False

        unchecked = False
        if is_checkbox and not cfg.dry_run:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: using _set_windows_checkbox_checked (is_checkbox=True)")
            unchecked = _set_windows_checkbox_checked(control, desired_checked=False)
        else:
            _checkbox_debug(
                f"_ensure_show_me_in_front_unchecked: using _invoke_button (is_checkbox={is_checkbox}, dry_run={cfg.dry_run})"
            )
            unchecked = _invoke_button(cfg, title, control, label, "Disable 'Show me in front'")

        _checkbox_debug(f"_ensure_show_me_in_front_unchecked: toggle unchecked={unchecked}")
        if not unchecked:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: toggle failed, but continuing (non-critical)")
            return {
                "ok": True,
                "reason": "Failed to uncheck 'Show me in front' option (continuing)",
                "window": title,
                "control": label,
                "warning": "uncheck_failed",
            }

        checked_after = _is_windows_checkbox_checked(control)
        _checkbox_debug(f"_ensure_show_me_in_front_unchecked: checked_after first attempt={checked_after}")
        
        if checked_after is True:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: still checked, attempting fallback")
            # Fallback: for some builds, checkbox toggles via keyboard space on focus.
            if not cfg.dry_run:
                if is_checkbox:
                    _checkbox_debug("_ensure_show_me_in_front_unchecked: fallback - calling _set_windows_checkbox_checked again")
                    _set_windows_checkbox_checked(control, desired_checked=False)
                else:
                    try:
                        _checkbox_debug("_ensure_show_me_in_front_unchecked: fallback - set_focus + Space key")
                        control.set_focus()
                        send_keys(" ")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"[WARN] _ensure_show_me_in_front_unchecked: fallback failed: {e}")
                        pass
                checked_after = _is_windows_checkbox_checked(control)
                _checkbox_debug(f"_ensure_show_me_in_front_unchecked: checked_after fallback={checked_after}")

        _checkbox_debug("_ensure_show_me_in_front_unchecked: success - option verified as unchecked")
        return {
            "ok": True,
            "window": title,
            "control": label,
            "already_unchecked": False,
            "verified_unchecked": checked_after is False,
        }

    if IS_LINUX:
        label_patterns = _compile_label_patterns(["Show me in front"])
        target = _find_clickable_target(label_patterns, title_regex=r"share|shared content|content")
        if not target:
            target = _find_clickable_target(label_patterns, title_regex=r".*")
        if not target:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: control not found (may not be present in this layout)")
            return {
                "ok": True,
                "reason": "'Show me in front' option not found (skipping)",
            }

        title, control, label = target
        unchecked = _invoke_button(cfg, title, control, label, "Disable 'Show me in front'")
        if not unchecked:
            _checkbox_debug("_ensure_show_me_in_front_unchecked: toggle failed, but continuing (non-critical)")
            return {
                "ok": True,
                "reason": "Failed to uncheck 'Show me in front' option (continuing)",
                "window": title,
                "control": label,
                "warning": "uncheck_failed",
            }

        return {
            "ok": True,
            "window": title,
            "control": label,
            "already_unchecked": False,
            "verified_unchecked": None,
        }

    return {
        "ok": True,
        "reason": "Unsupported platform (skipping 'Show me in front' check)",
    }


def _debug_share_controls() -> dict:
    controls = []
    all_texts = []  # Track ALL text values for inspection
    if not IS_WINDOWS:
        result = {"supported": False, "reason": "Debug control dump currently implemented for Windows"}
        print(f"[DEBUG] Share controls endpoint: {result}")
        return result

    print("[DEBUG] Dumping ALL Webex window controls (no filter)...")
    for window in _iter_candidate_windows(r".*"):
        if IS_WINDOWS and not _is_webex_window_windows(window):
            continue
        title = window.window_text() or ""

        print(f"[DEBUG] Window: '{title}'")
        # Try ALL control types, not just Button/ListItem/Text
        all_control_types = ["Button", "ListItem", "Text", "Pane", "Custom", "Image", "Edit", "ComboBox", "CheckBox", "RadioButton", "Static", "Group", "Hyperlink", "ProgressBar"]
        
        for control_type in all_control_types:
            try:
                descendants = window.descendants(control_type=control_type)
            except Exception:
                continue

            for control in descendants:
                text = (control.window_text() or "").strip()
                if not text:
                    continue
                
                # Log ALL text values
                all_texts.append(text)
                
                # Only include in returned data if it looks like it might be share-related
                if not re.search(r"viewing|share|screen|application|content", text, re.IGNORECASE):
                    # Still print everything to console for inspection
                    if len(all_texts) <= 50:  # Limit console spam
                        print(f"  [{control_type}] {text}")
                    continue

                rect = None
                try:
                    rect = control.rectangle()
                except Exception:
                    try:
                        rect = control.element_info.rectangle
                    except Exception:
                        rect = None

                control_info = {
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
                controls.append(control_info)
                print(f"  [MATCH] [{control_type}] {text}")

    result = {
        "supported": True,
        "count": len(controls),
        "all_text_values_found": len(all_texts),
        "sample_all_texts": all_texts[:20],  # Show first 20 for inspection
        "controls": controls[:200],
    }
    print(f"[DEBUG] Share controls endpoint found {len(controls)} matching controls, {len(all_texts)} total control texts")
    if "viewing" in " ".join(all_texts).lower():
        print(f"[DEBUG] SUCCESS: 'Viewing' text found in controls!")
    else:
        print(f"[DEBUG] WARNING: 'Viewing' text NOT found in any controls")
    return result


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
        title = _safe_control_text(window)
        if cfg.verbose:
            print(f"[DEBUG] Candidate window: {title}")

        button = _find_answer_button(window, label_patterns)
        if not button:
            continue

        label = _safe_control_text(button)
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


# Substrings that identify the leave-meeting confirmation dialog window title.
# Examples: "Do you want to leave the meeting?", "Leave meeting, Do you want to leave..."
_LEAVE_DIALOG_TITLE_MARKERS = (
    "do you want to leave",
    "leave meeting",
)


def _is_leave_dialog_title(title: str) -> bool:
    t = title.strip().lower()
    return any(marker in t for marker in _LEAVE_DIALOG_TITLE_MARKERS)


def _find_leave_meeting_target_windows(
    label_patterns: List[re.Pattern[str]],
    exclude_window_title: str = "",
):
    # Search all Webex top-level windows for a "Leave meeting" button,
    # but skip the meeting-room window (identified by exclude_window_title)
    # because it has a toolbar button with the same label that we do NOT want.
    # The confirmation dialog may be titled "Webex" (simple leave) or contain
    # the dialog text (host-reassignment leave) -- both are handled here.
    for window in _iter_candidate_windows(r".*"):
        if not _is_webex_window_windows(window):
            continue
        title = _safe_control_text(window)
        if exclude_window_title and title.strip().lower() == exclude_window_title.strip().lower():
            continue

        for control_type in ["Button", "ListItem", "Text", "Pane", "Custom"]:
            try:
                descendants = window.descendants(control_type=control_type)
            except Exception:
                continue
            for control in descendants:
                text = (control.window_text() or "").strip()
                if any(p.match(text) for p in label_patterns):
                    return title, control, text

    return None


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


def _start_screen_share(cfg: Config, immersive: bool = False) -> dict:
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

    show_me_in_front_result = None
    if immersive:
        show_me_in_front_result = _ensure_show_me_in_front_checked(cfg, dialog_title=dialog_title)
        if not show_me_in_front_result.get("ok"):
            return {
                "started": False,
                "reason": show_me_in_front_result.get("reason", "Failed to enable 'Show me in front'"),
                "selection": screen_label,
            }
    else:
        show_me_in_front_result = _ensure_show_me_in_front_unchecked(cfg, dialog_title=dialog_title)
        # For non-immersive mode, not finding or failing to uncheck "Show me in front" is non-critical,
        # so we log it but continue with the share operation.

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
    result = {
        "started": started,
        "window": confirm_title,
        "button": confirm_label,
        "selection": screen_label,
    }
    if show_me_in_front_result is not None:
        if immersive:
            result["show_me_in_front"] = {
                "mode": "immersive",
                "enabled": True,
                "already_checked": bool(show_me_in_front_result.get("already_checked", False)),
                "verified_checked": show_me_in_front_result.get("verified_checked", None),
                "warning": show_me_in_front_result.get("warning", ""),
                "window": show_me_in_front_result.get("window", ""),
                "control": show_me_in_front_result.get("control", "Show me in front"),
            }
        else:
            result["show_me_in_front"] = {
                "mode": "non-immersive",
                "unchecked": True,
                "already_unchecked": bool(show_me_in_front_result.get("already_unchecked", False)),
                "verified_unchecked": show_me_in_front_result.get("verified_unchecked", None),
                "warning": show_me_in_front_result.get("warning", ""),
                "window": show_me_in_front_result.get("window", ""),
                "control": show_me_in_front_result.get("control", "Show me in front"),
            }
    return result


def _set_open_dialog_file_name_windows(file_path: str, cfg: Config) -> dict:
    def _confirm_open_dialog_selection(window, title: str) -> bool:
        if cfg.dry_run:
            return True

        try:
            send_keys("{ENTER}")
        except Exception:
            return False

        # If Enter is ignored in some environments, explicitly click Open.
        time.sleep(0.2)
        open_patterns = _compile_label_patterns(["Open", "Choose", "Select"])
        try:
            buttons = window.descendants(control_type="Button")
        except Exception:
            buttons = []

        for button in buttons:
            label = _safe_control_text(button)
            if not any(p.match(label) for p in open_patterns):
                continue
            try:
                button.invoke()
                if cfg.verbose:
                    print(f"[INFO] Open dialog confirm fallback clicked in '{title}' via button '{label}'.")
                return True
            except Exception:
                try:
                    button.click_input()
                    if cfg.verbose:
                        print(f"[INFO] Open dialog confirm fallback clicked in '{title}' via click_input on '{label}'.")
                    return True
                except Exception:
                    continue

        return True

    def _window_looks_like_open_dialog(window, title: str) -> bool:
        title_low = title.lower()
        if re.search(r"open|choose|select", title_low):
            return True

        try:
            buttons = window.descendants(control_type="Button")
        except Exception:
            buttons = []
        open_patterns = _compile_label_patterns(["Open", "Choose", "Select"])
        for button in buttons:
            label = _safe_control_text(button)
            if any(p.match(label) for p in open_patterns):
                return True

        return False

    def _type_file_path_keyboard_first(window, title: str) -> bool:
        if cfg.dry_run:
            return True

        try:
            try:
                window.set_focus()
            except Exception:
                pass
            # Most common dialogs support Alt+N to focus "File name".
            send_keys("%n")
            time.sleep(0.1)
            send_keys("^a")
            time.sleep(0.1)
            send_keys(file_path, with_spaces=True)
            time.sleep(0.2)
            return _confirm_open_dialog_selection(window, title)
        except Exception as exc:
            if cfg.verbose:
                print(f"[WARN] keyboard-first file entry failed in '{title}': {exc}")
            return False

    deadline = time.time() + 12.0
    last_dialog_title = ""
    while time.time() < deadline:
        for window in _iter_candidate_windows(r".*"):
            title = _safe_control_text(window)
            if not _window_looks_like_open_dialog(window, title):
                continue
            last_dialog_title = title

            # First try resilient keyboard flow; some dialogs do not expose Edit controls via UIA.
            if _type_file_path_keyboard_first(window, title):
                return {
                    "ok": True,
                    "window": title,
                    "input": "keyboard_alt_n",
                }

            try:
                edits = window.descendants(control_type="Edit")
            except Exception:
                edits = []

            if not edits:
                continue

            edit = edits[0]
            if cfg.dry_run:
                return {
                    "ok": True,
                    "window": title,
                    "input": "edit.set_edit_text",
                    "dry_run": True,
                }

            try:
                try:
                    window.set_focus()
                except Exception:
                    pass
                try:
                    edit.set_focus()
                except Exception:
                    pass
                edit.set_edit_text(file_path)
                time.sleep(0.2)
                if not _confirm_open_dialog_selection(window, title):
                    return {
                        "ok": False,
                        "reason": "Failed to confirm selection in Open dialog",
                        "window": title,
                    }
                return {
                    "ok": True,
                    "window": title,
                    "input": "edit.set_edit_text",
                }
            except Exception as exc:
                if cfg.verbose:
                    print(f"[WARN] set_edit_text failed in open dialog '{title}': {exc}")

            try:
                window.set_focus()
                send_keys("^a")
                time.sleep(0.1)
                send_keys(file_path, with_spaces=True)
                time.sleep(0.2)
                if not _confirm_open_dialog_selection(window, title):
                    return {
                        "ok": False,
                        "reason": "Failed to confirm selection in Open dialog",
                        "window": title,
                    }
                return {
                    "ok": True,
                    "window": title,
                    "input": "keyboard_fallback",
                }
            except Exception as exc:
                if cfg.verbose:
                    print(f"[WARN] keyboard fallback failed in open dialog '{title}': {exc}")

        time.sleep(0.2)

    return {
        "ok": False,
        "reason": "Open file dialog or file name field not found",
        "window": last_dialog_title,
    }


def _start_file_share(cfg: Config, file_path: str = r"C:\WebexVDI-VC-Status.pdf") -> dict:
    if not IS_WINDOWS:
        return {
            "started": False,
            "reason": "File share route is only supported on Windows",
            "file": file_path,
        }

    focused_title = _focus_webex_window_windows(r"meeting|room|personal|call")
    if not focused_title:
        focused_title = _focus_webex_window_windows(exclude_exact_title="Webex")

    try:
        send_keys("^%o")
    except Exception as exc:
        return {
            "started": False,
            "reason": f"Failed to send Ctrl+Alt+O: {exc}",
            "shortcut": "Ctrl+Alt+O",
            "focused_window": focused_title or "",
            "file": file_path,
        }

    time.sleep(1.0)

    next_patterns = _compile_label_patterns(["Next"])
    next_target = None
    deadline = time.time() + 5.0
    while time.time() < deadline and next_target is None:
        if focused_title:
            next_target = _find_button_in_window_title(
                focused_title,
                next_patterns,
                webex_only=True,
                title_contains=True,
            )
        if not next_target:
            next_target = _find_button_target(next_patterns, title_regex=r"share|shared content|content")
        if not next_target:
            next_target = _find_button_target(next_patterns, title_regex=r".*")
        if next_target:
            break
        time.sleep(0.2)

    if not next_target:
        return {
            "started": False,
            "reason": "Next button not found in File tab",
            "shortcut": "Ctrl+Alt+O",
            "focused_window": focused_title or "",
            "file": file_path,
        }

    next_title, next_button, next_label = next_target
    if not _invoke_button(cfg, next_title, next_button, next_label, "Open file picker"):
        return {
            "started": False,
            "reason": "Failed to click Next button in File tab",
            "window": next_title,
            "button": next_label,
            "file": file_path,
        }

    time.sleep(0.8)

    set_file_result = _set_open_dialog_file_name_windows(file_path, cfg)
    if not set_file_result.get("ok"):
        return {
            "started": False,
            "reason": set_file_result.get("reason", "Failed to set file name in Open dialog"),
            "file": file_path,
        }

    verification = _wait_for_stop_sharing_button(timeout_seconds=8.0)
    if not verification.get("ok"):
        return {
            "started": False,
            "reason": verification.get("reason", "'Stop sharing' button not found after file share attempt"),
            "shortcut": "Ctrl+Alt+O",
            "next_button": next_label,
            "file": file_path,
            "open_dialog_window": set_file_result.get("window", ""),
            "input_method": set_file_result.get("input", ""),
            "share_verified": False,
        }

    return {
        "started": True,
        "shortcut": "Ctrl+Alt+O",
        "next_button": next_label,
        "file": file_path,
        "open_dialog_window": set_file_result.get("window", ""),
        "input_method": set_file_result.get("input", ""),
        "share_verified": True,
        "verification": {
            "window": verification.get("window", ""),
            "button": verification.get("button", ""),
            "method": verification.get("method", ""),
        },
    }


def _find_stop_sharing_target():
    stop_sharing_patterns = _compile_label_patterns([
        "Stop sharing",
        "Stop share",
    ])

    target = _find_button_target(stop_sharing_patterns, title_regex=r"meeting|room|personal|call")
    if not target:
        target = _find_clickable_target(stop_sharing_patterns, title_regex=r"meeting|room|personal|call")
    if not target:
        target = _find_button_target(stop_sharing_patterns, title_regex=r".*")
    if not target:
        target = _find_clickable_target(stop_sharing_patterns, title_regex=r".*")
    return target


def _wait_for_stop_sharing_button(timeout_seconds: float = 8.0) -> dict:
    deadline = time.time() + max(0.5, timeout_seconds)
    while time.time() < deadline:
        target = _find_stop_sharing_target()
        if target:
            title, _, label = target
            return {
                "ok": True,
                "window": title,
                "button": label,
                "method": "ui_control_match",
            }

        time.sleep(0.2)

    return {
        "ok": False,
        "reason": "'Stop sharing' button not found",
    }


def _stop_file_share(cfg: Config) -> dict:
    if not IS_WINDOWS and not IS_LINUX:
        return {
            "stopped": False,
            "reason": "Unsupported platform",
        }

    target = _find_stop_sharing_target()
    if not target:
        return {
            "stopped": False,
            "reason": "'Stop sharing' button not found",
        }

    title, button, label = target
    stopped = _invoke_button(cfg, title, button, label, "Stop file share")
    if not stopped:
        return {
            "stopped": False,
            "reason": "Failed to click 'Stop sharing' button",
            "window": title,
            "button": label,
        }

    return {
        "stopped": True,
        "window": title,
        "button": label,
        "method": "ui_button_click",
    }


def _is_screen_share_active() -> bool:
    """Check if current window shows active screen sharing.
    
    Indicators of active screen sharing:
    - "Shared content view" control text is present
    - "Shared file view" control text is present
    - Fallback: "Viewing X's screen/application/file" text is present

    In your current Webex build, "Shared content view" is the reliable UIA-exposed
    marker for receiving a share.
    """
    if IS_WINDOWS:
        for window in _iter_candidate_windows(r".*"):
            if not _is_webex_window_windows(window):
                continue

            # Search all controls in the window for share-receive markers.
            for control_type in ["Text", "Pane", "Custom", "Button", "ListItem"]:
                try:
                    descendants = window.descendants(control_type=control_type)
                except Exception:
                    continue
                
                for control in descendants:
                    try:
                        text = _safe_control_text(control)
                        text_lower = text.lower()
                        if "shared content view" in text_lower:
                            return True
                        if "shared file view" in text_lower:
                            return True
                        if "viewing" in text_lower and (
                            "screen" in text_lower
                            or "application" in text_lower
                            or "file" in text_lower
                        ):
                            return True
                    except Exception:
                        continue
    elif IS_LINUX:
        try:
            import pyatspi
        except Exception:
            return False
        
        try:
            desktop = pyatspi.Registry.getDesktop(0)
        except Exception:
            return False
        
        for app in desktop:
            app_name = (getattr(app, "name", "") or "").strip()
            if not re.search(r"webex", app_name, re.IGNORECASE):
                continue
            
            # Search all nodes for share-receive markers.
            for node in _iter_accessible_nodes(app):
                try:
                    node_name = (getattr(node, "name", "") or "").strip()
                    node_name_lower = node_name.lower()
                    if "shared content view" in node_name_lower:
                        return True
                    if "shared file view" in node_name_lower:
                        return True
                    if "viewing" in node_name_lower and (
                        "screen" in node_name_lower
                        or "application" in node_name_lower
                        or "file" in node_name_lower
                    ):
                        return True
                except Exception:
                    continue
    
    return False


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


def _dump_windows_and_controls() -> dict:
    """Debug: enumerate all Webex windows and their controls."""
    window_info = []
    for window in _iter_candidate_windows(r".*"):
        if not _is_webex_window_windows(window):
            continue
        title = _safe_control_text(window)
        controls = []
        for control_type in ["Button", "ListItem", "Text", "Pane", "Custom"]:
            try:
                descendants = window.descendants(control_type=control_type)
                for control in descendants:
                    text = (control.window_text() or "").strip()
                    if text:  # Only include controls with visible text
                        controls.append({"type": control_type, "text": text})
            except Exception:
                pass
        window_info.append({"title": title, "controls": controls})
    return window_info


def _leave_meeting(cfg: Config) -> dict:
    if IS_WINDOWS:
        if cfg.dry_run:
            return {
                "left": True,
                "dry_run": True,
                "shortcut": "Ctrl+L",
                "button": "Leave meeting",
            }

        # Prefer the actual meeting room window over background Webex processes.
        # Windows exactly titled "Webex" are typically the main Webex hub, not the
        # meeting room window where Ctrl+L opens the leave-meeting dialog.
        focused_title = _focus_webex_window_windows(r"meeting|room|personal|call")
        if not focused_title:
            # Broad fallback, but still skip exact "Webex" title (main hub/tray).
            focused_title = _focus_webex_window_windows(exclude_exact_title="Webex")
        if cfg.verbose and focused_title:
            print(f"[DEBUG] Focused Webex window before Ctrl+L: {focused_title}")
        elif cfg.verbose:
            print("[DEBUG] No Webex window focused before Ctrl+L; sending shortcut anyway.")

        try:
            send_keys("^l")
        except Exception as exc:
            return {
                "left": False,
                "shortcut": "Ctrl+L",
                "reason": f"Failed to send Ctrl+L: {exc}",
            }

        # Brief delay to allow the confirmation dialog to appear before polling.
        time.sleep(0.5)

        leave_patterns = _compile_label_patterns(["Leave meeting"])

        target = None
        deadline = time.time() + 5.0
        while time.time() < deadline and target is None:
            target = _find_leave_meeting_target_windows(leave_patterns, exclude_window_title=focused_title or "")
            if target:
                break
            time.sleep(0.2)

        if not target:
            # Fallback: look for the confirmation dialog by title markers and
            # send Enter (works for both "Webex"-titled and long-titled dialogs).
            dialog_target = None
            for w in _iter_candidate_windows(r".*"):
                t = _safe_control_text(w)
                t_low = t.strip().lower()
                if not _is_webex_window_windows(w):
                    continue
                # Match longer dialog title (contains explicit dialog text)
                if _is_leave_dialog_title(t_low):
                    dialog_target = (t, w)
                    break
                # Match simple dialog: "Webex" window that is NOT the focused meeting room.
                # Many Webex dialogs have no UIA-exposed controls, so we can't rely on
                # finding a button. Instead, after Ctrl+L and waiting, a "Webex" window
                # different from the meeting room is almost certainly the leave dialog.
                if t_low == "webex" and (not focused_title or t != focused_title):
                    dialog_target = (t, w)
                    break
            if dialog_target and not cfg.dry_run:
                dialog_title, _ = dialog_target
                try:
                    # Try Shift+Tab to move focus backward (Cancel is usually focused by default,
                    # so Shift+Tab should move focus back to "Leave meeting" button)
                    send_keys("+{TAB}")
                    time.sleep(0.1)
                    send_keys("{ENTER}")
                    return {
                        "left": True,
                        "shortcut": "Ctrl+L",
                        "focused_window": focused_title or "",
                        "window": dialog_title,
                        "button": "Shift+Tab+ENTER",
                        "fallback": "focus_previous_button",
                    }
                except Exception as exc:
                    return {
                        "left": False,
                        "shortcut": "Ctrl+L",
                        "focused_window": focused_title or "",
                        "window": dialog_title,
                        "reason": f"'Leave meeting' button not found and keyboard fallback (Shift+Tab+ENTER) failed: {exc}",
                    }

        if not target:
            # Include diagnostic info to help troubleshoot
            diagnostics = _dump_windows_and_controls()
            return {
                "left": False,
                "shortcut": "Ctrl+L",
                "focused_window": focused_title or "",
                "reason": "'Leave meeting' button not found in Webex window",
                "diagnostics": {
                    "webex_windows": diagnostics,
                },
            }

        title, button, label = target
        left = _invoke_button(cfg, title, button, label, "Leave meeting")
        return {
            "left": left,
            "shortcut": "Ctrl+L",
            "focused_window": focused_title or "",
            "window": title,
            "button": label,
        }

    if IS_LINUX:
        if cfg.dry_run:
            return {
                "left": True,
                "dry_run": True,
                "shortcut": "Ctrl+L",
                "button": "Leave meeting",
            }

        try:
            result = subprocess.run(
                ["xdotool", "key", "ctrl+l"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return {
                    "left": False,
                    "shortcut": "Ctrl+L",
                    "reason": (result.stderr or result.stdout or "xdotool failed").strip(),
                }
        except Exception as exc:
            return {
                "left": False,
                "shortcut": "Ctrl+L",
                "reason": f"Failed to send Ctrl+L: {exc}",
            }

        leave_patterns = _compile_label_patterns(["Leave meeting"])
        target = _find_button_target(leave_patterns, title_regex=r"webex")
        if not target:
            return {
                "left": False,
                "shortcut": "Ctrl+L",
                "reason": "'Leave meeting' button not found in Webex window",
            }

        title, button, label = target
        left = _invoke_button(cfg, title, button, label, "Leave meeting")
        return {
            "left": left,
            "shortcut": "Ctrl+L",
            "window": title,
            "button": label,
        }

    return {
        "left": False,
        "shortcut": "Ctrl+L",
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


def _should_emit_join_flow_debug(debug_key: str, min_interval_seconds: float = 3.0) -> bool:
    now = time.time()
    with STATE_LOCK:
        last_at = RUNTIME_STATE.last_join_flow_debug_at
        last_key = RUNTIME_STATE.last_join_flow_debug_key
        if last_at is None or debug_key != last_key or (now - last_at) >= min_interval_seconds:
            RUNTIME_STATE.last_join_flow_debug_at = now
            RUNTIME_STATE.last_join_flow_debug_key = debug_key
            return True
    return False


def _find_join_toast_target_windows(cfg: Config):
    join_patterns = _compile_label_patterns([cfg.join_toast_button_label])
    # Toast can be hosted by non-Webex shell windows, so don't require Webex process filtering.
    return _find_button_in_window_title(
        cfg.join_toast_title,
        join_patterns,
        webex_only=False,
        title_contains=True,
    )


def _find_get_ready_join_target(cfg: Config):
    join_meeting_patterns = _compile_label_patterns([cfg.prejoin_button_label])

    if IS_WINDOWS:
        target = _find_button_in_window_title(cfg.prejoin_window_title, join_meeting_patterns)
        if target:
            return target

    return _find_button_target(join_meeting_patterns, title_regex=re.escape(cfg.prejoin_window_title))


def try_join_meeting_toast_once(cfg: Config) -> bool:
    handled = False
    debug_lines = []

    # Step 1: Click Join in the compact toast window titled "Webex meeting".
    if IS_WINDOWS:
        toast_target = _find_join_toast_target_windows(cfg)
        if toast_target:
            title, button, label = toast_target
            if cfg.verbose:
                debug_lines.append(f"Join toast found in '{title}' with button '{label}'.")
            if _invoke_button(cfg, title, button, label, "Join toast"):
                handled = True
                # Allow the full pre-join window to appear before step 2.
                time.sleep(0.6)
        elif cfg.verbose:
            debug_lines.append("Join toast not found.")

    # Step 2: Click Join meeting in "Get ready to join" window.
    join_target = _find_get_ready_join_target(cfg)
    if join_target:
        title, button, label = join_target
        if cfg.verbose:
            debug_lines.append(f"Pre-join window found in '{title}' with button '{label}'.")
        if _invoke_button(cfg, title, button, label, "Join meeting"):
            handled = True
    elif cfg.verbose:
        debug_lines.append("Pre-join 'Join meeting' button not found.")

    if cfg.verbose:
        debug_key = "join-flow-handled" if handled else "join-flow-idle"
        if _should_emit_join_flow_debug(debug_key, min_interval_seconds=cfg.join_debug_interval):
            print("[DEBUG] Checking join-meeting toast flow.")
            for line in debug_lines:
                print(f"[DEBUG] {line}")

    return handled


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
    parser.add_argument(
        "--join-toast-title",
        default="Webex meeting",
        help="Window title for the compact join meeting toast.",
    )
    parser.add_argument(
        "--join-toast-button-label",
        default="Join",
        help="Button label to click on the join meeting toast.",
    )
    parser.add_argument(
        "--prejoin-window-title",
        default="Get ready to join",
        help="Window title for the pre-join window.",
    )
    parser.add_argument(
        "--prejoin-button-label",
        default="Join meeting",
        help="Button label to click in the pre-join window.",
    )
    parser.add_argument(
        "--join-debug-interval",
        type=float,
        default=3.0,
        help="Minimum seconds between repeated join-flow debug logs in verbose mode.",
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
    if args.join_debug_interval < 0:
        parser.error("--join-debug-interval must be >= 0")

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
        join_toast_title=args.join_toast_title.strip() or "Webex meeting",
        join_toast_button_label=args.join_toast_button_label.strip() or "Join",
        prejoin_window_title=args.prejoin_window_title.strip() or "Get ready to join",
        prejoin_button_label=args.prejoin_button_label.strip() or "Join meeting",
        join_debug_interval=args.join_debug_interval,
    )


def main() -> int:
    global CHECKBOX_DEBUG_VERBOSE
    cfg = parse_args()
    CHECKBOX_DEBUG_VERBOSE = bool(cfg.verbose)
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
    atexit.register(_stop_reaction_sender)
    _init_calling_info_and_upload(cfg)
    _ensure_webex_running(cfg)
    next_webex_check_at = time.time() + cfg.webex_monitor_interval

    try:
        while True:
            now = time.time()
            if now >= next_webex_check_at:
                _ensure_webex_running(cfg)
                next_webex_check_at = now + cfg.webex_monitor_interval

            try_join_meeting_toast_once(cfg)
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

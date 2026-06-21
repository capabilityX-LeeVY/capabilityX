"""
WME thread anomaly monitoring helpers (pure Python).

Records xctrace System Trace via the apple-thread-test-01 toolkit, runs the
7-pattern anomaly detection pipeline, then archives the human-readable report
and either deletes (PASS) or keeps (FAIL) the raw run directory.

Exposes two function.json-compatible entry points:
  - start_wme_thread_monitor(duration, label, ...) -> session_id (str)
  - finalize_wme_thread_monitor(session_id, fail_on, wait_timeout) -> True
        or returns dict{"status": "failed", ...} when threshold exceeded.

Failure semantics follow the framework's FunctionActionStrategy contract:
returning a dict with status in {"error", "failed", "failure"} causes the
step to be marked as failed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from common.utils.logger import LOGGER_ERROR, LOGGER_INFO, LOGGER_WARNING

# ── Constants ────────────────────────────────────────────────────────────────

# Toolkit dir is resolved at call time from (in order):
#   1) explicit `tool_dir` parameter from YAML
#   2) WME_THREAD_TOOL_DIR environment variable
#   3) /Users/webexdev/wme-thread-tools/apple-thread-test-01 (CI convention; pulled fresh from git per run)
DEFAULT_TOOL_DIR_CANDIDATES = [
    "/Users/webexdev/wme-thread-tools/apple-thread-test-01",
]
DEFAULT_TARGET_PROCESS = "Webex"
DEFAULT_DURATION = "30s"
DEFAULT_FAIL_ON = ["CRITICAL", "HIGH"]
ALL_SEVERITIES = ["CRITICAL", "HIGH", "MODERATE", "WARNING"]

_SESSION_ROOT = Path(tempfile.gettempdir()) / "wme_thread_sessions"
_ARCHIVE_DIR = Path.home() / "Desktop" / "wrs_artifacts" / "wme_thread_reports"
_SEVERITY_RE = re.compile(r"\[(CRITICAL|HIGH|MODERATE|WARNING)\]")


# ── Internal helpers ─────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    _SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _session_file(session_id: str) -> Path:
    return _SESSION_ROOT / f"{session_id}.json"


def _save_session(session_id: str, data: Dict[str, Any]) -> None:
    _session_file(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_session(session_id: str) -> Optional[Dict[str, Any]]:
    path = _session_file(session_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER_WARNING(f"[wme_thread_monitor] Failed to read session file {path}: {exc}")
        return None


def _resolve_pid(target_process: str) -> Optional[int]:
    try:
        out = subprocess.check_output(["pgrep", "-x", target_process], text=True).strip()
    except subprocess.CalledProcessError:
        return None
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None


def _count_severities(report_path: Path) -> Dict[str, int]:
    counts = {sev: 0 for sev in ALL_SEVERITIES}
    try:
        text = report_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        LOGGER_WARNING(f"[wme_thread_monitor] Cannot read report {report_path}: {exc}")
        return counts
    for match in _SEVERITY_RE.finditer(text):
        counts[match.group(1)] += 1
    return counts


def _find_run_dir(tool_dir: Path, label: str, started_at_epoch: float) -> Optional[Path]:
    """Locate the run dir for this session.

    profile.sh creates dirs named profile_<YYYYMMDD_HHMMSS>_<proc>__<pid>_<label>.
    We match by label suffix and dir mtime >= started_at_epoch (with 5s slack).
    """
    runs_dir = tool_dir / "runs"
    if not runs_dir.is_dir():
        return None
    suffix = f"_{label}"
    cutoff = started_at_epoch - 5
    candidates = [
        p for p in runs_dir.iterdir()
        if p.is_dir()
        and p.name.startswith("profile_")
        and p.name.endswith(suffix)
        and p.stat().st_mtime >= cutoff
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _reap_zombie(pid: int) -> None:
    """Non-blocking reap of a child PID we spawned. Safe if pid is not our child."""
    try:
        os.waitpid(pid, os.WNOHANG)
    except (ChildProcessError, OSError):
        pass


def _resolve_tool_dir(explicit: Optional[str]) -> Optional[Path]:
    """Find the toolkit dir using explicit param > env var > known fallbacks."""
    candidates: List[str] = []
    if explicit:
        candidates.append(explicit)
    env_val = os.environ.get("WME_THREAD_TOOL_DIR")
    if env_val:
        candidates.append(env_val)
    candidates.extend(DEFAULT_TOOL_DIR_CANDIDATES)
    for c in candidates:
        p = Path(c).expanduser().resolve()
        if (p / "profile.sh").is_file():
            return p
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def start_wme_thread_monitor(
    duration: str = DEFAULT_DURATION,
    label: str = "wrs_test",
    tool_dir: Optional[str] = None,
    target_process: str = DEFAULT_TARGET_PROCESS,
) -> Union[str, Dict[str, Any]]:
    """Start xctrace + analysis pipeline as a background process.

    Returns the session_id string on success (consumed via save_to in YAML),
    or a failure dict if the target process is missing or the toolkit is not
    found.
    """
    fn = "start_wme_thread_monitor"
    LOGGER_INFO(
        f"[{fn}] duration={duration} label={label} target={target_process}",
        "GREEN",
    )

    tool_path = _resolve_tool_dir(tool_dir)
    if tool_path is None:
        msg = (
            "WME thread toolkit not found. Set WME_THREAD_TOOL_DIR env var or pass "
            "tool_dir parameter. Searched: "
            + ", ".join([tool_dir or "<no explicit>", os.environ.get("WME_THREAD_TOOL_DIR", "<no env>")]
                        + DEFAULT_TOOL_DIR_CANDIDATES)
        )
        LOGGER_ERROR(f"[{fn}] {msg}")
        raise FileNotFoundError(msg)
    profile_sh = tool_path / "profile.sh"

    pid = _resolve_pid(target_process)
    if pid is None:
        msg = f"target process '{target_process}' is not running"
        LOGGER_ERROR(f"[{fn}] {msg}")
        raise RuntimeError(msg)

    _ensure_dirs()
    session_id = f"wme_thread_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    log_path = _SESSION_ROOT / f"{session_id}.log"

    cmd = [
        str(profile_sh),
        "record",
        "--pid", str(pid),
        "--duration", str(duration),
        "--label", str(label),
    ]
    LOGGER_INFO(f"[{fn}] launching: {' '.join(cmd)}", "CYAN")

    # Fully detach the recorder from the test framework so that:
    #   1. It survives any process-tree cleanup the framework performs
    #      between steps (we previously observed profile.sh dying right
    #      after `xctrace record` returned, before convert/analyze ran).
    #   2. It does not inherit the framework's stdin/stdout/stderr fds.
    #
    # Strategy: spawn via `nohup bash -c` with all I/O redirected at the
    # shell level to the session log. Python's Popen handle is used only
    # to capture the PID; all fds in Python are DEVNULL so closing them
    # cannot affect the child. start_new_session=True puts it in its own
    # process group + session (setsid), insulating it from SIGHUP.
    import shlex  # local import keeps top-level imports unchanged
    quoted_cmd = " ".join(shlex.quote(c) for c in cmd)
    quoted_log = shlex.quote(str(log_path))
    quoted_cwd = shlex.quote(str(tool_path))
    detached_shell_cmd = (
        f"cd {quoted_cwd} && exec nohup {quoted_cmd} >{quoted_log} 2>&1 </dev/null"
    )

    try:
        proc = subprocess.Popen(
            ["bash", "-c", detached_shell_cmd],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as exc:
        LOGGER_ERROR(f"[{fn}] failed to spawn recorder: {exc}")
        return {"status": "failed", "message": f"failed to spawn recorder: {exc}"}

    _save_session(session_id, {
        "session_id": session_id,
        "pid": proc.pid,
        "target_pid": pid,
        "tool_dir": str(tool_path),
        "duration": duration,
        "label": label,
        "log": str(log_path),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "started_at_epoch": time.time(),
    })

    LOGGER_INFO(f"[{fn}] session_id={session_id} recorder_pid={proc.pid}", "GREEN")
    return session_id


def finalize_wme_thread_monitor(
    session_id: str,
    fail_on: Optional[List[str]] = None,
    wait_timeout: int = 60,
) -> Union[bool, Dict[str, Any]]:
    """Wait for the recorder to finish, parse report, archive + cleanup.

    Returns True when no anomaly at or above the configured severities is
    found. Raises an exception (so the Mac GT framework halts the test case)
    when the threshold is exceeded or the pipeline fails.
    """
    fn = "finalize_wme_thread_monitor"
    fail_on = [s.upper() for s in (fail_on or DEFAULT_FAIL_ON)]
    LOGGER_INFO(
        f"[{fn}] session_id={session_id} fail_on={fail_on} wait_timeout={wait_timeout}s",
        "GREEN",
    )

    session = _load_session(session_id)
    if session is None:
        msg = f"session not found: {session_id!r}"
        LOGGER_ERROR(f"[{fn}] {msg}")
        raise RuntimeError(msg)

    recorder_pid = int(session["pid"])
    log_path = Path(session["log"])
    tool_dir = Path(session["tool_dir"])
    label = session.get("label", "")
    started_at_epoch = float(session.get("started_at_epoch", time.time()))

    # Poll for final_report.txt to appear in the matching run dir.
    # This is the canonical "analysis done" signal; PID liveness is unreliable
    # because Popen children become zombies until reaped.
    deadline = time.time() + max(1, int(wait_timeout))
    run_dir: Optional[Path] = None
    report_txt: Optional[Path] = None
    while time.time() < deadline:
        _reap_zombie(recorder_pid)
        run_dir = _find_run_dir(tool_dir, label, started_at_epoch)
        if run_dir is not None:
            candidate = run_dir / "final_report.txt"
            if candidate.is_file():
                report_txt = candidate
                break
        time.sleep(1)

    if report_txt is None:
        LOGGER_WARNING(
            f"[{fn}] final_report.txt not found within {wait_timeout}s; "
            f"killing recorder pid={recorder_pid}"
        )
        try:
            os.killpg(os.getpgid(recorder_pid), signal.SIGTERM)
            time.sleep(2)
            os.killpg(os.getpgid(recorder_pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
        _reap_zombie(recorder_pid)
        raise TimeoutError(
            f"final_report.txt did not appear within {wait_timeout}s; see log {log_path}"
        )

    report_json = run_dir / "final_report.json"

    counts = _count_severities(report_txt)
    LOGGER_INFO(
        f"[{fn}] anomaly counts: " + " ".join(f"{k}={v}" for k, v in counts.items()),
        "CYAN",
    )

    # Always archive the small text/json reports
    _ensure_dirs()
    archive_txt = _ARCHIVE_DIR / f"{run_dir.name}_final_report.txt"
    try:
        shutil.copyfile(report_txt, archive_txt)
        if report_json.is_file():
            shutil.copyfile(report_json, _ARCHIVE_DIR / f"{run_dir.name}_final_report.json")
    except OSError as exc:
        LOGGER_WARNING(f"[{fn}] failed to archive report: {exc}")

    triggered = [sev for sev in fail_on if counts.get(sev, 0) > 0]

    if not triggered:
        # PASS: delete bulky run dir to save disk
        LOGGER_INFO(
            f"[{fn}] PASS: no {fail_on} anomalies; deleting run dir {run_dir}",
            "GREEN",
        )
        try:
            shutil.rmtree(run_dir)
        except OSError as exc:
            LOGGER_WARNING(f"[{fn}] failed to delete {run_dir}: {exc}")
        # cleanup session file
        try:
            _session_file(session_id).unlink(missing_ok=True)
        except OSError:
            pass
        return True

    # FAIL: keep run dir for offline debug, then raise so the framework
    # halts the test case. Mac GT path does not inspect dict status, so we
    # must signal failure via exception.
    LOGGER_ERROR(
        f"[{fn}] FAIL: triggered={triggered} counts={counts}; run dir kept: {run_dir}"
    )
    raise AssertionError(
        f"WME thread anomalies detected ({', '.join(f'{s}={counts[s]}' for s in triggered)}); "
        f"see {archive_txt} and {run_dir}"
    )

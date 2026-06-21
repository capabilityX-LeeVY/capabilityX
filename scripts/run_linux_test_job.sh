#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-linux}"
REBUILD=0
MODE="run"

usage() {
    cat <<'EOF'
Usage:
  scripts/run_linux_test_job.sh [--setup-only] [--rebuild] [run_test_case_job args...]

Examples:
  scripts/run_linux_test_job.sh --setup-only
  scripts/run_linux_test_job.sh --test_suite "video_vbg"
  scripts/run_linux_test_job.sh --rebuild --test_case "vbg_static"

Environment overrides:
  PYTHON_BIN   Path to the Linux system Python 3.12 interpreter.
  VENV_DIR     Path to the Linux-only virtual environment.
EOF
}

while (($#)); do
    case "$1" in
        --setup-only)
            MODE="setup"
            shift
            ;;
        --rebuild)
            REBUILD=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

pick_python() {
    if [[ -n "${PYTHON_BIN:-}" ]]; then
        printf '%s\n' "$PYTHON_BIN"
        return
    fi

    if [[ -x /usr/bin/python3.12 ]]; then
        printf '%s\n' "/usr/bin/python3.12"
        return
    fi

    if command -v python3 >/dev/null 2>&1 && python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)
PY
    then
        command -v python3
        return
    fi

    echo "Python 3.12 was not found. Set PYTHON_BIN=/path/to/python3.12." >&2
    exit 1
}

PYTHON_BIN="$(pick_python)"

"$PYTHON_BIN" - <<'PY'
import importlib.util
import sys

if sys.version_info[:2] != (3, 12):
    raise SystemExit(
        f"Expected Python 3.12 for Linux override, got {sys.version.split()[0]} from {sys.executable}"
    )

missing = [name for name in ("gi", "pyatspi") if importlib.util.find_spec(name) is None]
if missing:
    joined = ", ".join(missing)
    raise SystemExit(
        "Missing required Linux system modules: "
        f"{joined}. Install python3-gi and python3-pyatspi first."
    )
PY

bootstrap_venv() {
    local venv_args
    local requirements_file
    venv_args=(--system-site-packages)
    requirements_file="$(mktemp)"
    trap 'rm -f "$requirements_file"' RETURN

    "$PYTHON_BIN" - <<'PY' > "$requirements_file"
import pathlib
import tomllib

deps = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["dependencies"]
filtered = []
for dep in deps:
    if ";" in dep:
        requirement, marker = dep.split(";", 1)
        if "win32" in marker:
            continue
        dep = requirement.strip()
    filtered.append(dep)

# Present in requirements.txt and imported in the repo, but not yet declared in pyproject.toml.
filtered.append("schedule>=1.2.0")
filtered.append("dogtail==2.0.1")

seen = set()
for dep in filtered:
    if dep not in seen:
        seen.add(dep)
        print(dep)
PY

    if [[ "$REBUILD" -eq 1 ]]; then
        venv_args+=(--clear)
    fi

    "$PYTHON_BIN" -m venv "${venv_args[@]}" "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
    "$VENV_DIR/bin/python" -m pip install -r "$requirements_file"
}

if [[ ! -x "$VENV_DIR/bin/python" || "$REBUILD" -eq 1 ]]; then
    bootstrap_venv
fi

if [[ "$MODE" == "setup" ]]; then
    echo "Linux override environment is ready at $VENV_DIR"
    echo "Run with: scripts/run_linux_test_job.sh --test_suite \"video_vbg\""
    exit 0
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV_DIR/bin/python" src/run_test_case_job.py --platform linux "$@"

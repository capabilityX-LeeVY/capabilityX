from __future__ import annotations

from pathlib import Path

DEFAULT_TC_IP = "10.72.208.41:8080"
TC_INFO_PATH = Path(r"C:\dev\auto_vdi\tc_info.txt")


def vdi_read_tc_ip(path: Path = TC_INFO_PATH, default_value: str = DEFAULT_TC_IP) -> str:
    if not path.exists():
        return default_value

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("tc_ip"):
            _, _, value = stripped.partition(":")
            value = value.strip()
            return value or default_value

    return default_value

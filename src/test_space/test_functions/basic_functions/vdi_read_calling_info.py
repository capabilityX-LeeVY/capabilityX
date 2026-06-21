from __future__ import annotations

from pathlib import Path

DEFAULT_PEER_IP = "10.140.100.108:5000"
DEFAULT_ACCOUNT = "bwc.sha+110@gmail.com"
DEFAULT_PHONE_NUMBER = "+1234567890"
CALLING_INFO_PATH = Path(r"C:\dev\auto_vdi\calling_info.txt")


def vdi_read_peer_ip(path: Path = CALLING_INFO_PATH, default_value: str = DEFAULT_PEER_IP) -> str:
    if not path.exists():
        return default_value

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("peer_ip"):
            _, _, value = stripped.partition(":")
            value = value.strip()
            return value or default_value

    return default_value


def vdi_read_account(path: Path = CALLING_INFO_PATH, default_value: str = DEFAULT_ACCOUNT) -> str:
    if not path.exists():
        return default_value

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("peer_account"):
            _, _, value = stripped.partition(":")
            value = value.strip()
            return value or default_value

    return default_value


def vdi_read_phone_number(path: Path = CALLING_INFO_PATH, default_value: str = DEFAULT_PHONE_NUMBER) -> str:
    if not path.exists():
        return default_value

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("phone_number"):
            _, _, value = stripped.partition(":")
            value = value.strip()
            return value or default_value

    return default_value

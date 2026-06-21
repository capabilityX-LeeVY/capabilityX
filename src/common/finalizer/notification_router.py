"""
Resolves which Webex room IDs to send test result notifications to, based on:
- settings.botRoomId (manual override, highest priority)
- Default room for the test suite / platform
- message_room field in the case/suite/batch YAML
"""

import yaml
from pathlib import Path
from config.paths import TEST_CASES_PATH, TEST_SUITE_PATH, TEST_BATCHES_PATH
from config.config import DEFAULT_WINDOWS_ROOM, DEFAULT_MAC_ROOM, PROMOTE_BLUE_ROOM


def get_notification_room_ids(settings_room_id=None, mode=None,
                               test_case=None, test_suite=None, test_batch=None,
                               default_room=None):
    """
    Return a deduplicated list of Webex room IDs to notify.
    """
    if settings_room_id:
        return _normalize(settings_room_id)

    room_ids = []
    if default_room:
        room_ids.append(default_room)
    room_ids.extend(_get_mode_message_room_ids(mode, test_case, test_suite, test_batch))
    return list(dict.fromkeys([r for r in room_ids if r]))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(message_room):
    if message_room is None:
        return []
    if isinstance(message_room, str):
        message_room = [message_room]
    if not isinstance(message_room, list):
        return []
    return [r.strip() for r in message_room if isinstance(r, str) and r.strip()]


def _read_message_room_from_yaml(yaml_path, root_key):
    if not yaml_path or not yaml_path.exists():
        return []
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return _normalize(data.get(root_key, {}).get('message_room'))
    except Exception:
        return []


def _resolve_case_yaml_path(case_name):
    if not case_name:
        return None
    rel = Path(str(case_name).strip())
    if rel.suffix == '.yaml':
        rel = rel.with_suffix('')
    yaml_file = rel.with_suffix('.yaml')
    path = TEST_CASES_PATH / yaml_file
    if path.exists():
        return path
    matches = list(TEST_CASES_PATH.rglob(yaml_file.name))
    return matches[0] if matches else None


def _get_mode_message_room_ids(mode, test_case, test_suite, test_batch):
    mode = (mode or '').lower()
    if mode == 'case':
        return _read_message_room_from_yaml(_resolve_case_yaml_path(test_case), 'test_case')
    if mode == 'suite' and test_suite:
        return _read_message_room_from_yaml(TEST_SUITE_PATH / f"{test_suite}.yaml", 'test_suite')
    if mode == 'batch' and test_batch:
        return _read_message_room_from_yaml(TEST_BATCHES_PATH / f"{test_batch}.yaml", 'test_case_batch')
    return []

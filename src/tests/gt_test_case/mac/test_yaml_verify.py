import os
import sys
import yaml
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from pathlib import Path
from core.structsDef import TestCase, TestSuite, TestCaseBatch
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from config.paths import TEST_CASES_PATH, TEST_SUITE_PATH, TEST_BATCHES_PATH


def _resolve_case_path(rel_path: str) -> str:
    """Resolve a relative test case path to an absolute path."""
    p = rel_path if rel_path.endswith(".yaml") else rel_path + ".yaml"
    if os.path.exists(p):
        return p
    full = str(TEST_CASES_PATH / p)
    return full


def _verify_test_case(file_path: str) -> tuple[bool, str]:
    """Verify a single TestCase file. Returns (ok, error_message)."""
    try:
        case = TestCase()
        case.from_yaml_file(file_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def _get_sub_cases(top_file: str) -> tuple[str, list[str]]:
    with open(top_file, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if "test_case_batch" in raw:
        cases = raw["test_case_batch"].get("test_cases", [])
        return "TestCaseBatch", [_resolve_case_path(c) for c in cases]
    elif "test_suite" in raw:
        cases = raw["test_suite"].get("test_cases", [])
        return "TestSuite", [_resolve_case_path(c) for c in cases]
    elif "test_case" in raw:
        return "TestCase", [top_file]
    else:
        LOGGER_ERROR(f"Unknown YAML type in: {top_file}")
        return "", []


def _log_results(results: list[dict]):
    workspace_root = Path(__file__).parents[4]
    LOGGER_INFO("========== Verify Summary ==========")
    for r in results:
        rel = os.path.relpath(r["file"], workspace_root)
        if r["ok"]:
            LOGGER_INFO(f"  [PASS]  {rel}")
        else:
            LOGGER_ERROR(f"  [FAIL]  {rel}")
            LOGGER_ERROR(f"          {r['error']}")
    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed
    LOGGER_INFO(f"Total: {len(results)}  Passed: {passed}  Failed: {failed}")


def test_yaml_verify(yaml_file: Optional[str] = None):
    if yaml_file is None:
        yaml_file = input("Enter the path to the test case/suite/batch YAML file to verify: ").strip()
    if not os.path.exists(yaml_file):
        LOGGER_ERROR(f"File not found: {yaml_file}")
        return
    type_label, sub_cases = _get_sub_cases(yaml_file)
    LOGGER_INFO(f"Verifying {type_label}: {yaml_file}  ({len(sub_cases)} sub-cases)")

    results = []
    for case_path in sub_cases:
        ok, error = _verify_test_case(case_path)
        results.append({"file": case_path, "ok": ok, "error": error})

    _log_results(results)


if __name__ == "__main__":
    # yaml_file = "src/test_space/test_batch/commercial_guest_signin_join.yaml"
    yaml_file = None
    test_yaml_verify(yaml_file)
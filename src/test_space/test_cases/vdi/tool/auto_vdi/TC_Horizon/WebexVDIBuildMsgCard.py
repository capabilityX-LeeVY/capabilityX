import argparse
import json
from datetime import datetime


def WebexVDIBuildMsgCard(
    title,
    timestamp,
    platform,
    vdi_env,
    webex_app_version,
    vdi_plugin_version,
    test_suite,
):
    status_color = _status_to_color(title)
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"\ud83d\ude80 Running Status: {title}",
                        "weight": "Bolder",
                        "size": "Medium",
                        "color": status_color,
                        "horizontalAlignment": "Center",
                        "wrap": True,
                    }
                ],
            },
            {
                "type": "Container",
                "items": [
                    _key_value_row("Time", timestamp),
                    _key_value_row("Platform", platform),
                    _key_value_row("VDI Env", vdi_env),
                    _key_value_row("Webex App Version", webex_app_version),
                    _key_value_row("VDI Plugin version", vdi_plugin_version),
                    _key_value_row("Test suite", test_suite),
                ],
            },
        ],
    }


def WebexVDIBuildFailureCard(
    title,
    timestamp,
    platform,
    webex_app_version,
    vdi_plugin_version,
    test_suite,
    failures,
):
    total_vdi_cases = _extract_total_vdi_cases(failures)
    first_failed_case = _extract_first_failed_case(failures)
    failure_lines = _normalize_failures(failures)
    if _contains_no_failure_marker(failure_lines):
        failure_lines = []
    failure_count = len(failure_lines)
    header = f"\ud83d\udea8 {title or 'AI Check Failure List'} ({failure_count})"
    first_failed_subtitle = None
    if first_failed_case:
        display_case = first_failed_case.removeprefix("VDI/meeting/")
        display_case = display_case.removeprefix("vdi/meeting/")
        first_failed_subtitle = f"⚠️ First Failed Test Case: {display_case}"
    subtitle = None
    if total_vdi_cases is not None:
        subtitle = f"🧮 Total VDI Test Case ({total_vdi_cases})"
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.2",
        "width": "stretch",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": header,
                                        "weight": "Bolder",
                                        "size": "Medium",
                                        "color": "Attention",
                                        "horizontalAlignment": "Center",
                                        "wrap": True,
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": first_failed_subtitle,
                                        "weight": "Bolder",
                                        "color": "Warning",
                                        "horizontalAlignment": "Center",
                                        "wrap": True,
                                        "spacing": "Small",
                                        "isVisible": first_failed_subtitle is not None,
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": subtitle,
                                        "weight": "Bolder",
                                        "color": "Accent",
                                        "horizontalAlignment": "Center",
                                        "wrap": True,
                                        "spacing": "Small",
                                        "isVisible": subtitle is not None,
                                    },
                                ],
                                "horizontalAlignment": "Center",
                            }
                        ],
                    }
                ],
            },
            {
                "type": "Container",
                "spacing": "Medium",
                "separator": True,
                "bleed": True,
                "items": _failure_text_blocks(failure_lines, header),
            },
        ],
    }


def _key_value_row(label, value):
    return {
        "type": "ColumnSet",
        "columns": [
            {
                "type": "Column",
                "width": "auto",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"{label}:",
                        "weight": "Bolder",
                        "wrap": True,
                    }
                ],
            },
            {
                "type": "Column",
                "width": "stretch",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": value or "-",
                        "wrap": True,
                    }
                ],
            },
        ],
    }


def _normalize_failures(failures):
    if not failures:
        return []
    if isinstance(failures, str):
        lines = [line.strip() for line in failures.splitlines()]
    else:
        lines = [str(line).strip() for line in failures]
    return [
        line
        for line in lines
        if line
        and "AI Check Failure List" not in line
        and "total vdi test case" not in line.lower()
        and "first failed test case" not in line.lower()
    ]


def _extract_total_vdi_cases(failures):
    if not failures:
        return None
    if isinstance(failures, str):
        lines = failures.splitlines()
    else:
        lines = [str(line) for line in failures]
    for line in lines:
        normalized = line.strip().lower()
        if normalized.startswith("total vdi test case"):
            parts = normalized.split(":", 1)
            if len(parts) != 2:
                return None
            value = parts[1].strip()
            return value or None
    return None


def _extract_first_failed_case(failures):
    if not failures:
        return None
    if isinstance(failures, str):
        lines = failures.splitlines()
    else:
        lines = [str(line) for line in failures]
    for line in lines:
        normalized = line.strip().lower()
        if normalized.startswith("first failed test case"):
            parts = line.split(":", 1)
            if len(parts) != 2:
                return None
            value = parts[1].strip()
            return value or None
    return None


def _contains_no_failure_marker(lines):
    marker = "no entries with 'failure. reasoning' found"
    for line in lines:
        if marker in line.lower():
            return True
    return False


def _failure_text_blocks(failure_lines, header_text, max_items=20):
    if not failure_lines:
        return [
            {
                "type": "TextBlock",
                "text": "No failed cases reported.",
                "wrap": True,
                "isSubtle": True,
            }
        ]
    items = []
    for idx, line in enumerate(failure_lines[:max_items], start=1):
        items.append(_failure_row(line, idx))
    if len(failure_lines) > max_items:
        items.append(
            {
                "type": "TextBlock",
                "text": f"...and {len(failure_lines) - max_items} more",
                "wrap": True,
                "isSubtle": True,
            }
        )
    return items


def _failure_header_row():
    return {
        "type": "ColumnSet",
        "spacing": "Small",
        "separator": True,
        "columns": [
            _failure_header_cell("number", "auto"),
            _failure_header_cell("case name", "20"),
            _failure_header_cell("failure reasoning", "80"),
        ],
    }


def _failure_header_cell(text, width):
    return {
        "type": "Column",
        "width": width,
        "items": [
            {
                "type": "TextBlock",
                "text": text,
                "weight": "Bolder",
                "wrap": True,
            }
        ],
    }


def _failure_row(line, index=None):
    number, case_name, reasoning = _parse_failure_line(line)
    if index is not None:
        number = str(index)
    return {
        "type": "ColumnSet",
        "spacing": "Small",
        "separator": True,
        "columns": [
            _failure_cell(number, "auto", is_number=True),
            _failure_cell(case_name, "20"),
            _failure_cell(reasoning, "80"),
        ],
    }


def _failure_cell(text, width, is_number=False):
    display_text = text or "-"
    if is_number and display_text != "-":
        display_text = f"#{display_text}"
    return {
        "type": "Column",
        "width": width,
        "items": [
            {
                "type": "TextBlock",
                "text": display_text,
                "weight": "Bolder" if is_number else None,
                "wrap": True,
            }
        ],
    }


def _parse_failure_line(line):
    if not line:
        return "-", "-", "-"
    if "|" not in line:
        return "-", line.strip(), "-"
    parts = [part.strip() for part in line.split("|") if part.strip()]
    number = parts[0] if len(parts) > 0 else "-"
    case_name = parts[1] if len(parts) > 1 else "-"
    reasoning = " | ".join(parts[2:]) if len(parts) > 2 else "-"
    return number, case_name, reasoning


def _status_to_color(status):
    if not status:
        return "Default"
    lowered = status.strip().lower()
    if lowered == "starting":
        return "Accent"
    if "succeed" in lowered:
        return "Good"
    if "failed" in lowered:
        return "Attention"
    return "Default"


def parse_args():
    parser = argparse.ArgumentParser(description="Build Webex Adaptive Card JSON")
    parser.add_argument(
        "--mode",
        choices=["status", "failures"],
        default="status",
        help="Card type to build",
    )
    parser.add_argument("--title", required=True, help="Test running status")
    parser.add_argument("--time", dest="timestamp", default=None, help="Time string")
    parser.add_argument("--platform", required=True, help="Windows or Linux")
    parser.add_argument("--webex-app-version", required=True, help="Webex App version")
    parser.add_argument("--vdi-plugin-version", required=True, help="VDI Plugin version")
    parser.add_argument("--test-suite", required=True, help="Test suite name")
    parser.add_argument(
        "--failures-file",
        default=None,
        help="Path to a UTF-8 text file containing failed cases",
    )
    parser.add_argument(
        "--failures",
        default=None,
        help="Inline failed cases separated by newlines",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    timestamp = args.timestamp or datetime.now().strftime("%Y-%m-%d-%H%M%S")
    if args.mode == "failures":
        failures_text = args.failures
        if args.failures_file:
            with open(args.failures_file, "r", encoding="utf-8", errors="replace") as handle:
                failures_text = handle.read()
        card = WebexVDIBuildFailureCard(
            title=args.title,
            timestamp=timestamp,
            platform=args.platform,
            webex_app_version=args.webex_app_version,
            vdi_plugin_version=args.vdi_plugin_version,
            test_suite=args.test_suite,
            failures=failures_text,
        )
    else:
        card = WebexVDIBuildMsgCard(
            title=args.title,
            timestamp=timestamp,
            platform=args.platform,
            webex_app_version=args.webex_app_version,
            vdi_plugin_version=args.vdi_plugin_version,
            test_suite=args.test_suite,
        )
    print(json.dumps(card, indent=2))


if __name__ == "__main__":
    main()

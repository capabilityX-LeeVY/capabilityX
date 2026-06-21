import argparse
import os
import sys
from typing import List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Webex alert message for a specific AI Check Failure entry "
            "from WebexVDIRsReportAnalyzer output."
        )
    )
    parser.add_argument(
        "--analyzer-output",
        required=True,
        help="Path to AI Check Failure List output file produced by WebexVDIRsReportAnalyzer.py",
    )
    parser.add_argument(
        "--match-case",
        default=None,
        help="Case name substring to match (case-insensitive)",
    )
    parser.add_argument(
        "--match-reason",
        default=None,
        help="Failure reason substring to match (case-insensitive)",
    )
    parser.add_argument(
        "--mention",
        default="",
        help="Base mention text to append on the same line (e.g., @john.doe)",
    )
    parser.add_argument(
        "--custom-message",
        default=None,
        help="Optional message to prepend above the alert",
    )
    parser.add_argument(
        "--out-file",
        default=None,
        help="Optional path to write the message (UTF-8). If omitted, prints to stdout.",
    )
    return parser.parse_args()


def normalize(text: str) -> str:
    return text.lower()


def format_person_email_mention(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("<@personEmail:") and cleaned.endswith(">"):
        return cleaned
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    return f"<@personEmail:{cleaned}>"


def collect_mentions(base_mention: str, case_name: str, reason: str) -> str:
    mentions = []
    if base_mention:
        mentions.append(format_person_email_mention(base_mention))
    normalized_case = normalize(case_name)
    normalized_reason = normalize(reason)

    if "vdi_healthchecker" in normalized_case:
        mentions.append(f"{format_person_email_mention('jingkhua@cisco.com')} 🔥 🚒")

    is_vbg = "vbg" in normalized_case
    is_sharing = "sharing" in normalized_case and "receive" not in normalized_case
    is_annotation = "annotation" in normalized_case
    is_whiteboard = "whiteboard" in normalized_case
    if is_vbg or is_sharing or is_annotation or is_whiteboard:
        mentions.append(f"{format_person_email_mention('hchen2@cisco.com')} 🌄 🖥️ 🖌️ 🛠️")

    blank_keywords = ("blank", "grey")
    context_keywords = ("window", "screen", "shared content", "video", "preview", "selfview")
    if any(keyword in normalized_reason for keyword in blank_keywords) and any(
        keyword in normalized_reason for keyword in context_keywords
    ):
        mentions.append(f"{format_person_email_mention('funiu@cisco.com')} 🔲 🛠️")

    unique_mentions = []
    seen = set()
    for mention in mentions:
        if mention not in seen:
            unique_mentions.append(mention)
            seen.add(mention)

    return " ".join(unique_mentions)


def parse_table_row(line: str) -> Optional[Tuple[str, str, str]]:
    if not line.startswith("|"):
        return None
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    if len(parts) < 3:
        return None
    index, case_name, reason = parts[0], parts[1], parts[2]
    if not index or not case_name or not reason:
        return None
    return index, case_name, reason


def match_row(
    case_name: str,
    reason: str,
    match_case: Optional[str],
    match_reason: Optional[str],
) -> bool:
    if match_case and match_case.strip():
        if normalize(match_case) not in normalize(case_name):
            return False
    if match_reason and match_reason.strip():
        if normalize(match_reason) not in normalize(reason):
            return False
    return True


def extract_header_lines(lines: List[str]) -> List[str]:
    header_lines: List[str] = []
    for line in lines[:8]:
        if "vdi test cases" in line:
            header_lines.append(line.rstrip("\n"))
            continue
        if "first failed test case" in line:
            header_lines.append(line.rstrip("\n"))
            continue
        if "AI Check Failure List" in line:
            header_lines.append(line.rstrip("\n"))
            continue
        if header_lines and line.strip() == "":
            header_lines.append("")
            break
    return header_lines


def build_message(
    lines: List[str],
    mention: str,
    match_case: Optional[str],
    match_reason: Optional[str],
    custom_message: Optional[str],
) -> str:
    header_lines = extract_header_lines(lines)
    if not header_lines:
        header_lines = ["AI Check Failure List", ""]

    matched_row: Optional[Tuple[str, str, str]] = None
    first_row: Optional[Tuple[str, str, str]] = None
    for line in lines:
        row = parse_table_row(line)
        if not row:
            continue
        if first_row is None:
            first_row = row
        index, case_name, reason = row
        if match_row(case_name, reason, match_case, match_reason):
            matched_row = (index, case_name, reason)
            break

    if not matched_row:
        if not match_case and not match_reason:
            matched_row = first_row

    if not matched_row:
        message_lines: List[str] = []
        if custom_message:
            message_lines.append(custom_message)
            message_lines.append("")
        message_lines.extend(header_lines)
        if first_row is None:
            message_lines.append("🙆‍♂️ 🆗 No entries with 'Failure. Reasoning' found.")
        else:
            message_lines.append("No matching AI check failure entry found.")
        return "\n".join(message_lines).rstrip() + "\n"

    index, case_name, reason = matched_row
    mention_text = collect_mentions(mention, case_name, reason)
    if mention_text:
        reason_with_mention = f"{reason} {mention_text}".rstrip()
    else:
        reason_with_mention = reason
    alert_row = f"| {index} | {case_name} | {reason_with_mention} |"

    message_lines: List[str] = []
    if custom_message:
        message_lines.append(custom_message)
        message_lines.append("")
    message_lines.extend(header_lines)
    message_lines.append(alert_row)

    return "\n".join(message_lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    if not os.path.isfile(args.analyzer_output):
        raise FileNotFoundError(f"Analyzer output not found: {args.analyzer_output}")

    # If no match filters are provided, the first failure entry is used.

    with open(args.analyzer_output, "r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()

    message = build_message(
        lines,
        mention=args.mention,
        match_case=args.match_case,
        match_reason=args.match_reason,
        custom_message=args.custom_message,
    )

    if args.out_file:
        with open(args.out_file, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(message)
    else:
        sys.stdout.write(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())

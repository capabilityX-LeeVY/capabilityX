#!/usr/bin/env python3
"""Download the Markdown report referenced in the TC_Citrix output file."""

from __future__ import annotations

import argparse
import os
import re
import sys
import ssl
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    import certifi
except ImportError:  # Optional dependency
    certifi = None


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
URL_RE = re.compile(r"https?://\S+\.md")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def find_report_url(output_path: str) -> str:
    with open(output_path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = strip_ansi(raw_line).strip()
            if "Test Report URL:" in line:
                match = URL_RE.search(line)
                if match:
                    return match.group(0)

    raise RuntimeError('Could not find "Test Report URL:" with an .md link in output file.')


def default_destination(url: str, dest_dir: str) -> str:
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "test-report.md"
    return os.path.join(dest_dir, filename)


def ensure_raw_url(url: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query.get("format") != "raw":
        query["format"] = "raw"
    updated = parsed._replace(query=urlencode(query))
    return urlunparse(updated)


def build_raw_url_candidates(url: str) -> list[str]:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    candidates = []

    query_variant = dict(query)
    query_variant["format"] = "raw"
    candidates.append(urlunparse(parsed._replace(query=urlencode(query_variant))))

    query_variant = dict(query)
    query_variant["raw"] = "1"
    candidates.append(urlunparse(parsed._replace(query=urlencode(query_variant))))

    query_variant = dict(query)
    query_variant["download"] = "1"
    candidates.append(urlunparse(parsed._replace(query=urlencode(query_variant))))

    candidates.append(url)

    # De-duplicate while preserving order
    seen = set()
    ordered = []
    for candidate in candidates:
        if candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    return ordered


def build_ssl_context(insecure: bool, cafile: str | None, capath: str | None) -> ssl.SSLContext:
    if insecure:
        return ssl._create_unverified_context()
    if cafile or capath:
        return ssl.create_default_context(cafile=cafile or None, capath=capath or None)
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def download(url: str, dest_path: str, insecure: bool, cafile: str | None, capath: str | None) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    last_error = None
    for use_insecure in (insecure, True) if not insecure else (True,):
        if use_insecure and not insecure:
            print("SSL verification failed; retrying with insecure mode.")
        context = build_ssl_context(use_insecure, cafile, capath)
        for candidate in build_raw_url_candidates(url):
            request = urllib.request.Request(
                candidate,
                headers={
                    "Accept": "text/markdown, text/plain, */*",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            try:
                with urllib.request.urlopen(request, context=context) as response:
                    content_type = (response.headers.get("Content-Type") or "").lower()
                    data = response.read()
                if "text/html" in content_type or data.lstrip().startswith(b"<"):
                    last_error = RuntimeError(
                        f"Received HTML content from {candidate}; trying next raw format."
                    )
                    continue
                with open(dest_path, "wb") as handle:
                    handle.write(data)
                return
            except ssl.SSLError as exc:
                last_error = exc
                if not use_insecure:
                    break
            except Exception as exc:
                last_error = exc

    if last_error:
        raise last_error


def parse_failure_entries(report_path: str) -> list[tuple[str, str]]:
    results = []
    with open(report_path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            if not raw_line.startswith("|"):
                continue
            if re.match(r"\|[-\s]+\|", raw_line):
                continue
            cells = [cell.strip() for cell in raw_line.strip().strip("|").split("|")]
            if not cells:
                continue
            for cell in cells:
                markers = ("Failure. Reasoning:", "Failure Reasoning:")
                matched_marker = next((m for m in markers if m in cell), None)
                if matched_marker:
                    marker_index = cell.find(matched_marker)
                    if marker_index != -1:
                        normalized = "❌" + cell[marker_index:]
                    else:
                        normalized = cell
                    results.append((cells[0], normalized))
                    break
    return results


def count_vdi_test_cases(report_path: str) -> int:
    header_re = re.compile(r"^##\s*Test Case:\s*\[(.+?)\]", re.IGNORECASE)
    excluded = {"vdi_reset_database", "vdi_compress_wbx_logs"}
    count = 0
    with open(report_path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            match = header_re.match(raw_line.strip())
            if not match:
                continue
            case_name = match.group(1).strip()
            last_segment = case_name.split("/")[-1].strip().lower()
            if last_segment.startswith("vdi_") and last_segment not in excluded:
                count += 1
    return count


def find_first_failed_test_case(report_path: str) -> str | None:
    header_re = re.compile(r"^##\s*Test Case:\s*\[(.+?)\]", re.IGNORECASE)
    failure_markers = ("❌Failed", "❌ Failure", "❌Failure", "Failed")
    current_case = None
    with open(report_path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            match = header_re.match(stripped)
            if match:
                current_case = match.group(1).strip()
                continue
            if not stripped.startswith("|"):
                continue
            if re.match(r"\|[-\s]+\|", stripped):
                continue
            if any(marker in stripped for marker in failure_markers):
                return current_case
    return None


def print_failure_table(failures: list[tuple[str, str]]) -> None:
    print("🤖 AI Check Failure List 🤖")
    print("")
    for index, (case_name, failure_reasoning) in enumerate(failures, 1):
        markers = ("Failure. Reasoning:", "Failure Reasoning:")
        cleaned_reasoning = failure_reasoning.replace("Γ¥î", "")
        matched_marker = next((m for m in markers if m in cleaned_reasoning), None)
        marker_index = cleaned_reasoning.find(matched_marker) if matched_marker else -1
        if marker_index != -1 and matched_marker:
            remainder = cleaned_reasoning[marker_index + len(matched_marker):].lstrip()
            red_prefix = "❌ **Failure. Reasoning**"
            cleaned_reasoning = f"{red_prefix}: {remainder}" if remainder else f"{red_prefix}:"
        safe_reasoning = cleaned_reasoning.replace("|", "\\|")
        safe_case = case_name.replace("|", "\\|")
        print(f"| **{index}** | **{safe_case}** | {safe_reasoning} |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Markdown report linked in TC_Citrix output.txt",
    )
    default_output = os.path.join(os.path.dirname(__file__), "output.txt")
    parser.add_argument(
        "--output-file",
        default=default_output,
        help=f"Path to output file (default: {default_output})",
    )
    parser.add_argument(
        "--dest-dir",
        default=os.path.dirname(__file__),
        help="Directory to save the downloaded Markdown file",
    )
    parser.add_argument(
        "--dest-file",
        default=None,
        help="Optional full path to save the Markdown file",
    )
    parser.add_argument(
        "--print-failures",
        action="store_true",
        help="Print entries with 'Failure. Reasoning:' from the downloaded report",
    )
    parser.add_argument(
        "--report-file",
        default=None,
        help="Use an existing report file instead of downloading",
    )
    parser.add_argument(
        "--result-file",
        default=None,
        help="Write output to a UTF-8 file instead of printing",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification (use only for trusted networks)",
    )
    parser.add_argument(
        "--cafile",
        default=None,
        help="Path to a PEM CA bundle file to trust",
    )
    parser.add_argument(
        "--capath",
        default=None,
        help="Path to a directory containing PEM CA files",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the downloaded report file after processing",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    downloaded_report = False
    if args.report_file:
        dest_path = args.report_file
        if not os.path.isfile(dest_path):
            raise FileNotFoundError(f"Report file not found: {dest_path}")
    else:
        if not os.path.isfile(args.output_file):
            raise FileNotFoundError(f"Output file not found: {args.output_file}")

        url = find_report_url(args.output_file)
        dest_path = args.dest_file or default_destination(url, args.dest_dir)

        download(url, dest_path, args.insecure, args.cafile, args.capath)
        downloaded_report = True
        print(f"Downloaded report to: {dest_path}")

    vdi_count = count_vdi_test_cases(dest_path)
    count_line = f"total vdi test cases: {vdi_count}"
    first_failed = find_first_failed_test_case(dest_path)
    first_failed_line = f"first failed test case: {first_failed or '-'}"
    if args.print_failures:
        failures = parse_failure_entries(dest_path)
        if args.result_file:
            with open(args.result_file, "w", encoding="utf-8", newline="\n") as handle:
                from io import StringIO

                buffer = StringIO()
                original_stdout = sys.stdout
                try:
                    sys.stdout = buffer
                    print(count_line)
                    print(first_failed_line)
                    print("")
                    if not failures:
                        print("🤖 AI Check Failure List 🤖")
                        print("")
                        print("🙆‍♂️ 🆗 No entries with 'Failure. Reasoning' found.")
                    else:
                        print_failure_table(failures)
                finally:
                    sys.stdout = original_stdout
                handle.write(buffer.getvalue())
        else:
            print(count_line)
            print(first_failed_line)
            print("")
            if not failures:
                print("🤖 AI Check Failure List 🤖")
                print("")
                print("🙆‍♂️ 🆗 No entries with 'Failure. Reasoning' found.")
            else:
                print_failure_table(failures)
    else:
        print(count_line)
        print(first_failed_line)
    if args.cleanup and downloaded_report:
        try:
            os.remove(dest_path)
            print(f"Deleted report file: {dest_path}")
        except OSError as exc:
            print(f"Failed to delete report file: {dest_path} ({exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
sr_coverage_validator.py

Validate that all visible text in the focused dialog's screenshot is also
exposed to screen readers. Captures the dialog (parent window of the focused
control), extracts text via OCR (GPT-4 Vision), collects accessible content
from the UIA tree, and reports the coverage with an OCR-vs-SR side-by-side
comparison table.
"""

import datetime as _dt
import os
import re
from pathlib import Path

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from config.paths import SCREEN_READER_REPORT_PATH, WINDOW_IMAGE_PATH, NAVIGATION_REPORT_PATH


# Pending updates queued for the navigation-report patch.
# Applied by patching RemoteArchiveProcessor.upload_archive, so updates are
# written to the markdown BEFORE the report is uploaded to the WRS server.
# Each entry: {"step_name": str, "passed": bool, "report_path": str, "coverage": float}
_PENDING_NAV_UPDATES = []
_UPLOAD_HOOK_INSTALLED = False


def _queue_nav_report_update(step_name: str, passed: bool, report_path: str, coverage: float):
    """Queue an SR coverage result for navigation-report patching at upload time."""
    _PENDING_NAV_UPDATES.append({
        "step_name": step_name,
        "passed": passed,
        "report_path": report_path,
        "coverage": coverage,
    })
    _install_upload_hook()


def _install_upload_hook():
    """
    Monkey-patch RemoteArchiveProcessor.upload_archive so pending
    navigation-report patches are applied just before upload.
    """
    global _UPLOAD_HOOK_INSTALLED
    if _UPLOAD_HOOK_INSTALLED:
        return
    try:
        from common.finalizer import archive_processor
        original_upload = archive_processor.RemoteArchiveProcessor.upload_archive

        def patched_upload(self, *args, **kwargs):
            try:
                _apply_nav_report_updates()
            except Exception as e:
                LOGGER_WARNING(f"[SR Coverage] Pre-upload patch failed: {e}")
            return original_upload(self, *args, **kwargs)

        archive_processor.RemoteArchiveProcessor.upload_archive = patched_upload
        _UPLOAD_HOOK_INSTALLED = True
        LOGGER_INFO("[SR Coverage] Upload hook installed for nav-report patching", "GREEN")
    except Exception as e:
        LOGGER_WARNING(f"[SR Coverage] Failed to install upload hook: {e}")


def validate_sr_coverage(window_title: str = None, coverage_threshold: float = 80.0) -> bool:
    """
    Validate screen reader coverage for the focused dialog/window.

    Pipeline:
        1. Resolve the parent dialog of the currently focused control.
        2. Capture a screenshot scoped to that dialog (not the full app).
        3. Extract visible text from the screenshot via GPT-4 Vision OCR.
        4. Collect all accessible content from the UIA tree of the same dialog.
        5. Compare each OCR text segment against the SR content side-by-side.
        6. PASS if coverage percentage >= threshold.

    Args:
        window_title: Optional window title for fallback when no focused dialog.
        coverage_threshold: Minimum coverage percentage to PASS (default 80%).

    Returns:
        bool: True if coverage meets the threshold, otherwise False.
    """
    from models.openai_client import OpenAIClient
    from test_space.test_functions.acc_functions.sr_content_collector import (
        collect_sr_content,
        get_focused_dialog_element,
    )

    LOGGER_INFO("=" * 70, "CYAN")
    LOGGER_INFO("[SR Coverage] Starting validation...", "CYAN")
    LOGGER_INFO("=" * 70, "CYAN")

    # Step 1: resolve focused dialog
    LOGGER_INFO("[SR Coverage] Step 1: Resolving focused dialog element...", "BLUE")
    dialog_element = get_focused_dialog_element()
    dialog_name = "foreground_window"
    if dialog_element is not None:
        try:
            dialog_name = (dialog_element.CurrentName or "dialog").strip() or "dialog"
        except Exception:
            pass
        LOGGER_INFO(f"[SR Coverage] Focused dialog: [{dialog_name}]", "GREEN")
    else:
        LOGGER_WARNING("[SR Coverage] No focused dialog found, will fall back to foreground window")

    # Step 2: capture dialog screenshot
    LOGGER_INFO("[SR Coverage] Step 2: Capturing dialog screenshot...", "BLUE")
    image_path = _capture_dialog_screenshot(dialog_element, dialog_name)
    if not image_path:
        LOGGER_ERROR("[SR Coverage] Failed to capture dialog screenshot")
        return False
    LOGGER_INFO(f"[SR Coverage] Screenshot saved: {image_path}", "GREEN")

    # Step 3: OCR
    LOGGER_INFO("[SR Coverage] Step 3: Extracting text from screenshot (AI Vision)...", "BLUE")
    client = OpenAIClient()
    ocr_text = client.extract_text_simple(image_path)
    if not ocr_text:
        LOGGER_ERROR("[SR Coverage] Failed to extract text from screenshot")
        return False
    LOGGER_INFO(f"[SR Coverage] OCR extracted text:\n{ocr_text}", "GREEN")

    # Step 4: collect SR content from UIA tree (scoped to dialog if available)
    LOGGER_INFO("[SR Coverage] Step 4: Collecting SR content from UIA tree...", "BLUE")
    sr_result = collect_sr_content(window_title=window_title, root_element=dialog_element)
    sr_items = sr_result["items"]
    sr_all_text = sr_result["all_text"]
    if not sr_all_text:
        LOGGER_ERROR("[SR Coverage] No SR content collected from UIA tree")
        return False
    LOGGER_INFO(
        f"[SR Coverage] SR content ({sr_result['count']} elements):\n{sr_all_text}",
        "GREEN",
    )

    # Step 5: compare OCR vs SR with side-by-side details
    LOGGER_INFO("[SR Coverage] Step 5: Comparing OCR text vs SR content...", "BLUE")
    comparison = _compare_texts(ocr_text, sr_items)

    # Step 6: report
    coverage = comparison["coverage"]
    LOGGER_INFO("=" * 70, "CYAN")
    LOGGER_INFO(
        f"[SR Coverage] Results: {coverage:.1f}% coverage "
        f"({comparison['matched']}/{comparison['total']} items)",
        "CYAN",
    )
    for item in comparison["details"]:
        status = item.get("status", "FAIL")
        color = {"PASS": "GREEN", "FAIL": "RED", "SKIP": "YELLOW"}.get(status, "RED")
        LOGGER_INFO(
            f"  [{status}] AI: \"{item['ocr_text']}\"  <->  SR: \"{item['sr_text']}\"",
            color,
        )

    passed = coverage >= coverage_threshold
    if passed:
        LOGGER_INFO(f"[SR Coverage] PASSED (>= {coverage_threshold}%)", "GREEN")
    else:
        LOGGER_ERROR(f"[SR Coverage] FAILED (< {coverage_threshold}%)")

    sr_report_path = _save_report(comparison, image_path, dialog_name, ocr_text, sr_all_text)

    # Queue navigation-report patch (applied at process exit so the framework
    # finishes writing the row first).
    if sr_report_path:
        _queue_nav_report_update(
            step_name="validate sr coverage for current window",
            passed=passed,
            report_path=sr_report_path,
            coverage=coverage,
        )

    LOGGER_INFO("=" * 70, "CYAN")
    return passed


def _capture_dialog_screenshot(dialog_element, dialog_name: str) -> str:
    """
    Capture a screenshot of the dialog element's bounding rectangle.

    Falls back to ControlRecorder.record_window_image() if the dialog
    element is unavailable.
    """
    if dialog_element is None:
        return _fallback_capture()

    try:
        from rs_sdk.utils import image_handler

        rect = dialog_element.CurrentBoundingRectangle
        if not rect or (rect.right - rect.left) <= 0 or (rect.bottom - rect.top) <= 0:
            LOGGER_WARNING("[SR Coverage] Dialog has invalid bounding rect; falling back")
            return _fallback_capture()

        result = image_handler.capture_image_from_currentBoundingRectangle(rect)
        if result is None or result.img is None:
            LOGGER_WARNING("[SR Coverage] Dialog capture returned no image; falling back")
            return _fallback_capture()

        timestamp = _dt.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = _sanitize_name(dialog_name)
        image_name = f"{timestamp}_dialog_{safe_name}"

        output_dir = Path(WINDOW_IMAGE_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_handler.save_image(image_name, img=result.img, output_path=output_dir.as_posix())

        return str(output_dir / f"{image_name}.jpg")
    except Exception as e:
        LOGGER_ERROR(f"[SR Coverage] Dialog screenshot error: {e}")
        return _fallback_capture()


def _fallback_capture() -> str:
    """Fallback to existing ControlRecorder window capture."""
    try:
        from rs_sdk.utils.control_recorder import ControlRecorder
        recorder = ControlRecorder()
        image_path, _ = recorder.record_window_image()
        if image_path:
            return image_path
        image_path, _ = recorder.capture_foreground_window_image()
        return image_path
    except Exception as e:
        LOGGER_ERROR(f"[SR Coverage] Fallback capture error: {e}")
        return None


import re


# Markdown formatting patterns to strip when comparing text semantically
_MARKDOWN_INLINE_RE = re.compile(r'(\*\*|__|\*|_|`)')
# Lines that are pure markdown noise / fence markers / formatting only
_MARKDOWN_NOISE_RE = re.compile(r'^(```[a-zA-Z]*|```|---+|===+|\*\*\*+)$')
# Italic-only descriptive lines added by GPT, e.g.
#   *Layout and hierarchy preserved as shown in the original dialog.*
# These describe the screenshot rather than transcribe its visible text.
# IMPORTANT: must NOT match bold (**...**) lines — bold-wrapped text is real
# UI content; we only want to skip true single-asterisk / single-underscore
# italic narrative wrappers.
_ITALIC_DESCRIPTION_RE = re.compile(
    r'^(?:\*(?!\*)|_(?!_)).+(?:(?<!\*)\*|(?<!_)_)$'
)
# Brackets / parens that surround OCR-extracted button text, e.g. "[OK]" → "OK"
_BRACKET_STRIP_RE = re.compile(r'[\[\]\(\)\{\}<>]')
# Markdown image / icon references such as:
#   ![Warning Icon]
#   ![Warning Icon](path/to/icon.png)
#   ![](icon.png)
# Icons are decorative, not visible text the screen reader needs to announce,
# so any line that is *only* one or more such image refs is skipped.
_MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\](?:\([^)]*\))?')
_IMAGE_ONLY_LINE_RE = re.compile(r'^(?:\s*!\[[^\]]*\](?:\([^)]*\))?\s*)+$')


def _normalize_for_compare(text: str) -> str:
    """Strip markdown markers, brackets and normalize whitespace for semantic comparison."""
    if not text:
        return ""
    # Drop markdown image refs first so e.g. "![Warning Icon] Heads up" -> "Heads up"
    cleaned = _MARKDOWN_IMAGE_RE.sub(' ', text)
    cleaned = _MARKDOWN_INLINE_RE.sub('', cleaned)
    cleaned = _BRACKET_STRIP_RE.sub(' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip().lower()


def _is_skip_line(text: str) -> bool:
    """Return True if the OCR line is markdown noise/formatting that should be skipped."""
    stripped = text.strip()
    if not stripped:
        return True
    if _MARKDOWN_NOISE_RE.match(stripped):
        return True
    # Pure markdown image / icon line, e.g. "![Warning Icon]" — decorative, skip.
    if _IMAGE_ONLY_LINE_RE.match(stripped):
        return True
    # Italic-only narrative lines GPT sometimes appends (description of layout, etc.)
    if _ITALIC_DESCRIPTION_RE.match(stripped):
        return True
    # If after removing markdown markers there is no real content left
    if not _normalize_for_compare(stripped):
        return True
    return False


def _compare_texts(ocr_text: str, sr_items: list) -> dict:
    """
    Compare OCR-extracted text against SR items.

    For each OCR segment, find the best-matching SR item and emit a row with
    one of three statuses: PASS, FAIL, or SKIP (for markdown formatting noise).
    """
    ocr_segments = _parse_ocr_into_segments(ocr_text)
    sr_names = [item["name"] for item in sr_items if item.get("name")]
    sr_text_lower = _normalize_for_compare("\n".join(sr_names))

    details = []
    matched = 0
    countable = 0
    for segment in ocr_segments:
        if _is_skip_line(segment):
            details.append({
                "ocr_text": segment,
                "sr_text": "(skipped: formatting only)",
                "status": "SKIP",
                "found": None,
            })
            continue

        countable += 1
        found = _is_text_in_sr(segment, sr_text_lower)
        best_sr = _find_best_sr_match(segment, sr_names)
        details.append({
            "ocr_text": segment,
            "sr_text": best_sr if best_sr else "(no match)",
            "status": "PASS" if found else "FAIL",
            "found": found,
        })
        if found:
            matched += 1

    total = countable if countable else 1
    coverage = (matched / total * 100) if countable else 0.0

    return {"coverage": coverage, "matched": matched, "total": total, "details": details}


def _parse_ocr_into_segments(ocr_text: str) -> list:
    """Split OCR text into meaningful per-line segments, dropping noise."""
    segments = []
    for line in ocr_text.split('\n'):
        line = line.rstrip()
        # Trim leading bullet markers like '- ', '* ', '> ', '| '
        stripped = line.lstrip()
        for prefix in ('- ', '* ', '> ', '| '):
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix):]
                break
        stripped = stripped.strip()
        if not stripped:
            continue
        segments.append(stripped)
    return segments


def _is_text_in_sr(text: str, sr_text_normalized: str) -> bool:
    """Check if the OCR segment is semantically present in the SR content."""
    text_norm = _normalize_for_compare(text)
    if not text_norm:
        return True
    if text_norm in sr_text_normalized:
        return True
    words = [w for w in text_norm.split() if len(w) > 2]
    if not words:
        return True
    matched_words = sum(1 for w in words if w in sr_text_normalized)
    return (matched_words / len(words)) >= 0.7


def _find_best_sr_match(ocr_segment: str, sr_names: list) -> str:
    """Find the SR name that best matches the OCR segment (word overlap)."""
    if not sr_names:
        return ""
    seg_norm = _normalize_for_compare(ocr_segment)
    seg_words = {w for w in seg_norm.split() if len(w) > 2}

    # 1. semantic substring match (after stripping markdown markers)
    for sr in sr_names:
        sr_norm = _normalize_for_compare(sr)
        if seg_norm and seg_norm in sr_norm:
            return sr
    for sr in sr_names:
        sr_norm = _normalize_for_compare(sr)
        if sr_norm and sr_norm in seg_norm:
            return sr

    # 2. best word-overlap
    best_score = 0.0
    best_sr = ""
    for sr in sr_names:
        sr_words = {w for w in _normalize_for_compare(sr).split() if len(w) > 2}
        if not seg_words or not sr_words:
            continue
        overlap = len(seg_words & sr_words)
        score = overlap / len(seg_words)
        if score > best_score:
            best_score = score
            best_sr = sr

    return best_sr if best_score > 0 else ""


def _sanitize_name(name: str) -> str:
    """Sanitize a name for use as a filename component."""
    safe = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
    return safe[:50] if safe else "dialog"


def _save_report(comparison: dict, image_path: str, dialog_name: str,
                 ocr_text: str, sr_text: str) -> str:
    """Save the comparison results to a markdown report file. Returns the path."""
    try:
        report_dir = Path(SCREEN_READER_REPORT_PATH)
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = _sanitize_name(dialog_name)
        report_file = report_dir / f"sr_coverage_{safe_name}_{timestamp}.md"

        lines = [
            f"# SR Coverage Report: {dialog_name}",
            f"**Date:** {timestamp}",
            f"**Coverage:** {comparison['coverage']:.1f}% "
            f"({comparison['matched']}/{comparison['total']})",
            f"**Screenshot:** `{image_path}`",
            "",
            "## AI Text vs Screen Reader Comparison",
            "",
            "| # | AI Text Recognition | Screen Reader Text | Status |",
            "|---|---------------------|--------------------|--------|",
        ]
        for i, item in enumerate(comparison["details"], 1):
            ocr_cell = item["ocr_text"].replace('|', '\\|').replace('\n', ' ')
            sr_cell = item["sr_text"].replace('|', '\\|').replace('\n', ' ')
            status = item.get("status", "FAIL" if not item.get("found") else "PASS")
            lines.append(f"| {i} | {ocr_cell} | {sr_cell} | {status} |")

        lines += [
            "",
            "## Raw Data",
            "",
            "### AI Text Recognition (from screenshot)",
            "```",
            ocr_text,
            "```",
            "",
            "### Screen Reader Content (from UIA tree)",
            "```",
            sr_text,
            "```",
        ]

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        LOGGER_INFO(f"[SR Coverage] Report saved: {report_file}", "GREEN")
        return str(report_file)
    except Exception as e:
        LOGGER_WARNING(f"[SR Coverage] Failed to save report: {e}")
        return ""


def _apply_nav_report_updates():
    """
    Patch the navigation report's Screen Reader column for every queued
    sr_coverage validation result.

    Called immediately before upload (via monkey-patched
    RemoteArchiveProcessor.upload_archive) so the uploaded markdown contains
    the SR Coverage status + clickable [details] link.
    """
    if not _PENDING_NAV_UPDATES:
        return

    nav_report = _find_latest_navigation_report()
    if not nav_report:
        LOGGER_WARNING("[SR Coverage] No navigation-report-*.md found; skip patching")
        return

    try:
        with open(nav_report, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        LOGGER_WARNING(f"[SR Coverage] Could not read navigation report: {e}")
        return

    nav_dir = os.path.dirname(nav_report)
    new_content = content

    for entry in _PENDING_NAV_UPDATES:
        step_name = entry["step_name"]
        passed = entry["passed"]
        coverage = entry["coverage"]
        sr_report = entry["report_path"]

        # Build the new SR cell content with link to the detailed report.
        try:
            rel_link = os.path.relpath(sr_report, nav_dir).replace('\\', '/')
        except Exception:
            rel_link = sr_report
        status_icon = "✅ Compliant" if passed else "❌ Non-compliant"
        # Use HTML anchor so the link is clickable both in raw markdown viewers
        # and after server-side md→HTML conversion (the table cell renderer
        # often does not re-parse inline markdown links).
        new_cell = f'{status_icon} ({coverage:.0f}%) <a href="{rel_link}">details</a>'

        new_content = _patch_sr_column_for_step(new_content, step_name, new_cell)

    if new_content != content:
        try:
            with open(nav_report, 'w', encoding='utf-8') as f:
                f.write(new_content)
            LOGGER_INFO(f"[SR Coverage] Patched navigation report: {nav_report}", "GREEN")
        except Exception as e:
            LOGGER_WARNING(f"[SR Coverage] Failed to write navigation report: {e}")


def _find_latest_navigation_report() -> str:
    """Return the most recently modified navigation-report-*.md path, if any."""
    try:
        nav_dir = Path(NAVIGATION_REPORT_PATH)
        if not nav_dir.exists():
            return ""
        candidates = sorted(
            nav_dir.glob("navigation-report-*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return str(candidates[0]) if candidates else ""
    except Exception:
        return ""


def _patch_sr_column_for_step(content: str, step_name: str, new_cell: str) -> str:
    """
    Replace the Screen Reader column (10th `|`-separated cell, 1-indexed) for
    every row whose 3rd cell (Step Name) matches `step_name`.
    """
    out_lines = []
    target = step_name.strip().lower()
    for line in content.splitlines(keepends=True):
        if not line.startswith('|') or line.startswith('|---'):
            out_lines.append(line)
            continue
        # Header rows are also markdown-table rows; skip if they contain 'Step Name'
        if 'Step Name' in line and 'Screen Reader' in line:
            out_lines.append(line)
            continue
        # Split preserving leading/trailing pipes
        # Format: '| c1 | c2 | ... | cN |\n'
        cells = line.rstrip('\n').split('|')
        # cells[0] and cells[-1] are empty (outer pipes); first real cell is cells[1]
        if len(cells) < 12:
            out_lines.append(line)
            continue
        step_cell = cells[3].strip().lower()
        if step_cell != target:
            out_lines.append(line)
            continue
        # Screen Reader is the 10th data column → index 10 in cells (1-based data start)
        cells[10] = f" {new_cell} "
        new_line = '|'.join(cells)
        if not new_line.endswith('\n'):
            new_line += '\n'
        out_lines.append(new_line)
    return ''.join(out_lines)

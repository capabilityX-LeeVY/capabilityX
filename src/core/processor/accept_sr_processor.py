"""
Accepted Screen Reader Processor

Manages the accepted_control_sr table — a whitelist of control SR descriptions
that are intentionally non-standard but acceptable. After AI SR analysis marks
controls as Non-compliant, this processor checks the whitelist and overrides
matching entries to "✅ Accepted".
"""

import pymysql
from typing import Optional, List, Dict
from config.config import CONTROL_DB
from db.handlers import get_db_connection
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR, LOGGER_DEBUG


_TABLE_INITIALIZED = False


def _ensure_table(connection: pymysql.Connection) -> None:
    """Create accepted_control_sr table if it does not exist (once per process)."""
    global _TABLE_INITIALIZED
    if _TABLE_INITIALIZED:
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accepted_control_sr (
                    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    control_name    VARCHAR(500)    NOT NULL,
                    expected_sr_text TEXT           DEFAULT NULL,
                    platform        VARCHAR(64)    DEFAULT 'Windows',
                    app_version     VARCHAR(32)    DEFAULT NULL,
                    language        VARCHAR(16)    DEFAULT 'en_US',
                    added_by        VARCHAR(255)   DEFAULT 'wrs',
                    added_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_control_name (control_name(255)),
                    INDEX idx_platform_lang (platform, language)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            connection.commit()
        _TABLE_INITIALIZED = True
    except pymysql.Error as e:
        LOGGER_ERROR(f"[AcceptSR] Failed to ensure table: {e}")


def _get_connection() -> Optional[pymysql.Connection]:
    """Get a connection to control_db."""
    return get_db_connection(CONTROL_DB)


def insert_accepted_control(
    control_name: str,
    expected_sr_text: Optional[str] = None,
    platform: str = "Windows",
    app_version: Optional[str] = None,
    language: str = "en_US",
    added_by: str = "wrs",
) -> bool:
    """
    Insert an accepted control into the whitelist.
    Skips insertion if the same control_name + platform + language already exists.

    Returns:
        True if inserted, False otherwise.
    """
    connection = _get_connection()
    if not connection:
        LOGGER_ERROR("[AcceptSR] No database connection")
        return False

    try:
        _ensure_table(connection)
        with connection.cursor() as cursor:
            # Check for duplicate
            cursor.execute(
                "SELECT id FROM accepted_control_sr WHERE control_name = %s AND platform = %s AND language = %s LIMIT 1",
                (control_name, platform, language),
            )
            if cursor.fetchone():
                LOGGER_WARNING(f"[AcceptSR] Already exists: {control_name!r} ({platform}/{language})")
                return False

            cursor.execute(
                """INSERT INTO accepted_control_sr
                   (control_name, expected_sr_text, platform, app_version, language, added_by)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (control_name, expected_sr_text, platform, app_version, language, added_by),
            )
            connection.commit()
            LOGGER_INFO(f"[AcceptSR] Inserted: {control_name!r}", "GREEN")
            return True
    except pymysql.Error as e:
        LOGGER_ERROR(f"[AcceptSR] Insert failed: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()


def get_accepted_controls(platform: str = "Windows", language: str = "en_US") -> Dict[str, str]:
    """
    Fetch all accepted controls for a given platform/language.

    Returns:
        dict mapping control_name → expected_sr_text (or empty string).
    """
    connection = _get_connection()
    if not connection:
        return {}

    try:
        _ensure_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT control_name, expected_sr_text FROM accepted_control_sr WHERE platform = %s AND language = %s",
                (platform, language),
            )
            return {row[0]: (row[1] or "") for row in cursor.fetchall()}
    except pymysql.Error as e:
        LOGGER_ERROR(f"[AcceptSR] Query failed: {e}")
        return {}
    finally:
        connection.close()


def is_accepted_control(control_name: str, platform: str = "Windows", language: str = "en_US") -> bool:
    """Check if a control_name is in the accepted whitelist (substring match)."""
    accepted = get_accepted_controls(platform, language)
    if not accepted:
        return False
    # Exact match first
    if control_name in accepted:
        return True
    # Substring match — accepted key found inside the SR description
    for accepted_name in accepted:
        if accepted_name in control_name or control_name in accepted_name:
            return True
    return False


def apply_accepted_overrides(
    report_id: str,
    platform: str = "Windows",
    language: str = "en_US",
    sr_report_path: Optional[str] = None,
) -> int:
    """
    After SR analysis sync, scan ScreenReaderReport for Non-compliant entries
    and override those whose description matches an accepted control.

    Updates ScreenReaderReport.compliance, TestCaseNavigateReport.screen_reader_result,
    and the SR details report markdown file.

    Returns:
        Number of overridden entries.
    """
    from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler

    accepted = get_accepted_controls(platform, language)
    if not accepted:
        LOGGER_DEBUG("[AcceptSR] No accepted controls found, skipping override")
        return 0

    db_handler = TestCaseDBHandler()
    connection = db_handler._get_db_connection()
    if not connection:
        return 0

    override_count = 0
    overridden_steps = set()
    try:
        with connection.cursor() as cursor:
            # Fetch non-compliant entries
            cursor.execute(
                """SELECT id, step_order, description 
                   FROM ScreenReaderReport 
                   WHERE report_id = %s AND compliance LIKE '%%Non-compliant%%'""",
                (report_id,),
            )
            rows = cursor.fetchall()

            for row_id, step_order, description in rows:
                matched = False
                for accepted_name in accepted:
                    if accepted_name in (description or "") or (description or "") in accepted_name:
                        matched = True
                        break

                if matched:
                    overridden_steps.add(step_order)
                    # Update ScreenReaderReport
                    cursor.execute(
                        "UPDATE ScreenReaderReport SET compliance = %s WHERE id = %s",
                        ("✅ Accepted", row_id),
                    )
                    # Update TestCaseNavigateReport
                    cursor.execute(
                        """UPDATE TestCaseNavigateReport 
                           SET screen_reader_result = %s 
                           WHERE report_id = %s AND step_order = %s""",
                        ("✅ Accepted", report_id, step_order),
                    )
                    override_count += 1
                    LOGGER_INFO(f"[AcceptSR] Overridden step {step_order}: {description!r} → ✅ Accepted", "GREEN")

            connection.commit()

    except pymysql.Error as e:
        LOGGER_ERROR(f"[AcceptSR] Override failed: {e}")
        connection.rollback()
    finally:
        connection.close()

    if override_count:
        LOGGER_INFO(f"[AcceptSR] Total overrides: {override_count}", "GREEN")
        # Patch the SR details report markdown file
        if sr_report_path:
            _patch_sr_report_file(sr_report_path, overridden_steps)
    return override_count


def _patch_sr_report_file(sr_report_path: str, overridden_steps: set) -> None:
    """
    Patch the SR details report markdown file — replace ❌ Non-compliant
    with ☑️ Accepted for overridden step_orders.

    The SR report table has format:
    | No. | Control Name | Compliance | Suggestions | ... |
    where No. matches step_order.
    """
    import os
    import re

    if not os.path.exists(sr_report_path):
        LOGGER_WARNING(f"[AcceptSR] SR report not found: {sr_report_path}")
        return

    try:
        with open(sr_report_path, "r", encoding="utf-8") as f:
            content = f.read()

        patched = 0
        lines = content.split("\n")
        updated_lines = []
        for line in lines:
            if line.startswith("|") and "Non-compliant" in line:
                cols = line.split("|")
                # cols[0] is empty (before first |), cols[1] is No./step_order
                if len(cols) >= 4:
                    step_str = cols[1].strip()
                    try:
                        step_num = int(step_str)
                        if step_num in overridden_steps:
                            cols[3] = " ☑️ Accepted "
                            line = "|".join(cols)
                            patched += 1
                    except ValueError:
                        pass
            updated_lines.append(line)

        if patched:
            with open(sr_report_path, "w", encoding="utf-8") as f:
                f.write("\n".join(updated_lines))
            LOGGER_INFO(f"[AcceptSR] Patched {patched} entries in SR report: {sr_report_path}", "GREEN")
    except Exception as e:
        LOGGER_WARNING(f"[AcceptSR] Failed to patch SR report: {e}")

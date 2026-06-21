import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

_LOCALE = "de"  # Set the test locale here (e.g., "en", "de", "fr", etc.)
# _SESSION_PATH = Path("/Users/weiqli/testData/20260508-132415") # macOS test path
_SESSION_PATH = Path(r"C:\workF\wrs-output\weiqin-x13_PF2C5Y8N\20260508-001335")
# _SESSION_PATH = Path(r"C:\Users\yanfzhen\Downloads") / "output" # Windows test path
_SR_DB_PATH = Path(r"C:\Users\yanfzhen\Downloads\ControlINFO-schedule-DE.db") # for specific db path testing

import config.paths as _paths
_paths.SESSION_OUTPUT_PATH = _SESSION_PATH
_paths.DB_FOLDER = _SESSION_PATH / "db"
_paths.DB_NAME = {
    "ControlINFO": _paths.DB_FOLDER / "ControlINFO.db",
}
_paths.DB_PATH = globals().get("_SR_DB_PATH") or _paths.DB_NAME.get(_paths.DB_TOGGLE, _paths.DB_FOLDER / "ControlINFO.db")
_paths.LOG_PATH = _SESSION_PATH / "log"
_data = _SESSION_PATH / "data"
_paths.WINDOW_IMAGE_PATH = _data / "img" / "window"
_paths.CONTROL_IMAGE_PATH = _data / "img" / "control"
_paths.CONTROL_SCREEN_READER_DATA_PATH = _data / "control-sr"
_paths.CONTROL_NAVIGATOR_DATA_PATH = _data / "control-navigator"
_report = _SESSION_PATH / "report"
_paths.SCREEN_READER_RESULT_PATH = _report / "screen-reader"
_paths.FOCUS_RING_RESULT_PATH = _report / "focus-ring"
_paths.LOCAL_REPORT_RESULT_PATH = _report / "localization"
# ─────────────────────────────────────────────────────────────────────────────

from tools.analysis_runner import ScreenReaderAnalysisRunner, i18nAnalysisRunner
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from common.i18n.locale_utils import LocaleManager
from common.handler.settingsHandler import DynamicConfig
from common.finalizer import archive_processor, notifier
from config.paths import SETTINGS_PATH

def _setup_language():
    i18n_language = LocaleManager.normalize(_LOCALE)
    DynamicConfig(SETTINGS_PATH).set("language", i18n_language)

def test_screen_reader_runner():
    LOGGER_INFO("=== [test] ScreenReaderAnalysisRunner().run_analysis() ===")
    try:
        result = ScreenReaderAnalysisRunner().run_analysis()
        LOGGER_INFO(f"ScreenReaderAnalysisRunner result: {result}")
    except Exception as e:
        LOGGER_ERROR(f"ScreenReaderAnalysisRunner failed: {e}")
        raise


def test_i18n_runner():
    LOGGER_INFO("=== [test] i18nAnalysisRunner().run_analysis() ===")
    try:
        result = i18nAnalysisRunner().run_analysis()
        LOGGER_INFO(f"i18nAnalysisRunner result: {result}")
    except Exception as e:
        LOGGER_ERROR(f"i18nAnalysisRunner failed: {e}")
        raise


def test_full_ai_analysis():
    LOGGER_INFO("=== [test] full AI analysis flow ===")
    ScreenReaderAnalysisRunner().run_analysis()
    i18nAnalysisRunner().run_analysis()
    LOGGER_INFO("full AI analysis flow: OK")


def upload_and_notify():
    """Upload report archive and send Webex bot notification."""
    settings = DynamicConfig(SETTINGS_PATH)
    roomID = settings.botRoomId or "c0af0ac0-772f-11ef-9431-6382b932281b"
    LOGGER_INFO("=== [upload] Uploading report archive ===")
    processor = archive_processor.RemoteArchiveProcessor()
    processor.upload_archive()
    # Build report URL: match archive arcname = parent_name/folder_name
    relative_path = f"{_SESSION_PATH.parent.name}/{_SESSION_PATH.name}"
    output_url = f"{processor.web_url_e2e}/{processor.short_version}/{relative_path}"
    LOGGER_INFO(f"Result upload completed! Report URL: {output_url}")
    notifier.notify_messageBot_card(str(output_url), roomId=roomID)
    LOGGER_INFO("Bot notification sent.")
    return output_url


if __name__ == "__main__":
    _setup_language()
    test_screen_reader_runner()
    # test_i18n_runner()
    upload_and_notify()

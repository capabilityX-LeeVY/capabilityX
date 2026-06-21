import os
import platform
import tempfile

from datetime import datetime
from pathlib import Path
from config.config import DB_TOGGLE, OUTPUT_NAME
from common.utils import deviceInfo


current_os = platform.system().lower()
if current_os == 'windows':
    LOCALAPPDATA = Path(os.environ['LOCALAPPDATA'])
    if (LOCALAPPDATA / 'CiscoSparkLauncher' / 'version.txt').exists():
        APP_VERSION_PATH = LOCALAPPDATA / 'CiscoSparkLauncher' / 'version.txt'
    else:
        APP_VERSION_PATH = LOCALAPPDATA / 'CiscoSparkLauncher_arm' / 'version.txt'
    if (LOCALAPPDATA / 'CiscoSpark' / 'current_log.txt').exists():
        APP_LOG_PATH = LOCALAPPDATA / 'CiscoSpark' / 'current_log.txt'
    else:
        APP_LOG_PATH = LOCALAPPDATA / 'CiscoSpark' / 'logs'/ 'current_log.txt'
    LOCAL_REPORT_PATH = LOCALAPPDATA / 'WebexRegressSheild' / 'report' / 'navigation'
elif current_os == 'darwin':
    LOCALAPPDATA = Path.home() / 'Library' / 'Application Support'
    APP_VERSION_PATH = Path('/Applications/Webex.app/Contents/Info.plist')
elif current_os == 'linux':
    LOCALAPPDATA = Path.home() / '.local' / 'share'
    APP_VERSION_PATH = LOCALAPPDATA / 'WebexLauncher' / 'version.txt'
    APP_LOG_PATH = LOCALAPPDATA / 'webex' / 'current_log.txt'
    LOCAL_REPORT_PATH = LOCALAPPDATA / 'WebexRegressSheild' / 'report' / 'navigation'

project_name = Path(__file__).resolve().parents[2]
config_path = Path(__file__).resolve().parent
src_path = project_name / "src"
OUTPUT_BASE_PATH = project_name.parent
# OUTPUT_BASE_PATH = LOCALAPPDATA
# OUTPUT_BASE_PATH = Path(tempfile.gettempdir()) / "WebexRegressShield"

# Dynamic settings
SETTINGS_PATH = config_path / 'settings.json'
# DB settings
DB_CONFIG_PATH = config_path / 'db_config.json'
# Color settings
COLOR_CONFIG_PATH = config_path / 'color_config.json'
# openAI api key
API_KEY_PATH = config_path / 'api_key.json'

# Webex APP feature toggle configurations
FEATURE_TOGGLE_CONFIG_PATH = config_path / 'features.json'

# remote storage configuration
REMOTE_STORAGE_CONFIG_PATH = config_path / 'remote_storage.json'

# Skipped controls folder path
CONTROL_FOLDER_PATH = src_path / "config" / "skipped_controls"

# i18n status mapping
I18N_STATUS = config_path / "i18n" / "control_status.json"
I18N_TYPES = config_path / "i18n" / "control_types.json"
I18N_LOCALE = config_path / "i18n" / "locale_mapping.json"


# output_initializer = OutputInitializer()
# workflow_path = output_initializer.setup()
OUTPUT_ROOT = OUTPUT_BASE_PATH / OUTPUT_NAME

_output_path = None
def get_output_path() -> Path:
    global _output_path
    if _output_path is None:
        hostname = deviceInfo.getHostName()
        sn = deviceInfo.getSerialNumber()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        _output_path = OUTPUT_ROOT / f"{hostname}_{sn}" / timestamp
    return _output_path
SESSION_OUTPUT_PATH = get_output_path()

#Datebase path
DB_FOLDER = SESSION_OUTPUT_PATH / "db"
DB_NAME = {
    "ControlINFOBenchmark": DB_FOLDER / "ControlINFOBenchmark.db",
    "ControlINFO": DB_FOLDER / "ControlINFO.db",
}
DB_PATH=DB_NAME[DB_TOGGLE]
DATASETS_PATH = rf"src\test_space\datasets\data\ControlINFO.db"
DATASETS_SPECIFIC_PATH = rf"src\test_space\datasets\data\ControlINFO_schedule.db"

# Log path
LOG_PATH = SESSION_OUTPUT_PATH / "log"

data_path = SESSION_OUTPUT_PATH / "data"
image_path = data_path / "img"
text_path = data_path / "text"
# Window image path
WINDOW_IMAGE_PATH = image_path / "window"
# Control image path
CONTROL_IMAGE_PATH = image_path / "control"
# Fullscreen image path
FULLSCREEN_IMAGE_PATH = image_path / "fullscreen"
# Control screen reader data path
CONTROL_SCREEN_READER_DATA_PATH = data_path / "control-sr"
# Control navigator data path
CONTROL_NAVIGATOR_DATA_PATH = data_path / "control-navigator"


report_path = SESSION_OUTPUT_PATH / "report"
# Screen reader report path
SCREEN_READER_RESULT_PATH = report_path / "screen-reader"
# Focus ring result path
FOCUS_RING_RESULT_PATH = report_path / "focus-ring"
# Localization result path
LOCAL_REPORT_RESULT_PATH = report_path / "localization"
# Font size result path
FONTSIZE_RESULT_PATH = report_path / "font-size"
# Control type
CONTROL_TYPE_PATH = report_path / "control-type"
# Navigation Report Path
NAVIGATION_REPORT_PATH = report_path
# Performance Report Path
PERFORMANCE_REPORT_PATH = report_path / "performance"
# Stress Report Path  
STRESS_REPORT_PATH = report_path / "stress"
# Screen Reader Report Path
SCREEN_READER_REPORT_PATH = report_path / "screen-reader"
# UI Response Report Path
UI_RESPONSE_REPORT_PATH = report_path / "ui-response"
# Overall Report Path
OVERALL_REPORT_PATH = report_path / "overall"
# Dashboard Path
DASHBOARD_PATH = report_path / "dashboard"
# Recording Path
RECORDING_PATH = report_path / "recording"

# prompts path
PROMPTS_PATH = src_path / "prompts"

# file paths for test cases and suites
TEST_SPACE_PATH = src_path / "test_space"
TEST_CASES_PATH = TEST_SPACE_PATH / "test_cases"
TEST_SUITE_PATH = TEST_SPACE_PATH / "test_suites"
TEST_BATCHES_PATH = TEST_SPACE_PATH / "test_batch"
TEST_CONTROL_DATASET_FOLDER_PATH = TEST_SPACE_PATH / "datasets"
DATASET_IMG_FOLDER_PATH = TEST_CONTROL_DATASET_FOLDER_PATH / "img"
TEST_CASE_COMMON_SETTINGS_PATH = TEST_SPACE_PATH / "common" / "common_settings.yaml"

# Test case prompts (SR evaluation samples, etc.)
TEST_CASE_PROMPTS_PATH = TEST_SPACE_PATH / "prompts"
SR_SAMPLES_PATH = TEST_CASE_PROMPTS_PATH / "sr_samples"

# API and agent node configuration paths
TEST_FUNCTIONS_PATH = TEST_SPACE_PATH / "test_functions"
API_CONFIG_PATH = TEST_FUNCTIONS_PATH / "api_config.json"
AGENT_NODES_CONFIG_PATH = TEST_FUNCTIONS_PATH / "agent_nodes.json"
FUNCTION_CONFIG_PATH = TEST_FUNCTIONS_PATH / "function.json"

# Agent paths (formerly ChatBot)
AGENT_PATH = src_path / "agent"
AGENT_DATASETS_PATH = AGENT_PATH / "datasets"
# Keep old names for backward compatibility
CHATBOT_PATH = AGENT_PATH
CHATBOT_DATASETS_PATH = AGENT_DATASETS_PATH

# Project structure paths
PROJECT_ROOT_PATH = src_path.parent
SRC_PATH = src_path

CONTROL_DEFAULT_DATASET_PATH = TEST_CONTROL_DATASET_FOLDER_PATH / "control_datasets.json"
CONTROL_METADATA_PATH = TEST_CONTROL_DATASET_FOLDER_PATH / "control_metadata.json"
CONTROL_SPECIFIC_METADATA_PATH = TEST_CONTROL_DATASET_FOLDER_PATH / "control_specific_metadata.json"
CUSTOM_CONTROL_METADATA_PATH = TEST_CONTROL_DATASET_FOLDER_PATH / "custom_control_metadata.json"
CONTROL_DATASET_WITH_UI_PATH = CHATBOT_DATASETS_PATH / "control_datasets_with_ui_path.json"

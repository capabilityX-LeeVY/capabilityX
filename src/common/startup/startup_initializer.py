from config.paths import SETTINGS_PATH, API_KEY_PATH
from config.settingsInitializer import SettingsManager
from common.startup.output_initializer import OutputInitializer
from rs_sdk.utils.control_db import ControlDB
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_INFO
import sys


class StartupInitializer:
    _settings_initialized = False
    _set_up = False

    def __init__(self):
        if not StartupInitializer._set_up:
            self.setup()
            StartupInitializer._set_up = True

    def settings_init(self, settings_path=SETTINGS_PATH):
        if not StartupInitializer._settings_initialized:
            settings_Manager = SettingsManager(settings_path)
            settings_Manager.settingsSetUp()
            StartupInitializer._settings_initialized = True

    def setup(self):
        self.settings_init()
        settings = DynamicConfig(SETTINGS_PATH)

        if settings.onNewVersion and settings.installOptions.version in ('latest', 'eft'):
            from common.finalizer.version_tracker import AppVersionTracker
            from tools.webexApp.appHandler import get_latest_version
            version = get_latest_version()
            version_tracker = AppVersionTracker()
            app_versions = version_tracker.get_app_versions(
                version_tracker.test_mode,
                version_tracker.test_name,
                version_tracker.platform
            )
            if app_versions and version in app_versions:
                LOGGER_INFO(f"The requested version {version} has already been run")
                sys.exit(0)

        output_initializer = OutputInitializer()
        output_initializer.setup()

        local_db = ControlDB()
        local_db.db_initializer()

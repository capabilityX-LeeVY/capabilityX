from datetime import datetime
from typing import Optional
from common.utils.logger import LOGGER_DEBUG, LOGGER_ERROR
from config.mysql import ConnectToDB
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH


class AppVersionTracker:
    DB_NAME = "testcase_db"
    TABLE_NAME = "version_history"
    _CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        test_name   VARCHAR(255)   NOT NULL DEFAULT '',
        test_mode   VARCHAR(64)    NOT NULL DEFAULT '',
        app_version VARCHAR(128)   NOT NULL DEFAULT '',
        platform    VARCHAR(64)    NOT NULL DEFAULT '',
        created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """

    def __init__(self):
        self._connection = ConnectToDB(self.DB_NAME)
        if not self._connection:
            LOGGER_ERROR(f"[AppVersionTracker] Cannot connect to {self.DB_NAME}.")
            return
        
        self.settings = DynamicConfig(SETTINGS_PATH)
        self.app_version = self.settings.appVersion or '0.0.0.0'
        self.platform = self.settings.platform or 'unknown'
        self.test_case = self.settings.test_case
        self.test_suite = self.settings.test_suite
        self.test_batch = self.settings.test_batch
        if self.test_suite:
            self.test_mode = 'test_suite'
            self.test_name = self.test_suite
        elif self.test_batch:
            self.test_mode = 'test_batch'
            self.test_name = self.test_batch
        elif self.test_case:
            self.test_mode = 'test_case'
            self.test_name = self.test_case
        else:
            self.test_mode = ''
            self.test_name = ''
        if self.test_name and isinstance(self.test_name, str):
            self.test_name = self.test_name.replace('\\', '/')
        self._connection.Execute(self._CREATE_TABLE_SQL)

    def save_app_version(
        self,
    ) -> bool:
        if not self.test_mode or self.app_version == '0.0.0.0' or self.settings.installOptions.version not in ('latest', 'eft'):
            return False
        try:
            sql = f"""
                INSERT INTO {self.TABLE_NAME} (test_name, test_mode, app_version, platform)
                VALUES (%s, %s, %s, %s)
            """
            value = (self.test_name, self.test_mode, self.app_version, self.platform)
            self._connection.ExecuteWithData(sql, value)
            return True
        except Exception as e:
            LOGGER_ERROR(f"[VersionTracker] Failed to save version: {e}")
        return False

    def get_app_versions(self, test_mode: Optional[str] = None, test_name: Optional[str] = None, platform: Optional[str] = None) -> Optional[list]:
        if not self._connection:
            LOGGER_ERROR("[VersionTracker] No database connection.")
            return None
        try:
            sql = f"SELECT app_version FROM {self.TABLE_NAME} WHERE 1=1"
            params = []
            if test_mode:
                sql += " AND test_mode = %s"
                params.append(test_mode)
            if test_name:
                sql += " AND test_name = %s"
                params.append(test_name)
            if platform:
                sql += " AND platform = %s"
                params.append(platform)
            sql += " ORDER BY created_at"
            results, columns = self._connection.QueryWithData(sql, tuple(params))
            return [row[0] for row in results] if results else None
        except Exception as e:
            return None
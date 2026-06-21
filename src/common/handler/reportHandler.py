import os
from config.paths import SETTINGS_PATH, APP_VERSION_PATH
from common.handler.settingsHandler import DynamicConfig
from common.utils import deviceInfo
from common.utils.logger import LOGGER_ERROR
from common.handler import fileHandler
from common.utils import generatelogs


def _generateNavigationReport(settings):
    osInfo = settings.get('osInfo')
    appVersion = settings.get('appVersion')
    qtVersion = settings.get('installOptions', 'qtversion')
    
    report_file_path = os.path.expandvars(
        os.path.join('%LOCALAPPDATA%', 'WebexRegressSheild', 'report', 'navigation', f'acc-navigation-report-QT{qtVersion}-{appVersion}.md')
    )
    navigation_report_file_path = fileHandler.getFilePath(report_file_path)

    with open(navigation_report_file_path, 'w') as file:
        file.write(f"# WebEx APP Meetings Accessibility Report [{osInfo}] [Version: {appVersion}] [qtVersion: {qtVersion}]\n\n")
        file.write("| Tab Order | Project ID  | Process ID  | Description  | Control Localized Type | IsEnabled | IsKeyboardFocusable | HasKeyboardFocus | default action | keyboard action | result |\n")
        file.write("|-----------|-------------|-------------|--------------|------------------------|-----------|---------------------|------------------|----------------|-----------------|--------|\n")    

    return navigation_report_file_path

def setBasicInfo():
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

def initializeReport():
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

    report_file_path = _generateNavigationReport(settings)
    generatelogs.setup_logging(report_file_path)
    return report_file_path

class reportTopicManager:
    def __init__(self, settings):
        self.settings = settings

    def setInfo(self):
        os_info = deviceInfo.getOSInfo()
        app_version = self.getAppInfo()
        self.saveInfo(os_info, app_version)

    def getAppInfo(self):
        app_version = fileHandler.readFile(APP_VERSION_PATH)
        return app_version

    def saveInfo(self, os_info, app_version):
        self.settings.set('appVersion', app_version)
        self.settings.set('osInfo', os_info)
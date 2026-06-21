import pythoncom
import time
import os

from common.startup.startup_initializer import StartupInitializer
from common.utils.featureToggle import FeatureToggle
from config.config import JOIN_A_MEETING_AUTOID,CALLWINDOWAUTOID,START_JOIN_BUTTON, MAINWINDOW, MAINWINDOW_QT68, JOIN_A_MEETING_AUTOID_QT68
from config.paths import FEATURE_TOGGLE_CONFIG_PATH
from core.explorer_base import ExplorerBase
from rs_sdk.utils.control_handler import ControlHandler
from rs_sdk.utils.event_listener import FocusListener
from rs_sdk.utils.control import Control
from rs_sdk.utils.control_db import ControlDB
from common.finalizer import output_runner
from common.utils.logger import LOGGER_INFO
from tools.analysis_runner import NavigatorAnalysisRunner

class ControlExplorerRunner:
    def __init__(self):
        StartupInitializer()
        if Control.toggle_listener:
            listener = FocusListener()
            listener.start()
            time.sleep(1)
        Control.toggle_listener = True
        FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)

    def run(self):
        
        if FeatureToggle.isEnabled('installer'):
            from tools.webexApp import appHandler
            appHandler.installWebex()
            time.sleep(5)

        self.control_handler = ControlHandler()
        self.control_handler.focus_on_webex_agreement_window()

        # for debugging meetings window
        # self.control_handler.focus_on_meeting_main_window()
        # pid = self.control_handler.get_pid_by_name()
        # self.control_handler.focus_on_window_by_pid(pid,JOIN_A_MEETING_AUTOID)
        # self.control_handler.focus_on_window_by_pid(pid, JOIN_A_MEETING_AUTOID_QT68, MAINWINDOW_QT68)

        self.explorer = ExplorerBase()
        self.explorer.explorer_base()

        output_runner.build_output()
        self.navigator_analyze = NavigatorAnalysisRunner()
        report_file_path = self.navigator_analyze.run_analysis()
        self.navigator_analyze.create_jira(report_file_path)

        control_db = ControlDB()
        control_db.upload_local_control_info_to_database()
        LOGGER_INFO("Run workflow complete.")

if __name__ == '__main__':  
    pythoncom.CoInitialize()
    explorer_runner = ControlExplorerRunner()
    explorer_runner.run()

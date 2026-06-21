import os
import pandas as pd

from pathlib import Path
from typing import Union, Optional
from config.paths import DB_PATH, CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH, LOCAL_REPORT_RESULT_PATH, WINDOW_IMAGE_PATH
from common.utils.featureToggle import FeatureToggle
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR
from core.processor.focus_processor import FocusRingProcessor
from core.processor.bug_processor import BugProcessor
from report.focus_ring.sync_workflow_accessibility_data import FocusRingDataSync
from tools.Jira.reportParserToJira import CReportParserToJira
from core.processor.srText_processor import ScreenReaderDataProcessor
from core.processor.navigator_processor import NavigatorDataProcessor


class FocusRingAnalysisRunner:
    def __init__(self, control_image_path=CONTROL_IMAGE_PATH, result_path=FOCUS_RING_RESULT_PATH):
        self.image_path = control_image_path
        self.result_path = result_path
        self.fr_detector = FocusRingProcessor(self.image_path, self.result_path)

    def run_analysis(self):
        LOGGER_INFO("Start to analyze focus ring...")
        onfocus_md = self.fr_detector.validate_onFocus_controls()
        lostfocus_md = self.fr_detector.validate_onFocusLost_controls()
        md_files = [onfocus_md, lostfocus_md]
        valid_md_files = [Path(f) for f in md_files if f and Path(f).exists()]
        LOGGER_INFO(f"Focus ring analysis completed. Valid reports: {[f.name for f in valid_md_files]}")

        fr_data_sync = FocusRingDataSync(valid_md_files)
        fr_data_sync.sync_data()
        
        return valid_md_files
    

    def create_jira(self, report_files: Optional[Union[str, Path, list[Union[str, Path]]]] = None):
        if not report_files:
            LOGGER_WARNING("No report file(s) provided to create_jira()")
            return
        if isinstance(report_files, (str, Path)):
            report_files = [report_files]
        for report_file in report_files:
            if not report_file:
                continue
            report_file = Path(report_file)
            if not report_file.exists():
                LOGGER_WARNING(f"File does not exist: {report_file}")
                continue
            fr_jira = CReportParserToJira(report_file, issueType="Focus Ring")
            fr_jira.ParserReportAndFileBugs()
            LOGGER_INFO(f"Processing file: {report_file.name}")

class ScreenReaderAnalysisRunner:
    def __init__(self, windows_db = DB_PATH):
        self.processor = ScreenReaderDataProcessor(windows_db)
        from report.accessibility.sr_report_generator import SrReportGenerator
        self.sr_report_generator = SrReportGenerator()

    def run_analysis(self):
        LOGGER_INFO("Start to extract screen reader data...")
        self.processor.get_screen_reader_data()
        LOGGER_INFO("Screen reader data extraction completed.")
        LOGGER_INFO("Start to analyze screen reader...")
        md_file = self.sr_report_generator.run()
        LOGGER_INFO("Screen reader analysis completed.")
        return md_file

    def create_jira(self, report_file=None):
        if not report_file or not os.path.exists(report_file):
            LOGGER_WARNING("No valid report file provided to create_jira()")
            return
        sr_jira = CReportParserToJira(report_file, issueType="Screen Reader")
        sr_jira.ParserReportAndFileBugs()
        LOGGER_INFO(f"Processing file: {report_file.name}")

class BugAnalysisRunner:
    def __init__(self):
        self.bug_processor = BugProcessor()

    def run_analysis(self):
        self.bug_processor.process()
class i18nAnalysisRunner:
    def __init__(self, window_image_path=WINDOW_IMAGE_PATH, result_path=LOCAL_REPORT_RESULT_PATH):
        self.image_path = window_image_path
        self.result_path = result_path
        from report.accessibility.i18n_analyzer import I18nAnalyzer
        from report.accessibility.i18n_report_generator import I18nReportGenerator
        self.i18n_analyzer = I18nAnalyzer()
        self.i18n_report = I18nReportGenerator(self.result_path)

    def run_analysis(self):
        if self.image_path is None or not os.path.exists(self.image_path):
            LOGGER_WARNING(f"Image path does not exist: {self.image_path}")
            return None
        
        LOGGER_INFO("Start to analyze i18n localization...")
        self.i18n_analyzer.analyze_images(self.image_path, self.result_path)
        self.i18n_analyzer.format_markdown_file(self.result_path)
        md_file = self.i18n_analyzer.remove_duplicate_rows(self.result_path)
        return md_file

    def create_jira(self, report_file=None):
        if not report_file or not os.path.exists(report_file):
            LOGGER_WARNING("No valid report file provided to create_jira()")
            return
        i18n_jira = CReportParserToJira(report_file, issueType="i18n")
        i18n_jira.ParserReportAndFileBugs()
        LOGGER_INFO(f"Processing file: {report_file.name}")

class NavigatorAnalysisRunner:
    def __init__(self, windows_db = DB_PATH):
        self.processor = NavigatorDataProcessor(windows_db)

    def run_analysis(self):
        output_path = self.processor.process_data()
        return output_path

    def create_jira(self, report_file=None):
        if not report_file or not os.path.exists(report_file):
            LOGGER_WARNING("No valid report file provided to create_jira()")
            return
        nv_jira = CReportParserToJira(report_file, issueType="Navigator")
        nv_jira.ParserReportAndFileBugs()
        LOGGER_INFO(f"Processing file: {report_file.name}")

if __name__ == "__main__":
    fr_runner = FocusRingAnalysisRunner()
    md_files = fr_runner.run_analysis()
    fr_runner.create_jira([str(f) for f in md_files])

    ScreenReaderAnalysisRunner().run_analysis()
    BugAnalysisRunner().run_analysis()
    i18n_runner = i18nAnalysisRunner()
    md_file = i18n_runner.run_analysis()
    i18n_runner.create_jira(md_file)

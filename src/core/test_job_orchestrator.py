"""
test_job_orchestrator.py

Orchestrates the complete test job workflow including test execution, 
screen reader analysis, performance analysis, and result upload.
"""

import os
import yaml
from common.startup.startup_initializer import StartupInitializer
from common.utils.featureToggle import FeatureToggle
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_WARNING, LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR
from rs_sdk.utils.model_handler import ModelHandler
from common.finalizer import archive_processor, notifier
from core.processor.focus_processor import FocusRingProcessor
from core.test_case_runner import TestCaseRunner
from core.managers.report_manager import ReportManager
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
from tools.Jira.jira_handler import JiraHandler
from common.utils.video_recorder import start_test_recording, stop_test_recording
from common.finalizer.notification_router import (
    get_notification_room_ids,
    DEFAULT_WINDOWS_ROOM,
    PROMOTE_BLUE_ROOM
)
from config.paths import (
    FEATURE_TOGGLE_CONFIG_PATH,
    CONTROL_IMAGE_PATH,
    FOCUS_RING_RESULT_PATH,
    REMOTE_STORAGE_CONFIG_PATH,
    OUTPUT_ROOT,
    OVERALL_REPORT_PATH,
    TEST_SUITE_PATH
)


class TestJobOrchestrator:
    """
    Orchestrates the complete test job workflow.
    
    This class coordinates the execution of:
    1. Test suites/cases
    2. Screen reader analysis
    3. Performance analysis
    4. UI response report generation
    5. Focus ring detection
    6. Overall report generation
    7. Result upload
    8. Notification with execution result summary
    """
    
    def __init__(self):
        # Check if StartupInitializer has already been called to avoid overwriting settings
        from config.paths import SETTINGS_PATH
        import os
        
        # Only call StartupInitializer if settings file doesn't exist or platform is not set
        if not os.path.exists(SETTINGS_PATH):
            LOGGER_DEBUG(f"🔧 [ORCHESTRATOR] Calling StartupInitializer for first-time setup")
            StartupInitializer()
            settings_config = DynamicConfig(SETTINGS_PATH)
        else:
            settings_config = DynamicConfig(SETTINGS_PATH)
            if not settings_config.get('platform'):
                LOGGER_DEBUG(f"🔧 [ORCHESTRATOR] Calling StartupInitializer - platform not configured")
                StartupInitializer()
                settings_config = DynamicConfig(SETTINGS_PATH)
            else:
                LOGGER_DEBUG(f"🔧 [ORCHESTRATOR] StartupInitializer already called, skipping to preserve settings")
            
        FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
        
        # Import settings AFTER initialization is complete
        from config.global_settings import settings
        self.settings = settings
        self.remote_storage = DynamicConfig(REMOTE_STORAGE_CONFIG_PATH)
        
        # Extract settings (auto-initialized with latest values from StartupInitializer)
        self.test_suite = self.settings.test_suite
        self.test_case = self.settings.test_case
        self.test_batch = self.settings.test_batch
        self.mode = self.settings.mode
        self.openai = self.settings.openai
        self.recording = self.settings.recording
        LOGGER_INFO(f"[ORCHESTRATOR][Init] Test Suite: {self.test_suite}, Test Case: {self.test_case}, Test Batch: {self.test_batch}, Mode: {self.mode}, OpenAI: {self.openai}, Recording: {self.recording}")

        
        # Initialize components - get platform from settings
        platform = settings_config.get('platform', default='windows')
        self.test_runner = TestCaseRunner(platform=platform)
        self.fr_detector = FocusRingProcessor(CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH)
        
        # Initialize report manager for test result summary
        db_handler = TestCaseDBHandler()
        self.report_manager = ReportManager(db_handler)
    
    def run_screen_reader_analysis(self, report_id=None, test_suite=None, navigate_report_path=None, sr_enabled_cases=None, sr_prompt_path=None):
        """
        Run screen reader analysis using ModelHandler
        
        Args:
            report_id: Report ID to analyze
            test_suite: Test suite name
            navigate_report_path: Path to navigation report markdown file for regeneration
            sr_enabled_cases: List of test case names that have Screen Reader enabled.
                              If None, all cases are analyzed. If provided, only matching cases are analyzed.
            sr_prompt_path: Relative path to area-specific SR prompt samples file
        
        Returns:
            str: Path to the screen reader report file, or None if failed
        """
        LOGGER_INFO("Running screen reader analysis...", "CYAN")
        if sr_enabled_cases is not None:
            LOGGER_INFO(f"Screen reader analysis limited to cases: {sr_enabled_cases}", "CYAN")
        
        model_handler = ModelHandler()
        result = model_handler.handle_screen_reader_analysis(
            report_id=report_id, 
            test_suite=test_suite,
            sr_enabled_cases=sr_enabled_cases,
            sr_prompt_path=sr_prompt_path
        )
        
        if result['success']:
            LOGGER_INFO("Screen reader analysis completed successfully!", "GREEN")
            LOGGER_INFO(f"Report saved to: {result['report_path']}", "GREEN")
            
            # If sync was successful and navigate_report_path is provided, regenerate the navigation report
            if result.get('sync_success') and navigate_report_path:
                LOGGER_INFO("Regenerating navigation report with screen reader results...", "CYAN")
                regen_success = self.report_manager.regenerate_navigate_report_with_screen_reader(
                    navigate_report_path=navigate_report_path,
                    report_id=report_id,
                    sr_report_path=result.get('report_path')
                )
                if regen_success:
                    LOGGER_INFO("Navigation report successfully regenerated with screen reader data!", "GREEN")
                else:
                    LOGGER_WARNING("Failed to regenerate navigation report", "YELLOW")
            
            return result.get('report_path')
        else:
            LOGGER_WARNING(f"Screen reader analysis failed: {result.get('error', 'Unknown error')}", "YELLOW")
            return None
    
    def run_i18n_analysis(self, report_id=None, test_suite=None, test_case=None):
        """Run i18n analysis using ModelHandler"""
        LOGGER_INFO("Running i18n analysis...", "CYAN")
        
        model_handler = ModelHandler()
        result = model_handler.handle_i18n_analysis(
            report_id=report_id, 
            test_suite=test_suite,
            test_case=test_case
        )
        
        if result:
            LOGGER_INFO("i18n analysis completed successfully!", "GREEN")
            LOGGER_INFO(f"Report saved to: {result['report_path']}", "GREEN")
        else:
            LOGGER_WARNING(f"i18n analysis failed: {result}", "YELLOW")
        
        return result
    
    def run_performance_analysis(self, performance_report_path):
        """Run performance data analysis"""
        LOGGER_INFO("Analyzing performance data...", "CYAN")
        
        if not os.path.exists(performance_report_path):
            LOGGER_WARNING("Performance report not found", "YELLOW")
            return {'success': False, 'error': 'Report file not found'}
        
        try:
            model_handler = ModelHandler()
            result = model_handler.handle_analyze_performance(performance_report_path)
            
            if result['success']:
                LOGGER_INFO("Performance analysis completed successfully!", "GREEN")
            else:
                LOGGER_WARNING(f"Performance analysis failed: {result.get('error', 'Unknown error')}", "YELLOW")
            
            return result
        except Exception as e:
            LOGGER_WARNING(f"Performance analysis failed with exception: {str(e)}", "YELLOW")
            return {'success': False, 'error': str(e)}
    
    def generate_ui_response_report(self):
        """Generate UI response time report if UI response data exists"""
        try:
            from config.paths import UI_RESPONSE_REPORT_PATH
            from common.handler.ui_response_report_handler import UIResponseReportHandler
            
            # Check if UI response feature is available
            db_handler = TestCaseDBHandler()
            report_handler = UIResponseReportHandler(db_handler)
            
            # Ensure UI response report directory exists
            UI_RESPONSE_REPORT_PATH.mkdir(parents=True, exist_ok=True)
            
            # Generate report with current report_id if available
            from common.handler.report_id_generator import report_id_generator
            current_report_id = getattr(report_id_generator, 'global_report_id', None)
            
            # Set report file name with timestamp for uniqueness
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            report_filename = f"ui_response_report_{timestamp}.md"
            output_path = UI_RESPONSE_REPORT_PATH / report_filename
            
            LOGGER_INFO(f"Generating UI response report: {output_path}")
            success = report_handler.generate_ui_response_report(
                str(output_path), 
                report_id=current_report_id
            )
            
            if success:
                LOGGER_INFO(f"✅ UI response report generated successfully: {output_path}", "GREEN")
            else:
                LOGGER_INFO("ℹ️ No UI response data found for report generation", "YELLOW")
                
        except Exception as e:
            LOGGER_WARNING(f"UI response report generation failed: {str(e)}", "YELLOW")
    
    def run_focus_ring_detection(self):
        """Run focus ring detection if enabled"""
        if FeatureToggle.isEnabled('croppedImage'):
            LOGGER_INFO("Running focus ring detection...", "CYAN")
            self.fr_detector.validate_onFocus_controls()
            LOGGER_INFO("Focus ring detection completed", "GREEN")
        else:
            LOGGER_INFO("Focus ring detection skipped (disabled)", "YELLOW")
    
    def generate_overall_report(self):
        """Generate overall test report"""
        try:
            from rs_sdk.utils.overall_report_generator import OverallReportGenerator
            
            LOGGER_INFO("Generating overall test report...", "CYAN")
            generator = OverallReportGenerator()
            
            # Generate report for current session
            result = generator.generate_overall_report()
            
            if result['success']:
                LOGGER_INFO(f"Overall report generated successfully: {result['file_path']}", "GREEN")
                LOGGER_INFO(f"Test cases processed: {result['test_cases_count']}", "CYAN")
            else:
                LOGGER_WARNING(f"Overall report generation failed: {result.get('error', 'Unknown error')}", "YELLOW")
            
            return result
            
        except Exception as e:
            LOGGER_WARNING(f"Overall report generation failed with exception: {str(e)}", "YELLOW")
            return {'success': False, 'error': str(e)}
    
    def upload_results(self):
        """Upload test results if enabled"""
        if not FeatureToggle.isEnabled('upload_output'):
            LOGGER_INFO("Result upload skipped (disabled)", "YELLOW")
            return None
        
        LOGGER_INFO("Uploading test results...", "CYAN")
        try:
            upload_processor = archive_processor.RemoteArchiveProcessor()
            upload_processor.upload_archive()
            output_url = upload_processor.get_report_url(GT=True)
            LOGGER_INFO("Result upload completed successfully!", "GREEN")
            return output_url
        except Exception as e:
            LOGGER_WARNING(f"Result upload failed: {str(e)}", "YELLOW")
            return None

    def send_notification_with_summary(self, output_url):
        """
        Step 6: Send notification with execution result summary.
        
        Args:
            output_url (str): URL of uploaded results
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not output_url:
            LOGGER_INFO("Notification skipped (no output URL)", "YELLOW")
            return False
        
        LOGGER_INFO("Sending notification with test result summary...", "CYAN")
        try:
            # Get overall report summary
            report_summary = self.report_manager.get_overall_report_summary()
            execution_result = report_summary['result_summary']
            
            # Extract detailed failure counts
            llm_failures = report_summary['llm_fail_count']
            nav_failures = report_summary['navigate_fail_count']
            focus_ring_failures = report_summary['focus_ring_fail_count']
            screen_reader_failures = report_summary['screen_reader_fail_count']
            
            LOGGER_INFO(f"Execution Result: {execution_result}", "CYAN")
            LOGGER_INFO(f"LLM Failures: {llm_failures}, Navigate Failures: {nav_failures}, Focus Ring Failures: {focus_ring_failures}, Screen Reader Failures: {screen_reader_failures}", "CYAN")
            
            # Get JIRA open issue count
            jira_open_count = None
            try:
                LOGGER_INFO("Getting JIRA open issue count...", "CYAN")
                open_issue_jql = 'labels = WebexRegressSheild and issuetype = Bug and status in (Open, New, "In Progress")'
                jira_result = JiraHandler.count_issues_by_jql(open_issue_jql)
                if jira_result:
                    jira_open_count = jira_result['total_issues']
                    LOGGER_INFO(f"JIRA Open Issues: {jira_open_count}", "CYAN")
                else:
                    LOGGER_WARNING("Failed to get JIRA open issue count", "YELLOW")
            except Exception as jira_e:
                LOGGER_WARNING(f"Failed to get JIRA open issue count: {str(jira_e)}", "YELLOW")
            
            settings_room_id = getattr(self.settings, 'botRoomId', None) or None
            default_room = PROMOTE_BLUE_ROOM if self.test_suite == "promote_blue_channel" else DEFAULT_WINDOWS_ROOM
            target_room_ids = get_notification_room_ids(
                settings_room_id, self.mode, self.test_case, self.test_suite, self.test_batch, default_room
            )
            LOGGER_INFO(f"Sending notification to rooms: {target_room_ids}", "CYAN")

            for room_id in target_room_ids:
                notifier.notify_messageBot_card(
                    report_url=str(output_url),
                    execution_result=execution_result,
                    jira_open_count=jira_open_count,
                    llm_failures=llm_failures,
                    nav_failures=nav_failures,
                    focus_ring_failures=focus_ring_failures,
                    screen_reader_failures=screen_reader_failures,
                    roomId=room_id
                )
            
            # Send @mention message to owner only if there are failures
            if execution_result and "FAIL" in execution_result.upper():
                owner_email = self._get_suite_owner_email()
                if owner_email:
                    from tools.MessageBot import BotMessage
                    mention_message = f"<@personEmail:{owner_email}|> Please review the test results above"
                    for room_id in target_room_ids:
                        BotMessage.sendMessageToTeams(mention_message, room_id)
                    LOGGER_INFO(f"Mention sent to owner due to test failures: {owner_email}", "CYAN")
                else:
                    LOGGER_WARNING("Could not get owner email from suite YAML", "YELLOW")
            else:
                LOGGER_INFO("No failures detected, mention to owner skipped", "CYAN")
            
            LOGGER_INFO("Notification sent successfully!", "GREEN")
            return True
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to send notification with summary: {str(e)}", "YELLOW")
            
            # Fallback to simple notification without execution result
            try:
                settings_room_id = getattr(self.settings, 'botRoomId', None) or None
                default_room = PROMOTE_BLUE_ROOM if self.test_suite == "promote_blue_channel" else DEFAULT_WINDOWS_ROOM
                target_room_ids = get_notification_room_ids(
                    settings_room_id, self.mode, self.test_case, self.test_suite, self.test_batch, default_room
                )
                for room_id in target_room_ids:
                    notifier.notify_messageBot_card(str(output_url), roomId=room_id)
                LOGGER_INFO("Fallback notification sent (without execution result)", "YELLOW")
                return True
            except Exception as fallback_e:
                LOGGER_WARNING(f"Fallback notification also failed: {str(fallback_e)}", "RED")
                return False

    def _get_suite_owner_email(self):
        """
        Get owner email from test suite YAML file.
        
        Returns:
            str: Owner email (owner@cisco.com), or None if not found
        """
        try:
            import yaml
            from config.paths import TEST_SUITE_PATH
            
            suite_file = TEST_SUITE_PATH / f"{self.test_suite}.yaml"
            
            if not suite_file.exists():
                LOGGER_WARNING(f"Test suite file not found: {suite_file}", "YELLOW")
                return None
            
            with open(suite_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            owner = data.get('test_suite', {}).get('owner', None)
            if owner:
                # Format as Cisco email
                owner_email = f"{owner}@cisco.com"
                LOGGER_INFO(f"Suite owner email: {owner_email}", "CYAN")
                return owner_email
            else:
                LOGGER_WARNING("Owner field not found in suite YAML", "YELLOW")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get owner email from suite YAML: {str(e)}", "RED")
            return None

    def run_complete_workflow(self, test_suite=None, mode=None, progress_callback=None):
        """
        Execute the complete test job workflow.
        
        Args:
            test_suite (str): Test suite name (optional, uses settings default if not provided)
            mode (str): Execution mode ('suite', 'case', or 'batch')
            
        Returns:
            str: URL of uploaded results (if upload is enabled)
        """
        LOGGER_INFO("=" * 60, "BLUE")
        LOGGER_INFO("[Beginning] Start Test Job Workflow", "BLUE")
        LOGGER_INFO("=" * 60, "BLUE")
        
        # Use provided parameters or fall back to settings values
        current_test_suite = test_suite or self.test_suite
        current_mode = mode or self.mode
        
        # Update settings to reflect the actual execution parameters
        # This ensures all subsequent components use the correct values
        if test_suite and test_suite != self.test_suite:
            self.settings.set('test_suite', test_suite)
            self.test_suite = test_suite
            LOGGER_DEBUG(f"Updated test_suite setting to: {test_suite}")
        
        if mode and mode != self.mode:
            self.settings.set('mode', mode)
            self.mode = mode
            LOGGER_DEBUG(f"Updated mode setting to: {mode}")
        
        # Determine what to run based on mode
        if current_mode == "case":
            # For test case mode, use test_case setting or provided test_suite
            target_name = current_test_suite or self.test_case
        elif current_mode == "batch":
            # For test batch mode, use test_batch setting or provided test_suite  
            target_name = current_test_suite or self.test_batch
        else:
            # For test suite mode, use test_suite setting or provided test_suite
            target_name = current_test_suite
        
        # Step 1: Execute test suite/case
        LOGGER_INFO("[ORCHESTRATOR][Init] Executing test suite/case...", "CYAN")
        LOGGER_INFO(f"[ORCHESTRATOR][Init] Test Name: {target_name}, Mode: {current_mode}", "CYAN")
        # Start video recording (if enabled)
        if self.recording:
            LOGGER_INFO("[ORCHESTRATOR][Init] Starting video recording...", "GREEN")
            start_test_recording()
        
        try:
            result = self.test_runner.run_test_suite(
                target_name, 
                mode=current_mode,
                progress_callback=progress_callback
            )
            
            # Handle different return formats
            navigate_report_path = None
            performance_report_path = None
            stress_report_path = None
            check_points = None
            
            sr_enabled_cases = None
            sr_prompt_path = None
            if result is not None and isinstance(result, tuple):
                if len(result) >= 2:
                    navigate_report_path = result[0]
                    performance_report_path = result[1]
                if len(result) >= 3:
                    stress_report_path = result[2]
                if len(result) >= 4:
                    check_points = result[3]
                if len(result) >= 5:
                    sr_enabled_cases = result[4]
                if len(result) >= 6:
                    sr_prompt_path = result[5]
        finally:
            # Stop video recording (if enabled)
            if self.recording:
                LOGGER_INFO("Stopping video recording...", "GREEN")
                stop_test_recording()
        
        LOGGER_INFO("Test execution completed", "GREEN")
        
        # Determine if Screen Reader check point is enabled
        enable_screen_reader = False
        if check_points is None:
            # No check_points defined - default to enabled for backward compatibility
            enable_screen_reader = True
            LOGGER_DEBUG("No check_points defined, Screen Reader enabled by default")
        elif 'Screen Reader' in check_points:
            enable_screen_reader = True
            LOGGER_DEBUG(f"Screen Reader check point found in: {check_points}")
        else:
            LOGGER_DEBUG(f"Screen Reader check point not found in: {check_points}")
        
        # Step 2: Screen reader analysis (if Screen Reader check point is enabled)
        screen_reader_report_path = None
        if enable_screen_reader:
            LOGGER_INFO("Step 2: Running screen reader analysis...", "CYAN")
            sr_test_suite = f"sr_{target_name}_job"
            screen_reader_report_path = self.run_screen_reader_analysis(
                test_suite=sr_test_suite,
                navigate_report_path=navigate_report_path,  # Pass navigate_report_path for regeneration
                sr_enabled_cases=sr_enabled_cases,  # Only analyze cases with Screen Reader check point
                sr_prompt_path=sr_prompt_path  # Area-specific SR prompt samples
            )
        else:
            LOGGER_INFO("Step 2: Screen reader analysis skipped (Screen Reader check point disabled)", "YELLOW")
        
        # Step 3: Performance analysis (if AI enabled and report available)
        # if self.openai and performance_report_path:
        #     LOGGER_INFO("Step 3: Running performance analysis...", "CYAN")
        #     self.run_performance_analysis(performance_report_path)
        # else:
        #     if not self.openai:
        #         LOGGER_INFO("Step 3: Performance analysis skipped (AI disabled)", "YELLOW")
        #     else:
        #         LOGGER_INFO("Step 3: Performance analysis skipped (no report)", "YELLOW")
        
        # Step 4: Generate UI response report (if any UI response data exists)
        # LOGGER_INFO("Step 4: Generating UI response report...", "CYAN")
        # self.generate_ui_response_report()
        
        # Step 5: Focus ring detection
        # LOGGER_INFO("Step 5: Running focus ring detection...", "CYAN")
        # self.run_focus_ring_detection()
        
        # Step 6: Generate overall report
        LOGGER_INFO("Step 6: Generating overall test report...", "CYAN")
        self.generate_overall_report()
        
        # Step 7: Upload results
        LOGGER_INFO("Step 7: Uploading test results...", "CYAN")
        output_url = self.upload_results()
        # Save the report URL for external access
        self._last_report_url = output_url
        
        # Step 8: Send notification with execution result summary
        LOGGER_INFO("Step 8: Sending notification with summary...", "CYAN")
        self.send_notification_with_summary(output_url)
        
        # Summary
        LOGGER_INFO("=" * 60, "BLUE")
        LOGGER_INFO("Complete Test Job Workflow Finished", "BLUE")
        if output_url:
            LOGGER_INFO(f"Test Report URL: {output_url}   ", "GREEN")
        if screen_reader_report_path:
            LOGGER_INFO(f"Screen Reader Report: {screen_reader_report_path}", "GREEN")
        LOGGER_INFO("=" * 60, "BLUE")
        
        return navigate_report_path, screen_reader_report_path
    
    def run_test_only(self, test_suite=None):
        """
        Execute only the test suite/case without additional workflow steps.
        
        Args:
            test_suite (str): Test suite name (optional)
            
        Returns:
            tuple: (navigate_report_path, performance_report_path)
        """
        current_test_suite = test_suite or self.test_suite
        return self.test_runner.run_test_suite(current_test_suite, mode=self.mode)

    def get_report_url(self):
        """
        Get the last generated report URL.
        
        Returns:
            str: The report URL if available, None otherwise
        """
        return getattr(self, '_last_report_url', None)

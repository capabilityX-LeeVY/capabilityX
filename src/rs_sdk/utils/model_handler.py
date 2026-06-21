import os
from models.openai_client import OpenAIClient
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

from rs_sdk.utils.report_handler import write_screen_reader_report, append_analysis_to_report

class ModelHandler:
    def __init__(self):
        pass
    
    def handle_ai_check_report(self, reference_image_url, image_url, message=None):
        client = OpenAIClient()
        if reference_image_url is not None:
            llm_response = client.ai_analyze_image_comparison(reference_image_url, image_url, message=message)
        else:
            llm_response = client.ai_analyze_image(image_url, message=message)

        return llm_response
    
    def handle_screen_reader_analysis(self, report_id=None, test_suite=None, test_case=None, sr_enabled_cases=None, sr_prompt_path=None):
        """
        Handle screen reader data analysis with AI
        
        Args:
            report_id (str, optional): Specific report ID to analyze. If None, uses current report_id
            test_suite (str, optional): Test suite name for report file naming. Defaults to 'sr_analysis'
            test_case (str, optional): Test case name. If None, uses test_suite as test_case
            sr_enabled_cases (list, optional): List of test case names that have Screen Reader enabled.
                                               If None, all cases are analyzed.
            sr_prompt_path (str, optional): Relative path to area-specific SR prompt samples file
                                            (e.g. "sr_samples/calling_sr_wcag_evaluation.md").
                                            Loaded from TEST_CASE_PROMPTS_PATH.
        
        Returns:
            dict: Analysis result containing file_path, report_path, and analysis_result
        """
        try:
            # Get report_id
            from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
            from core.processor.srText_processor import ScreenReaderDataProcessor
            
            db_handler = TestCaseDBHandler()
            if report_id is None:
                report_id = db_handler.get_current_report_id()
            
            LOGGER_INFO(f"Starting screen reader analysis for report_id: {report_id}", "BLUE")
            
            # Step 1: Process screen reader data
            srText_processor = ScreenReaderDataProcessor()
            file_name_path = srText_processor.get_screen_reader_data_for_cloud(report_id, sr_enabled_cases=sr_enabled_cases)
            
            if not file_name_path:
                LOGGER_WARNING("No screen reader data file found", "YELLOW")
                return {
                    'success': False,
                    'error': 'No screen reader data file found',
                    'report_id': report_id
                }
            
            if not os.path.exists(file_name_path):
                LOGGER_ERROR(f"Screen reader data file not found: {file_name_path}", "RED")
                return {
                    'success': False,
                    'error': f'File not found: {file_name_path}',
                    'report_id': report_id
                }
            
            LOGGER_INFO(f"Screen reader data file: {file_name_path}", "GREEN")
            
            # Step 2: Analyze with OpenAI
            # Load base SR analysis prompt + area-specific samples
            sr_prompt = None
            try:
                from prompts.prompt_loader import load_prompt
                from config.paths import TEST_CASE_PROMPTS_PATH
                sr_prompt = load_prompt('sr_wcag_evaluation.md')
                
                # Priority 1: Use explicit sr_prompt_path from test case YAML
                # Priority 2: Auto-match by test_case name keyword
                samples_loaded = False
                if sr_prompt_path:
                    samples_file = TEST_CASE_PROMPTS_PATH / sr_prompt_path
                    if samples_file.exists():
                        with open(samples_file, 'r', encoding='utf-8') as f:
                            samples = f.read()
                        sr_prompt = f"{sr_prompt}\n\n{samples}"
                        LOGGER_INFO(f"Loaded SR samples from test case config: {sr_prompt_path}", "CYAN")
                        samples_loaded = True
                    else:
                        LOGGER_WARNING(f"SR samples file not found: {samples_file}", "YELLOW")
                
                if not samples_loaded:
                    # Fallback: auto-match area-specific samples based on test_case name
                    area_keywords = ['calling', 'meeting', 'messaging', 'settings', 'spaces']
                    matched_area = None
                    tc_lower = (test_case or test_suite or '').lower()
                    for keyword in area_keywords:
                        if keyword in tc_lower:
                            matched_area = keyword
                            break
                    
                    if matched_area:
                        samples_file = TEST_CASE_PROMPTS_PATH / "sr_samples" / f"{matched_area}_sr_wcag_evaluation.md"
                        if samples_file.exists():
                            with open(samples_file, 'r', encoding='utf-8') as f:
                                samples = f.read()
                            sr_prompt = f"{sr_prompt}\n\n{samples}"
                            LOGGER_INFO(f"Loaded SR prompt with [{matched_area}] samples (auto-matched)", "CYAN")
                        else:
                            LOGGER_INFO(f"No area-specific samples for [{matched_area}], using base prompt", "CYAN")
                    else:
                        LOGGER_INFO("Loaded base SR analysis prompt (no area match)", "CYAN")
            except Exception as e:
                LOGGER_WARNING(f"SR analysis prompt not found, using server default: {e}", "YELLOW")
            
            client = OpenAIClient()
            analysis_result = client.chat_sr(file_name_path, message=sr_prompt)
            
            if not analysis_result:
                LOGGER_WARNING("Screen reader analysis returned empty result", "YELLOW")
                return {
                    'success': False,
                    'error': 'Analysis returned empty result',
                    'report_id': report_id,
                    'file_path': file_name_path
                }
            
            LOGGER_INFO("Screen reader analysis completed successfully", "GREEN")
            
            # Step 3: Write report
            if test_suite is None:
                test_suite = 'sr_analysis'
                
            report_file_path = write_screen_reader_report(
                markdown_content=analysis_result,
                test_suite=test_suite,
                report_id=report_id
            )
            
            if report_file_path:
                LOGGER_INFO(f"Screen reader report saved to: {report_file_path}", "GREEN")
                
                # Step 4: Insert data into database
                if test_case is None:
                    test_case = test_suite
                
                db_insert_success = db_handler.insert_screen_reader_report(
                    report_id=report_id,
                    test_case=test_case,
                    markdown_file_path=report_file_path
                )
                
                if db_insert_success:
                    LOGGER_INFO("Screen reader data successfully inserted into database", "GREEN")
                    
                    # Step 5: Synchronize screen reader data to TestCaseNavigateReport
                    sync_success = db_handler.sync_screen_reader_to_navigate_report(report_id)
                    if sync_success:
                        LOGGER_INFO("Screen reader data successfully synchronized to navigation report", "GREEN")
                        
                        # Step 6: Apply accepted control overrides
                        try:
                            from core.processor.accept_sr_processor import apply_accepted_overrides
                            override_count = apply_accepted_overrides(report_id, sr_report_path=report_file_path)
                            if override_count > 0:
                                LOGGER_INFO(f"Applied {override_count} accepted SR overrides", "GREEN")
                        except Exception as e:
                            LOGGER_WARNING(f"Failed to apply accepted SR overrides: {e}", "YELLOW")
                    else:
                        LOGGER_WARNING("Failed to synchronize screen reader data to navigation report", "YELLOW")
                else:
                    LOGGER_WARNING("Failed to insert screen reader data into database", "YELLOW")
                    sync_success = False
                
                return {
                    'success': True,
                    'report_id': report_id,
                    'file_path': file_name_path,
                    'report_path': report_file_path,
                    'analysis_result': analysis_result,
                    'db_inserted': db_insert_success,
                    'sync_success': sync_success
                }
            else:
                LOGGER_WARNING("Failed to save screen reader report", "YELLOW")
                return {
                    'success': False,
                    'error': 'Failed to save report',
                    'report_id': report_id,
                    'file_path': file_name_path,
                    'analysis_result': analysis_result
                }
                
        except Exception as e:
            LOGGER_ERROR(f"Screen reader analysis failed: {str(e)}", "RED")
            return {
                'success': False,
                'error': str(e),
                'report_id': report_id if 'report_id' in locals() else None
            }
    
    def handle_i18n_analysis(self, report_id, test_suite=None, test_case=None):
        """
        Handle i18n image analysis with AI
        
        Args:
            image_path (str): Path to the directory containing images
            result_path (str): Path to save the analysis report
        
        Returns:
            str: Path to the generated markdown report
        """
        try:
            # Get report_id
            test_case_db_handler = TestCaseDBHandler()
            if report_id is None:
                report_id = test_case_db_handler.get_current_report_id()
            
            LOGGER_INFO(f"Starting i18n analysis for report_id: {report_id}", "BLUE")
            # Step 1: Process i18n data
            i18n_image_data = test_case_db_handler.get_i18n_image_data(report_id)
            
            image_path = i18n_image_data.get('window_image_path', '')
            # Step 2: Analyze with OpenAI
            client = OpenAIClient()
            md_content = client.chat_i18n(image_path, message=None)
            return md_content

        except Exception as e:
            LOGGER_ERROR(f"i18n analysis failed: {str(e)}", "RED")
            return ""

    def handle_batch_screen_reader_analysis(self, report_ids, test_suite='batch_sr_analysis'):
        """
        Handle batch screen reader analysis for multiple report IDs
        
        Args:
            report_ids (list): List of report IDs to analyze
            test_suite (str): Test suite name for report file naming
        
        Returns:
            list: List of analysis results for each report ID
        """
        results = []
        
        LOGGER_INFO(f"Starting batch screen reader analysis for {len(report_ids)} reports", "BLUE")
        
        for i, report_id in enumerate(report_ids, 1):
            LOGGER_INFO(f"Processing report {i}/{len(report_ids)}: {report_id}", "CYAN")
            
            result = self.handle_screen_reader_analysis(
                report_id=report_id,
                test_suite=f"{test_suite}_batch_{i}"
            )
            
            results.append(result)
            
            if result['success']:
                LOGGER_INFO(f"Report {i} completed successfully", "GREEN")
            else:
                LOGGER_WARNING(f"Report {i} failed: {result.get('error', 'Unknown error')}", "YELLOW")
        
        successful_count = sum(1 for r in results if r['success'])
        LOGGER_INFO(f"Batch analysis completed: {successful_count}/{len(report_ids)} successful", "BLUE")
        
        return results

    def handle_analyze_performance(self, performance_report_path):
        """
        Handle performance data analysis with AI
        
        Args:
            performance_report_path (str): Path to the performance report markdown file
        
        Returns:
            dict: Analysis result containing success status, original_path, analysis_result, and updated_path
        """
        from rs_sdk.utils.performance_handler import PerformanceHandler
        try:
            LOGGER_INFO(f"Starting performance analysis for file: {performance_report_path}", "BLUE")
            
            # Check if the performance report file exists
            if not os.path.exists(performance_report_path):
                LOGGER_ERROR(f"Performance report file not found: {performance_report_path}", "RED")
                return {
                    'success': False,
                    'error': f'File not found: {performance_report_path}',
                    'original_path': performance_report_path
                }
            
            LOGGER_INFO(f"Performance report file found: {performance_report_path}", "GREEN")
            
            # Step 1: Generate performance trend charts using performance_handler
            try:
                performance_handler = PerformanceHandler()
                performance_handler.generate_performance_charts(performance_report_path)
                LOGGER_INFO("Performance trend charts generated and added to report successfully", "GREEN")
            except Exception as e:
                LOGGER_WARNING(f"Failed to generate performance charts: {str(e)}", "YELLOW")
            
            # Step 2: Analyze with OpenAI
            client = OpenAIClient()
            analysis_result = client.analyze_performance(file_path=performance_report_path)
            
            if not analysis_result:
                LOGGER_WARNING("Performance analysis returned empty result", "YELLOW")
                return {
                    'success': False,
                    'error': 'Analysis returned empty result',
                    'original_path': performance_report_path
                }
            
            LOGGER_INFO("Performance analysis completed successfully", "GREEN")
            
            # Step 3: Append analysis result to the original file using report_handler
            return append_analysis_to_report(performance_report_path, analysis_result)
                
        except Exception as e:
            LOGGER_ERROR(f"Performance analysis failed: {str(e)}", "RED")
            return {
                'success': False,
                'error': str(e),
                'original_path': performance_report_path if 'performance_report_path' in locals() else None
            }

    def handle_stress_analysis(self, stress_report_path):
        """
        Handle stress testing data analysis with AI
        
        Args:
            stress_report_path (str): Path to the stress report markdown file
        
        Returns:
            dict: Analysis result containing success status, original_path, analysis_result, and updated_path
        """
        try:
            LOGGER_INFO(f"Starting stress analysis for file: {stress_report_path}", "BLUE")
            
            # Check if the stress report file exists
            if not os.path.exists(stress_report_path):
                LOGGER_ERROR(f"Stress report file not found: {stress_report_path}", "RED")
                return {
                    'success': False,
                    'error': f'File not found: {stress_report_path}',
                    'original_path': stress_report_path
                }
            
            LOGGER_INFO(f"Stress report file found: {stress_report_path}", "GREEN")
            
            # Step 1: Generate stress trend charts using stress_handler
            try:
                from rs_sdk.utils.stress_handler import StressHandler
                stress_handler = StressHandler()
                stress_handler.generate_stress_charts(stress_report_path)
                LOGGER_INFO("Stress trend charts generated and added to report successfully", "GREEN")
            except Exception as e:
                LOGGER_WARNING(f"Failed to generate stress charts: {str(e)}", "YELLOW")
            
            # Step 2: Analyze with OpenAI
            client = OpenAIClient()
            analysis_result = client.analyze_stress_testing(file_path=stress_report_path)
            
            # Step 3: Append analysis result to the original file using report_handler
            return append_analysis_to_report(stress_report_path, analysis_result)
                
        except Exception as e:
            LOGGER_ERROR(f"Stress analysis failed: {str(e)}", "RED")
            return {
                'success': False,
                'error': str(e),
                'original_path': stress_report_path if 'stress_report_path' in locals() else None
            }
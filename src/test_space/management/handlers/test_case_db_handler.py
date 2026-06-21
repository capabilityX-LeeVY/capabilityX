import uuid
import pymysql
import json
from typing import Optional
import re
import os
import pandas as pd

from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG, LOGGER_WARNING
from common.handler.report_id_generator import report_id_generator
from db.handlers import get_db_connection
from config.paths import DB_CONFIG_PATH
from config.global_settings import settings
from config.config import TEST_CASE_DB

class TestCaseDBHandler:
    _instance: Optional['TestCaseDBHandler'] = None
    
    def __new__(cls, db_config=None):
        if cls._instance is None:
            cls._instance = super(TestCaseDBHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_config=None):
        if self._initialized:
            return
            
        self._step_counter = 0  
        self._initialized = True
        
        # Load settings using global settings manager
        self._appVersion = settings.appVersion
        self._test_suite = settings.test_suite
        self._test_batch = settings.test_batch
        
        # Initialize device information from global settings
        self._device_name = settings.device_name
        self._device_ip = settings.device_ip
        LOGGER_DEBUG(f"Device info initialized - Name: {self._device_name}, IP: {self._device_ip}")
        LOGGER_DEBUG(f"Settings loaded - appVersion: {self._appVersion}, test_suite: {self._test_suite}")

    def reset_report_session(self):
        """Reset the global report session and step counter."""
        report_id_generator.reset_global_report_session()
        self._step_counter = 0
        LOGGER_DEBUG(f"Reset report session, new report_id: {report_id_generator.global_report_id}")
    
    def get_current_report_id(self):
        """Get the current global report ID."""
        return report_id_generator.global_report_id
    
    def _get_db_connection(self):
        """Get database connection specifically for test case database."""
        return get_db_connection(TEST_CASE_DB)
    
    
    def get_navigate_report_data(self, report_id=None):
        """Select test case navigate report by report_id, ordered by step_start_time"""
        
        if report_id is None:
            report_id = report_id_generator.global_report_id
            
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for selecting navigate report")
            return pd.DataFrame()
        
        try:
            with connection.cursor() as cursor:
                sql_statement = """
                    SELECT *
                    FROM TestCaseNavigateReport
                    WHERE report_id = %s
                    ORDER BY step_start_time ASC
                """
                
                cursor.execute(sql_statement, (report_id,))
                results = cursor.fetchall()
                
                # Get column names from cursor description
                columns = [desc[0] for desc in cursor.description]
                
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                LOGGER_DEBUG(f"Retrieved {len(df)} navigate report records for report_id: {report_id}")
                return df
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to select test case navigate report: {e}")
            LOGGER_ERROR(f"Report ID: {report_id}")
            return pd.DataFrame()  # Return empty DataFrame on error
            
        finally:
            if connection:
                connection.close()

    def get_i18n_image_data(self, report_id=None):
        """Select i18n image analysis data by report_id"""
        
        if report_id is None:
            report_id = report_id_generator.global_report_id
            
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for selecting i18n image data")
            return pd.DataFrame()
        
        try:
            with connection.cursor() as cursor:
                sql_statement = """
                    SELECT
                    test_suite,
                    test_case,
                    step_order,
                    test_steps,
                    window_image_path,
                    window_img
                    FROM TestCaseNavigateReport
                    WHERE report_id = %s
                    ORDER BY step_order ASC
                """
                
                cursor.execute(sql_statement, (report_id,))
                results = cursor.fetchall()
                
                # Get column names from cursor description
                columns = [desc[0] for desc in cursor.description]
                
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                LOGGER_DEBUG(f"Retrieved {len(df)} i18n image analysis records for report_id: {report_id}")
                return df
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to select i18n image analysis data: {e}")
            LOGGER_ERROR(f"Report ID: {report_id}")
            return pd.DataFrame()
        finally:
            if connection:
                connection.close()

    def insert_navigate_report(self, test_case, test_steps, locate_control_name, 
                             current_control_name="",
                             llm_response="", expect_result="", actual_result="", 
                             navigate_result="", focus_ring_result="N/A", locate_control_image="", 
                             reference_image="", window_image_path="", control_image_path="",
                             platform=None, language=None,
                             screen_reader_description="", screen_reader_result="N/A", 
                             screen_reader_suggestions="", screen_reader_suggested_revision="",
                             control_type=None, full_description=None,
                             access_key=None, window_level1=None, window_level2=None,
                             parent=None, parent_type=None, default_action=None,
                             legacy_value=None, legacy_role=None, legacy_state=None,
                             control_pre_img=None, control_img=None, window_img=None,
                             step_start_time=None, step_end_time=None, step_duration_ms=None,
                             ui_response_enabled=False, ui_response_time_ms=None, ui_response_success=None,
                             ui_response_expected_state=None, ui_response_actual_state=None, 
                             ui_response_polling_count=None, ui_response_timeout_occurred=False, ui_response_error_message=None,
                             value_verify_result="N/A",
                             device_name=None, device_ip=None, main_cpu=None, main_mem=None, main_gpu=None, pid=None):

        connection = self._get_db_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                self._step_counter += 1
                current_step_order = self._step_counter
                
                insert_query = """
                    INSERT INTO TestCaseNavigateReport (
                        report_id, test_suite, test_batch, test_case, step_order, test_steps, locate_control_name, current_control_name,
                        locate_control_image, reference_image, window_image_path, control_image_path, llm_response,
                        expect_result, actual_result, navigate_result, focus_ring_result, value_verify_result,
                        screen_reader_description, screen_reader_result, screen_reader_suggestions, screen_reader_suggested_revision,
                        app_version, language, platform, device_name, device_ip,
                        control_type, full_description, accessKey, window_level1, window_level2,
                        parent, parent_type, default_action, legacy_value, legacy_role, legacy_state,
                        control_pre_img, control_img, window_img, step_start_time, step_end_time, step_duration_ms,
                        ui_response_enabled, ui_response_time_ms, ui_response_success, ui_response_expected_state,
                        ui_response_actual_state, ui_response_polling_count, ui_response_timeout_occurred, ui_response_error_message,
                        main_cpu, main_mem, main_gpu, pid
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                values = (
                    report_id_generator.global_report_id,
                    self._test_suite,
                    self._test_batch,
                    test_case,
                    current_step_order,  
                    test_steps,
                    locate_control_name,
                    current_control_name,
                    locate_control_image,
                    reference_image,
                    window_image_path,
                    control_image_path,
                    llm_response,
                    expect_result,
                    actual_result,
                    navigate_result,
                    focus_ring_result,
                    value_verify_result,  # Add value_verify_result to VALUES tuple
                    screen_reader_description,
                    screen_reader_result,
                    screen_reader_suggestions,
                    screen_reader_suggested_revision,
                    self._appVersion,
                    language,
                    platform,
                    self._device_name,
                    self._device_ip,
                    control_type,
                    full_description,
                    access_key,
                    window_level1,
                    window_level2,
                    parent,
                    parent_type,
                    default_action,
                    legacy_value,
                    legacy_role,
                    legacy_state,
                    control_pre_img,
                    control_img,
                    window_img,
                    step_start_time,
                    step_end_time,
                    step_duration_ms,
                    ui_response_enabled,
                    ui_response_time_ms,
                    ui_response_success,
                    ui_response_expected_state,
                    ui_response_actual_state,
                    ui_response_polling_count,
                    ui_response_timeout_occurred,
                    ui_response_error_message,
                    main_cpu,
                    main_mem,
                    main_gpu,
                    pid
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                LOGGER_INFO(f"Successfully inserted test case navigate report: {report_id_generator.global_report_id} step {current_step_order} for {test_case}")
                LOGGER_DEBUG(f"Navigate report - Report ID: {report_id_generator.global_report_id}, Step: {current_step_order}, Steps: {test_steps}, Control: {locate_control_name}, Result: {navigate_result}, Device: {self._device_name}({self._device_ip})")
                
                return True
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to insert test case navigate report: {e}")
            LOGGER_ERROR(f"Test case: {test_case}, Steps: {test_steps}, Report ID: {report_id_generator.global_report_id}, Step Order: {current_step_order}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def update_navigate_report_ui_response(self, ui_response_data, test_case=None, step_order=None):
        """
        Update UI response time data for an existing navigate report record
        
        Args:
            ui_response_data (dict): UI response measurement data
            test_case (str): Test case name (optional, will use current if not provided)
            step_order (int): Step order (optional, will use current step counter if not provided)
        
        Returns:
            bool: True if successful, False otherwise
        """
        connection = self._get_db_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                # Use provided step_order or current step counter
                target_step_order = step_order if step_order is not None else self._step_counter
                target_test_case = test_case if test_case else ui_response_data.get('test_case', '')
                
                update_query = """
                    UPDATE TestCaseNavigateReport 
                    SET 
                        ui_response_enabled = %s,
                        ui_response_time_ms = %s,
                        ui_response_success = %s,
                        ui_response_expected_state = %s,
                        ui_response_actual_state = %s,
                        ui_response_polling_count = %s,
                        ui_response_timeout_occurred = %s,
                        ui_response_error_message = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE report_id = %s AND test_case = %s AND step_order = %s
                """
                
                values = (
                    True,  # ui_response_enabled
                    float(ui_response_data.get('response_time_ms', 0.0)),
                    bool(ui_response_data.get('success', False)),
                    ui_response_data.get('expected_state', ''),
                    ui_response_data.get('actual_state', ''),
                    int(ui_response_data.get('polling_count', 0)),
                    bool(ui_response_data.get('timeout_occurred', False)),
                    ui_response_data.get('error_message'),
                    report_id_generator.global_report_id,
                    target_test_case,
                    target_step_order
                )
                
                cursor.execute(update_query, values)
                affected_rows = cursor.rowcount
                connection.commit()
                
                if affected_rows > 0:
                    LOGGER_DEBUG(f"Successfully updated UI response data: {ui_response_data.get('control_name')} = {ui_response_data.get('response_time_ms', 0):.1f}ms "
                               f"(success: {ui_response_data.get('success', False)}, report_id: {report_id_generator.global_report_id}, step: {target_step_order})")
                    return True
                else:
                    LOGGER_WARNING(f"No navigate report record found to update UI response data for: report_id={report_id_generator.global_report_id}, test_case={target_test_case}, step_order={target_step_order}")
                    return False
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to update UI response data in navigate report: {e}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()
    
    def insert_performance_report(self, test_case, control_name, main_cpu=0.0, 
                                main_mem=0.0, media_cpu=0.0, media_mem=0.0, 
                                app_version=""):

        connection = self._get_db_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                insert_query = """
                    INSERT INTO TestCasePerformanceReport (
                        report_id, test_case, test_suite, test_batch, control_name, main_cpu,
                        main_mem, media_cpu, media_mem, app_version, device_name, device_ip
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                values = (
                    report_id_generator.global_report_id,
                    test_case,
                    self._test_suite,
                    self._test_batch,
                    control_name,
                    float(main_cpu),
                    float(main_mem),
                    float(media_cpu),
                    float(media_mem),
                    app_version if app_version else self._appVersion,
                    self._device_name,
                    self._device_ip
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                LOGGER_DEBUG(f"Successfully inserted test case performance report for {test_case} (test_suite: {self._test_suite}, report_id: {report_id_generator.global_report_id}, device: {self._device_name}({self._device_ip}))")
                
                return True
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to insert test case performance report: {e}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def insert_ui_response_record(self, ui_response_data):
        """
        Insert/Update UI response time measurement in the navigate report
        
        This method now delegates to update_navigate_report_ui_response to maintain
        backward compatibility while using the integrated navigate report table.
        
        Args:
            ui_response_data (dict): Dictionary containing UI response measurement data
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_navigate_report_ui_response(ui_response_data)
    
    def get_report_steps_count(self, report_id=None):
        
        if report_id is None:
            report_id = report_id_generator.global_report_id
            
        connection = self._get_db_connection()
        if not connection:
            return 0
        
        try:
            with connection.cursor() as cursor:
                query = "SELECT COUNT(*) as step_count FROM TestCaseNavigateReport WHERE report_id = %s"
                cursor.execute(query, (report_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to get report steps count: {e}")
            return 0
            
        finally:
            if connection:
                connection.close()
    
    def get_test_case_navigate_reports_by_report_id(self, report_id=None):
        
        if report_id is None:
            report_id = report_id_generator.global_report_id
            
        connection = self._get_db_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor: # type: ignore
                query = """
                    SELECT * FROM TestCaseNavigateReport 
                    WHERE report_id = %s 
                    ORDER BY step_order ASC
                """
                
                cursor.execute(query, (report_id,))
                results = cursor.fetchall()
                
                LOGGER_DEBUG(f"Retrieved {len(results)} navigate reports for report_id: {report_id}")
                return results
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to retrieve navigate reports by report_id: {e}")
            return []
            
        finally:
            if connection:
                connection.close()
    
    def get_test_execution_summary(self):
        """
        Get test execution summary including LLM responses, navigate results, and detailed failure analysis
        
        Returns:
            dict: Dictionary containing:
                - llm_responses: List of all LLM responses
                - navigate_results: List of all navigate results
                - fail_count: Number of failed test steps (based on navigate_result)
                - total_count: Total number of test steps
                - llm_fail_count: Number of failed LLM responses
                - navigate_fail_count: Number of failed navigate results
                - llm_success_count: Number of successful LLM responses
                - navigate_success_count: Number of successful navigate results
                - report_id: The report ID used for the query
        """
        report_id = report_id_generator.global_report_id
            
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for test execution summary")
            return {
                'llm_responses': [],
                'navigate_results': [],
                'fail_count': 0,
                'total_count': 0,
                'llm_fail_count': 0,
                'navigate_fail_count': 0,
                'llm_success_count': 0,
                'navigate_success_count': 0,
                'focus_ring_fail_count': 0,
                'focus_ring_success_count': 0,
                'report_id': report_id
            }
        
        try:
            with connection.cursor() as cursor:
                # Query to get LLM responses and navigate results
                sql_statement = """
                    SELECT 
                        step_order,
                        llm_response,
                        navigate_result,
                        test_case,
                        test_steps,
                        locate_control_name,
                        focus_ring_result,
                        screen_reader_result
                    FROM TestCaseNavigateReport
                    WHERE report_id = %s
                    ORDER BY step_order ASC
                """
                
                cursor.execute(sql_statement, (report_id,))
                results = cursor.fetchall()
                
                if not results:
                    LOGGER_WARNING(f"No test execution data found for report_id: {report_id}")
                    return {
                        'llm_responses': [],
                        'navigate_results': [],
                        'fail_count': 0,
                        'total_count': 0,
                        'llm_fail_count': 0,
                        'navigate_fail_count': 0,
                        'llm_success_count': 0,
                        'navigate_success_count': 0,
                        'focus_ring_fail_count': 0,
                        'focus_ring_success_count': 0,
                        'screen_reader_fail_count': 0,
                        'screen_reader_success_count': 0,
                        'report_id': report_id
                    }
                
                # Process results
                llm_responses = []
                navigate_results = []
                fail_count = 0  # Overall failure count (based on navigate_result)
                total_count = len(results)
                
                # Detailed failure counters
                llm_fail_count = 0
                navigate_fail_count = 0
                llm_success_count = 0
                navigate_success_count = 0
                focus_ring_fail_count = 0
                focus_ring_success_count = 0
                screen_reader_fail_count = 0
                screen_reader_success_count = 0
                
                for row in results:
                    step_order, llm_response, navigate_result, test_case, test_steps, locate_control_name, focus_ring_result, screen_reader_result = row
                    
                    # Collect LLM responses and analyze failures
                    if llm_response and llm_response.strip():
                        llm_response_data = {
                            'step_order': step_order,
                            'test_case': test_case,
                            'test_steps': test_steps,
                            'locate_control_name': locate_control_name,
                            'llm_response': llm_response
                        }
                        llm_responses.append(llm_response_data)
                        
                        # Check if LLM response indicates failure
                        if self._is_failure_result(llm_response):
                            llm_fail_count += 1
                            llm_response_data['is_failure'] = True
                        else:
                            llm_success_count += 1
                            llm_response_data['is_failure'] = False
                    
                    # Collect navigate results and analyze failures
                    if navigate_result and navigate_result.strip():
                        navigate_result_data = {
                            'step_order': step_order,
                            'test_case': test_case,
                            'test_steps': test_steps,
                            'locate_control_name': locate_control_name,
                            'navigate_result': navigate_result
                        }
                        navigate_results.append(navigate_result_data)
                        
                        # Check if navigate result indicates failure
                        if self._is_failure_result(navigate_result):
                            navigate_fail_count += 1
                            fail_count += 1  # Overall failure count
                            navigate_result_data['is_failure'] = True
                        else:
                            navigate_success_count += 1
                            navigate_result_data['is_failure'] = False
                    
                    # Process focus ring results
                    if focus_ring_result and focus_ring_result.strip() and focus_ring_result != "N/A":
                        # Check if focus ring result indicates failure
                        if "❌" in focus_ring_result or "WCAG" in focus_ring_result:
                            focus_ring_fail_count += 1
                        elif "✅" in focus_ring_result or "Success" in focus_ring_result:
                            focus_ring_success_count += 1
                    
                    # Process screen reader results
                    if screen_reader_result and screen_reader_result.strip() and screen_reader_result != "N/A":
                        # Check if screen reader result indicates failure
                        if "❌" in screen_reader_result or "WCAG" in screen_reader_result or "Failed" in screen_reader_result:
                            screen_reader_fail_count += 1
                        elif "✅" in screen_reader_result or "Success" in screen_reader_result or "Passed" in screen_reader_result:
                            screen_reader_success_count += 1
                
                summary = {
                    'llm_responses': llm_responses,
                    'navigate_results': navigate_results,
                    'fail_count': fail_count,  # Overall failure count (based on navigate_result)
                    'total_count': total_count,
                    'llm_fail_count': llm_fail_count,
                    'navigate_fail_count': navigate_fail_count,
                    'llm_success_count': llm_success_count,
                    'navigate_success_count': navigate_success_count,
                    'focus_ring_fail_count': focus_ring_fail_count,
                    'focus_ring_success_count': focus_ring_success_count,
                    'screen_reader_fail_count': screen_reader_fail_count,
                    'screen_reader_success_count': screen_reader_success_count,
                    'report_id': report_id
                }
                
                LOGGER_INFO(f"Retrieved test execution summary for report_id: {report_id} - "
                           f"Total: {total_count}, Navigate Failures: {navigate_fail_count}, "
                           f"LLM Failures: {llm_fail_count}, Focus Ring Failures: {focus_ring_fail_count}, "
                           f"Screen Reader Failures: {screen_reader_fail_count}, "
                           f"LLM Responses: {len(llm_responses)}, Navigate Results: {len(navigate_results)}")
                
                return summary
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get test execution summary: {str(e)}")
            return {
                'llm_responses': [],
                'navigate_results': [],
                'fail_count': 0,
                'total_count': 0,
                'llm_fail_count': 0,
                'navigate_fail_count': 0,
                'llm_success_count': 0,
                'navigate_success_count': 0,
                'focus_ring_fail_count': 0,
                'focus_ring_success_count': 0,
                'screen_reader_fail_count': 0,
                'screen_reader_success_count': 0,
                'report_id': report_id
            }
            
        finally:
            if connection:
                connection.close()
    
    def _is_failure_result(self, navigate_result):
        """
        Check if a navigate result indicates a failure
        
        Args:
            navigate_result (str): The navigate result string
        
        Returns:
            bool: True if the result indicates failure, False otherwise
        """
        if not navigate_result:
            return False

        if '✅' in navigate_result:
            return False
        if '❌' in navigate_result:
            return True

        return False

    def get_detailed_failure_analysis(self):
        """
        Get detailed failure analysis with breakdown by LLM responses and navigate results
        
        Returns:
            dict: Dictionary containing detailed failure analysis:
                - llm_failures: List of failed LLM responses with details
                - navigate_failures: List of failed navigate results with details
                - failure_summary: Summary statistics
        """
        summary = self.get_test_execution_summary()
        
        # Extract failed items
        llm_failures = [item for item in summary['llm_responses'] if item.get('is_failure', False)]
        navigate_failures = [item for item in summary['navigate_results'] if item.get('is_failure', False)]
        
        # Create failure patterns analysis
        llm_failure_patterns = {}
        navigate_failure_patterns = {}
        
        # Analyze LLM failure patterns
        for failure in llm_failures:
            response_lower = failure['llm_response'].lower()
            for keyword in ['fail', 'error', 'timeout', 'not found', 'unable', 'cannot']:
                if keyword in response_lower:
                    llm_failure_patterns[keyword] = llm_failure_patterns.get(keyword, 0) + 1
        
        # Analyze navigate failure patterns
        for failure in navigate_failures:
            result_lower = failure['navigate_result'].lower()
            for keyword in ['fail', 'error', 'timeout', 'not found', 'unable', 'cannot']:
                if keyword in result_lower:
                    navigate_failure_patterns[keyword] = navigate_failure_patterns.get(keyword, 0) + 1
        
        failure_analysis = {
            'llm_failures': llm_failures,
            'navigate_failures': navigate_failures,
            'failure_summary': {
                'total_steps': summary['total_count'],
                'llm_total': len(summary['llm_responses']),
                'navigate_total': len(summary['navigate_results']),
                'llm_fail_count': summary['llm_fail_count'],
                'navigate_fail_count': summary['navigate_fail_count'],
                'llm_success_rate': (summary['llm_success_count'] / len(summary['llm_responses']) * 100) if summary['llm_responses'] else 0,
                'navigate_success_rate': (summary['navigate_success_count'] / len(summary['navigate_results']) * 100) if summary['navigate_results'] else 0,
                'llm_failure_patterns': llm_failure_patterns,
                'navigate_failure_patterns': navigate_failure_patterns
            },
            'report_id': summary['report_id']
        }
        
        LOGGER_INFO(f"Detailed failure analysis for report_id: {summary['report_id']} - "
                   f"LLM failures: {len(llm_failures)}, Navigate failures: {len(navigate_failures)}")
        
        return failure_analysis

    def insert_screen_reader_report(self, report_id, test_case, markdown_file_path):
        """
        Parse markdown file and insert screen reader analysis results into database
        
        Args:
            report_id (str): Report ID
            test_case (str): Test case name (will be overridden by data from TestCaseNavigateReport)
            markdown_file_path (str): Path to the markdown report file
        
        Returns:
            bool: True if successful, False otherwise
        """
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for screen reader report insertion")
            return False
        
        try:
            # Check if file exists
            if not os.path.exists(markdown_file_path):
                LOGGER_ERROR(f"Markdown file not found: {markdown_file_path}")
                return False
            
            # Read markdown file
            with open(markdown_file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
            
            LOGGER_DEBUG(f"Reading markdown file: {markdown_file_path}")
            
            # Parse markdown table
            parsed_data = self._parse_screen_reader_markdown(markdown_content)
            
            if not parsed_data:
                LOGGER_WARNING("No valid data found in markdown file")
                return False
            
            # Insert data into database
            with connection.cursor() as cursor:
                insert_sql = """
                    INSERT INTO ScreenReaderReport 
                    (report_id, step_order, test_case, test_suite, test_batch, description, compliance, 
                     suggestions, suggested_revision, wcag_level, device_name, device_ip, `references`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                inserted_count = 0
                for row_data in parsed_data:
                    try:
                        # Get test_case from TestCaseNavigateReport based on report_id and step_order
                        actual_test_case = self._get_test_case_from_navigate_report(
                            connection, report_id, row_data.get('step_order', 0)
                        )
                        
                        cursor.execute(insert_sql, (
                            report_id,
                            row_data.get('step_order', 0),
                            actual_test_case,
                            self._test_suite,
                            self._test_batch,
                            row_data.get('description', ''),
                            row_data.get('compliance', 'Unknown'),
                            row_data.get('suggestions', ''),
                            row_data.get('suggested_revision', ''),
                            row_data.get('wcag_level', ''),
                            self._device_name,
                            self._device_ip,
                            row_data.get('references', '')
                        ))
                        inserted_count += 1
                    except Exception as e:
                        LOGGER_ERROR(f"Failed to insert row {row_data.get('step_order', 'unknown')}: {str(e)}")
                        continue
                
                connection.commit()
                LOGGER_INFO(f"Successfully inserted {inserted_count} screen reader report records for report_id: {report_id}")
                return True
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to insert screen reader report: {str(e)}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def _get_test_case_from_navigate_report(self, connection, report_id, step_order):
        """
        Get test_case from TestCaseNavigateReport based on report_id and step_order
        
        Args:
            connection: Database connection
            report_id (str): Report ID
            step_order (int): Step order
        
        Returns:
            str: Test case name or 'Unknown' if not found
        """
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT test_case 
                    FROM TestCaseNavigateReport 
                    WHERE report_id = %s AND step_order = %s 
                    LIMIT 1
                """
                cursor.execute(sql, (report_id, step_order))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # If no exact match, try to get any test_case for this report_id
                    sql_fallback = """
                        SELECT test_case 
                        FROM TestCaseNavigateReport 
                        WHERE report_id = %s 
                        LIMIT 1
                    """
                    cursor.execute(sql_fallback, (report_id,))
                    result_fallback = cursor.fetchone()
                    
                    if result_fallback:
                        LOGGER_DEBUG(f"Using fallback test_case for report_id: {report_id}, step_order: {step_order}")
                        return result_fallback[0]
                    else:
                        LOGGER_WARNING(f"No test_case found for report_id: {report_id}, step_order: {step_order}")
                        return 'Unknown'
                        
        except Exception as e:
            LOGGER_ERROR(f"Failed to get test_case from navigate report: {str(e)}")
            return 'Unknown'

    def _parse_screen_reader_markdown(self, markdown_content):
        """
        Parse markdown table content and extract screen reader analysis data
        
        Args:
            markdown_content (str): Raw markdown content
        
        Returns:
            list: List of dictionaries containing parsed data
        """
        try:
            parsed_data = []
            
            # Find table in markdown using regex
            table_pattern = r'\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|'
            table_matches = re.findall(table_pattern, markdown_content, re.MULTILINE)
            
            if not table_matches:
                LOGGER_WARNING("No table found in markdown content")
                return parsed_data
            
            # Skip header rows (first 2 lines are usually header and separator)
            data_rows = table_matches[2:] if len(table_matches) > 2 else []
            
            for i, row in enumerate(data_rows):
                try:
                    # Split by | and clean up
                    columns = [col.strip() for col in row.split('|') if col.strip()]
                    
                    if len(columns) >= 7:  # Ensure we have enough columns
                        # Map columns based on expected format:
                        # | No. | Description | Compliance | Suggestions | Suggested Revision | WCAG Level | References |
                        row_data = {
                            'step_order': self._parse_control_number(columns[0]),
                            'description': columns[1] if len(columns) > 1 else '',
                            'compliance': columns[2] if len(columns) > 2 else 'Unknown',  # Keep original compliance text
                            'suggestions': columns[3] if len(columns) > 3 else '',
                            'suggested_revision': columns[4] if len(columns) > 4 else '',
                            'wcag_level': columns[5] if len(columns) > 5 else '',
                            'references': columns[6] if len(columns) > 6 else ''
                        }
                        
                        parsed_data.append(row_data)
                        LOGGER_DEBUG(f"Parsed row {i+1}: No. {row_data['step_order']}")
                    
                except Exception as e:
                    LOGGER_WARNING(f"Failed to parse table row {i+1}: {str(e)}")
                    continue
            
            LOGGER_INFO(f"Successfully parsed {len(parsed_data)} rows from markdown table")
            return parsed_data
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to parse markdown content: {str(e)}")
            return []

    def _parse_control_number(self, control_text):
        """Extract control number from control text"""
        try:
            # Try to extract number from text like "1", "Control 1", etc.
            numbers = re.findall(r'\d+', str(control_text))
            return int(numbers[0]) if numbers else 0
        except:
            return 0

    def get_screen_reader_report_by_report_id(self, report_id):
        """
        Get screen reader report data by report_id
        
        Args:
            report_id (str): Report ID
        
        Returns:
            pd.DataFrame: Screen reader report data
        """
        connection = self._get_db_connection()
        if not connection:
            return pd.DataFrame()
        
        try:
            with connection.cursor() as cursor:
                sql_statement = """
                    SELECT 
                        step_order,
                        report_id,
                        test_case,
                        test_suite,
                        description,
                        compliance,
                        suggestions,
                        suggested_revision,
                        wcag_level,
                        device_name,
                        device_ip,
                        `references`,
                        created_at,
                        updated_at
                    FROM ScreenReaderReport
                    WHERE report_id = %s
                    ORDER BY step_order ASC
                """
                
                cursor.execute(sql_statement, (report_id,))
                results = cursor.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                LOGGER_DEBUG(f"Retrieved {len(df)} screen reader report records for report_id: {report_id}")
                return df
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get screen reader report: {str(e)}")
            return pd.DataFrame()
            
        finally:
            if connection:
                connection.close()
    
    def get_performance_data(self, report_id=None, test_suite=None, app_version=None):
        """
        Get performance data from database by report_id, test_suite, or app_version.
        If parameters are empty, get data from the most recent report based on created_at.
        
        Args:
            report_id (str, optional): Report ID to filter by
            test_suite (str, optional): Test suite to filter by  
            app_version (str, optional): App version to filter by
        
        Returns:
            pd.DataFrame: Performance data with columns: report_id, test_case, test_suite, 
                         control_name, main_cpu, main_mem, media_cpu, media_mem, app_version, created_at
        """
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for performance data")
            return pd.DataFrame()
        
        try:
            with connection.cursor() as cursor:
                # Build dynamic query based on provided parameters
                where_conditions = []
                query_params = []
                
                if report_id:
                    where_conditions.append("report_id = %s")
                    query_params.append(report_id)
                    
                if test_suite:
                    where_conditions.append("test_suite = %s")
                    query_params.append(test_suite)
                    
                if app_version:
                    where_conditions.append("app_version = %s")
                    query_params.append(app_version)
                
                # Base query
                base_query = """
                    SELECT 
                        report_id,
                        test_case,
                        test_suite,
                        control_name,
                        main_cpu,
                        main_mem,
                        media_cpu,
                        media_mem,
                        app_version,
                        created_at
                    FROM TestCasePerformanceReport
                """
                
                if where_conditions:
                    # Use provided filters
                    sql_statement = base_query + " WHERE " + " AND ".join(where_conditions) + " ORDER BY created_at DESC"
                    LOGGER_DEBUG(f"Querying performance data with filters: {dict(zip(['report_id', 'test_suite', 'app_version'], [report_id, test_suite, app_version]))}")
                else:
                    # No filters provided, get the most recent report_id first
                    LOGGER_DEBUG("No filters provided, getting most recent performance data")
                    
                    # First, get the most recent report_id
                    recent_report_query = """
                        SELECT report_id 
                        FROM TestCasePerformanceReport 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """
                    
                    cursor.execute(recent_report_query)
                    recent_result = cursor.fetchone()
                    
                    if not recent_result:
                        LOGGER_WARNING("No performance data found in database")
                        return pd.DataFrame()
                    
                    most_recent_report_id = recent_result[0]
                    LOGGER_INFO(f"Using most recent report_id: {most_recent_report_id}")
                    
                    # Now get all data for this report_id
                    sql_statement = base_query + " WHERE report_id = %s ORDER BY created_at ASC"
                    query_params = [most_recent_report_id]
                
                cursor.execute(sql_statement, query_params)
                results = cursor.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                if not df.empty:
                    LOGGER_INFO(f"Retrieved {len(df)} performance records")
                    LOGGER_DEBUG(f"Performance data summary - Report ID: {df['report_id'].iloc[0] if len(df) > 0 else 'N/A'}, "
                               f"Test Suite: {df['test_suite'].iloc[0] if len(df) > 0 else 'N/A'}, "
                               f"App Version: {df['app_version'].iloc[0] if len(df) > 0 else 'N/A'}")
                else:
                    LOGGER_WARNING("No performance data found matching the criteria")
                
                return df
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get performance data: {str(e)}")
            return pd.DataFrame()
            
        finally:
            if connection:
                connection.close()

    def insert_stress_report(self, report_id, test_case, control_name, main_cpu=None, main_mem=None, 
                           media_cpu=None, media_mem=None, cpu_check='N/A', memory_check='N/A',
                           process_count=None, process_types=None, window_response_time=None, 
                           process_status='UNKNOWN', warnings=None, log_archive_path=None):
        """
        Insert stress testing report data into database
        
        Args:
            report_id (str): Test execution batch ID
            test_case (str): Test case name
            control_name (str): Control/action description
            main_cpu (float, optional): Main process CPU usage
            main_mem (float, optional): Main process memory usage
            media_cpu (float, optional): Media process CPU usage
            media_mem (float, optional): Media process memory usage
            cpu_check (str): CPU check result (PASS/FAIL)
            memory_check (str): Memory check result (PASS/FAIL)
            process_count (int, optional): Number of processes
            process_types (str, optional): Process type descriptions
            window_response_time (int, optional): Window response time in ms
            process_status (str): Overall process status (HEALTHY/WARNING/UNHEALTHY/CRITICAL)
            warnings (str, optional): Warning messages
            log_archive_path (str, optional): Path to log archive
        
        Returns:
            bool: True if insertion successful, False otherwise
        """
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for stress report insertion")
            return False

        try:
            with connection.cursor() as cursor:
                # Insert stress report data
                sql_statement = """
                    INSERT INTO TestCaseStressReport (
                        report_id, test_case, test_suite, control_name,
                        main_cpu, main_mem, media_cpu, media_mem,
                        cpu_check, memory_check, process_count, process_types,
                        window_response_time, process_status, warnings, log_archive_path,
                        app_version, device_name, device_ip
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                cursor.execute(sql_statement, (
                    report_id, test_case, self._test_suite, control_name,
                    main_cpu, main_mem, media_cpu, media_mem,
                    cpu_check, memory_check, process_count, process_types,
                    window_response_time, process_status, warnings, log_archive_path,
                    self._appVersion, self._device_name, self._device_ip
                ))
                
                connection.commit()
                LOGGER_DEBUG(f"Inserted stress report: {test_case} - {control_name}")
                return True
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to insert stress report: {str(e)}")
            connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def get_stress_data(self, report_id=None, test_suite=None, app_version=None):
        """
        Get stress testing data from database by report_id, test_suite, or app_version.
        If parameters are empty, get data from the most recent report based on created_at.
        
        Args:
            report_id (str, optional): Report ID to filter by
            test_suite (str, optional): Test suite to filter by  
            app_version (str, optional): App version to filter by
        
        Returns:
            pd.DataFrame: Stress data with all columns from TestCaseStressReport
        """
        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR("Failed to get database connection for stress data")
            return pd.DataFrame()
        
        try:
            with connection.cursor() as cursor:
                # Build dynamic query based on provided parameters
                where_conditions = []
                query_params = []
                
                if report_id:
                    where_conditions.append("report_id = %s")
                    query_params.append(report_id)
                    
                if test_suite:
                    where_conditions.append("test_suite = %s")
                    query_params.append(test_suite)
                    
                if app_version:
                    where_conditions.append("app_version = %s")
                    query_params.append(app_version)
                
                # Base query
                base_query = """
                    SELECT 
                        report_id, test_case, test_suite, control_name,
                        main_cpu, main_mem, media_cpu, media_mem,
                        cpu_check, memory_check, process_count, process_types,
                        window_response_time, process_status, warnings, log_archive_path,
                        app_version, device_name, device_ip, test_time, created_at
                    FROM TestCaseStressReport
                """
                
                if where_conditions:
                    # Use provided filters
                    sql_statement = base_query + " WHERE " + " AND ".join(where_conditions) + " ORDER BY created_at DESC"
                    cursor.execute(sql_statement, query_params)
                    LOGGER_DEBUG(f"Querying stress data with filters: {dict(zip(['report_id', 'test_suite', 'app_version'], [report_id, test_suite, app_version]))}")
                else:
                    # No filters provided, get the most recent report_id first
                    LOGGER_DEBUG("No filters provided, getting most recent stress data")
                    
                    # First, get the most recent report_id
                    recent_report_query = """
                        SELECT report_id 
                        FROM TestCaseStressReport 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """
                    
                    cursor.execute(recent_report_query)
                    recent_result = cursor.fetchone()
                    
                    if not recent_result:
                        LOGGER_WARNING("No stress data found in database")
                        return pd.DataFrame()
                    
                    most_recent_report_id = recent_result[0]
                    LOGGER_INFO(f"Using most recent report_id: {most_recent_report_id}")
                    
                    # Now get all data for this report_id
                    sql_statement = base_query + " WHERE report_id = %s ORDER BY created_at ASC"
                    query_params = [most_recent_report_id]
                
                cursor.execute(sql_statement, query_params)
                results = cursor.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                if not df.empty:
                    LOGGER_INFO(f"Retrieved {len(df)} stress records")
                    LOGGER_DEBUG(f"Stress data summary - Report ID: {df['report_id'].iloc[0] if len(df) > 0 else 'N/A'}, "
                               f"Test Suite: {df['test_suite'].iloc[0] if len(df) > 0 else 'N/A'}, "
                               f"App Version: {df['app_version'].iloc[0] if len(df) > 0 else 'N/A'}")
                else:
                    LOGGER_WARNING("No stress data found matching the criteria")
                
                return df
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get stress data: {str(e)}")
            return pd.DataFrame()
            
        finally:
            if connection:
                connection.close()

    def sync_screen_reader_to_navigate_report(self, report_id=None):
        """
        Synchronize screen reader data from ScreenReaderReport to TestCaseNavigateReport
        
        Args:
            report_id (str, optional): Specific report ID to sync. If None, uses current report_id
            
        Returns:
            bool: Success status of the synchronization
        """
        connection = self._get_db_connection()
        if not connection:
            return False
        
        try:
            # Get report_id if not provided
            if report_id is None:
                report_id = self.get_current_report_id()
            
            LOGGER_INFO(f"Starting screen reader data synchronization for report_id: {report_id}", "BLUE")
            
            with connection.cursor() as cursor:
                # Update TestCaseNavigateReport with data from ScreenReaderReport
                # Match records based on report_id and step_order
                sync_query = """
                    UPDATE TestCaseNavigateReport tcnr
                    INNER JOIN ScreenReaderReport srr 
                    ON tcnr.report_id = srr.report_id 
                    AND tcnr.step_order = srr.step_order
                    SET 
                        tcnr.screen_reader_description = srr.description,
                        tcnr.screen_reader_result = srr.compliance,
                        tcnr.screen_reader_suggestions = srr.suggestions,
                        tcnr.screen_reader_suggested_revision = srr.suggested_revision
                    WHERE tcnr.report_id = %s
                """
                
                cursor.execute(sync_query, (report_id,))
                updated_rows = cursor.rowcount
                connection.commit()
                
                if updated_rows > 0:
                    LOGGER_INFO(f"Successfully synchronized {updated_rows} screen reader records to navigation report for report_id: {report_id}", "GREEN")
                else:
                    LOGGER_WARNING(f"No screen reader records found to synchronize for report_id: {report_id}", "YELLOW")
                
                return True
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to synchronize screen reader data: {str(e)}")
            connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def sync_all_screen_reader_to_navigate_report(self):
        """
        Synchronize all unsynced screen reader data from ScreenReaderReport to TestCaseNavigateReport
        This method syncs data where TestCaseNavigateReport.screen_reader_result is 'N/A' or NULL
        
        Returns:
            bool: Success status of the synchronization
        """
        connection = self._get_db_connection()
        if not connection:
            return False
        
        try:
            LOGGER_INFO("Starting bulk screen reader data synchronization", "BLUE")
            
            with connection.cursor() as cursor:
                # Update TestCaseNavigateReport with data from ScreenReaderReport
                # Only update records where screen_reader_result is 'N/A' or NULL
                bulk_sync_query = """
                    UPDATE TestCaseNavigateReport tcnr
                    INNER JOIN ScreenReaderReport srr 
                    ON tcnr.report_id = srr.report_id 
                    AND tcnr.step_order = srr.step_order
                    SET 
                        tcnr.screen_reader_description = srr.description,
                        tcnr.screen_reader_result = srr.compliance,
                        tcnr.screen_reader_suggestions = srr.suggestions,
                        tcnr.screen_reader_suggested_revision = srr.suggested_revision
                    WHERE (tcnr.screen_reader_result = 'N/A' OR tcnr.screen_reader_result IS NULL)
                """
                
                cursor.execute(bulk_sync_query)
                updated_rows = cursor.rowcount
                connection.commit()
                
                if updated_rows > 0:
                    LOGGER_INFO(f"Successfully synchronized {updated_rows} screen reader records to navigation reports", "GREEN")
                else:
                    LOGGER_INFO("No screen reader records found to synchronize", "CYAN")
                
                return True
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to bulk synchronize screen reader data: {str(e)}")
            connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()

    def get_screen_reader_sync_status(self, report_id=None):
        """
        Check the synchronization status between ScreenReaderReport and TestCaseNavigateReport
        
        Args:
            report_id (str, optional): Specific report ID to check. If None, checks all data
            
        Returns:
            dict: Sync status information
        """
        connection = self._get_db_connection()
        if not connection:
            return {}
        
        try:
            with connection.cursor() as cursor:
                # Build query based on whether report_id is provided
                if report_id:
                    status_query = """
                        SELECT 
                            COUNT(*) as total_navigate_records,
                            SUM(CASE WHEN tcnr.screen_reader_result != 'N/A' AND tcnr.screen_reader_result IS NOT NULL THEN 1 ELSE 0 END) as synced_records,
                            COUNT(srr.id) as available_sr_records
                        FROM TestCaseNavigateReport tcnr
                        LEFT JOIN ScreenReaderReport srr 
                        ON tcnr.report_id = srr.report_id AND tcnr.step_order = srr.step_order
                        WHERE tcnr.report_id = %s
                    """
                    cursor.execute(status_query, (report_id,))
                else:
                    status_query = """
                        SELECT 
                            COUNT(*) as total_navigate_records,
                            SUM(CASE WHEN tcnr.screen_reader_result != 'N/A' AND tcnr.screen_reader_result IS NOT NULL THEN 1 ELSE 0 END) as synced_records,
                            COUNT(srr.id) as available_sr_records
                        FROM TestCaseNavigateReport tcnr
                        LEFT JOIN ScreenReaderReport srr 
                        ON tcnr.report_id = srr.report_id AND tcnr.step_order = srr.step_order
                    """
                    cursor.execute(status_query)
                
                result = cursor.fetchone()
                
                return {
                    'total_navigate_records': result[0] or 0,
                    'synced_records': result[1] or 0,
                    'available_sr_records': result[2] or 0,
                    'sync_percentage': round((result[1] or 0) / (result[0] or 1) * 100, 2)
                }
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get screen reader sync status: {str(e)}")
            return {}
            
        finally:
            if connection:
                connection.close()

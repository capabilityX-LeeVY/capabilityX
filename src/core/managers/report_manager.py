from common.utils.logger import LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR, LOGGER_INFO
from rs_sdk.utils import report_handler


class ReportManager:

    
    def __init__(self, test_case_db_handler):
        self.test_case_db_handler = test_case_db_handler
    
    def write_and_insert_navigate_report(self, 
                                       navigate_report_path, 
                                       test_case, 
                                       ctrl_name, 
                                       locate_control_name,
                                       ctrl_ai_check_reference_image_path,
                                       current_control_window_image,
                                       current_control_image,
                                       llm_response,
                                       ctrl_expect_state,
                                       ctrl_expect,
                                       current_expect_state,
                                       platform,
                                       language,
                                       control_metadata=None,
                                       image_data=None,
                                       step_index=None,
                                       ui_response_data=None,
                                       focus_ring_status=None,
                                       window_image_path=None,
                                       control_image_path=None,
                                       step_start_time=None,
                                       step_end_time=None,
                                       step_duration_ms=None,
                                       ui_response_threshold_ms=None,
                                       performance_thresholds=None,
                                       main_cpu=None,
                                       main_mem=None,
                                       main_gpu=None,
                                       value_verify_result=None,
                                       enable_performance=True,  # Default to True for backward compatibility
                                       enable_focus_ring=True):  # Default to True for backward compatibility
        try:
            # Convert step_index from 0-based to 1-based for display (more intuitive for users)
            step_name = f"{step_index + 1}" if step_index is not None else ctrl_name
            
            # Format UI response time data for display (with configurable threshold)
            ui_response_display = ""
            if ui_response_data and ui_response_data.get('response_time_ms') is not None:
                response_time = ui_response_data.get('response_time_ms')
                success = ui_response_data.get('success', True)
                
                # Convert all times to seconds for unified display
                time_in_seconds = response_time / 1000
                time_display = f"{time_in_seconds:.2f}s"
                
                # Use dynamic threshold: step-level > test-case-level > global default (3000ms)
                threshold_ms = ui_response_threshold_ms or 3000  # Default to 3 seconds if not specified
                
                # Apply threshold: success in functionality AND within performance threshold
                if success and response_time <= threshold_ms:
                    ui_response_display = f"✅{time_display}"
                else:
                    ui_response_display = f"❌{time_display}"
            
            # Format performance data for display with threshold checking (only if Performance is enabled)
            if enable_performance:
                # Default thresholds if not specified
                default_thresholds = {
                    'cpu_threshold': 60,
                    'mem_threshold_mb': 1024, 
                    'gpu_threshold': 60
                }
                
                if performance_thresholds:
                    thresholds = {**default_thresholds, **performance_thresholds}
                else:
                    thresholds = default_thresholds
                
                # Format CPU with threshold checking
                if main_cpu is not None:
                    if main_cpu <= thresholds['cpu_threshold']:
                        main_cpu_display = f"✅{main_cpu}%"
                    else:
                        main_cpu_display = f"❌{main_cpu}%"
                else:
                    main_cpu_display = "N/A"
                
                # Format Memory with threshold checking
                if main_mem is not None:
                    if main_mem <= thresholds['mem_threshold_mb']:
                        main_mem_display = f"✅{main_mem} MB"
                    else:
                        main_mem_display = f"❌{main_mem} MB"
                else:
                    main_mem_display = "N/A"
                
                # Format GPU with threshold checking
                if main_gpu is not None:
                    if main_gpu <= thresholds['gpu_threshold']:
                        main_gpu_display = f"✅{main_gpu}%"
                    else:
                        main_gpu_display = f"❌{main_gpu}%"
                else:
                    main_gpu_display = "N/A"
            else:
                # Performance monitoring disabled - show "Disabled" instead of "N/A"
                main_cpu_display = "—"
                main_mem_display = "—"
                main_gpu_display = "—"
                LOGGER_DEBUG(f"[report][performance] Performance check point disabled, using '—' placeholder")
            
            # Format Focus Ring status based on check point
            if enable_focus_ring:
                focus_ring_display = focus_ring_status if focus_ring_status else "N/A"
            else:
                focus_ring_display = "—"
                LOGGER_DEBUG(f"[report][focus_ring] Focus Ring check point disabled, using '—' placeholder")
            
            # Get actual current control name from metadata, fallback to locate target if not available
            current_control_name = control_metadata.get('current_control_name', locate_control_name) if control_metadata else locate_control_name
            
            # Screen Reader: Always show "N/A" during execution, actual results synced after analysis
            screen_reader_display = "—"
            
            report_handler.write_navigate_report_body(
                navigate_report_path,
                test_case,
                step_name,
                locate_control_name,  # Step Name (locate target)
                current_control_name,  # Current Control Name (actual focused control)
                ctrl_ai_check_reference_image_path if ctrl_ai_check_reference_image_path else "",
                current_control_window_image if current_control_window_image else "",
                current_control_image if current_control_image else "",
                ctrl_expect_state,    # KB Navigate 
                focus_ring_display,  # Focus Ring detection
                screen_reader_display,  # Screen Reader detection
                llm_response if llm_response else "",  # AI check result
                value_verify_result if value_verify_result else "N/A",  # Value Verify result
                ui_response_display,  # Response Time - time to reach next focusable state
                main_cpu_display,     # Main CPU usage
                main_mem_display,     # Main Memory usage  
                main_gpu_display      # Main GPU usage
            )
            
            control_metadata = control_metadata or {}
            image_data = image_data or {}
            
            # Extract UI response data for database storage
            ui_response_enabled = bool(ui_response_data and ui_response_data.get('response_time_ms') is not None)
            ui_response_time_ms = ui_response_data.get('response_time_ms') if ui_response_data else None
            ui_response_success = ui_response_data.get('success') if ui_response_data else None
            ui_response_expected_state = ui_response_data.get('expected_state') if ui_response_data else None
            ui_response_actual_state = ui_response_data.get('actual_state') if ui_response_data else None
            ui_response_polling_count = ui_response_data.get('polling_count') if ui_response_data else None
            ui_response_timeout_occurred = ui_response_data.get('timeout_occurred', False) if ui_response_data else False
            ui_response_error_message = ui_response_data.get('error_message') if ui_response_data else None

            db_insert_success = self.test_case_db_handler.insert_navigate_report(
                test_case=test_case,
                test_steps=ctrl_name if ctrl_name else "",
                locate_control_name=locate_control_name if locate_control_name else "",
                current_control_name=current_control_name,
                locate_control_image="",
                reference_image=ctrl_ai_check_reference_image_path if ctrl_ai_check_reference_image_path else "",
                window_image_path=window_image_path if window_image_path else "",
                control_image_path=control_image_path if control_image_path else "",
                llm_response=llm_response if llm_response else "",
                expect_result=ctrl_expect if ctrl_expect else "",
                actual_result=current_expect_state if current_expect_state else "",
                navigate_result=ctrl_expect_state if ctrl_expect_state else "",
                focus_ring_result=focus_ring_status if focus_ring_status else "N/A",
                value_verify_result=value_verify_result if value_verify_result else "N/A",
                platform=platform,
                language=language,
                control_type=control_metadata.get('current_control_type_name'),
                full_description=control_metadata.get('full_description'),
                access_key=control_metadata.get('control_accesskey'),
                window_level1=control_metadata.get('current_control_level1_window_name'),
                window_level2=control_metadata.get('current_control_level2_window_name'),
                parent=control_metadata.get('parent_name'),
                parent_type=control_metadata.get('parent_type'),
                # Legacy properties fields
                default_action=control_metadata.get('default_action'),
                legacy_value=control_metadata.get('legacy_value'),
                legacy_role=control_metadata.get('legacy_role'),
                legacy_state=control_metadata.get('legacy_state'),
                # Image byte data fields
                control_pre_img=image_data.get('pre_control_image_bytes'),
                control_img=image_data.get('control_image_bytes'),
                window_img=image_data.get('window_image_bytes'),
                # UI Response measurement fields
                ui_response_enabled=ui_response_enabled,
                ui_response_time_ms=ui_response_time_ms,
                ui_response_success=ui_response_success,
                ui_response_expected_state=ui_response_expected_state,
                ui_response_actual_state=ui_response_actual_state,
                ui_response_polling_count=ui_response_polling_count,
                ui_response_timeout_occurred=ui_response_timeout_occurred,
                ui_response_error_message=ui_response_error_message,
                step_start_time=step_start_time,
                step_end_time=step_end_time,
                step_duration_ms=step_duration_ms,
                main_cpu=main_cpu,
                main_mem=main_mem,
                main_gpu=main_gpu,
                pid=control_metadata.get('control_pid') if control_metadata else None
            )
            
            if db_insert_success:
                LOGGER_DEBUG(f"[report][navigate]Successfully inserted navigate report to database for test case: {test_case}")
            else:
                LOGGER_WARNING(f"[report][navigate]Failed to insert navigate report to database for test case: {test_case}")

            return db_insert_success
            
        except Exception as e:
            LOGGER_ERROR(f"[report][navigate]Exception occurred while writing navigate report to database: {e}")
            return False
    
    def write_and_insert_performance_report(self, 
                                          performance_report_path, 
                                          test_case, 
                                          current_control_name,
                                          main_cpu, 
                                          main_mem, 
                                          media_cpu, 
                                          media_mem,
                                          step_description=None):

        try:
            report_handler.write_performance_report_body(
                performance_report_path,
                test_case,
                current_control_name,
                main_cpu=main_cpu,
                main_mem=main_mem,
                media_cpu=media_cpu,
                media_mem=media_mem,
            )
            
            db_performance_success = self.test_case_db_handler.insert_performance_report(
                test_case=test_case,
                control_name=current_control_name if current_control_name else "",
                main_cpu=float(main_cpu) if main_cpu is not None and main_cpu != '0' else 0.0,
                main_mem=float(main_mem) if main_mem is not None and main_mem != '0' else 0.0,
                media_cpu=float(media_cpu) if media_cpu is not None and media_cpu != '0' else 0.0,
                media_mem=float(media_mem) if media_mem is not None and media_mem != '0' else 0.0
            )
            
            success_msg = f"[report][performance]Successfully inserted performance report to database for test case: {test_case}"
            failure_msg = f"[report][performance]Failed to insert performance report to database for test case: {test_case}"
            
            if step_description:
                success_msg += f", step: {step_description}"
                failure_msg += f", step: {step_description}"
            
            if db_performance_success:
                LOGGER_DEBUG(success_msg)
            else:
                LOGGER_WARNING(failure_msg)
                
            return db_performance_success
            
        except Exception as e:
            error_msg = f"[report][performance]Exception occurred while writing performance report to database: {e}"
            if step_description:
                error_msg += f" (step: {step_description})"
            LOGGER_ERROR(error_msg)
            return False
    
    def batch_write_performance_reports(self, 
                                      performance_report_path, 
                                      test_case, 
                                      test_case_execution_duration,
                                      webex_app_main_pid,
                                      webex_app_media_pid,
                                      process_handler):

        LOGGER_DEBUG(f"[report][record][performance][test_case_execution_duration: {test_case_execution_duration}]", "CYAN")
        
        success_count = 0
        total_count = test_case_execution_duration
        
        for j in range(test_case_execution_duration):
            current_control_count = f"{j+1}"
            current_main_cpu, current_main_mem, current_media_cpu, current_media_mem, current_main_gpu = process_handler.get_performance_cisco_collab_pid_meta()
            
            success = self.write_and_insert_performance_report(
                performance_report_path,
                test_case,
                current_control_count,
                current_main_cpu,
                current_main_mem,
                current_media_cpu,
                current_media_mem,
                step_description=current_control_count
            )
            
            if success:
                success_count += 1

            LOGGER_DEBUG(f"[report][record][performance][main: {webex_app_main_pid}], [media: {webex_app_media_pid}]", "CYAN")

        LOGGER_DEBUG(f"[report][record][performance]Batch performance report completed: {success_count}/{total_count} successful")
        return success_count == total_count
    
    def get_overall_report_summary(self):
        """
        Get overall test report summary with pass/fail status
        
        Returns:
            dict: Dictionary containing:
                - llm_fail_count: Number of failed LLM responses
                - navigate_fail_count: Number of failed navigate results
                - focus_ring_fail_count: Number of failed focus ring validations
                - screen_reader_fail_count: Number of failed screen reader validations
                - result_summary: 'PASSED' or 'FAILED {total_failures}'
                - report_id: The report ID used for analysis
        """
        try:
            # Get the enhanced execution summary with detailed failure counts
            summary = self.test_case_db_handler.get_test_execution_summary()
            
            llm_failures = summary['llm_fail_count']
            nav_failures = summary['navigate_fail_count']
            focus_ring_failures = summary['focus_ring_fail_count']
            screen_reader_failures = summary['screen_reader_fail_count']
            total_failures = llm_failures + nav_failures + focus_ring_failures + screen_reader_failures
            
            # Determine result summary
            if llm_failures > 0 or nav_failures > 0 or focus_ring_failures > 0 or screen_reader_failures > 0:
                result_summary = f"FAILED {total_failures}"
            else:
                result_summary = "PASSED"
            
            result = {
                'llm_fail_count': llm_failures,
                'navigate_fail_count': nav_failures,
                'focus_ring_fail_count': focus_ring_failures,
                'screen_reader_fail_count': screen_reader_failures,
                'result_summary': result_summary,
                'report_id': summary['report_id']
            }
            
            LOGGER_DEBUG(f"[report][summary]LLM failures: {llm_failures}, "
                        f"Navigate failures: {nav_failures}, "
                        f"Focus Ring failures: {focus_ring_failures}, "
                        f"Screen Reader failures: {screen_reader_failures}, "
                        f"Result: {result_summary} for report_id: {result['report_id']}")
            
            return result
            
        except Exception as e:
            LOGGER_ERROR(f"[report][summary]Failed to get overall report summary: {e}")
            return {
                'llm_fail_count': 0,
                'navigate_fail_count': 0,
                'focus_ring_fail_count': 0,
                'screen_reader_fail_count': 0,
                'result_summary': 'PASSED',
                'report_id': 'unknown'
            }
    
    def regenerate_navigate_report_with_screen_reader(self, navigate_report_path, report_id=None, sr_report_path=None):
        """
        Update navigation report's Screen Reader column with actual results from database.
        This should be called AFTER screen reader analysis completes and data is synced.
        Only updates the Screen Reader column values, preserving all other content.
        
        Args:
            navigate_report_path: Path to the navigation report markdown file
            report_id: Report ID to query data for (uses global report_id if not provided)
            sr_report_path: Path to the screen reader details report (for adding "details" links)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get all navigate report data from database
            df = self.test_case_db_handler.get_navigate_report_data(report_id)
            
            if df.empty:
                LOGGER_WARNING(f"[report][screen_reader]No navigate report data found for update")
                return False
                        
            # Read the existing report file
            try:
                with open(navigate_report_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except FileNotFoundError:
                LOGGER_ERROR(f"[report][screen_reader]Navigation report file not found: {navigate_report_path}")
                return False
            
            # Compute relative link to SR details report
            sr_details_link = ""
            if sr_report_path:
                try:
                    import os
                    nav_dir = os.path.dirname(navigate_report_path)
                    sr_details_link = os.path.relpath(sr_report_path, nav_dir).replace('\\', '/')
                except Exception as e:
                    LOGGER_WARNING(f"[report][screen_reader]Failed to compute relative SR report path: {e}")
            
            # Build a mapping of (test_case, step_order) -> screen_reader_result
            screen_reader_map = {}
            for idx, row in df.iterrows():
                test_case = row.get('test_case', '')
                step_order = str(row.get('step_order', ''))
                screen_reader_result = row.get('screen_reader_result', 'N/A')
                
                # Only update if we have an actual result (not N/A)
                if screen_reader_result and screen_reader_result != 'N/A':
                    key = (test_case, step_order)
                    screen_reader_map[key] = screen_reader_result
            
            # Update the report lines
            updated_lines = []
            current_test_case = None
            update_count = 0
            global_step_order = 0
            
            for line in lines:
                if line.startswith('## Test Case:'):
                    current_test_case = line.split('[')[1].split(']')[0] if '[' in line and ']' in line else None
                    updated_lines.append(line)
                elif line.startswith('|') and not line.startswith('|---') and '|' in line[1:]:
                    if 'Test Case' in line or 'Step Num' in line:
                        updated_lines.append(line)
                        continue
                    
                    columns = line.split('|')
                    
                    if len(columns) >= 12:
                        global_step_order += 1
                        step_order = str(global_step_order)
                        
                        if current_test_case and step_order:
                            key = (current_test_case, step_order)
                            if key in screen_reader_map:
                                sr_value = screen_reader_map[key]
                                # Add details link for non-compliant entries
                                if 'Non-compliant' in sr_value and sr_details_link:
                                    sr_value = f'{sr_value} <a href="{sr_details_link}">details</a>'
                                columns[10] = ' ' + sr_value + ' '
                                update_count += 1
                        
                        updated_line = '|'.join(columns)
                        if not updated_line.endswith('\n'):
                            updated_line += '\n'
                        updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Write the updated content back to the file
            with open(navigate_report_path, 'w', encoding='utf-8') as file:
                file.writelines(updated_lines)
            
            LOGGER_INFO(f"[report][screen_reader]Successfully updated {update_count} Screen Reader values in navigation report", "GREEN")
            return update_count > 0
            
        except Exception as e:
            LOGGER_ERROR(f"[report][screen_reader]Failed to update navigate report: {e}")
            import traceback
            LOGGER_ERROR(f"[report][screen_reader]Traceback: {traceback.format_exc()}")
            return False

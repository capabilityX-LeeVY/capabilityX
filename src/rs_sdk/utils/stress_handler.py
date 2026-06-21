"""
Stress Testing Handler
Handles stress testing data collection, analysis, and report generation.
"""

import os
import re
import time
import ctypes
from ctypes import wintypes
from pathlib import Path
from datetime import datetime
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
from typing import Optional, List, Dict, Any

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR, LOGGER_DEBUG
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
from rs_sdk.utils.process_handler import ProcessHandler


class StressHandler:
    """Handle stress testing data collection, analysis and reporting"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize stress handler with configuration"""
        if config_path is None:
            from config.paths import SRC_PATH
            config_path = str(SRC_PATH / "config" / "stress_config.ini")
        
        self.config_path = config_path
        self.process_handler = ProcessHandler()
        self._load_config()
        
        # Process health tracking
        self._previous_pids = set()
        self._process_history = {}  # pid -> {last_seen, last_cpu_time, low_cpu_count}
        self._hang_thresholds = {
            'main_timeout': 60,      # seconds
            'media_timeout': 90,     # seconds  
            'low_cpu_threshold': 0.1, # percent
            'min_checks_for_hang': 3  # consecutive low CPU checks
        }
    
    def _load_config(self):
        """Load stress testing configuration from INI file"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding='utf-8')
            
            # Load stress thresholds
            self.cpu_threshold = float(config.get('stress_thresholds', 'cpu_threshold', fallback=40.0))
            self.memory_threshold = float(config.get('stress_thresholds', 'memory_threshold', fallback=3000))
            
            # Load monitoring settings
            self.enable_crash_detection = config.getboolean('monitoring', 'enable_crash_detection', fallback=True)
            self.enable_hang_detection = config.getboolean('monitoring', 'enable_hang_detection', fallback=True)
            self.enable_window_responsiveness = config.getboolean('monitoring', 'enable_window_responsiveness', fallback=True)
            
            LOGGER_INFO(f"Loaded stress config: CPU threshold={self.cpu_threshold}%, Memory threshold={self.memory_threshold}MB")
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to load stress config, using defaults: {e}")
            self.cpu_threshold = 40.0
            self.memory_threshold = 3000
            self.enable_crash_detection = True
            self.enable_hang_detection = True
            self.enable_window_responsiveness = True
    
    def _get_windows_for_pid(self, pid):
        """Get all window handles for a given process ID"""
        windows = []
        
        def enum_windows_proc(hwnd, lParam):
            window_pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid and ctypes.windll.user32.IsWindowVisible(hwnd):
                windows.append(hwnd)
            return True
        
        # Define the callback function type
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        callback = EnumWindowsProc(enum_windows_proc)
        
        ctypes.windll.user32.EnumWindows(callback, 0)
        return windows
    
    def _check_window_responsiveness(self, hwnd, timeout_ms=5000):
        """Check window responsiveness using SendMessageTimeout"""
        try:
            WM_NULL = 0x0000
            SMTO_ABORTIFHUNG = 0x0002
            SMTO_BLOCK = 0x0001
            
            start_time = time.time()
            result = wintypes.DWORD()
            
            # Use SendMessageTimeout to check window responsiveness
            success = ctypes.windll.user32.SendMessageTimeoutW(
                hwnd,                    # Window handle
                WM_NULL,                 # Message (WM_NULL is safe)
                0,                       # wParam
                0,                       # lParam
                SMTO_ABORTIFHUNG | SMTO_BLOCK,  # Flags
                timeout_ms,              # Timeout in milliseconds
                ctypes.byref(result)     # Result
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            if success:
                return {
                    'responsive': True,
                    'response_time_ms': round(response_time_ms, 1),
                    'status': 'RESPONSIVE'
                }
            else:
                return {
                    'responsive': False,
                    'response_time_ms': timeout_ms,
                    'status': 'TIMEOUT'
                }
        except Exception as e:
            LOGGER_WARNING(f"Error checking window responsiveness: {e}")
            return {
                'responsive': False,
                'response_time_ms': 0.0,
                'status': 'ERROR'
            }
    
    def _get_window_response_status(self, pid_info):
        """Get comprehensive window response status for all Webex processes"""
        if not self.enable_window_responsiveness:
            return {'response_time_ms': 0.0, 'status': 'DISABLED', 'responsive': True}
        
        try:
            all_pids = pid_info.get('all_pids', [])
            if not all_pids:
                return {'response_time_ms': 0.0, 'status': 'NO_PROCESSES', 'responsive': False}
            
            total_response_time = 0.0
            responsive_count = 0
            max_response_time = 0.0
            unresponsive_count = 0
            
            for pid in all_pids:
                try:
                    windows = self._get_windows_for_pid(pid)
                    if windows:
                        for hwnd in windows:
                            result = self._check_window_responsiveness(hwnd)
                            if result['responsive']:
                                total_response_time += result['response_time_ms']
                                responsive_count += 1
                                max_response_time = max(max_response_time, result['response_time_ms'])
                            else:
                                unresponsive_count += 1
                except Exception as e:
                    LOGGER_DEBUG(f"Error checking windows for PID {pid}: {e}")
                    continue
            
            if responsive_count > 0:
                avg_response_time = total_response_time / responsive_count
                if unresponsive_count > 0:
                    status = 'MIXED'  # Some responsive, some not
                elif max_response_time > 1000:  # > 1 second
                    status = 'SLOW'
                elif max_response_time > 500:   # > 0.5 seconds
                    status = 'MODERATE'
                else:
                    status = 'GOOD'
                
                return {
                    'response_time_ms': round(avg_response_time, 1),
                    'max_response_time_ms': round(max_response_time, 1),
                    'status': status,
                    'responsive': unresponsive_count == 0,
                    'responsive_count': responsive_count,
                    'unresponsive_count': unresponsive_count
                }
            else:
                return {
                    'response_time_ms': 5000.0,  # Timeout value
                    'status': 'UNRESPONSIVE',
                    'responsive': False,
                    'responsive_count': 0,
                    'unresponsive_count': len(all_pids)
                }
                
        except Exception as e:
            LOGGER_WARNING(f"Error getting window response status: {e}")
            return {'response_time_ms': 0.0, 'status': 'ERROR', 'responsive': False}
    
    def _format_window_response(self, window_response_data):
        """Format window response data for display in reports"""
        if not window_response_data:
            return "❌ NO_DATA"
        
        response_time = window_response_data.get('response_time_ms', 0.0)
        status = window_response_data.get('status', 'UNKNOWN')
        responsive = window_response_data.get('responsive', False)
        
        # Format the response time display based on performance thresholds
        if not responsive or status in ['TIMEOUT', 'UNRESPONSIVE', 'ERROR']:
            if status == 'TIMEOUT':
                return f"❌ TIMEOUT ({response_time}ms)"
            elif status == 'UNRESPONSIVE':
                return f"❌ UNRESPONSIVE"
            elif status == 'ERROR':
                return f"❌ ERROR"
            elif status == 'DISABLED':
                return f"⚪ DISABLED"
            elif status == 'NO_PROCESSES':
                return f"❌ NO_PROCESSES"
            else:
                return f"❌ {status}"
        
        # For responsive windows, format based on response time
        if response_time <= 50:      # Excellent (≤50ms)
            return f"✅ {response_time}ms"
        elif response_time <= 200:   # Good (≤200ms)
            return f"🟢 {response_time}ms"
        elif response_time <= 500:   # Moderate (≤500ms) 
            return f"🟡 {response_time}ms"
        elif response_time <= 1000:  # Slow (≤1s)
            return f"🟠 {response_time}ms"
        else:                        # Very slow (>1s)
            return f"🔴 {response_time}ms"
    
    def _detect_crashes(self, current_pids, pid_info):
        """Detect process crashes by comparing current and previous PIDs"""
        try:
            current_pid_set = set(current_pids)
            
            # First run - initialize tracking
            if not self._previous_pids:
                self._previous_pids = current_pid_set
                return False, []
            
            # Check for crashed processes
            crashed_pids = self._previous_pids - current_pid_set
            crashed_info = []
            
            if crashed_pids:
                LOGGER_WARNING(f"Detected crashed processes: {list(crashed_pids)}")
                
                # Determine which type of processes crashed
                main_pid = pid_info.get('main_pid')
                media_pid = pid_info.get('media_pid')
                
                for pid in crashed_pids:
                    if pid == main_pid:
                        crashed_info.append(f"Main process (PID:{pid})")
                    elif pid == media_pid:
                        crashed_info.append(f"Media process (PID:{pid})")
                    else:
                        crashed_info.append(f"Process (PID:{pid})")
                
                # Update tracking
                self._previous_pids = current_pid_set
                return True, crashed_info
            
            # Update tracking for next check
            self._previous_pids = current_pid_set
            return False, []
            
        except Exception as e:
            LOGGER_WARNING(f"Error in crash detection: {e}")
            return False, []
    
    def _detect_hangs(self, pid_info, window_response_data, process_info):
        """Detect process hangs using CPU activity and window responsiveness"""
        try:
            current_time = time.time()
            main_pid = pid_info.get('main_pid')
            media_pid = pid_info.get('media_pid')
            hung_processes = []
            
            # Get current CPU usage
            main_meta = process_info.get('main_meta', {})
            media_meta = process_info.get('media_meta', {})
            main_cpu = main_meta.get('cpu_percent', 0)
            media_cpu = media_meta.get('cpu_percent', 0)
            
            # Check main process for hang
            if main_pid:
                hang_detected, reason = self._check_process_hang(
                    main_pid, 
                    main_cpu, 
                    current_time,
                    self._hang_thresholds['main_timeout'],
                    window_response_data,
                    'main'
                )
                if hang_detected:
                    hung_processes.append(f"Main process: {reason}")
            
            # Check media process for hang  
            if media_pid:
                hang_detected, reason = self._check_process_hang(
                    media_pid,
                    media_cpu,
                    current_time, 
                    self._hang_thresholds['media_timeout'],
                    window_response_data,
                    'media'
                )
                if hang_detected:
                    hung_processes.append(f"Media process: {reason}")
            
            return len(hung_processes) > 0, hung_processes
            
        except Exception as e:
            LOGGER_WARNING(f"Error in hang detection: {e}")
            return False, []
    
    def _check_process_hang(self, pid, cpu_percent, current_time, timeout_threshold, window_response_data, process_type):
        """Check if a specific process is hanging"""
        try:
            # Initialize process history if needed
            if pid not in self._process_history:
                self._process_history[pid] = {
                    'last_seen': current_time,
                    'last_cpu_time': current_time,
                    'low_cpu_count': 0,
                    'first_low_cpu_time': None
                }
            
            history = self._process_history[pid]
            
            # Update last seen time
            history['last_seen'] = current_time
            
            # Check CPU activity
            if cpu_percent < self._hang_thresholds['low_cpu_threshold']:
                history['low_cpu_count'] += 1
                if history['first_low_cpu_time'] is None:
                    history['first_low_cpu_time'] = current_time
            else:
                # CPU activity detected - reset counters
                history['low_cpu_count'] = 0
                history['first_low_cpu_time'] = None
                history['last_cpu_time'] = current_time
                return False, ""
            
            # Check if we have enough consecutive low CPU readings
            if history['low_cpu_count'] >= self._hang_thresholds['min_checks_for_hang']:
                low_cpu_duration = current_time - history['first_low_cpu_time']
                
                # Check if low CPU duration exceeds threshold
                if low_cpu_duration >= timeout_threshold:
                    # For main process, also check window responsiveness
                    if process_type == 'main':
                        window_responsive = window_response_data.get('responsive', True)
                        if not window_responsive:
                            return True, f"Low CPU ({cpu_percent}%) for {low_cpu_duration:.1f}s + unresponsive windows"
                        else:
                            # High threshold for responsive windows (might be idle but functional)
                            if low_cpu_duration >= timeout_threshold * 2:
                                return True, f"Low CPU ({cpu_percent}%) for {low_cpu_duration:.1f}s (extended idle)"
                    else:
                        # Media process - stricter CPU-only check
                        return True, f"Low CPU ({cpu_percent}%) for {low_cpu_duration:.1f}s"
            
            return False, ""
            
        except Exception as e:
            LOGGER_DEBUG(f"Error checking hang for PID {pid}: {e}")
            return False, ""
    
    def _cleanup_process_history(self, current_pids):
        """Clean up history for processes that no longer exist"""
        try:
            current_pid_set = set(current_pids)
            pids_to_remove = []
            
            for pid in self._process_history.keys():
                if pid not in current_pid_set:
                    pids_to_remove.append(pid)
            
            for pid in pids_to_remove:
                del self._process_history[pid]
                LOGGER_DEBUG(f"Cleaned up history for terminated PID {pid}")
                
        except Exception as e:
            LOGGER_DEBUG(f"Error cleaning up process history: {e}")
    
    def _get_process_types(self, pid_info: Dict) -> Dict[str, Any]:
        """Generate detailed process type information from PID data"""
        try:
            import psutil
            
            main_pid = pid_info.get('main_pid')
            media_pid = pid_info.get('media_pid')
            all_pids = pid_info.get('all_pids', [])
            
            process_details = []
            process_type_counts = {'Main Application': 0, 'Media Handler': 0, 'Background Service': 0}
            
            for pid in all_pids:
                try:
                    proc = psutil.Process(pid)
                    cmdline = " ".join(proc.cmdline())
                    
                    # Classify process type based on command line and PID matching
                    if pid == main_pid and "Hosted" in cmdline:
                        process_type = "Main Application"
                        process_type_counts['Main Application'] += 1
                    elif pid == media_pid and "media" in cmdline.lower():
                        process_type = "Media Handler"
                        process_type_counts['Media Handler'] += 1
                    else:
                        process_type = "Background Service"
                        process_type_counts['Background Service'] += 1
                    
                    process_details.append({
                        'pid': pid,
                        'type': process_type,
                        'cmdline': cmdline[:100] + ('...' if len(cmdline) > 100 else '')  # Truncate long cmdlines
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Handle processes that may have terminated
                    process_details.append({
                        'pid': pid,
                        'type': 'Unknown (Terminated)',
                        'cmdline': 'Process not accessible'
                    })
                    continue
            
            # Generate summary string for the report
            summary_parts = []
            if process_type_counts['Main Application'] > 0:
                summary_parts.append(f"Main App ({process_type_counts['Main Application']})")
            if process_type_counts['Media Handler'] > 0:
                summary_parts.append(f"Media ({process_type_counts['Media Handler']})")
            if process_type_counts['Background Service'] > 0:
                summary_parts.append(f"Background ({process_type_counts['Background Service']})")
            
            summary = " + ".join(summary_parts) if summary_parts else "Webex Application"
            
            return {
                'summary': summary,
                'details': process_details,
                'counts': process_type_counts,
                'total_processes': len(all_pids)
            }
            
        except Exception as e:
            LOGGER_DEBUG(f"Error generating process types: {e}")
            return {
                'summary': 'Webex Application',
                'details': [],
                'counts': {'Unknown': len(pid_info.get('all_pids', []))},
                'total_processes': len(pid_info.get('all_pids', []))
            }

    def get_comprehensive_stress_status(self) -> Dict[str, Any]:
        """Get comprehensive stress testing status including process health and resource usage"""
        try:
            # Get basic process performance data
            main_cpu, main_mem, media_cpu, media_mem, main_gpu = self.process_handler.get_performance_cisco_collab_pid_meta()
            pid_info = self.process_handler.get_cisco_collab_pid_info()
            
            # Get current PIDs and clean up history
            current_pids = pid_info.get('all_pids', [])
            self._cleanup_process_history(current_pids)
            
            # Generate detailed process types information
            process_types_info = self._get_process_types(pid_info)
            
            # Build process status dict
            process_status = {
                'main_meta': {
                    'cpu_percent': main_cpu if main_cpu is not None else 0,
                    'memory_mb': main_mem if main_mem is not None else 0
                },
                'media_meta': {
                    'cpu_percent': media_cpu if media_cpu is not None else 0,
                    'memory_mb': media_mem if media_mem is not None else 0
                },
                'pid_info': pid_info,
                'process_types_detailed': process_types_info,  # Add detailed process info
            }
            
            # Get window response data for hang detection
            window_response_data = self._get_window_response_status(pid_info)
            
            # Perform real crash and hang detection
            crash_detected, crashed_processes = self._detect_crashes(current_pids, pid_info)
            hang_detected, hung_processes = self._detect_hangs(pid_info, window_response_data, process_status)
            
            # Update process status with real detection results
            process_status.update({
                'crash_detected': crash_detected,
                'hang_detected': hang_detected,
                'crashed_processes': crashed_processes,
                'hung_processes': hung_processes
            })
            
            # Add stress-specific analysis
            stress_status = {
                'timestamp': datetime.now().isoformat(),
                'process_info': process_status,
                'stress_analysis': self._analyze_stress_metrics(process_status),
                'health_status': self._determine_health_status(process_status),
                'process_count': len(current_pids),  # Use actual process count
                'window_response': window_response_data,  # Add window responsiveness
                'thresholds': {
                    'cpu_threshold': self.cpu_threshold,
                    'memory_threshold': self.memory_threshold
                }
            }
            
            return stress_status
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to get stress status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'health_status': 'ERROR'
            }
    
    def _analyze_stress_metrics(self, process_status: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stress-specific metrics from process status"""
        analysis = {
            'cpu_stress_level': 'NORMAL',
            'memory_stress_level': 'NORMAL',
            'overall_stress_level': 'NORMAL',
            'warnings': [],
            'recommendations': []
        }
        
        try:
            main_meta = process_status.get('main_meta', {})
            media_meta = process_status.get('media_meta', {})
            
            # Analyze CPU stress - calculate total CPU usage
            main_cpu = main_meta.get('cpu_percent', 0)
            media_cpu = media_meta.get('cpu_percent', 0)
            total_cpu = main_cpu + media_cpu
            
            if total_cpu > self.cpu_threshold:
                analysis['cpu_stress_level'] = 'HIGH'
                analysis['warnings'].append(f"High CPU usage detected: Total={total_cpu}% (Main={main_cpu}%, Media={media_cpu}%)")
                analysis['recommendations'].append("Consider reducing message frequency or test complexity")
            
            # Analyze memory stress - calculate total memory usage
            main_mem = main_meta.get('memory_mb', 0)
            media_mem = media_meta.get('memory_mb', 0)
            total_mem = main_mem + media_mem
            
            if total_mem > self.memory_threshold:
                analysis['memory_stress_level'] = 'HIGH'
                analysis['warnings'].append(f"High memory usage detected: Total={total_mem}MB (Main={main_mem}MB, Media={media_mem}MB)")
                analysis['recommendations'].append("Monitor for memory leaks during extended stress tests")
            
            # Determine overall stress level
            if analysis['cpu_stress_level'] == 'HIGH' or analysis['memory_stress_level'] == 'HIGH':
                analysis['overall_stress_level'] = 'HIGH'
            elif analysis['cpu_stress_level'] == 'MEDIUM' or analysis['memory_stress_level'] == 'MEDIUM':
                analysis['overall_stress_level'] = 'MEDIUM'
                
        except Exception as e:
            LOGGER_WARNING(f"Error analyzing stress metrics: {e}")
            analysis['warnings'].append(f"Analysis error: {str(e)}")
        
        return analysis
    
    def _determine_health_status(self, process_status: Dict[str, Any]) -> str:
        """Determine overall health status for stress testing with enhanced detection"""
        try:
            # Priority 1: Check for crashes (most critical)
            if process_status.get('crash_detected', False):
                crashed_processes = process_status.get('crashed_processes', [])
                if crashed_processes:
                    LOGGER_ERROR(f"Process crash detected: {', '.join(crashed_processes)}")
                return 'CRITICAL'
            
            # Priority 2: Check for hangs (high severity)
            if process_status.get('hang_detected', False):
                hung_processes = process_status.get('hung_processes', [])
                if hung_processes:
                    LOGGER_WARNING(f"Process hang detected: {', '.join(hung_processes)}")
                return 'UNHEALTHY'
            
            # Priority 3: Check resource thresholds and responsiveness
            main_meta = process_status.get('main_meta', {})
            media_meta = process_status.get('media_meta', {})
            
            main_cpu = main_meta.get('cpu_percent', 0)
            main_mem = main_meta.get('memory_mb', 0)
            media_cpu = media_meta.get('cpu_percent', 0)
            media_mem = media_meta.get('memory_mb', 0)
            
            # Calculate total usage for threshold comparison
            total_cpu = main_cpu + media_cpu
            total_mem = main_mem + media_mem
            
            # Check critical resource thresholds
            over_threshold = (total_cpu > self.cpu_threshold or total_mem > self.memory_threshold)
            
            # Check window responsiveness if available in stress_status context
            window_unresponsive = False
            try:
                # Try to get window response from parent stress_status if available
                # This is a bit of a hack since we don't have direct access here
                import inspect
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    caller_locals = frame.f_back.f_locals
                    if 'window_response_data' in caller_locals:
                        window_data = caller_locals['window_response_data']
                        window_unresponsive = not window_data.get('responsive', True)
            except:
                pass  # Fallback gracefully
            
            # Determine status based on multiple factors
            if over_threshold and window_unresponsive:
                LOGGER_WARNING(f"High resource usage (CPU:{total_cpu:.1f}%, Mem:{total_mem:.0f}MB) + unresponsive windows")
                return 'DEGRADED'
            elif over_threshold:
                LOGGER_INFO(f"High resource usage detected (CPU:{total_cpu:.1f}%, Mem:{total_mem:.0f}MB)")
                return 'WARNING' 
            elif window_unresponsive:
                LOGGER_WARNING("Windows unresponsive but resource usage normal")
                return 'SLUGGISH'
            
            return 'HEALTHY'
            
        except Exception as e:
            LOGGER_WARNING(f"Error determining health status: {e}")
            return 'UNKNOWN'
    
    def generate_stress_charts(self, stress_report_path: str) -> List[str]:
        """Generate stress testing charts and embed them in the report"""
        if not MATPLOTLIB_AVAILABLE:
            LOGGER_WARNING("Matplotlib not available, skipping chart generation")
            return []
            
        try:
            # Extract report info from path
            report_dir = Path(stress_report_path).parent
            report_filename = Path(stress_report_path).stem
            
            # Parse test suite from filename
            test_suite_match = re.search(r'stress-report-(.+)', report_filename)
            test_suite = test_suite_match.group(1) if test_suite_match else None
            
            # Get app version from report content
            app_version = self._extract_app_version_from_report(stress_report_path)
            
            LOGGER_INFO(f"Generating stress charts for: {stress_report_path}", "CYAN")
            
            # Get stress data from database
            db_handler = TestCaseDBHandler()
            stress_df = db_handler.get_stress_data(
                test_suite=test_suite,
                app_version=app_version
            )
            
            if stress_df.empty:
                LOGGER_WARNING("No stress data found in database", "YELLOW")
                return []
                
            LOGGER_INFO(f"Retrieved {len(stress_df)} stress records from database", "GREEN")
            
            # Create img directory if it doesn't exist
            img_dir = report_dir / 'img'
            img_dir.mkdir(exist_ok=True)
            LOGGER_INFO(f"Created/verified img directory: {img_dir}", "CYAN")
            
            generated_charts = []
            
            # Generate CPU stress chart
            cpu_chart_path = self._generate_cpu_stress_chart(stress_df, img_dir, stress_report_path)
            if cpu_chart_path:
                generated_charts.append(str(cpu_chart_path))
            
            # Generate Memory stress chart  
            memory_chart_path = self._generate_memory_stress_chart(stress_df, img_dir, stress_report_path)
            if memory_chart_path:
                generated_charts.append(str(memory_chart_path))
            
            # Generate Process health chart
            health_chart_path = self._generate_health_status_chart(stress_df, img_dir, stress_report_path)
            if health_chart_path:
                generated_charts.append(str(health_chart_path))
            
            # Update report with charts
            if generated_charts:
                self._embed_charts_in_report(stress_report_path, generated_charts)
                
            LOGGER_INFO(f"Generated {len(generated_charts)} stress charts successfully", "GREEN")
            return generated_charts
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate stress charts: {e}")
            return []
    
    def _generate_cpu_stress_chart(self, stress_df: pd.DataFrame, img_dir: Path, report_path: str) -> Optional[str]:
        """Generate CPU stress usage chart"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Plot CPU usage over time
            if 'test_time' in stress_df.columns:
                stress_df['test_time'] = pd.to_datetime(stress_df['test_time'])
                plt.plot(stress_df['test_time'], stress_df['main_cpu'], label='Main Process CPU', marker='o')
                plt.plot(stress_df['test_time'], stress_df['media_cpu'], label='Media Process CPU', marker='s')
                
                # Add threshold line
                plt.axhline(y=self.cpu_threshold, color='red', linestyle='--', label=f'Threshold ({self.cpu_threshold}%)')
                
                plt.xlabel('Time')
                plt.ylabel('CPU Usage (%)')
                plt.title('CPU Usage During Stress Testing')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save chart
                chart_path = img_dir / 'cpu_stress_chart.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                LOGGER_INFO(f"Generated CPU stress chart: {chart_path}")
                return str(chart_path)
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate CPU stress chart: {e}")
            plt.close()
        
        return None
    
    def _generate_memory_stress_chart(self, stress_df: pd.DataFrame, img_dir: Path, report_path: str) -> Optional[str]:
        """Generate Memory stress usage chart"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Plot memory usage over time
            if 'test_time' in stress_df.columns:
                stress_df['test_time'] = pd.to_datetime(stress_df['test_time'])
                plt.plot(stress_df['test_time'], stress_df['main_mem'], label='Main Process Memory', marker='o')
                plt.plot(stress_df['test_time'], stress_df['media_mem'], label='Media Process Memory', marker='s')
                
                # Add threshold line
                plt.axhline(y=self.memory_threshold, color='red', linestyle='--', label=f'Threshold ({self.memory_threshold}MB)')
                
                plt.xlabel('Time')
                plt.ylabel('Memory Usage (MB)')
                plt.title('Memory Usage During Stress Testing')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save chart
                chart_path = img_dir / 'memory_stress_chart.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                LOGGER_INFO(f"Generated Memory stress chart: {chart_path}")
                return str(chart_path)
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate Memory stress chart: {e}")
            plt.close()
        
        return None
    
    def _generate_health_status_chart(self, stress_df: pd.DataFrame, img_dir: Path, report_path: str) -> Optional[str]:
        """Generate health status distribution chart"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Count health status occurrences
            if 'process_status' in stress_df.columns:
                status_counts = stress_df['process_status'].value_counts()
                
                colors = {
                    'HEALTHY': 'green',
                    'WARNING': 'orange', 
                    'UNHEALTHY': 'red',
                    'CRITICAL': 'darkred',
                    'UNKNOWN': 'gray'
                }
                
                chart_colors = [colors.get(status, 'gray') for status in status_counts.index]
                
                plt.bar(status_counts.index, status_counts.values, color=chart_colors)
                plt.xlabel('Health Status')
                plt.ylabel('Count')
                plt.title('Process Health Status Distribution During Stress Testing')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save chart
                chart_path = img_dir / 'health_status_chart.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                LOGGER_INFO(f"Generated health status chart: {chart_path}")
                return str(chart_path)
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate health status chart: {e}")
            plt.close()
        
        return None
    
    def _extract_app_version_from_report(self, report_path: str) -> Optional[str]:
        """Extract app version from report content"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for version pattern in report header
            version_match = re.search(r'\[([0-9]+\.[0-9]+\.[0-9]+[^\]]*)\]', content)
            if version_match:
                return version_match.group(1)
                
        except Exception as e:
            LOGGER_WARNING(f"Failed to extract app version from report: {e}")
        
        return None
    
    def _embed_charts_in_report(self, report_path: str, chart_paths: List[str]):
        """Embed generated charts in the stress report"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add charts section before the data table
            charts_section = "\n## Stress Testing Charts\n\n"
            
            for chart_path in chart_paths:
                chart_name = Path(chart_path).stem.replace('_', ' ').title()
                relative_path = Path(chart_path).relative_to(Path(report_path).parent)
                charts_section += f"### {chart_name}\n\n"
                charts_section += f"![{chart_name}](./{relative_path})\n\n"
            
            # Insert charts section after the header but before the table
            lines = content.split('\n')
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('|') and 'Test Case' in line:
                    header_end = i
                    break
            
            if header_end > 0:
                lines.insert(header_end, charts_section)
                updated_content = '\n'.join(lines)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                LOGGER_INFO(f"Embedded {len(chart_paths)} charts in stress report")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to embed charts in report: {e}")

    def collect_and_save_stress_data(self, stress_report_path: str, test_case: Dict, execution_context) -> bool:
        """
        Collect comprehensive stress data and save to database and report
        
        Args:
            stress_report_path: Path to stress report file
            test_case: Test case information
            execution_context: Current execution context
            
        Returns:
            bool: True if data collection and saving was successful
        """
        try:
            # Get comprehensive stress status
            stress_data = self.get_comprehensive_stress_status()
            LOGGER_INFO(f"Debug: stress_data type: {type(stress_data)}", "DEBUG")
            LOGGER_INFO(f"Debug: stress_data: {stress_data}", "DEBUG")
            
            # Import and initialize database handler
            from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
            db_handler = TestCaseDBHandler()
            
            # Prepare data for database
            if isinstance(test_case, str):
                test_case_name = test_case
            else:
                test_case_name = test_case.get('name', 'Unknown')
            
            # Use actual control name if available, otherwise use generic format
            if hasattr(execution_context, 'current_control_name') and execution_context.current_control_name:
                step_name = execution_context.current_control_name
            else:
                step_name = f"stress_monitoring_{execution_context.step_index if hasattr(execution_context, 'step_index') else 0}"
            
            # Generate report ID if not available
            import uuid
            report_id = getattr(execution_context, 'report_id', str(uuid.uuid4()))
            
            # Save stress data to database using the correct method signature
            try:
                process_status = stress_data.get('process_status', {})
                system_status = stress_data.get('system_status', {})
                analysis = stress_data.get('analysis', {})
                
                # Calculate actual process count from pid_info
                process_info = stress_data.get('process_info', {})
                pid_info = process_info.get('pid_info', {})
                actual_process_count = len(pid_info.get('all_pids', []))
                
                # Get detailed process types for database
                process_types_data = process_info.get('process_types_detailed', {})
                process_types_summary = process_types_data.get('summary', 'Webex Application')
                
                db_handler.insert_stress_report(
                    report_id=report_id,
                    test_case=test_case_name,
                    control_name=step_name,
                    main_cpu=process_status.get('cpu_percent'),
                    main_mem=process_status.get('memory_mb'),
                    cpu_check='PASS' if analysis.get('cpu_stress_level') == 'NORMAL' else 'WARNING' if analysis.get('cpu_stress_level') == 'MEDIUM' else 'FAIL',
                    memory_check='PASS' if analysis.get('memory_stress_level') == 'NORMAL' else 'WARNING' if analysis.get('memory_stress_level') == 'MEDIUM' else 'FAIL',
                    process_count=actual_process_count,  # Use actual process count
                    process_types=process_types_summary,  # Use detailed process types
                    process_status=stress_data.get('health_status', 'UNKNOWN').upper(),
                    warnings=str(analysis.get('warnings', [])) if analysis.get('warnings') else None
                )
                LOGGER_INFO(f"Successfully saved stress data to database for: {test_case_name}")
            except Exception as db_error:
                LOGGER_ERROR(f"Failed to insert stress report to database: {db_error}")
                LOGGER_INFO(f"Continuing with report generation despite database error")
            
            # Generate stress report if path provided
            if stress_report_path:
                # Import report handler to write stress report body
                from rs_sdk.utils.report_handler import write_stress_report_body
                
                # Prepare data for the enhanced stress report format with safe key access
                raw_image_path = getattr(execution_context, 'current_control_image', '') if hasattr(execution_context, 'current_control_image') else ''
                LOGGER_DEBUG(f"DEBUG: raw_image_path = {raw_image_path}")
                
                # Calculate relative path for image (similar to navigation report)
                image_path = ''
                if raw_image_path:
                    # Calculate relative path from stress report file to image file
                    image_path = os.path.relpath(raw_image_path, os.path.dirname(stress_report_path))
                    # Convert to forward slashes for HTML compatibility
                    image_path = image_path.replace('\\', '/')
                    LOGGER_INFO(f"DEBUG: Stress report image_path = {image_path}", "GREEN")
                else:
                    LOGGER_WARNING(f"DEBUG: No raw_image_path found in execution_context", "YELLOW")
                
                # Safely extract process data from nested structure
                process_info = stress_data.get('process_info', {})
                main_meta = process_info.get('main_meta', {})
                media_meta = process_info.get('media_meta', {})
                
                main_cpu_formatted = f"{main_meta.get('cpu_percent', 0.0)}"
                main_mem_formatted = f"{main_meta.get('memory_mb', 0.0)}"
                
                media_cpu = media_meta.get('cpu_percent', 0.0)
                media_mem = media_meta.get('memory_mb', 0.0)
                
                # Safely extract analysis data
                analysis = stress_data.get('stress_analysis', {})
                cpu_check = 'PASS' if analysis.get('cpu_stress_level') == 'NORMAL' else 'FAIL'
                memory_check = 'PASS' if analysis.get('memory_stress_level') == 'NORMAL' else 'FAIL'
                
                # Format process types with detailed information
                process_types_data = stress_data.get('process_info', {}).get('process_types_detailed', {})
                process_types = process_types_data.get('summary', 'Webex Application')
                
                # Format window response with actual measurements
                window_response_data = stress_data.get('window_response', {})
                window_response = self._format_window_response(window_response_data)
                
                # Format process status
                health_status = stress_data.get('health_status', 'UNKNOWN').upper()
                
                # Process AI check results if available
                ai_check_status = ''
                participants_number = ''
                
                if hasattr(execution_context, 'ai_check_result') and execution_context.ai_check_result:
                    ai_result = execution_context.ai_check_result
                    if ai_result.llm_response:
                        llm_response = ai_result.llm_response
                        
                        # Check if AI check was successful (not just "." or empty)
                        if llm_response and llm_response.strip() != '.' and llm_response.strip():
                            ai_check_status = 'PASS'
                            
                            # Extract participant count if present
                            if 'PARTICIPANTS_COUNT:' in llm_response:
                                try:
                                    # Extract number after "PARTICIPANTS_COUNT:"
                                    parts = llm_response.split('PARTICIPANTS_COUNT:')
                                    if len(parts) > 1:
                                        # Get the number part and clean it
                                        number_part = parts[1].strip().split()[0]  # Get first word after colon
                                        # Remove any trailing punctuation
                                        participants_number = ''.join(c for c in number_part if c.isdigit())
                                except Exception as e:
                                    LOGGER_DEBUG(f"Error extracting participant count: {e}")
                        else:
                            ai_check_status = 'FAIL'
                
                # Format issues if any
                issues = ', '.join(analysis.get('warnings', [])) if analysis.get('warnings') else ''
                
                # Write to stress report
                write_stress_report_body(
                    report_path=stress_report_path,
                    test_case=test_case_name,
                    ctrl_desc=step_name,
                    image=image_path,
                    main_cpu=main_cpu_formatted,
                    main_mem=main_mem_formatted,
                    media_cpu=f"{media_cpu}",
                    media_mem=f"{media_mem}",
                    cpu_check=cpu_check,
                    memory_check=memory_check,
                    process_count=str(stress_data.get('process_count', 1)),  # Use actual process count from stress_data
                    process_types=process_types,
                    window_response=window_response,
                    process_status=health_status,
                    ai_check=ai_check_status,
                    participants_number=participants_number,
                    issues=issues,
                    log_archive=''  # Can be enhanced later
                )
                LOGGER_INFO(f"Successfully wrote stress report entry for: {test_case_name}")
                
                # Generate charts and update report
                chart_paths = self.generate_stress_charts(stress_report_path)
                if chart_paths:
                    self._embed_charts_in_report(stress_report_path, chart_paths)
            
            LOGGER_INFO(f"Successfully collected and saved stress data for test case: {test_case_name}")
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to collect and save stress data: {e}")
            return False

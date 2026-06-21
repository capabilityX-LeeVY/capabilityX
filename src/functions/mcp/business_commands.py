#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebexRegressSheild MCP business command implementations
"""
import sys
import os
import subprocess
from typing import Dict, Any

# Robust path setup - ensure correct module paths regardless of where called from
def setup_project_paths():
    """Setup project paths to ensure all dependency modules can be found"""
    # Method 1: Based on current file location
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_1 = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
    src_dir_1 = os.path.join(project_root_1, 'src')
    
    # Method 2: Based on current working directory
    cwd = os.getcwd()
    
    # Method 3: Find parent directory containing src directory
    project_root_2 = None
    search_dir = current_file_dir
    for _ in range(5):  # Search up to 5 levels
        if os.path.exists(os.path.join(search_dir, 'src', 'run_test_case_job.py')):
            project_root_2 = search_dir
            break
        search_dir = os.path.dirname(search_dir)
    
    print(f"🔍 Path setup debug:")
    print(f"  Current file: {__file__}")
    print(f"  Current file dir: {current_file_dir}")
    print(f"  Current working dir: {cwd}")
    print(f"  Project root (method 1): {project_root_1}")
    print(f"  Project root (method 2): {project_root_2}")
    
    # Choose the best project root directory
    project_root = project_root_2 if project_root_2 else project_root_1
    src_dir = os.path.join(project_root, 'src')
    
    print(f"  Selected project root: {project_root}")
    print(f"  Selected src dir: {src_dir}")
    print(f"  run_test_case_job.py exists: {os.path.exists(os.path.join(src_dir, 'run_test_case_job.py'))}")
    
    # Add paths to sys.path (if not already there)
    paths_to_add = [project_root, src_dir]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
            print(f"  ✅ Added to sys.path: {path}")
        else:
            print(f"  ⏭️ Already in sys.path: {path}")
    
    # Change working directory to src (if possible)
    try:
        if os.path.exists(src_dir):
            original_cwd = os.getcwd()
            os.chdir(src_dir)
            print(f"  ✅ Changed working directory: {original_cwd} -> {src_dir}")
        else:
            print(f"  ⚠️ src directory does not exist: {src_dir}")
    except Exception as e:
        print(f"  ⚠️ Could not change working directory: {e}")
    
    return project_root, src_dir

# Execute path setup
print("🚀 Setting up project paths...")
PROJECT_ROOT, SRC_DIR = setup_project_paths()

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

def load_progress_config():
    """Load progress configuration file"""
    import json
    try:
        config_path = os.path.join(SRC_DIR, 'config', 'progress_config.json')
        print(f"🔍 Loading progress config from: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Progress config loaded successfully")
            return config
        else:
            print(f"⚠️ Progress config file not found, using defaults")
            # Return default configuration
            return {
                "progress_server": {
                    "enabled": True,
                    "url": "https://wrs.qa.webex.com/mcp",
                    "timeout": 10,
                    "retry_attempts": 3,
                    "retry_delay": 1.0
                },
                "workflow_settings": {
                    "default_workflow_type": "test_execution",
                    "step_delay": 0.5,
                    "log_progress": True,
                    "send_detailed_info": True
                },
                "client_settings": {
                    "auto_generate_id": True,
                    "id_prefix": "mcp_client",
                    "clear_on_start": False,
                    "clear_on_completion": True
                }
            }
    except Exception as e:
        print(f"❌ Error loading progress config: {e}")
        # Return disabled configuration
        return {
            "progress_server": {"enabled": False},
            "workflow_settings": {"log_progress": True},
            "client_settings": {"id_prefix": "mcp_client"}
        }

def load_mcp_progress_config():
    """Load MCP performance configuration file"""
    import json
    try:
        config_path = os.path.join(SRC_DIR, 'config', 'mcp_performance_config.json')
        print(f"🔍 Loading MCP performance config from: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ MCP performance config loaded successfully")
            return config
        else:
            print(f"⚠️ MCP performance config file not found, using defaults")
            # Return default configuration with HTTP (not HTTPS)
            return {
                "progress_server": {
                    "enabled": True,
                    "url": "https://wrs.qa.webex.com/mcp",
                    "timeout": 10,
                    "retry_attempts": 3,
                    "retry_delay": 1.0
                },
                "workflow_settings": {
                    "default_workflow_type": "test_execution",
                    "step_delay": 0.5,
                    "log_progress": True,
                    "send_detailed_info": True
                },
                "client_settings": {
                    "auto_generate_id": True,
                    "id_prefix": "mcp_client",
                    "clear_on_start": False,
                    "clear_on_completion": True
                }
            }
    except Exception as e:
        print(f"❌ Error loading MCP performance config: {e}")
        # Return disabled configuration
        return {
            "progress_server": {"enabled": False},
            "workflow_settings": {"log_progress": True},
            "client_settings": {"id_prefix": "mcp_client"}
        }

try:
    # Delayed import - avoid immediate initialization during module loading
    print(f"🔍 TestCaseJobRunner import available")
    TestCaseJobRunner = None  # Delayed loading
except ImportError as e:
    print(f"❌ Could not prepare TestCaseJobRunner import: {e}")
    import traceback
    traceback.print_exc()
    run_suite_case = None
    TestCaseJobRunner = None

def get_test_case_job_runner():
    """Delayed TestCaseJobRunner instance acquisition"""
    print(f"🔧 [GET_RUNNER] Entering get_test_case_job_runner function")
    global TestCaseJobRunner
    print(f"🔧 [GET_RUNNER] Current TestCaseJobRunner value: {TestCaseJobRunner}")
    
    if TestCaseJobRunner is None:
        print(f"🔧 [GET_RUNNER] TestCaseJobRunner is None, attempting import...")
        try:
            print(f"🔧 [GET_RUNNER] About to import from run_test_case_job...")
            print(f"🔧 [GET_RUNNER] Current working directory: {os.getcwd()}")
            print(f"🔧 [GET_RUNNER] run_test_case_job.py exists: {os.path.exists('run_test_case_job.py')}")
            
            # First try to import module, not the class
            print(f"🔧 [GET_RUNNER] Step 1: Importing module...")
            import run_test_case_job
            print(f"🔧 [GET_RUNNER] Step 1 SUCCESS: Module imported: {run_test_case_job}")
            
            # Then try to access the class
            print(f"🔧 [GET_RUNNER] Step 2: Getting class from module...")
            TCJR = run_test_case_job.TestCaseJobRunner
            print(f"🔧 [GET_RUNNER] Step 2 SUCCESS: Class obtained: {TCJR}")
            
            # Finally assign
            print(f"🔧 [GET_RUNNER] Step 3: Assigning to global variable...")
            TestCaseJobRunner = TCJR
            print(f"✅ [GET_RUNNER] TestCaseJobRunner imported successfully: {TestCaseJobRunner}")
            
        except ImportError as e:
            print(f"❌ [GET_RUNNER] Import error: {e}")
            import traceback
            print(f"❌ [GET_RUNNER] Full traceback:")
            traceback.print_exc()
            raise
        except AttributeError as e:
            print(f"❌ [GET_RUNNER] Attribute error (class not found): {e}")
            import traceback
            print(f"❌ [GET_RUNNER] Full traceback:")
            traceback.print_exc()
            raise
        except Exception as e:
            print(f"❌ [GET_RUNNER] Unexpected error during import: {e}")
            print(f"❌ [GET_RUNNER] Error type: {type(e)}")
            import traceback
            print(f"❌ [GET_RUNNER] Full traceback:")
            traceback.print_exc()
            raise
    else:
        print(f"🔧 [GET_RUNNER] TestCaseJobRunner already imported, returning: {TestCaseJobRunner}")
    
    print(f"🔧 [GET_RUNNER] Returning TestCaseJobRunner: {TestCaseJobRunner}")
    return TestCaseJobRunner


def handle_run_test_suite(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run test suite"""
    try:
        # Re-check path setup before execution each time
        print("🔄 Re-checking path setup before execution...")
        setup_project_paths()
        
        suite_names = params.get('suite_names', ['smoke'])
        mode = params.get('mode', 'suite')
        platform = params.get('platform', 'windows')
        
        print(f"🚀 Starting test suite execution: {suite_names}")
        print(f"📋 Mode: {mode}, Platform: {platform}")
        
        # Declare global variable
        global TestCaseJobRunner
        
        print(f"🔍 TestCaseJobRunner status: {TestCaseJobRunner}")
        
        # Record received parameters
        execution_log = {
            "received_params": params,
            "suite_names": suite_names,
            "mode": mode,
            "platform": platform,
            "testcasejobrunner_available": "not_yet_loaded",
            "current_working_dir": os.getcwd(),
            "sys_path_first_3": sys.path[:3],
            "timestamp": __import__('time').time()
        }
        
        # Directly try to use TestCaseJobRunner (most reliable method)
        try:
            # Import TestCaseJobRunner directly
            from run_test_case_job import TestCaseJobRunner
            
            # Get first test suite name
            test_suite = suite_names[0] if suite_names else 'smoke'
            
            print(f"🚀 Using TestCaseJobRunner for: {test_suite}")
            
            # Create and run test suite
            runner = TestCaseJobRunner()
            print(f"✅ TestCaseJobRunner instance created successfully")
            
            # Execute test suite
            print(f"📋 Executing test suite: {test_suite}")
            result = runner.run_complete_workflow_with_ui_response(test_suite)
            print(f"✅ Test suite {test_suite} execution completed")
            
            return {
                "success": True,
                "result": f"Test suite '{test_suite}' executed successfully",
                "test_suite": test_suite,
                "suite_names": suite_names,
                "mode": mode,
                "platform": platform,
                "execution_method": "TestCaseJobRunner",
                "execution_log": execution_log,
                "note": "Test execution completed, check application logs for detailed results"
            }
            
        except Exception as runner_error:
            print(f"❌ TestCaseJobRunner execution failed: {runner_error}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"TestCaseJobRunner execution failed: {str(runner_error)}",
                "test_suite": test_suite,
                "suite_names": suite_names,
                "execution_method": "TestCaseJobRunner",
                "execution_log": execution_log
            }

    except Exception as e:
        print(f"❌ Handle run test suite error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": f"Failed to run test suite: {str(e)}",
            "suite_names": params.get('suite_names', ['smoke']),
            "exception_type": type(e).__name__
        }


def handle_run_single_test(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run single test case"""
    try:
        # Import TestCaseJobRunner directly
        from run_test_case_job import TestCaseJobRunner
            
        test_case = params.get('test_case')
        if not test_case:
            return {"success": False, "error": "test_case parameter is required"}
        
        # Use TestCaseJobRunner class
        runner = TestCaseJobRunner()
        result = runner.run_complete_workflow_with_ui_response(test_case)
        
        return {
            "success": True,
            "result": f"Test case runner executed successfully",
            "test_case": test_case
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run test case: {str(e)}"
        }


def handle_get_test_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get test report"""
    try:
        report_type = params.get('report_type', 'latest')
        
        # Check report directory
        report_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'report')
        if not os.path.exists(report_dir):
            return {"success": False, "error": "Report directory not found"}
        
        # Get latest report file
        report_files = [f for f in os.listdir(report_dir) if f.endswith('.html') or f.endswith('.json')]
        if not report_files:
            return {"success": False, "error": "No report files found"}
        
        latest_report = max(report_files, key=lambda x: os.path.getmtime(os.path.join(report_dir, x)))
        
        return {
            "success": True,
            "result": f"Latest report: {latest_report}",
            "report_path": os.path.join(report_dir, latest_report),
            "available_reports": report_files
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get test report: {str(e)}"
        }


def handle_cleanup_test_environment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Clean test environment"""
    try:
        cleanup_type = params.get('cleanup_type', 'basic')
        
        result = []
        
        # Clean temporary files
        temp_dirs = ['src/__pycache__', 'src/build/run_record']
        for temp_dir in temp_dirs:
            temp_path = os.path.join(os.path.dirname(__file__), '..', '..', temp_dir)
            if os.path.exists(temp_path):
                try:
                    import shutil
                    shutil.rmtree(temp_path)
                    result.append(f"Cleaned: {temp_dir}")
                except Exception as e:
                    result.append(f"Failed to clean {temp_dir}: {str(e)}")
        
        # Clean log files (if needed)
        if cleanup_type == 'full':
            log_files = ['src/logs/task_output.log', '@AutomationLog.txt']
            for log_file in log_files:
                log_path = os.path.join(os.path.dirname(__file__), '..', '..', log_file)
                if os.path.exists(log_path):
                    try:
                        open(log_path, 'w').close()  # Clear file
                        result.append(f"Cleared: {log_file}")
                    except Exception as e:
                        result.append(f"Failed to clear {log_file}: {str(e)}")
        
        return {
            "success": True,
            "result": "Environment cleanup completed",
            "details": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to cleanup environment: {str(e)}"
        }


def handle_get_test_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get test status"""
    try:
        import psutil
        
        # Check if there are running test processes
        running_tests = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in ['run_suite_case', 'run_test_case', 'pytest']):
                    running_tests.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "success": True,
            "result": f"Found {len(running_tests)} running test processes",
            "running_tests": running_tests,
            "test_framework_available": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get test status: {str(e)}"
        }


def handle_execute_workflow(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute workflow - supports complete test workflow"""
    import threading
    import time
    
    try:
        # Robust path setup
        setup_project_paths()
        
        # Extract configuration from parameters
        workflow_type = params.get('workflow_type', 'complete')  # 'complete' or 'explorer'
        test_suite = params.get('test_suite', None)
        enable_sr_analysis = params.get('enable_sr_analysis', True)
        enable_upload = params.get('enable_upload', True)
        acc_case = params.get('acc_case', False)
        # Basic configuration object
        build_config = params.get('build_config', {})
        
        # Platform and owner information
        platform = params.get('platform', 'windows')
        test_owner = params.get('test_owner', 'default')
        location = params.get('location', 'Shanghai')
        build_type = params.get('build_type', 'Qt6build')
        
        # Version configuration
        version_config = params.get('version_config', {})
        version_mode = version_config.get('mode', 'latest')
        version_value = version_config.get('value', 'release')
        
        # Environment configuration
        environment = params.get('environment', {})
        username = environment.get('username', '')
        password = environment.get('password', '')  # Already masked
        has_credentials = environment.get('has_credentials', False)
        
        # Validation points configuration
        validation_points = params.get('validation_points', {})
        validate_kb = validation_points.get('kb', False)
        validate_sr = validation_points.get('sr', False) 
        validate_fr = validation_points.get('fr', False)
        validate_ai_verify = validation_points.get('ai_verify', False)
        validate_performance = validation_points.get('performance', False)
        validate_ui_legacy = validation_points.get('ui_legacy', False)
        
        # Execution context
        execution_context = params.get('execution_context', {})
        source = execution_context.get('source', 'webex_regress_shield_ai_gateway')
        test_suite_name = execution_context.get('test_suite_name', test_suite)  # Backup test_suite
        timestamp = execution_context.get('timestamp', '')
        
        # Create pramas as JSON string to store all extracted parameters
        import json
        build_config_pramas = json.dumps({
            "test_suite": test_suite,
            "acc_case": acc_case,
            "account": username,
            "owner": test_owner,
            "platform": platform,
            "location": location,
            "build_type": build_type,
            "version_config": {
                "mode": version_mode,
                "value": version_value
            },
            "validation_points": {
                "kb": validate_kb,
                "sr": validate_sr,
                "fr": validate_fr,
                "ai_verify": validate_ai_verify,
                "performance": validate_performance,
                "ui_legacy": validate_ui_legacy
            }})
        acc_case_pramas = json.dumps({
            "acc_case": acc_case,
            "test_suite": test_suite
        })
        print(f"{build_config_pramas}")
        
        if workflow_type == 'complete':
            # Use TestCaseJobRunner to execute complete workflow - synchronous execution
            print(f"📋 [EXECUTE_WORKFLOW] Executing complete workflow using TestCaseJobRunner (sync)...")
            
            try:
                import time
                import platform
                
                # Import TestCaseJobRunner directly
                print(f"🔧 [SYNC_WORKFLOW] Importing TestCaseJobRunner directly...")
                from run_test_case_job import TestCaseJobRunner
                print(f"✅ [SYNC_WORKFLOW] TestCaseJobRunner imported successfully: {TestCaseJobRunner}")
                
                # Note: COM initialization is handled internally by TestCaseJobRunner's Windows_Main()
                print(f"ℹ️ [SYNC_WORKFLOW] COM initialization will be handled by TestCaseJobRunner internally")
                
                # Create TestCaseJobRunner instance
                print(f"🔧 [SYNC_WORKFLOW] Creating TestCaseJobRunner instance...")
                test_runner = TestCaseJobRunner()
                print(f"✅ [SYNC_WORKFLOW] TestCaseJobRunner instance created successfully")
                
                # Update settings.json with build configuration after TestCaseJobRunner creation
                # This ensures our settings won't be overwritten by StartupInitializer
                # print(f"🔧 [SYNC_WORKFLOW] Updating settings.json with build configuration...")
                # update_settings_from_build_config(build_config_pramas)
                # print(f"✅ [SYNC_WORKFLOW] Build configuration applied successfully")                # Record start time
                start_time = time.time()
                print(f"🕐 [SYNC_WORKFLOW] Starting execution at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
                
                # Call run_complete_workflow and wait for completion
                print(f"▶️ [SYNC_WORKFLOW] ======== About to call run_complete_workflow ========")
                print(f"   test_suite: {test_suite}")
                
                def create_mcp_progress_callback():
                    """Create MCP progress callback function"""
                    
                    def mcp_progress_callback(progress_data):
                        """
                        MCP progress callback function - receives progress data from suite_case_runner
                        Args:
                            progress_data: Progress data in string or dictionary format
                        """
                        try:
                            print(f"📊 [MCP_PROGRESS] Received: {progress_data}")
                            
                            # Handle different formats of progress data
                            if isinstance(progress_data, dict):
                                # Dictionary format: detailed data from suite_case_runner
                                step = progress_data.get('step', 'unknown')
                                status = progress_data.get('status', 'unknown')
                                message = progress_data.get('message', str(progress_data))
                                
                                # Build generic progress server message format
                                normalized_progress = {
                                    "step": step,
                                    "status": status,
                                    "message": message,
                                    "timestamp": time.time(),
                                    "test_case_name": step,
                                    "test_result": "PASS" if status == "completed" else "FAIL",
                                   
                                }
                            else:
                                # String format: simple progress message
                                normalized_progress = {
                                    "step": "test_execution",
                                    "status": "completed" if "Completed" in str(progress_data) else "running",
                                    "message": str(progress_data),
                                    "timestamp": time.time(),
                                  
                                }
                            
                            # Generate client ID
                            import socket
                            client_id = f"mcp_client_{socket.gethostname()}_{int(time.time())}"
                            
                            # Build generic progress server message format
                            message_data = {
                                "type": "workflow_progress",
                                "client_id": client_id,
                                "workflow_type": "test_execution",
                                "progress": normalized_progress,
                                "timestamp": time.time()
                            }
                            
                            # Send to generic progress server
                            try:
                                # Use progress server configuration
                                progress_config = load_mcp_progress_config()
                                server_url = progress_config.get("progress_server", {}).get("url", "https://wrs.qa.webex.com/mcp")
                                timeout = progress_config.get("progress_server", {}).get("timeout", 3)
                                
                                print(f"📤 [PROGRESS] Sending to {server_url}: {normalized_progress['step']} - {normalized_progress['status']}")
                                print(f"   Message: {normalized_progress['message']}")
                                
                                import requests
                                response = requests.post(
                                    f"{server_url}/workflow_progress",
                                    json=message_data,
                                    timeout=timeout
                                )
                                
                                if response.status_code == 200:
                                    print(f"✅ [PROGRESS] Progress sent successfully to server")
                                else:
                                    print(f"⚠️ [PROGRESS] Server response: {response.status_code}")
                                    
                            except Exception as send_error:
                                print(f"❌ [PROGRESS] Error sending to progress server: {send_error}")
                            
                            # Always print progress info to console as backup
                            print(f"📊 [PROGRESS] {normalized_progress.get('message', str(progress_data))}")
                            
                        except Exception as callback_error:
                            print(f"❌ [MCP_PROGRESS] Error in MCP progress callback: {callback_error}")
                            import traceback
                            traceback.print_exc()
                    
                    return mcp_progress_callback
                
                # Create MCP progress callback
                mcp_progress_callback = create_mcp_progress_callback()
                print(f"✅ [SYNC_WORKFLOW] MCP progress callback created")
                
                # Check if acc_case is true to determine which function to call
                if acc_case:
                    print(f"🎯 [ACC_WORKFLOW] acc_case is True, calling run_acc_testcase instead")
                    print(f"   test_suite: {test_suite}")
                    print(f"   build_config_pramas: {build_config_pramas}")
                    
                    workflow_result = test_runner.run_acc_testcase(
                        test_suite=test_suite,
                        pramas=acc_case_pramas
                    )
                else:
                    # Call run_complete_workflow with progress callback
                    print(f"▶️ [SYNC_WORKFLOW] ======== About to call run_complete_workflow with MCP progress callback ========")
                    print(f"   test_suite: {test_suite}")
                    print(f"   progress_callback: {mcp_progress_callback}")
                    
                    workflow_result = test_runner.run_complete_workflow_with_ui_response(
                        test_suite=test_suite,
                        progress_callback=mcp_progress_callback,
                        pramas=build_config_pramas,
                        return_report_url=True
                    )
                # Record end time
                end_time = time.time()
                duration = end_time - start_time
                print(f"🕐 [SYNC_WORKFLOW] Execution completed at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))} (took {duration:.2f}s)")
                
                print(f"✅ [SYNC_WORKFLOW] Complete workflow executed successfully")
                print(f"   Result: {workflow_result}")
                print(f"   Result type: {type(workflow_result)}")
                
                # Note: COM cleanup is handled internally by TestCaseJobRunner
                print(f"ℹ️ [SYNC_WORKFLOW] COM cleanup handled by TestCaseJobRunner internally")
                
                # Extract report URL - simplified logic
                report_url = None
                if isinstance(workflow_result, tuple) and len(workflow_result) >= 2:
                    # Get the second element as report URL from tuple
                    report_url = workflow_result[1]
                elif isinstance(workflow_result, str):
                    # Direct string is the report URL
                    report_url = workflow_result
                
                print(f"📋 [FINAL] Report URL: {report_url}")
                
                # Return simplified result with just the report URL
                return {
                    "success": True,
                    "test_suite": test_suite or "default",
                    "report_url": report_url
                }
                
            except Exception as e:
                print(f"❌ [SYNC_WORKFLOW] Workflow execution failed: {str(e)}")
                print(f"❌ [SYNC_WORKFLOW] Exception type: {type(e)}")
                import traceback
                print(f"❌ [SYNC_WORKFLOW] Traceback:")
                traceback.print_exc()
                
                # Note: COM cleanup is handled internally by TestCaseJobRunner
                print(f"ℹ️ [SYNC_WORKFLOW] COM cleanup handled by TestCaseJobRunner internally")
                
                return {
                    "success": False,
                    "test_suite": test_suite or "default",
                    "error": str(e),
                    "report_url": None
                }
                
        else:
            # Use original run_explorer.py (backward compatibility)
            workflow = params.get('workflow', 'sign_in')
            print(f"🔧 [EXECUTE_WORKFLOW] Using legacy explorer workflow: {workflow}")
            
            cmd = [
                sys.executable, '-u', 
                os.path.join(os.path.dirname(__file__), '..', '..', 'run_explorer.py'),
                '--workflow', workflow
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "result": f"Explorer workflow '{workflow}' executed",
                "workflow_type": "explorer",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "test_suite": test_suite or "default", 
            "error": "Workflow timed out after 5 minutes",
            "report_url": None
        }
    except Exception as e:
        error_msg = f"Failed to execute workflow: {str(e)}"
        print(f"❌ [EXECUTE_WORKFLOW] {error_msg}")
        return {
            "success": False,
            "test_suite": test_suite or "default",
            "error": error_msg,
            "report_url": None
        }

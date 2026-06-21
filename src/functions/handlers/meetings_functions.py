"""
Meeting-related functions for Webex meetings
"""
import os
import sys
import subprocess
from typing import Optional

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from core.suite_case_runner import SuiteCaseRunner
from core.test_case_runner import TestCaseRunner
from core.test_job_orchestrator import TestJobOrchestrator
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING

# ── Auto git-pull ────────────────────────────────────────────────
_AUTO_PULL = os.getenv("AGENT_AUTO_PULL", "").lower() in ("1", "true", "yes")
_GIT_REMOTE = os.getenv("AGENT_GIT_REMOTE", "origin")
_GIT_BRANCH = os.getenv("AGENT_GIT_BRANCH", "main")
_DEPLOY_KEY = os.getenv("WRS_DEPLOY_KEY", "")
# Repo root = project root (two levels up from this file)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def sync_code(remote: Optional[str] = None, branch: Optional[str] = None, restart: bool = False) -> dict:
    remote = remote or _GIT_REMOTE
    branch = branch or _GIT_BRANCH
    try:
        env = os.environ.copy()
        if _DEPLOY_KEY:
            key = os.path.expanduser(_DEPLOY_KEY)
            if os.path.isfile(key):
                env["GIT_SSH_COMMAND"] = f"ssh -i {key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
        result = subprocess.run(
            ["git", "pull", remote, branch],
            cwd=_REPO_ROOT, capture_output=True, text=True, timeout=60, env=env,
        )
        ok = result.returncode == 0
        restarting = False
        if ok and restart and "Already up to date" not in result.stdout:
            from functions.api.server import request_restart
            request_restart(delay=1.5)
            restarting = True
        return {
            "success": ok,
            "message": (result.stdout if ok else result.stderr).strip(),
            "stdout": result.stdout, "stderr": result.stderr, "restarting": restarting,
        }
    except Exception as e:
        msg = "git pull timed out" if isinstance(e, subprocess.TimeoutExpired) else \
              "git not found on PATH" if isinstance(e, FileNotFoundError) else str(e)
        LOGGER_ERROR(msg)
        return {"success": False, "message": msg, "stdout": "", "stderr": "", "restarting": False}


def _auto_pull_if_enabled():
    if _AUTO_PULL:
        LOGGER_INFO(f"AGENT_AUTO_PULL is enabled — pulling {_GIT_REMOTE}/{_GIT_BRANCH}")
        sync_code()


def run_test_suite_function(test_suite_name: str, platform: str = "windows"):
    """
    Run a test suite using TestCaseRunner
    
    Args:
        test_suite_name (str): Name of the test suite to run (e.g., "web_video_vbg", "smoke")
        platform (str): Platform to run on (default: "windows")
        
    Returns:
        dict: Result of the test suite execution
    """
    try:
        # Create test case runner instance
        test_runner = TestCaseRunner(platform=platform)
        
        # Execute the test suite using run_test_suite method
        navigate_report_path, performance_report_path, stress_report_path = test_runner.run_test_suite(
            test_suite=test_suite_name,
            mode="suite"
        )
        
        return {
            "status": "success",
            "message": f"Test suite '{test_suite_name}' executed successfully on {platform}",
            "test_suite_name": test_suite_name,
            "platform": platform,
            "navigate_report_path": navigate_report_path,
            "performance_report_path": performance_report_path,
            "stress_report_path": stress_report_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test suite '{test_suite_name}' execution failed: {str(e)}",
            "test_suite_name": test_suite_name,
            "platform": platform,
            "navigate_report_path": None,
            "performance_report_path": None,
            "stress_report_path": None
        }


def run_meetings_functions(test_suite_list = ['smoke']):
    """
    Run the specified test suites for Webex meetings
    """
    suite_case_runner = SuiteCaseRunner()
    suite_case_runner.run(test_suite_list)
    
    return {
        "status": "success",
        "message": "meeting started successfully",
        "action": "start_meeting"
    }


def run_test_case_function(test_case_name: str, **kwargs):
    """
    Run a specific test case with dynamic parameter support
    
    Accepts any parameters from API request and updates settings before test execution.
    Supports nested path syntax using "/" (e.g., "installOptions/version")
    
    Args:
        test_case_name (str): Name of the test case to run (e.g., "sign_in")
        **kwargs: Any parameters (platform, account, language, version, openai, jira, mode, etc.)
                  Nested paths: "installOptions/version" → settings.json: installOptions.version
                  mode: "suite" or "case" - controls whether to execute preconditions
        
    Returns:
        dict: Result of the test case execution
    """
    from config.global_settings import settings
    
    try:
        LOGGER_INFO(f"API handler received parameters: {kwargs}")
        
        # Extract mode before updating settings (don't save mode to settings)
        mode = kwargs.pop('mode', 'case')  # Default to 'case' for backward compatibility
        LOGGER_INFO(f"Execution mode: {mode} (preconditions will {'NOT' if mode == 'suite' else ''} be executed)", "CYAN")
        
        # Update settings with all provided parameters before test execution
        for key, value in kwargs.items():
            if value is not None:
                # Support nested path syntax: "installOptions/version"
                if '/' in key:
                    path_parts = key.split('/')
                    parent_key = path_parts[0]
                    nested_key = path_parts[1]
                    
                    # Get parent object, update nested field, then save back
                    parent_obj = settings.get(parent_key) or {}
                    parent_obj[nested_key] = value
                    settings.set(parent_key, parent_obj)
                    LOGGER_INFO(f"Updated settings['{parent_key}']['{nested_key}'] = '{value}'")
                else:
                    settings.set(key, value)
                    LOGGER_INFO(f"Updated settings['{key}'] = '{value}'")
        
        platform = kwargs.get('platform', 'windows')
        test_runner = TestCaseRunner(platform=platform)
        
        if mode == 'case':
            result = test_runner.run_test_case(test_case_name, platform)
        elif mode == 'suite':
            from core.suite_case_runner import SuiteCaseRunner
            suite_runner = SuiteCaseRunner(platform=platform)
            
            from core.managers.test_data_processor import TestDataProcessor
            processor = TestDataProcessor()
            case_data_list = processor.prepare_test_execution_data([test_case_name], mode='case')
            
            if case_data_list:
                case_data = case_data_list[0]
                success = suite_runner._execute_single_test_case(case_data, mode='suite', need_initialization=True)
                result = (suite_runner.navigate_report_path, suite_runner.performance_report_path, suite_runner.stress_report_path)
        
        # Handle different return formats
        if isinstance(result, tuple) and len(result) == 3:
            navigate_report_path, performance_report_path, stress_report_path = result
        elif isinstance(result, tuple) and len(result) == 2:
            # Legacy return format (backwards compatibility)
            first_element, second_element = result
            if isinstance(first_element, list):
                # Case mode returns (test_results_list, navigate_report_path)
                navigate_report_path = second_element
                performance_report_path = None
                stress_report_path = None
            else:
                # Suite mode returns (navigate_report_path, performance_report_path)
                navigate_report_path = first_element
                performance_report_path = second_element
                stress_report_path = None
        else:
            navigate_report_path = None
            performance_report_path = None
            stress_report_path = None
        
        return {
            "status": "success",
            "message": f"Test case '{test_case_name}' executed successfully",
            "test_case_name": test_case_name,
            "navigate_report_path": navigate_report_path,
            "performance_report_path": performance_report_path,
            "stress_report_path": stress_report_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test case '{test_case_name}' execution failed: {str(e)}",
            "test_case_name": test_case_name,
            "navigate_report_path": None,
            "performance_report_path": None
        }


def run_stress_test_function(test_case_name: str, platform: str, stress_duration: int,
                           participant_count: int, custom_message: Optional[str] = None,
                           enable_chat_test: bool = True, enable_video: bool = True,
                           enable_audio: bool = False):
    """
    Core stress test processing function
    
    Execution flow:
    1. Prepare stress test environment
    2. Set dynamic parameters in settings
    3. Execute test_stress_api.yaml (for API calls) or test_stress.yaml (for direct calls)
    4. Return execution results
    
    Args:
        test_case_name: Test case name
        platform: Execution platform
        stress_duration: Stress test duration in seconds
        participant_count: Number of participants
        custom_message: Custom stress test message
        enable_chat_test: Whether to enable chat testing
        enable_video: Whether to enable video
        enable_audio: Whether to enable audio
        
    Returns:
        dict: Execution results
    """
    try:
        from datetime import datetime
        
        # Import settings for dynamic parameter passing
        try:
            from config.global_settings import settings
        except ImportError:
            settings = None
        
        # Set dynamic parameters in settings for API-driven execution
        if settings is not None:
            # Convert audio/video/chat settings to on/off strings
            audio_setting = "on" if enable_audio else "off"
            video_setting = "on" if enable_video else "off"
            chat_setting = "on" if enable_chat_test else "off"
            reactions_setting = "on"  # Default to on for reactions
            
            # Set all parameters in settings
            settings.set('stress_participants', participant_count)
            settings.set('stress_duration', stress_duration // 60)  # Convert seconds to minutes
            settings.set('stress_audio', audio_setting)
            settings.set('stress_video', video_setting)
            settings.set('stress_chat', chat_setting)
            settings.set('stress_reactions', reactions_setting)
            
            print(f"🔧 Dynamic parameters set:")
            print(f"   Participants: {participant_count}")
            print(f"   Duration: {stress_duration // 60} minutes")
            print(f"   Audio: {audio_setting}")
            print(f"   Video: {video_setting}")
            print(f"   Chat: {chat_setting}")
            print(f"   Reactions: {reactions_setting}")
        
        # For API calls, use the new dynamic YAML file
        yaml_file = "stress/test_stress_api" if test_case_name == "test_stress" else test_case_name
        
        # Build stress test message for logging purposes
        if not custom_message:
            audio_setting = "on" if enable_audio else "off"
            video_setting = "on" if enable_video else "off"
            chat_setting = "on" if enable_chat_test else "off"
            
            stress_message = (
                f"<@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com "
                f"audio={audio_setting} video={video_setting} send_reactions=on "
                f"send_chat={chat_setting} with {participant_count} ucf_api "
                f"duration {stress_duration // 60}"
            )
        else:
            stress_message = custom_message
        
        # Create test job orchestrator for complete workflow (including report upload)
        print("🎯 Creating TestJobOrchestrator for complete workflow...")
        
        # Ensure COM is initialized for API context
        try:
            import pythoncom
            pythoncom.CoInitialize()
            print("✅ COM initialized for API context")
        except Exception as e:
            print(f"⚠️ COM initialization warning: {e}")
        
        orchestrator = TestJobOrchestrator()
        
        # Re-set dynamic parameters after orchestrator initialization
        # (StartupInitializer might have reset them)
        if settings is not None:
            # Re-apply all dynamic parameters
            audio_setting = "on" if enable_audio else "off"
            video_setting = "on" if enable_video else "off"
            chat_setting = "on" if enable_chat_test else "off"
            reactions_setting = "on"  # Default to on for reactions
            
            settings.set('stress_participants', participant_count)
            settings.set('stress_duration', stress_duration // 60)  # Convert seconds to minutes
            settings.set('stress_audio', audio_setting)
            settings.set('stress_video', video_setting)
            settings.set('stress_chat', chat_setting)
            settings.set('stress_reactions', reactions_setting)
            
            print(f"🔧 Re-applied dynamic parameters after orchestrator init:")
            print(f"   Participants: {participant_count}")
            print(f"   Duration: {stress_duration // 60} minutes")
            print(f"   Audio: {audio_setting}")
            print(f"   Video: {video_setting}")
            print(f"   Chat: {chat_setting}")
            print(f"   Reactions: {reactions_setting}")
        
        # Execute complete workflow with the appropriate YAML file
        # This includes test execution + analysis + report upload
        print(f"🚀 Starting complete workflow for: {yaml_file} in mode: case")
        result_url = orchestrator.run_complete_workflow(
            test_suite=yaml_file,
            mode="case"
        )
        
        print(f"✅ Complete workflow finished. Result URL: {result_url}")
        
        stress_config = {
            "duration": stress_duration,
            "participants": participant_count,
            "chat_enabled": enable_chat_test,
            "video_enabled": enable_video,
            "audio_enabled": enable_audio,
            "message": stress_message
        }
        
        # TestJobOrchestrator returns URL string, not tuple
        # Set default report paths since we're using the orchestrator
        navigate_report_path = None
        performance_report_path = None
        stress_report_path = None
        
        # If result_url is returned, it means reports were uploaded successfully
        if result_url:
            print(f"📤 Reports uploaded successfully to: {result_url}")
        
        return {
            "status": "success",
            "message": f"Stress test executed with {participant_count} participants for {stress_duration}s and reports uploaded",
            "test_case_name": test_case_name,
            "stress_config": stress_config,
            "result_url": result_url,  # Add the upload URL
            "navigate_report_path": navigate_report_path,
            "performance_report_path": performance_report_path,
            "stress_report_path": stress_report_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Stress test failed: {str(e)}",
            "test_case_name": test_case_name,
            "stress_config": {
                "duration": stress_duration,
                "participants": participant_count,
                "chat_enabled": enable_chat_test,
                "video_enabled": enable_video,
                "audio_enabled": enable_audio,
                "message": custom_message or "Failed to generate message"
            },
            "navigate_report_path": None,
            "performance_report_path": None,
            "stress_report_path": None  # No stress report when execution fails
        }
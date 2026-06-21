"""
run_test_case_job.py

Main Test Job Executor
=====================

This file executes the complete test job workflow, including:
1. Test suite execution
2. Screen reader analysis
3. Performance analysis  
4. Focus ring detection
5. Results upload

Usage:
    python src/run_test_case_job.py
"""

from common.startup.startup_initializer import StartupInitializer
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH, WINDOW_IMAGE_PATH, CONTROL_IMAGE_PATH, NAVIGATION_REPORT_PATH
from common.utils.logger import LOGGER_ERROR, LOGGER_INFO
from common.utils.featureToggle import FeatureToggle
from tools.webexApp import appHandler
from common.finalizer import archive_processor, notifier
from common.finalizer.notification_router import (
    get_notification_room_ids,
    DEFAULT_MAC_ROOM
)
from common.finalizer.version_tracker import AppVersionTracker
from urllib.parse import urlparse
import sys
import os



def update_test_suite_yaml_with_account(test_suite, account):
    """
    Update test_suite YAML file with account parameter
    
    Args:
        test_suite: Name of the test suite
        account: Account value to add to the YAML file
    """
    import os
    
    try:
        # Construct YAML file path
        yaml_file_path = os.path.join(
            os.path.dirname(__file__), 
            'test_space', 
            'test_suites', 
            f'{test_suite}.yaml'
        )
        
        LOGGER_INFO(f"🔍 Looking for YAML file: {yaml_file_path}")
        
        # Check if file exists
        if not os.path.exists(yaml_file_path):
            LOGGER_INFO(f"⚠️ YAML file not found: {yaml_file_path}")
            return
        
        # Read existing content as text
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the position to insert/update account parameter
        lines = content.split('\n')
        new_lines = []
        account_found = False
        owner_line_index = -1
        
        for i, line in enumerate(lines):
            # Check if this line is the account line
            if line.strip().startswith('account:'):
                # Update existing account value
                indent = len(line) - len(line.lstrip())
                account_line = ' ' * indent + f'account: {account}'
                new_lines.append(account_line)
                account_found = True
                LOGGER_INFO(f"✅ Updating existing account parameter: {account}")
            else:
                new_lines.append(line)
                # Track owner line position for potential insertion
                if line.strip().startswith('owner:'):
                    owner_line_index = len(new_lines) - 1
        
        # If account was not found, insert it after owner line
        if not account_found and owner_line_index >= 0:
            owner_line = new_lines[owner_line_index]
            indent = len(owner_line) - len(owner_line.lstrip())
            account_line = ' ' * indent + f'account: {account}'
            # Insert after owner line
            new_lines.insert(owner_line_index + 1, account_line)
            LOGGER_INFO(f"✅ Adding new account parameter after owner line: {account}")
        
        # Write updated content back to file
        updated_content = '\n'.join(new_lines)
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        LOGGER_INFO(f"✅ Successfully updated {test_suite}.yaml with account: {account}")
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error updating YAML file for test_suite {test_suite}: {e}")
        import traceback
        traceback.print_exc()


def update_test_suite_yaml_with_owner(test_suite, owner):
    """
    Update test_suite YAML file with owner parameter
    
    Args:
        test_suite: Name of the test suite
        owner: Owner value to update in the YAML file
    """
    import os
    
    try:
        # Construct YAML file path
        yaml_file_path = os.path.join(
            os.path.dirname(__file__), 
            'test_space', 
            'test_suites', 
            f'{test_suite}.yaml'
        )
        
        LOGGER_INFO(f"🔍 Looking for YAML file: {yaml_file_path}")
        
        # Check if file exists
        if not os.path.exists(yaml_file_path):
            LOGGER_INFO(f"⚠️ YAML file not found: {yaml_file_path}")
            return
        
        # Read existing content as text
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the position to insert/update owner parameter
        lines = content.split('\n')
        new_lines = []
        owner_found = False
        team_line_index = -1
        
        for i, line in enumerate(lines):
            # Check if this line is the owner line
            if line.strip().startswith('owner:'):
                # Update existing owner value
                indent = len(line) - len(line.lstrip())
                owner_line = ' ' * indent + f'owner: {owner}'
                new_lines.append(owner_line)
                owner_found = True
                LOGGER_INFO(f"✅ Updating existing owner parameter: {owner}")
            else:
                new_lines.append(line)
                # Track team line position for potential insertion
                if line.strip().startswith('team:'):
                    team_line_index = len(new_lines) - 1
        
        # If owner was not found, insert it after team line
        if not owner_found and team_line_index >= 0:
            team_line = new_lines[team_line_index]
            indent = len(team_line) - len(team_line.lstrip())
            owner_line = ' ' * indent + f'owner: {owner}'
            # Insert after team line
            new_lines.insert(team_line_index + 1, owner_line)
            LOGGER_INFO(f"✅ Adding new owner parameter after team line: {owner}")
        elif not owner_found:
            # If no team line found, try to find name line and insert after it
            name_line_index = -1
            for i, line in enumerate(new_lines):
                if line.strip().startswith('name:'):
                    name_line_index = i
                    break
            
            if name_line_index >= 0:
                name_line = new_lines[name_line_index]
                indent = len(name_line) - len(name_line.lstrip())
                owner_line = ' ' * indent + f'owner: {owner}'
                new_lines.insert(name_line_index + 1, owner_line)
                LOGGER_INFO(f"✅ Adding new owner parameter after name line: {owner}")
        
        # Write updated content back to file
        updated_content = '\n'.join(new_lines)
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        LOGGER_INFO(f"✅ Successfully updated {test_suite}.yaml with owner: {owner}")
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error updating YAML file for test_suite {test_suite}: {e}")
        import traceback
        traceback.print_exc()


def update_test_suite_yaml_with_check_points(test_suite, validation_points):
    """
    Update test_suite YAML file with check_points parameter based on validation_points
    
    Args:
        test_suite: Name of the test suite
        validation_points: Dict containing validation point flags (kb, sr, fr, ai_verify, performance, ui_legacy)
    """
    import os
    
    try:
        # Construct YAML file path
        yaml_file_path = os.path.join(
            os.path.dirname(__file__), 
            'test_space', 
            'test_suites', 
            f'{test_suite}.yaml'
        )
        
        LOGGER_INFO(f"🔍 Looking for YAML file: {yaml_file_path}")
        
        # Check if file exists
        if not os.path.exists(yaml_file_path):
            LOGGER_INFO(f"⚠️ YAML file not found: {yaml_file_path}")
            return
        
        # Mapping validation points to check point names
        check_point_mapping = {
            'kb': 'Keyboard Navigation',
            'sr': 'Screen Reader',
            'fr': 'Focus Ring',
            'ai_verify': 'AI Verify',
            'performance': 'Performance',
            'ui_legacy': 'UI Legacy'
        }
        
        # Build list of active check points
        active_check_points = []
        for key, check_point_name in check_point_mapping.items():
            if validation_points.get(key, False):
                active_check_points.append(check_point_name)
        
        LOGGER_INFO(f"🔧 Active check points: {active_check_points}")
        
        # Read existing content as text
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the position to insert/update check_points parameter
        lines = content.split('\n')
        new_lines = []
        check_points_found = False
        test_cases_line_index = -1
        
        for i, line in enumerate(lines):
            # Check if this line is the check_points line
            if line.strip().startswith('check_points:'):
                # Update existing check_points value
                indent = len(line) - len(line.lstrip())
                if active_check_points:
                    check_points_line = ' ' * indent + f'check_points: {active_check_points}'
                else:
                    check_points_line = ' ' * indent + 'check_points: []'
                new_lines.append(check_points_line)
                check_points_found = True
                LOGGER_INFO(f"✅ Updating existing check_points parameter: {active_check_points}")
            else:
                new_lines.append(line)
                # Track test_cases line position for potential insertion
                if line.strip().startswith('test_cases:'):
                    test_cases_line_index = len(new_lines) - 1
        
        # If check_points was not found, insert it after test_cases section
        if not check_points_found and test_cases_line_index >= 0:
            # Find end of test_cases list
            insert_index = test_cases_line_index + 1
            while insert_index < len(new_lines) and new_lines[insert_index].strip().startswith('- '):
                insert_index += 1
            
            # Get indentation from test_cases line
            test_cases_line = new_lines[test_cases_line_index]
            indent = len(test_cases_line) - len(test_cases_line.lstrip())
            
            if active_check_points:
                check_points_line = ' ' * indent + f'check_points: {active_check_points}'
            else:
                check_points_line = ' ' * indent + 'check_points: []'
            
            # Insert after test_cases section
            new_lines.insert(insert_index, check_points_line)
            LOGGER_INFO(f"✅ Adding new check_points parameter after test_cases: {active_check_points}")
        
        # Write updated content back to file
        updated_content = '\n'.join(new_lines)
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        LOGGER_INFO(f"✅ Successfully updated {test_suite}.yaml with check_points: {active_check_points}")
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error updating YAML file for test_suite {test_suite}: {e}")
        import traceback
        traceback.print_exc()


def apply_workflow_configuration(pramas):
    """
    Apply workflow configuration parameters to settings
    
    Args:
        pramas: Configuration parameters (can be dict or JSON string)
    
    Returns:
        dict: Parameters ready for settings.set() calls
    """
    if not pramas:
        return {}
        
    import json
    
    # Handle case where pramas is a JSON string
    if isinstance(pramas, str):
        try:
            pramas = json.loads(pramas)
            LOGGER_INFO(f"Parsed pramas: {pramas}")
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"Error parsing pramas JSON: {e}")
            return {}
    
    if not isinstance(pramas, dict):
        return {}
    
    # Build settings parameters that match settings.json structure
    settings_params = {}
    
    # Direct mappings
    if 'platform' in pramas:
        platform_value = pramas['platform']
        # Normalize platform values
        if platform_value.lower() in ['win', 'windows']:
            settings_params['platform'] = 'windows'
        elif platform_value.lower() in ['mac', 'macos', 'mac_http2', 'mac_arm64_http2']:
            settings_params['platform'] = 'mac'
        else:
            settings_params['platform'] = platform_value.lower()
    
    # Handle installOptions mapping with default values
    install_options = {
        # Set default values for all installOptions keys
        'source': 'shanghai',
        'qtversion': '6', 
        'version': 'latest',
        'path': '',
        'uninstall': True,
        'arch': 'x64',
        'cdntoken': '',
        'http2': False,
        'notResetDB': False,
        'downloadonly': False,
        'continueRun': False
    }
    
    # Location mapping (override default if provided)
    if 'location' in pramas:
        install_options['source'] = pramas['location'].lower()
    
    # Build type mapping (override default if provided)
    if 'build_type' in pramas:
        build_type = pramas['build_type']
        install_options['qtversion'] = "6" if build_type.lower().startswith('qt6') else "5"
    
    # Version configuration mapping (override default if provided)
    version_config = pramas.get('version_config', {})
    if version_config:
        version_mode = version_config.get('mode', 'latest')
        version_value = version_config.get('value', 'release')
        
        # Determine the correct version setting based on mode and value
        if version_mode == 'current':
            install_version = version_value
        elif version_mode == 'latest':
            if version_value in ['main', 'main_branch']:
                install_version = 'latest'
            elif version_value in ['release', 'release_branch']:
                install_version = 'eft'
            else:
                install_version = 'latest'
        elif version_mode in ['main', 'main_branch']:
            install_version = 'latest'
        elif version_mode in ['release', 'release_branch']:
            install_version = 'eft'
        else:
            install_version = version_value
            
        install_options['version'] = install_version
        LOGGER_INFO(f"✅ Version mapping: {version_mode}:{version_value} → {install_version}")
    
    # Override other installOptions if provided in pramas
    if 'path' in pramas:
        install_options['path'] = pramas['path']
    if 'uninstall' in pramas:
        install_options['uninstall'] = pramas['uninstall']
    if 'arch' in pramas:
        install_options['arch'] = pramas['arch']
    if 'cdntoken' in pramas:
        install_options['cdntoken'] = pramas['cdntoken']
    if 'http2' in pramas:
        install_options['http2'] = pramas['http2']
    else:
        # Set http2 based on platform if not explicitly provided
        current_platform = settings_params.get('platform')
        if current_platform == 'mac':
            install_options['http2'] = True
        elif current_platform == 'windows':
            install_options['http2'] = False
        else:
            # Keep default False for unknown platforms
            install_options['http2'] = False
    if 'notResetDB' in pramas:
        install_options['notResetDB'] = pramas['notResetDB']
    if 'downloadonly' in pramas:
        install_options['downloadonly'] = pramas['downloadonly']
    if 'continueRun' in pramas:
        install_options['continueRun'] = pramas['continueRun']
    if 'test_suite' in pramas:
        settings_params['test_suite'] = pramas['test_suite']
    
    # Always include installOptions in settings_params
    settings_params['installOptions'] = install_options
    
    # Ensure upload is enabled for report URL generation
    settings_params['upload'] = True
    
    # Handle account configuration if provided
    if 'account' in pramas:
        LOGGER_INFO(f"✅ Account configuration: {pramas['account']}")
        
        # Update test_suite YAML file with account parameter
        current_test_suite = pramas.get('test_suite')
        if current_test_suite:
            update_test_suite_yaml_with_account(current_test_suite, pramas['account'])
            
            # Update test_suite YAML file with owner parameter
            owner = pramas.get('owner')
            if owner and owner != 'default':
                update_test_suite_yaml_with_owner(current_test_suite, owner)
                LOGGER_INFO(f"✅ Updated owner for test_suite: {current_test_suite} -> {owner}")
            
            # Update test_suite YAML file with check_points parameter
            validation_points = pramas.get('validation_points', {})
            if validation_points:
                update_test_suite_yaml_with_check_points(current_test_suite, validation_points)
                LOGGER_INFO(f"✅ Updated check_points for test_suite: {current_test_suite}")
        else:
            LOGGER_INFO(f"⚠️ No test_suite found in pramas, cannot update YAML file")
    # settings_params['workflow'] = "guest_join_meeting"
    if 'acc_case' in pramas:
        current_test_suite = pramas.get('test_suite')
        if current_test_suite:
            settings_params['workflow'] = current_test_suite
    
    LOGGER_INFO(f"✅ Built settings params: {settings_params}")
    return settings_params


def webexInitialize():
    appHandler.installWebex() 

def Windows_Main(test_suite=None, progress_callback=None, other_params=None):
    import pythoncom
    from core.test_job_orchestrator import TestJobOrchestrator
    
    # Re-apply configuration after import (since import resets settings)
    if other_params is not None:
        settings = DynamicConfig(SETTINGS_PATH)
        for key, value in other_params.items():
            settings.set(key, value)
    
    # Initialize COM
    pythoncom.CoInitialize()
    

    _orchestrator = TestJobOrchestrator()
    result = _orchestrator.run_complete_workflow(test_suite, progress_callback=progress_callback)
    
    # Get the report URL from the orchestrator after workflow completion
    report_url = _orchestrator.get_report_url()

    return report_url

def Linux_Main(test_suite=None, progress_callback=None, other_params=None):
    from core.test_job_orchestrator import TestJobOrchestrator
    
    # Re-apply configuration after import (since import resets settings)
    if other_params is not None:
        settings = DynamicConfig(SETTINGS_PATH)
        for key, value in other_params.items():
            settings.set(key, value)
    
    _orchestrator = TestJobOrchestrator()
    result = _orchestrator.run_complete_workflow(test_suite, progress_callback=progress_callback)
    
    # Get the report URL from the orchestrator after workflow completion
    report_url = _orchestrator.get_report_url()
    LOGGER_INFO(f"DEBUG: Report URL from orchestrator: {report_url}   ")
    LOGGER_INFO(f"INFO: Window image path: {WINDOW_IMAGE_PATH}   ")
    LOGGER_INFO(f"INFO: Control image path: {CONTROL_IMAGE_PATH}   ")
    LOGGER_INFO(f"INFO: Navigation report path: {NAVIGATION_REPORT_PATH}   ")

    return report_url


def Mac_Main(test_suite=None, progress_callback=None):
    from core.mac.GTManager import GTManager
    from tools.MessageBot import BotMessage

    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language") or "en_US"
    test_case = settings.get("test_case")
    test_suite = settings.get("test_suite")
    test_batch = settings.get("test_batch")
    results = {}
    exception_occurred = False
    error = ""
    fileName = test_case or test_suite or test_batch or "unknown"
    try:
        if test_case and test_case != '':
            if str(test_case).lower() == "all":
                results =GTManager.run_all_test_cases(language, progress_callback=progress_callback)
            else:
                results = GTManager.run_by_file(test_case, language,progress_callback=progress_callback)
        elif test_suite and test_suite != '':
            if str(test_suite).lower() == "all":
                results = GTManager.run_all_test_suites(language, progress_callback=progress_callback)
            else:
                results = GTManager.run_by_file(test_suite, language,progress_callback=progress_callback)
        elif test_batch and test_batch != '':
            if str(test_batch).lower() == "all":
                results = GTManager.run_all_test_case_batches(language, progress_callback=progress_callback)
            else:
                results = GTManager.run_by_file(test_batch, language,progress_callback=progress_callback)
        else:
            LOGGER_ERROR("No test_case, test_suite or test_batch specified in settings.")
            raise Exception("No test_case, test_suite or test_batch specified in settings.")
    except Exception as e:
        exception_occurred = True
        error = str(e)
        import traceback
        LOGGER_ERROR(f"Exception during test execution: {e}\n{traceback.format_exc()}")


    # Determine mode for notification room resolution
    if test_case and test_case != '':
        mode = 'case'
    elif test_suite and test_suite != '':
        mode = 'suite'
    elif test_batch and test_batch != '':
        mode = 'batch'
    else:
        mode = None

    archive_processor.RemoteArchiveProcessor().upload_archive()
    report_url = archive_processor.RemoteArchiveProcessor().get_report_url(GT=True)

    settings_room_id = settings.get("botRoomId") or None
    room_ids = get_notification_room_ids(
        settings_room_id, mode, test_case, test_suite, test_batch,
        default_room=DEFAULT_MAC_ROOM
    )

    if exception_occurred:
        # If an exception occurred during test execution, we can choose to return early or continue with empty results
        LOGGER_ERROR("An exception occurred during test execution. Returning with empty results.")
        for botRoomID in room_ids:
            notifier.notify_messageBot_card(report_url, execution_result="FAIL", roomId=botRoomID)
        
        mention_message = (
                f"❌ Run {mode}: **{fileName}** failed with error: **{error}**"
            )
        
        for botRoomID in room_ids:
            BotMessage.sendMessageToTeams(mention_message, roomId=botRoomID)

        if settings.onNewVersion:
            AppVersionTracker().save_app_version()
        raise Exception(f"Test execution failed with error: {mention_message}")
    
    if results is not None and results["failed"] and len(results["failed"]) > 0:
        for botRoomID in room_ids:
            notifier.notify_messageBot_card(report_url, execution_result="FAIL", roomId=botRoomID)
        
        for failed_case in results["failed"]:
            cec = failed_case["owner"]
            if not cec:
                continue
            if cec.endswith("@cisco.com"):
                cec = cec.split("@")[0]
            owner_email = f"{cec}@cisco.com|{cec}"
            caseName = failed_case["name"]
            error = failed_case["error"]
            mention_message = (
                f"<@personEmail:{owner_email}|> Please review the test results above, "
                f"❌ Test case '{caseName}' failed with error: {error}"
            )
            for botRoomID in room_ids:
                BotMessage.sendMessageToTeams(mention_message, roomId=botRoomID)
    else:
        for botRoomID in room_ids:
            notifier.notify_messageBot_card(report_url, execution_result="PASS", roomId=botRoomID)
    return report_url


def Main(test_suite=None, progress_callback=None,other_params=None):
    # Register global hotkey (Ctrl+Alt+0) to stop test from any window
    try:
        from common.utils.global_hotkey import start_hotkey_listener
        start_hotkey_listener()
    except Exception:
        pass  # Non-critical — skip on non-Windows or if registration fails
    
    StartupInitializer()
    settings = DynamicConfig(SETTINGS_PATH)
    if other_params is not None:
        LOGGER_INFO(f"Received other_params: {other_params}")
        for key, value in other_params.items():
            settings.set(key, value)
    
    platform = settings.get("platform")
    if platform == "mac":
        result = Mac_Main(test_suite, progress_callback)
    elif platform == "windows":
        result = Windows_Main(test_suite, progress_callback, other_params)
    elif platform == "linux":
        result = Linux_Main(test_suite, progress_callback, other_params)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    if settings.onNewVersion:
        AppVersionTracker().save_app_version()
    return result


class TestCaseJobRunner:
    """
    Main Test Case Job Runner
    
    This class handles the complete test job workflow execution.
    """
    
    def __init__(self):
        """Initialize the test case job runner"""
        pass

    def run_complete_workflow_with_ui_response(self, test_suite=None, progress_callback=None, pramas=None, return_report_url=False):
        """
        Run complete workflow with UI response
        
        Args:
            test_suite: Test suite name to run
            progress_callback: Callback function for progress updates
            pramas: Configuration parameters
            return_report_url: Whether to return report URL as tuple
            
        Returns:
            str or tuple: Report URL string, or tuple (result, report_url) if return_report_url=True
        """
        # Apply configuration parameters
        pramas = apply_workflow_configuration(pramas)
        
        # Run the main workflow
        main_result = Main(test_suite, progress_callback, other_params=pramas)
        
        # Extract report URL from result
        report_url = None
        if main_result is not None:
            if isinstance(main_result, str):
                # Direct string result is the report URL
                report_url = main_result
            elif isinstance(main_result, tuple) and len(main_result) > 0:
                # Extract first element as report URL
                report_url = main_result[0]
        
        LOGGER_INFO(f"📋 [WORKFLOW] Report URL: {report_url}")
        
        # Return format based on return_report_url parameter
        if return_report_url:
            return main_result, report_url
        else:
            return report_url

    def run_acc_testcase(self, test_suite=None, pramas=None):
        """
        Run ACC (Accessibility) test case workflow
        
        Args:
            test_suite: Test suite name to run
            pramas: Configuration parameters as JSON string
            
        Returns:
            str: Report URL or execution result
        """
        # Apply configuration parameters
        acc_case_pramas = apply_workflow_configuration(pramas)
        StartupInitializer()
        settings = DynamicConfig(SETTINGS_PATH)
        if acc_case_pramas is not None:
            LOGGER_INFO(f"Received other_params: {acc_case_pramas}")
            for key, value in acc_case_pramas.items():
                settings.set(key, value)
        from run_explorer import ControlExplorerRunner
        explorer_runner = ControlExplorerRunner()
        explorer_runner.run()
if __name__ == "__main__":
    Main()
    
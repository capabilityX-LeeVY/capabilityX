import yaml
import json
import os
import re
from pathlib import Path
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
from db.handlers import get_db_connection
from config.config import TEST_CASE_DB
from config.paths import src_path, TEST_CASES_PATH
from rs_sdk.utils.control_datasets_loader import (
    get_complete_control_metadata_by_name,
    get_control_datasets,
    get_control_count,
    is_step_supported_on_platform
)


class WorkflowLoader:
    def __init__(self):
        # Use TestCaseDBHandler for database operations
        self.db_handler = TestCaseDBHandler()
        LOGGER_DEBUG("WorkflowLoader initialized with TestCaseDBHandler", "GREEN")

    def build_ui_path(self, test_case_path=None, current_platform="windows"):
        """
        Build UI path with platform filtering.
        
        Args:
            test_case_path: Path to test case YAML file
            current_platform: Current platform (windows/mac/web), default: "windows"
            
        Returns:
            list: Platform-filtered UI path
        """
        if test_case_path:
            with open(test_case_path, "r", encoding="utf-8") as f:
                workflow_dict = yaml.safe_load(f)
        else:
            LOGGER_ERROR("No test_case_path provided, cannot build UI path.")
            return []

        test_case_dict = workflow_dict.get("test_case", [])
        ui_path = []
        ui_path.extend(test_case_dict.get("steps", []))

        # Expand include directives
        ui_path = self._expand_includes(ui_path, test_case_path)

        account_name = self.get_test_case_account(test_case_path)
        ui_path = self.resolve_account_variables(ui_path, account_name)
        
        # Filter steps based on platform
        filtered_ui_path = self._filter_steps_by_platform(ui_path, current_platform)

        return filtered_ui_path
    
    def build_ui_path_with_account(self, test_case_path=None, override_account=None, test_suite_path=None, current_platform="windows"):
        """
        Build UI path with account variable resolution and platform filtering.
        
        Args:
            test_case_path: Path to test case YAML file
            override_account: Override account name (highest priority)
            test_suite_path: Path to test suite YAML file (optional)
            current_platform: Current platform (windows/mac/web), default: "windows"
            
        Returns:
            list: UI path with resolved account variables and platform-filtered steps
        """
        if test_case_path:
            with open(test_case_path, "r", encoding="utf-8") as f:
                workflow_dict = yaml.safe_load(f)
        else:
            LOGGER_ERROR("No test_case_path provided, cannot build UI path.")
            return []

        test_case_dict = workflow_dict.get("test_case", [])
        ui_path = []
        ui_path.extend(test_case_dict.get("steps", []))

        # Expand include directives
        ui_path = self._expand_includes(ui_path, test_case_path)

        # Get effective account with priority: override > test_case > test_suite
        account_name = self.get_effective_account(test_case_path, test_suite_path, override_account)
        
        ui_path = self.resolve_account_variables(ui_path, account_name)
        
        # Filter steps based on platform
        filtered_ui_path = self._filter_steps_by_platform(ui_path, current_platform)

        return filtered_ui_path
    
    def _filter_steps_by_platform(self, steps: list, current_platform: str) -> list:
        """
        Filter test steps based on current platform.
        
        Args:
            steps: List of test step dictionaries
            current_platform: Current platform (windows/mac/web)
        
        Returns:
            list: Filtered steps that should execute on current platform
        """
        filtered_steps = []
        for step in steps:
            if self._should_execute_step(step, current_platform):
                filtered_steps.append(step)
                step_name = step.get('name', 'Unknown')
                LOGGER_INFO(f"[Platform:{current_platform}] Step included: {step_name}", "GREEN")
            else:
                step_name = step.get('name', 'Unknown')
                step_platforms = step.get('platforms', 'all')
                LOGGER_DEBUG(f"[Platform:{current_platform}] Step skipped: {step_name} (platforms: {step_platforms})", "YELLOW")
        
        return filtered_steps
    
    def _should_execute_step(self, step: dict, current_platform: str) -> bool:
        """
        Determine if step should execute on current platform.
        
        Args:
            step: Test step dictionary
            current_platform: Current platform (windows/mac/web)
        
        Returns:
            True if step should execute, False otherwise
        """
        if 'platforms' not in step:
            # No platforms specified = execute on all platforms
            return True
        
        step_platforms = step['platforms']
        
        # Handle single platform string (for backward compatibility)
        if isinstance(step_platforms, str):
            return step_platforms.lower() == current_platform.lower()
        
        # Handle platform list
        if isinstance(step_platforms, list):
            return current_platform.lower() in [p.lower() for p in step_platforms]
        
        return False

    def _expand_includes(self, steps: list, base_path: str) -> list:
        """
        Expand include directives and ``local_api`` action steps to actual step
        content.

        Two expansion patterns are supported:

        1. **include directive** (existing)::

               - include: "navigations/some/path"
                 params:
                   key: value

        2. **local_api action** — calls another YAML test case inline and
           substitutes runtime parameters::

               - name: "run join meeting"
                 action:
                   type: local_api
                   value: "navigations/preconditions/app_entry/guest_join_a_meeting"
                   parameters:
                     meeting_link: "binbiwan@cisco.webex.com"
                     name: "tony"

           The referenced YAML's steps are loaded and the ``parameters`` dict is
           passed to ``_replace_params``, which handles ``${key}`` placeholders
           (canonical style — do NOT use ``{key}`` in sub-workflow YAMLs).

        Args:
            steps: List of steps (may contain include directives or local_api actions)
            base_path: Base path for resolving relative include paths
            
        Returns:
            list: Expanded steps with includes/local_api replaced by actual content
        """
        if not steps:
            return steps
            
        expanded_steps = []
        
        for step in steps:
            if isinstance(step, dict) and 'include' in step:
                # Load the included file
                include_path = step['include']
                params = step.get('params', {})
                
                LOGGER_INFO(f"[Include] Expanding: {include_path} with params: {params}", "CYAN")
                
                # Load steps from included file
                included_steps = self._load_included_steps(include_path, base_path)
                
                # Replace parameters in included steps
                if params and included_steps:
                    included_steps = self._replace_params(included_steps, params)
                
                # Attach ai_check from include block to the last expanded step
                if included_steps and 'ai_check' in step:
                    included_steps[-1]['ai_check'] = step['ai_check']
                    LOGGER_INFO(f"[Include] Attached ai_check to last step: {included_steps[-1].get('name', 'Unknown')}", "CYAN")
                
                # Attach ui_response from include block to the last expanded step
                if included_steps and 'ui_response' in step:
                    included_steps[-1]['ui_response'] = step['ui_response']
                    LOGGER_INFO(f"[Include] Attached ui_response to last step: {included_steps[-1].get('name', 'Unknown')}", "CYAN")
                
                LOGGER_INFO(f"[Include] Expanded {len(included_steps)} steps from {include_path}", "GREEN")
                expanded_steps.extend(included_steps)

            elif (isinstance(step, dict)
                  and isinstance(step.get('action'), dict)
                  and step['action'].get('type') == 'local_api'):
                # ── local_api: inline-expand a referenced YAML with parameters ──
                action = step['action']
                yaml_path = action.get('value', '')
                params = action.get('parameters', {})

                LOGGER_INFO(
                    f"[LocalAPI] Expanding: {yaml_path} with params: {params}", "CYAN"
                )

                # Load steps from the referenced YAML file
                included_steps = self._load_included_steps(yaml_path, base_path)

                # Substitute ${key} placeholders with provided parameter values
                if params and included_steps:
                    included_steps = self._replace_params(included_steps, params)

                LOGGER_INFO(
                    f"[LocalAPI] Expanded {len(included_steps)} steps from {yaml_path}", "GREEN"
                )

                # Carry over ai_check and stop_on_ai_check_failure from the
                # parent local_api step to the last expanded step so that
                # verification still runs after the navigation completes.
                if included_steps:
                    last_step = included_steps[-1]
                    if isinstance(last_step, dict):
                        if 'ai_check' in step and 'ai_check' not in last_step:
                            last_step['ai_check'] = step['ai_check']
                        if 'stop_on_ai_check_failure' in step and 'stop_on_ai_check_failure' not in last_step:
                            last_step['stop_on_ai_check_failure'] = step['stop_on_ai_check_failure']

                expanded_steps.extend(included_steps)

            else:
                expanded_steps.append(step)
        
        return expanded_steps

    def _load_included_steps(self, include_path: str, base_path: str) -> list:
        """
        Load steps from an included YAML file.
        
        Args:
            include_path: Relative path to include (without .yaml extension)
            base_path: Base path of the current test case file
            
        Returns:
            list: Steps from the included file
        """
        from config.paths import TEST_CASES_PATH
        
        # Try multiple resolution strategies
        possible_paths = [
            # 1. Relative to current test case directory
            Path(base_path).parent / f"{include_path}.yaml",
            # 2. Relative to test_cases root
            TEST_CASES_PATH / f"{include_path}.yaml",
            # 3. Absolute path (if provided)
            Path(f"{include_path}.yaml") if Path(f"{include_path}.yaml").is_absolute() else None
        ]
        
        include_full_path = None
        for path in possible_paths:
            if path and path.exists():
                include_full_path = path
                break
        
        if not include_full_path:
            LOGGER_ERROR(f"[Include] Could not find included file: {include_path}", "RED")
            LOGGER_ERROR(f"[Include] Searched paths: {[str(p) for p in possible_paths if p]}", "RED")
            return []
        
        LOGGER_INFO(f"[Include] Loading from: {include_full_path}", "CYAN")
        
        try:
            with open(include_full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Support both 'action' wrapper (for reusable actions) and 'test_case' wrapper
            if 'action' in data:
                return data.get('action', {}).get('steps', [])
            elif 'test_case' in data:
                return data.get('test_case', {}).get('steps', [])
            else:
                # Direct steps list
                return data.get('steps', [])
                
        except Exception as e:
            LOGGER_ERROR(f"[Include] Failed to load {include_full_path}: {str(e)}", "RED")
            return []

    def _replace_params(self, steps: list, params: dict) -> list:
        """
        Replace ``${param}`` and ``{param}`` placeholders with actual values in steps.

        ``${key}`` (canonical, used in all sub-workflow YAMLs such as
        ``guest_join_a_meeting.yaml``) is replaced first so that the ``{key}`` pass
        does not leave a stray leading ``$`` in the substituted value.

        Args:
            steps: List of step dictionaries
            params: Dictionary of parameter name -> value
            
        Returns:
            list: Steps with placeholders replaced
        """
        if not params:
            return steps
        
        # Convert steps to JSON string for easy replacement
        import copy
        steps_copy = copy.deepcopy(steps)
        steps_str = json.dumps(steps_copy, ensure_ascii=False)
        
        # Replace ${param} first (canonical style used in sub-workflow YAMLs),
        # then {param} (legacy style used in include directive params blocks).
        for key, value in params.items():
            dollar_placeholder = "${" + key + "}"
            curly_placeholder = "{" + key + "}"
            steps_str = steps_str.replace(dollar_placeholder, str(value))
            steps_str = steps_str.replace(curly_placeholder, str(value))
        
        # Warn about any still-unreplaced placeholders
        import re
        unreplaced_dollar = re.findall(r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}', steps_str)
        unreplaced_curly  = re.findall(r'(?<!\$)\{([a-zA-Z_][a-zA-Z0-9_]*)\}', steps_str)
        unreplaced = unreplaced_dollar + unreplaced_curly
        if unreplaced:
            LOGGER_WARNING(f"[Include] Unreplaced placeholders found: {unreplaced}", "YELLOW")
        
        return json.loads(steps_str)

    def get_test_cases_from_suite(self, test_suite):
        with open(test_suite, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        test_case_suite_dict = suite_dict.get("test_suite", {})
        return test_case_suite_dict.get("test_cases", [])
    
    def parse_parameterized_test_case(self, test_case_item):
        """
        Parse parameterized test case in supported formats:
        
        Format 1 (Nested Dict with test case name as key):
            navigations/basic/install_app:
                agent_node: "meeting_agent_01"
                parameters:
                    installOptions/version: "eft"
                    language: "en_US"
        
        Format 2 (Plain string - No parameters):
            "navigations/basic/install_app"
        
        Returns:
            tuple: (test_case_name, agent_node, params_dict) 
                   or (test_case_name, None, None) if no parameters
        """
        if isinstance(test_case_item, dict):
            if len(test_case_item) == 1:
                test_case_name = list(test_case_item.keys())[0]
                config = test_case_item[test_case_name]
                if isinstance(config, dict):
                    agent_node = config.get('agent_node')
                    params = config.get('parameters', {})
                    return test_case_name, agent_node, params if params else {}
            LOGGER_WARNING(f"Unsupported dict format: {test_case_item}, treating as string", "YELLOW")
            return str(test_case_item), None, None
        
        if isinstance(test_case_item, str):
            return test_case_item.strip(), None, None
        
        LOGGER_WARNING(f"Unsupported test case format: {test_case_item}, treating as string", "YELLOW")
        return str(test_case_item), None, None
    


    def get_test_cases_pre_conditions(self, test_suite):
        with open(test_suite, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        test_case_suite_dict = suite_dict.get("test_case", {})
        return test_case_suite_dict.get("pre_conditions", None)
    
    def get_test_cases_post_conditions(self, test_suite):
        with open(test_suite, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        test_case_suite_dict = suite_dict.get("test_case", {})
        return test_case_suite_dict.get("post_conditions", None)
    
    def get_test_case_execution_count(self, test_case_path):
        with open(test_case_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('test_case', {}).get('execution_count', 1)
    
    def get_test_case_execution_duration(self, test_case_path):
        with open(test_case_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('test_case', {}).get('execution_duration', 1)
    
    def get_test_suite_languages(self, test_case_path):
        with open(test_case_path, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        return suite_dict.get("test_suite", {}).get("language", [])
    
    def get_test_suite_check_points(self, test_case_path):
        with open(test_case_path, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        return suite_dict.get("test_suite", {}).get("check_points", None)
    
    def get_test_case_check_points(self, test_case_path):
        """
        Get check_points configuration from test case YAML.
        
        Args:
            test_case_path: Path to test case YAML file
            
        Returns:
            list: Check points list or None if not defined
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('test_case', {}).get('check_points', None)
        except Exception as e:
            LOGGER_ERROR(f"Failed to get check_points from test case {test_case_path}: {str(e)}", "RED")
            return None

    def get_test_case_message_room(self, test_case_path):
        """
        Returns:
            list[str]: Room ID list. Empty list when not configured or invalid.
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            message_bot = data.get('test_case', {}).get('message_bot', [])

            if message_bot is None:
                return []

            if isinstance(message_bot, str):
                message_bot = [message_bot]

            if not isinstance(message_bot, list):
                LOGGER_WARNING(
                    f"Invalid message_bot type in {test_case_path}: {type(message_bot).__name__}. Expected list[str].",
                    "YELLOW"
                )
                return []

            normalized_room_ids = []
            for room_id in message_bot:
                if isinstance(room_id, str) and room_id.strip():
                    normalized_room_ids.append(room_id.strip())

            return normalized_room_ids
        except Exception as e:
            LOGGER_ERROR(f"Failed to get message_bot from test case {test_case_path}: {str(e)}", "RED")
            return []
    
    def get_test_suite_platform(self, test_case_path):
        with open(test_case_path, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        return suite_dict.get("test_suite", {}).get("platform", "windows")
    
    def get_test_suite_project(self, test_case_path):
        """Get project name from test suite YAML configuration."""
        with open(test_case_path, "r", encoding="utf-8") as f:
            suite_dict = yaml.safe_load(f)
        return suite_dict.get("test_suite", {}).get("project", None)
    
    def get_test_case_platforms(self, test_case_path):
        """
        Get platform support configuration from test case YAML.
        
        Args:
            test_case_path: Path to test case YAML file
            
        Returns:
            dict: Platform configuration with 'supported' and 'primary' keys,
                  or default configuration if not specified
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            platforms = data.get('test_case', {}).get('platforms', {})
            
            # Default configuration if not specified
            if not platforms:
                platforms = {
                    'supported': ['windows'],  # Default to Windows only
                    'primary': 'windows'
                }
            
            # Ensure 'supported' is a list
            if 'supported' not in platforms:
                platforms['supported'] = ['windows']
            
            # Ensure 'primary' is set
            if 'primary' not in platforms:
                platforms['primary'] = platforms['supported'][0] if platforms['supported'] else 'windows'
            
            LOGGER_INFO(f"Test case platform configuration: {platforms}", "CYAN")
            return platforms
        except Exception as e:
            LOGGER_ERROR(f"Failed to get platforms from test case {test_case_path}: {str(e)}", "RED")
            return {'supported': ['windows'], 'primary': 'windows'}
    
    def validate_platform_support(self, test_case_path, current_platform):
        """
        Validate if current platform is supported by test case.
        
        Args:
            test_case_path: Path to test case YAML file
            current_platform: Current platform (windows/mac/web)
            
        Returns:
            bool: True if platform is supported, False otherwise
        """
        platforms = self.get_test_case_platforms(test_case_path)
        supported = platforms.get('supported', ['windows'])
        
        is_supported = current_platform.lower() in [p.lower() for p in supported]
        
        if not is_supported:
            LOGGER_WARNING(f"Platform '{current_platform}' is not supported by this test case. Supported platforms: {supported}", "YELLOW")
        else:
            LOGGER_INFO(f"Platform '{current_platform}' is supported by this test case", "GREEN")
        
        return is_supported
    
    def get_test_suite_account(self, test_suite_path):
        """
        Get account name from test suite YAML configuration.
        
        Args:
            test_suite_path: Path to test suite YAML file
            
        Returns:
            str: Account name configured in test suite, or None if not specified
        """
        try:
            with open(test_suite_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            account = data.get('test_suite', {}).get('account', None)
            if account:
                LOGGER_INFO(f"Test suite configured account: {account}", "CYAN")
            return account
        except Exception as e:
            LOGGER_ERROR(f"Failed to get account from test suite {test_suite_path}: {str(e)}", "RED")
            return None
    
    def get_test_case_account(self, test_case_path):
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('test_case', {}).get('account', None)
        except Exception as e:
            LOGGER_ERROR(f"Failed to get account from test case {test_case_path}: {str(e)}", "RED")
            return None
    
    def get_effective_account(self, test_case_path=None, test_suite_path=None, override_account=None):
        """
        Get the effective account to use with priority: override_account > test_suite account > test_case account.
        
        Args:
            test_case_path: Path to test case YAML file (optional)
            test_suite_path: Path to test suite YAML file (optional)
            override_account: Override account name (highest priority)
            
        Returns:
            str: The effective account name to use, or None if no account is configured
        """
        # Priority 1: Override account (from command line or API call)
        if override_account:
            LOGGER_INFO(f"Using override account: {override_account} (Priority 1: Override)", "CYAN")
            return override_account
        
        # Priority 2: Test suite account
        if test_suite_path:
            test_suite_account = self.get_test_suite_account(test_suite_path)
            if test_suite_account:
                LOGGER_INFO(f"Using test suite configured account: {test_suite_account} (Priority 2: Test Suite)", "CYAN")
                return test_suite_account
        
        # Priority 3: Test case account
        if test_case_path:
            test_case_account = self.get_test_case_account(test_case_path)
            if test_case_account:
                LOGGER_INFO(f"Using test case configured account: {test_case_account} (Priority 3: Test Case)", "CYAN")
                return test_case_account
        
        # No account configured
        LOGGER_WARNING("No account configured (checked override, test_suite, test_case)", "YELLOW")
        return None
    
    def get_test_case_retry_enabled(self, test_case_path):
        """
        Get retry_enabled configuration from test case YAML.
        
        Args:
            test_case_path: Path to test case YAML file
            
        Returns:
            bool: True if retry is enabled, False if disabled. Defaults to True if not specified.
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            # Default to True (retry enabled) if not specified for backward compatibility
            retry_enabled = data.get('test_case', {}).get('retry_enabled', True)
            LOGGER_INFO(f"Test case retry_enabled configuration: {retry_enabled}", "CYAN")
            return retry_enabled
        except Exception as e:
            LOGGER_ERROR(f"Failed to get retry_enabled from test case {test_case_path}: {str(e)}", "RED")
            return True  # Default to enabled on error
    
    def get_test_case_record_traversal(self, test_case_path):
        """
        Get record_traversal configuration from test case YAML.
        
        Args:
            test_case_path: Path to test case YAML file
            
        Returns:
            bool: True if recording controls during traversal, False to skip recording. 
                  Defaults to False if not specified (test validation mode).
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            # Default to False (record disabled) if not specified - test validation mode
            record_traversal = data.get('test_case', {}).get('record_traversal', False)
            LOGGER_INFO(f"Test case record_traversal configuration: {record_traversal}", "CYAN")
            return record_traversal
        except Exception as e:
            LOGGER_ERROR(f"Failed to get record_traversal from test case {test_case_path}: {str(e)}", "RED")
            return False  # Default to disabled on error
    
    def get_test_case_continue_on_error(self, test_case_path):
        """
        Get continue_on_error configuration from test case YAML.
        
        Args:
            test_case_path: Path to test case YAML file
            
        Returns:
            bool: True if should continue on error, False to stop execution. 
                  Defaults to False if not specified.
        """
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            continue_on_error = data.get('test_case', {}).get('continue_on_error', False)
            LOGGER_INFO(f"Test case continue_on_error configuration: {continue_on_error}", "CYAN")
            return continue_on_error
        except Exception as e:
            LOGGER_ERROR(f"Failed to get continue_on_error from test case {test_case_path}: {str(e)}", "RED")
            return False  # Default to stop on error

    
    def resolve_account_variables(self, ui_path, account_name=None):
        from config.account_config import account_config
        
        if not ui_path:
            return ui_path
        
        # Get account information
        account_info = account_config.get_account_info(account_name)
        if not account_info:
            LOGGER_WARNING(f"No account info found for '{account_name}', variables will not be resolved", "YELLOW")
            return ui_path
        
        resolved_ui_path = []
        for step in ui_path:
            if isinstance(step, dict):
                resolved_step = step.copy()
                
                # Check if this step has an action with a value that needs resolution
                if 'action' in resolved_step and 'value' in resolved_step['action']:
                    value = resolved_step['action']['value']
                    step_name = resolved_step.get('name', '').lower()
                    
                    # Helper function to check if value is empty or placeholder
                    def is_empty_or_placeholder(val):
                        """Check if value is empty, None, or a common placeholder"""
                        if not val:  # None or empty string
                            return True
                        if isinstance(val, str):
                            val_stripped = val.strip()
                            # Check for empty or common placeholders
                            return val_stripped == '' or val_stripped == 'placeholder' or val_stripped == 'TODO'
                        return False
                    
                    # Priority 1: Explicit variable replacement (${email}, ${password}, etc.)
                    if value == '${email}':
                        resolved_step['action']['value'] = account_info['email']
                        LOGGER_INFO(f"✅ Resolved variable ${{email}} to: {account_info['email']}", "CYAN")
                    elif value == '${password}':
                        resolved_step['action']['value'] = account_info['password']
                        LOGGER_INFO(f"✅ Resolved variable ${{password}}", "CYAN")
                    elif value == '${phone_username}':
                        resolved_step['action']['value'] = account_info['phone_username']
                        LOGGER_INFO(f"✅ Resolved variable ${{phone_username}} to: {account_info['phone_username']}", "CYAN")
                    elif value == '${phone_password}':
                        resolved_step['action']['value'] = account_info['phone_password']
                        LOGGER_INFO(f"✅ Resolved variable ${{phone_password}}", "CYAN")
                    
                    # Priority 2: Keep explicit non-empty values (user specified values)
                    elif value and not is_empty_or_placeholder(value) and not value.startswith('${'):
                        # User has specified a concrete value, keep it as-is
                        LOGGER_INFO(f"⭐ Keeping user-specified value for '{resolved_step.get('name', '')}': {value}", "GREEN")
                        # No change needed, keep the original value
                    
                    # Priority 3: Auto-detect and replace only for empty/placeholder values
                    elif 'email' in step_name and resolved_step['action']['type'] == 'input':
                        if is_empty_or_placeholder(value):
                            resolved_step['action']['value'] = account_info['email']
                            LOGGER_INFO(f"🔄 Auto-resolved empty email field to: {account_info['email']}", "YELLOW")
                        else:
                            LOGGER_INFO(f"⏭️  Skipping auto-resolve for email field (has value): {value}", "YELLOW")
                    elif 'password' in step_name and resolved_step['action']['type'] == 'input':
                        if is_empty_or_placeholder(value):
                            resolved_step['action']['value'] = account_info['password']
                            LOGGER_INFO(f"🔄 Auto-resolved empty password field", "YELLOW")
                        else:
                            LOGGER_INFO(f"⏭️  Skipping auto-resolve for password field (has value)", "YELLOW")
                    elif 'phone' in step_name and 'username' in step_name and resolved_step['action']['type'] == 'input':
                        if is_empty_or_placeholder(value):
                            resolved_step['action']['value'] = account_info['phone_username']
                            LOGGER_INFO(f"🔄 Auto-resolved empty phone username field to: {account_info['phone_username']}", "YELLOW")
                        else:
                            LOGGER_INFO(f"⏭️  Skipping auto-resolve for phone username field (has value): {value}", "YELLOW")
                    elif 'phone' in step_name and 'password' in step_name and resolved_step['action']['type'] == 'input':
                        if is_empty_or_placeholder(value):
                            resolved_step['action']['value'] = account_info['phone_password']
                            LOGGER_INFO(f"🔄 Auto-resolved empty phone password field", "YELLOW")
                        else:
                            LOGGER_INFO(f"⏭️  Skipping auto-resolve for phone password field (has value)", "YELLOW")
                
                resolved_ui_path.append(resolved_step)
            else:
                resolved_ui_path.append(step)
        
        return resolved_ui_path

    def build_control_name_ui_path(self, test_case_path=None, override_account=None, platform="windows", test_suite_path=None):
        """
        Build UI path with control_name information from control datasets and platform filtering.
        
        Args:
            test_case_path: Path to test case YAML file
            override_account: Override account name (highest priority)
            platform: Target platform (default: "windows")
            test_suite_path: Path to test suite YAML file (optional)
            
        Returns:
            list: UI path with control metadata, resolved account variables, and platform filtering
        """
        if test_case_path:
            with open(test_case_path, "r", encoding="utf-8") as f:
                workflow_dict = yaml.safe_load(f)
        else:
            LOGGER_ERROR("No test_case_path provided, cannot build control name UI path.")
            return []

        test_case_dict = workflow_dict.get("test_case", [])
        original_ui_path = []
        original_ui_path.extend(test_case_dict.get("steps", []))

        # Get effective account with priority: override > test_case > test_suite
        account_name = self.get_effective_account(test_case_path, test_suite_path, override_account)
        
        # Resolve account variables first
        ui_path = self.resolve_account_variables(original_ui_path, account_name)
        
        # Filter steps based on platform
        ui_path = self._filter_steps_by_platform(ui_path, platform)

        # Build control name UI path using control_datasets_loader
        control_name_ui_path = []
        total_controls = get_control_count()
        LOGGER_INFO(f"[Built][control name UI path metadata] Loaded {total_controls} controls from control datasets", "GREEN")

        for step in ui_path:
            if isinstance(step, dict):
                enhanced_step = step.copy()
                step_name = step.get('name', '')
                
                # Get complete control metadata using control_datasets_loader
                control_metadata = get_complete_control_metadata_by_name(step_name, platform)
                
                if control_metadata:
                    # Add control information to the step
                    enhanced_step['control_metadata'] = control_metadata
                    
                    # Update action target if it's a click action
                    if 'action' in enhanced_step and enhanced_step['action'].get('type') == 'click':
                        if 'target' not in enhanced_step['action']:
                            enhanced_step['action']['target'] = {}
                        
                        # Add control_name and control_id to target
                        enhanced_step['action']['target']['control_name'] = control_metadata.get('control_name', '')
                        enhanced_step['action']['target']['control_id'] = control_metadata.get('control_id', '')
                        
                        LOGGER_INFO(f"Enhanced click action for '{step_name}' with control_name: {control_metadata.get('control_name', '')}", "CYAN")                    
                else:
                    # Check if step is supported on platform
                    if is_step_supported_on_platform(step_name, platform):
                        LOGGER_WARNING(f"Step '{step_name}' is supported on {platform} but metadata is empty", "YELLOW")
                    else:
                        LOGGER_WARNING(f"Step '{step_name}' is not supported on platform '{platform}'", "YELLOW")
                
                control_name_ui_path.append(enhanced_step)
            else:
                control_name_ui_path.append(step)

        LOGGER_INFO(f"[Built][control name UI path metadata] with {len(control_name_ui_path)} steps", "GREEN")
        return control_name_ui_path

    def build_automation_id_ui_path(self, test_case_path=None, override_account=None, platform="windows", test_suite_path=None):
        """
        Build UI path with automation_id information from control datasets and platform filtering.
        
        Args:
            test_case_path: Path to test case YAML file
            override_account: Override account name (highest priority)
            platform: Target platform (default: "windows")
            test_suite_path: Path to test suite YAML file (optional)
            
        Returns:
            list: UI path with automation metadata, resolved account variables, and platform filtering
        """
        if test_case_path:
            with open(test_case_path, "r", encoding="utf-8") as f:
                workflow_dict = yaml.safe_load(f)
        else:
            LOGGER_ERROR("No test_case_path provided, cannot build automation ID UI path.")
            return []

        test_case_dict = workflow_dict.get("test_case", [])
        original_ui_path = []
        original_ui_path.extend(test_case_dict.get("steps", []))

        # Get effective account with priority: override > test_case > test_suite
        account_name = self.get_effective_account(test_case_path, test_suite_path, override_account)
        
        # Resolve account variables first
        ui_path = self.resolve_account_variables(original_ui_path, account_name)
        
        # Filter steps based on platform
        ui_path = self._filter_steps_by_platform(ui_path, platform)

        # Build automation ID UI path using control_datasets_loader
        automation_id_ui_path = []
        total_controls = get_control_count()
        LOGGER_INFO(f"Loaded {total_controls} controls from control datasets", "GREEN")
        
        for step in ui_path:
            if isinstance(step, dict):
                enhanced_step = step.copy()
                step_name = step.get('name', '')
                
                # Get complete control metadata using control_datasets_loader
                control_metadata = get_complete_control_metadata_by_name(step_name, platform)
                
                if control_metadata:
                    # Add automation ID information to the step (control_id as automation_id)
                    control_id = control_metadata.get('control_id', '')
                    enhanced_step['automation_metadata'] = {
                        'automation_id': control_id,
                        'control_name': control_metadata.get('control_name', ''),
                        'from_control': control_metadata.get('from_control', ''),
                        'hierarchical_level': control_metadata.get('hierarchical_level', ''),
                        'platform': platform
                    }
                    
                    # Update action target if it's a click action
                    if 'action' in enhanced_step and enhanced_step['action'].get('type') == 'click':
                        if 'target' not in enhanced_step['action']:
                            enhanced_step['action']['target'] = {}
                        
                        # Add automation_id and control_name to target
                        enhanced_step['action']['target']['automation_id'] = control_id
                        enhanced_step['action']['target']['control_name'] = control_metadata.get('control_name', '')
                        
                        LOGGER_INFO(f"Enhanced click action for '{step_name}' with automation_id: {control_id}", "CYAN")
                    
                    LOGGER_INFO(f"Enhanced step '{step_name}' with automation metadata", "CYAN")
                else:
                    # Check if step is supported on platform
                    if is_step_supported_on_platform(step_name, platform):
                        LOGGER_WARNING(f"Step '{step_name}' is supported on {platform} but metadata is empty", "YELLOW")
                    else:
                        LOGGER_WARNING(f"Step '{step_name}' is not supported on platform '{platform}'", "YELLOW")
                
                automation_id_ui_path.append(enhanced_step)
            else:
                automation_id_ui_path.append(step)

        LOGGER_INFO(f"Built automation ID UI path with {len(automation_id_ui_path)} steps", "GREEN")
        return automation_id_ui_path

    def get_test_case_from_db(self, test_case_name):
        """Get test case from database using centralized db connection"""
        try:
            connection = get_db_connection(TEST_CASE_DB)
            if not connection:
                LOGGER_ERROR("Failed to get database connection", "RED")
                return None
                
            try:
                # Use DictCursor to get results as dictionaries directly
                import pymysql.cursors
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Search for test case by name
                    cursor.execute("""
                        SELECT id, name, team, owner, description, expect_result, 
                               execution_duration, execution_count, module_path
                        FROM TestCase 
                        WHERE name = %s
                        LIMIT 1
                    """, (test_case_name,))
                    
                    result = cursor.fetchone()
                    if result:
                        LOGGER_INFO(f"Found test case '{test_case_name}' in database: {result}", "GREEN")
                        return result
                    else:
                        LOGGER_WARNING(f"Test case '{test_case_name}' not found in database", "YELLOW")
                        return None
                        
            finally:
                connection.close()
                
        except Exception as e:
            LOGGER_ERROR(f"Error while searching for test case '{test_case_name}': {str(e)}", "RED")
            return None

    def record_test_case_execution_result(self, testcase_id, execution_start_time, execution_end_time, 
                                        execution_duration_seconds, execution_status):
        """Record test case execution result using centralized db connection"""
        try:
            connection = get_db_connection(TEST_CASE_DB)
            if not connection:
                LOGGER_ERROR("Failed to get database connection", "RED")
                return False
                
            try:
                with connection.cursor() as cursor:
                    # Insert execution result
                    cursor.execute("""
                        INSERT INTO TestCaseExecutionResult (
                            testcase_id, execution_start_time, execution_end_time, 
                            execution_duration_seconds, execution_status
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (testcase_id, execution_start_time, execution_end_time, 
                          execution_duration_seconds, execution_status))
                    
                    connection.commit()
                    LOGGER_INFO(f"Recorded execution result for testcase_id {testcase_id}: {execution_status}", "GREEN")
                    return True
                        
            finally:
                connection.close()
                
        except Exception as e:
            LOGGER_ERROR(f"Error while recording execution result: {str(e)}", "RED")
            return False
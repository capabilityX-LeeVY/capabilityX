"""
Linux Control Operator - UI Automation for Linux using dogtail

Provides UI automation capabilities for Linux with full Windows architecture parity.

Architecture mirrors Windows (Navigator + Explorer):
    ControlOperator
        ├── ControlNavigator (keyboard-based navigation for tests)
        ├── ControlExplorer (tree-based exploration for data collection)
        └── ControlLocatorProcessor (unified location with retry logic)
"""

from core.linux.control_navigator import ControlNavigator
from core.linux.control_explorer import ControlExplorer
from core.linux.processors import ControlLocatorProcessor
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING, LOGGER_DEBUG
from config.key_map import KEY_MAP
from core.managers.function_loader import FunctionLoader
from rs_sdk.utils import control_datasets_loader
from rs_sdk.utils.control_datasets_loader import get_complete_control_metadata_by_name
from rs_sdk.utils.process_handler import ProcessHandler
import subprocess
import time


class ControlOperator:
    """
    Linux Control Operator for UI automation
    
    Full feature parity with Windows ControlOperator:
    - ControlNavigator: Keyboard-based UI navigation (simulates user input)
    - ControlExplorer: Tree-based data collection (accessibility tree walking)
    - ControlLocatorProcessor: Unified location strategy with retry logic
    """
    
    def __init__(self):
        """Initialize the Linux Control Operator with full architecture"""
        # Core components - matching Windows architecture
        self.control_navigator = ControlNavigator()  # Keyboard navigation
        self.control_explorer = ControlExplorer()    # Tree exploration
        self.control_locator = ControlLocatorProcessor(
            self.control_navigator,  # Primary: keyboard-based navigation
            self.control_explorer    # Fallback: direct tree access
        )
        
        # Function registry for API calls
        self.function_registry = None  # Lazy initialization to avoid circular import
        self.function_loader = FunctionLoader()
        self.process_handler = ProcessHandler()
        
        LOGGER_INFO("Linux ControlOperator initialized with full architecture (Navigator + Explorer)", "GREEN")
    
    def _get_function_registry(self):
        """Get function registry instance (lazy initialization to avoid circular import)"""
        if self.function_registry is None:
            from functions.registry import FunctionRegistry
            self.function_registry = FunctionRegistry()
        return self.function_registry
    
    def locate_control_by_ui_path(self, test_case, control_ui_path, navigate_report_path=None,
                                  performance_report_path=None, stress_report_path=None,
                                  test_case_execution_duration=1, test_case_execution_count=1,
                                  locate_id_flag=True, platform='linux', language='en_us',
                                  test_case_path=None, check_points=None):
        """
        Execute test steps from UI path
        
        Args:
            test_case: Test case name
            control_ui_path: List of UI control steps to execute
            navigate_report_path: Path for navigation report (unused for now)
            performance_report_path: Path for performance report (unused for now)
            stress_report_path: Path for stress report (unused for now)
            test_case_execution_duration: Duration for test execution (unused for now)
            test_case_execution_count: Count of test executions (unused for now)
            locate_id_flag: Whether to locate controls by ID (unused for now)
            platform: Target platform ('linux')
            language: Language for the test (unused for now)
            test_case_path: Path to test case YAML file (unused for now)
            check_points: Check points for validation (unused for now)
        
        Returns:
            bool: True if all steps executed successfully, False otherwise
        """
        LOGGER_INFO(f"Linux ControlOperator: Processing test case '{test_case}'")
        
        success = True
        
        for step in control_ui_path:
            if not isinstance(step, dict):
                LOGGER_WARNING(f"Invalid step format: {step}")
                continue
            
            step_name = step.get('name', 'Unknown step')
            action = step.get('action', {})
            action_type = action.get('type', '')
            action_value = action.get('value', '')
            expect_state = step.get('expect_state', '')
            wait_time = action.get('wait_time', 1)
            
            LOGGER_INFO(f"Executing step: {step_name} (type: {action_type})")
            
            try:
                # Handle function/API actions
                if action_type == 'function':
                    result = self._execute_function_action(action_value, action)
                    LOGGER_INFO(f"✅ Function '{action_value}' completed: {result}")

                elif action_type == 'api':
                    LOGGER_INFO(f"✅ Executing API action via registry: {action_value}")
                    registry = self._get_function_registry()
                    result = registry.execute_function(action_value)
                    LOGGER_INFO(f"✅ API action '{action_value}' completed: {result}")
                    
                # Handle key actions (keyboard navigation - matches Windows strategy)
                elif action_type == 'key':
                    if action_value == 'default':
                        # Use keyboard navigation (Navigator) - matches Windows production strategy
                        LOGGER_INFO(f"⌨️ Navigating to control via keyboard: {step_name}")
                        
                        # Get complete metadata from datasets (try linux, fallback to windows) - matches Windows pattern
                        complete_metadata = get_complete_control_metadata_by_name(step_name, platform='linux')
                        if complete_metadata is None:
                            # Fallback to windows metadata if linux not available
                            LOGGER_INFO(
                                f"[Linux][Operator] No linux metadata for '{step_name}', "
                                "falling back to windows metadata",
                                "YELLOW",
                            )
                            complete_metadata = get_complete_control_metadata_by_name(step_name, platform='windows')
                        
                        if complete_metadata:
                            actual_control_name = complete_metadata.get('control_name')
                            control_id = complete_metadata.get('control_id', '')
                            control_type = complete_metadata.get('control_type')
                            control_type_name = complete_metadata.get('control_type_name', '')
                        else:
                            # If no metadata found, use step_name as-is
                            actual_control_name = step_name
                            control_id = ''
                            control_type = ''
                            control_type_name = ''
                        
                        LOGGER_DEBUG(f"[Linux][Operator] Mapped '{step_name}' → actual_control_name='{actual_control_name}', control_id='{control_id}', type={control_type} ({control_type_name})", "CYAN")
                        
                        # Build control metadata dictionary (matching Windows format)
                        control_meta = {
                            'name': actual_control_name,
                            'id': control_id or '',
                            'test_case_step_description': step_name,
                            'control_type': control_type or '',
                            'control_type_name': control_type_name or ''
                        }
                        
                        # Use ControlLocatorProcessor which delegates to ControlNavigator (keyboard simulation)
                        # Match Windows signature: locate_control_handler_for_operator(control_meta, close_flag=False, locate_id_flag=True, is_optional=False)
                        is_optional = step.get('optional', False)
                        control_visited, result = self.control_locator.locate_control_handler_for_operator(
                            control_meta, locate_id_flag=True, is_optional=is_optional
                        )
                        
                        if result:
                            LOGGER_INFO(f"✅ Keyboard navigation successful: {step_name}")
                            time.sleep(wait_time)
                        else:
                            if is_optional:
                                LOGGER_INFO(f"⚠️ Optional control '{step_name}' not found, continuing...", "YELLOW")
                            else:
                                LOGGER_ERROR(f"❌ Keyboard navigation failed: {step_name}")
                                success = False
                    else:
                        # TODO: Handle specific key codes (Enter, Tab, etc.)
                        LOGGER_WARNING(f"⚠️ Specific key action not yet implemented: {action_value}")

                elif action_type == 'direct_key':
                    self._execute_direct_key_action(action_value)
                    time.sleep(wait_time)
                
                # Handle input actions (text entry via keyboard)
                elif action_type == 'input':
                    # Use keyboard navigation to reach the control, then type
                    LOGGER_INFO(f"⌨️ Navigating to input control via keyboard: {step_name}")
                    
                    # Get complete metadata from datasets (try linux, fallback to windows) - matches Windows pattern
                    complete_metadata = get_complete_control_metadata_by_name(step_name, platform='linux')
                    if complete_metadata is None:
                        # Fallback to windows metadata if linux not available
                        LOGGER_INFO(
                            f"[Linux][Operator] No linux metadata for '{step_name}', "
                            "falling back to windows metadata",
                            "YELLOW",
                        )
                        complete_metadata = get_complete_control_metadata_by_name(step_name, platform='windows')
                    
                    if complete_metadata:
                        actual_control_name = complete_metadata.get('control_name')
                        control_id = complete_metadata.get('control_id', '')
                        control_type = complete_metadata.get('control_type', 'input')
                        control_type_name = complete_metadata.get('control_type_name', 'text')
                    else:
                        # If no metadata found, use step_name as-is
                        actual_control_name = step_name
                        control_id = ''
                        control_type = 'input'
                        control_type_name = 'text'  # Default for input fields
                    
                    LOGGER_DEBUG(f"[Linux][Operator] Input field: '{step_name}' → actual_control_name='{actual_control_name}', control_id='{control_id}', type={control_type} ({control_type_name})", "CYAN")
                    
                    # Build control metadata dictionary (matching Windows format)
                    control_meta = {
                        'name': actual_control_name,
                        'id': control_id or '',
                        'test_case_step_description': step_name,
                                    'control_type': control_type or 'input',
                        'control_type_name': control_type_name or 'text'
                    }
                    
                    # Navigate to control using keyboard (matches Windows strategy)
                    is_optional = step.get('optional', False)
                    control_visited, result = self.control_locator.locate_control_handler_for_operator(
                        control_meta, locate_id_flag=True, is_optional=is_optional
                    )
                    
                    if result:
                        # Control is now focused via keyboard navigation
                        # Type the text directly (control already has focus)
                        LOGGER_INFO(f"✅ Typing text via keyboard: '{action_value}'")
                        subprocess.run(['xdotool', 'type', '--', action_value], check=True)
                        time.sleep(wait_time)
                    else:
                        if is_optional:
                            LOGGER_INFO(f"⚠️ Optional input control '{step_name}' not found, continuing...", "YELLOW")
                        else:
                            LOGGER_ERROR(f"❌ Failed to navigate to input control: {step_name}")
                            success = False
                
                else:
                    LOGGER_WARNING(f"⚠️ Unknown action type: {action_type}")
                
                # TODO: Implement expect_state verification
                if expect_state:
                    LOGGER_DEBUG(f"Expected state: {expect_state} (verification not yet implemented)")
                    
            except Exception as e:
                LOGGER_ERROR(f"❌ Error executing step '{step_name}': {str(e)}")
                success = False
        
        LOGGER_INFO(f"Test case '{test_case}' processing completed with result: {success}")
        return success
    
    def execute_test_case(self, *args, **kwargs):
        """
        Legacy method for compatibility
        
        Delegates to locate_control_by_ui_path for actual execution.
        """
        return self.locate_control_by_ui_path(*args, **kwargs)

    def _execute_function_action(self, function_name, action):
        """Execute YAML-configured functions through the dynamic function loader."""
        params = self._prepare_function_parameters(action)
        LOGGER_INFO(f"✅ Executing function: {function_name} with params: {params}")
        return self.function_loader.execute_function(function_name, **params)

    def _prepare_function_parameters(self, action):
        """Build runtime parameters for dynamically loaded functions."""
        params = {}

        action_params = action.get("params", {}) or action.get("parameters", {})
        if action_params:
            params.update(action_params)

        pid_info = self.process_handler.get_cisco_collab_pid_info()
        if pid_info.get("main_pid") is not None and "webex_main_pid" not in params:
            params["webex_main_pid"] = pid_info["main_pid"]
        if pid_info.get("media_pid") is not None and "webex_media_pid" not in params:
            params["webex_media_pid"] = pid_info["media_pid"]

        return params

    def _execute_direct_key_action(self, action_value):
        """Send a direct keyboard action using xdotool-compatible key names."""
        key_name = self._map_direct_key_value(action_value)
        LOGGER_INFO(f"⌨️ Sending direct key: {action_value} -> {key_name}")
        self.control_navigator._send_key(key_name)

    def _map_direct_key_value(self, action_value):
        """Translate YAML direct_key values to xdotool key names."""
        normalized = str(action_value).strip().lower()
        mapped = KEY_MAP.get(normalized, action_value)

        key_translation = {
            "{SPACE}": "space",
            "{ENTER}": "Return",
            "{ESC}": "Escape",
            "{TAB}": "Tab",
            "{SHIFT}{TAB}": "shift+Tab",
            "{LEFT}": "Left",
            "{RIGHT}": "Right",
            "{UP}": "Up",
            "{DOWN}": "Down",
        }

        return key_translation.get(mapped, str(action_value).strip())

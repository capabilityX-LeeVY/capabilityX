"""
Function Action Strategy

This module contains the FunctionActionStrategy for function call actions.
Enhanced version with dynamic function loading capabilities.
"""

from typing import Dict, Any
from pathlib import Path
from core.windows.strategies.action_strategy import ActionStrategy
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING
from core.managers.function_loader import FunctionLoader


class FunctionActionStrategy(ActionStrategy):
    """Function call action strategy with dynamic loading capabilities"""
    
    def __init__(self, control_handler):
        # Note: control_handler parameter is retained for backward compatibility
        # All functions are now executed via dynamic loading
        self.control_handler = control_handler
        
        # Initialize function loader
        function_config_path = str(Path(__file__).parent.parent.parent.parent / 
                                  "test_space" / "test_functions" / "function.json")
        self.function_loader = FunctionLoader(function_config_path)
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        """
        Execute function action using dynamic loading for all functions
        
        Args:
            ctrl_action: Control action configuration containing function info
            execution_context: Execution context with runtime information
            dependencies: Additional dependencies for function execution
            
        Returns:
            str: Result of function execution or error message
        """
        value = ctrl_action.get("value", None)
        
        if not value:
            LOGGER_WARNING("[FunctionActionStrategy] No function value specified")
            return ""
        
        # All functions now use dynamic loading
        result = self._execute_dynamic_function(value, ctrl_action, execution_context, dependencies)
        
        # Save return value to variable if save_to is specified
        save_to = ctrl_action.get("save_to")
        if save_to and execution_context:
            LOGGER_INFO(f"[FunctionActionStrategy] Saving return value to variable: {save_to}")
            execution_context.set_variable(save_to, result)
            LOGGER_INFO(f"[FunctionActionStrategy] Variable '{save_to}' = {result}")
        
        return result
    
    def _execute_dynamic_function(self, function_name: str, ctrl_action: Dict[str, Any], 
                                 execution_context, dependencies: Dict[str, Any]) -> str:
        """Execute function using dynamic loading"""
        try:
            # Check if function exists in configuration
            func_info = self.function_loader.get_function_info(function_name)
            if not func_info:
                LOGGER_ERROR(f"[FunctionActionStrategy] Function '{function_name}' not found in configuration")
                return f"ERROR: Function '{function_name}' not configured"
            
            LOGGER_INFO(f"[FunctionActionStrategy][Dynamic] Executing function: {function_name}")
            
            # Prepare function parameters
            params = self._prepare_function_parameters(ctrl_action, execution_context, dependencies)
            
            # Execute the function
            result = self.function_loader.execute_function(function_name, **params)

            if result is False:
                error_msg = f"{function_name} returned False"
                LOGGER_ERROR(f"[FunctionActionStrategy][Dynamic] {error_msg}")
                return f"ERROR: {error_msg}"

            if isinstance(result, dict) and result.get("status") in {"error", "failed", "failure"}:
                error_msg = result.get("message") or f"{function_name} returned failure status"
                LOGGER_ERROR(f"[FunctionActionStrategy][Dynamic] {function_name} failed: {error_msg}")
                return f"ERROR: {error_msg}"
             
            LOGGER_INFO(f"[FunctionActionStrategy][Dynamic] Function '{function_name}' completed successfully")
            
            # Return string representation of result
            return str(result) if result is not None else function_name
            
        except Exception as e:
            LOGGER_ERROR(f"[FunctionActionStrategy][Dynamic] Error executing function '{function_name}': {e}")
            return f"ERROR: {function_name} execution failed: {e}"
    
    def _prepare_function_parameters(self, ctrl_action: Dict[str, Any], 
                                   execution_context, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for function execution with variable resolution"""
        params = {}
        
        # Extract parameters from control action (support both 'params' and 'parameters')
        action_params = ctrl_action.get("params", {}) or ctrl_action.get("parameters", {})
        if action_params:
            # Resolve variables in parameters using ExecutionContext's method
            if execution_context and hasattr(execution_context, 'resolve_variables'):
                resolved_params = execution_context.resolve_variables(action_params)
            else:
                resolved_params = action_params
            params.update(resolved_params)
        
        # Add execution context information if needed
        if hasattr(execution_context, 'test_case'):
            params['test_case'] = execution_context.test_case
        
        # Add dependencies
        if dependencies:
            params.update(dependencies)
        
        # Add common execution context parameters that functions might need
        context_params = {
            'webex_main_pid': getattr(execution_context, 'webex_app_main_pid', None),
            'webex_media_pid': getattr(execution_context, 'webex_app_media_pid', None),
            'execution_duration': getattr(execution_context, 'execution_duration', 1),
            'execution_count': getattr(execution_context, 'execution_count', 1)
        }
        
        # Only add context params if they don't conflict with explicit parameters
        for key, value in context_params.items():
            if key not in params and value is not None:
                params[key] = value
        
        return params
    
    def get_action_type(self) -> str:
        """Get action type name"""
        return "function"
    
    def list_available_functions(self) -> Dict[str, str]:
        """List all available functions for debugging/documentation purposes"""
        return self.function_loader.list_available_functions()
    
    def reload_function_config(self):
        """Reload function configuration (useful for development/testing)"""
        LOGGER_INFO("[FunctionActionStrategy] Reloading function configuration")
        self.function_loader._load_function_config()

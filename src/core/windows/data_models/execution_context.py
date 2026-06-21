"""
Execution Context Data Model

This module contains the ExecutionContext dataclass for runtime environment information.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict, Union
import re
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING


@dataclass
class ExecutionContext:
    """Execution context data class - contains runtime environment information"""
    test_case: str
    execution_duration: int = 1
    execution_count: int = 1
    report_id: Optional[str] = None  # Added for UI response tracking
    check_points: Optional[List[str]] = None  # Test suite check points configuration
    webex_app_main_pid: Optional[int] = None
    webex_app_media_pid: Optional[int] = None
    current_main_cpu: str = "0"
    current_main_mem: str = "0"
    current_media_cpu: str = "0"
    current_media_mem: str = "0"
    current_main_gpu: str = "0"  # Added for GPU monitoring
    send_value: str = "{SPACE}"
    current_expect_state: str = ""
    current_control_image: Optional[str] = None
    verification_processor: Optional[Any] = None  # Added for value verification
    current_control: Optional[Any] = None  # Added for backward compatibility
    ai_check_result: Optional[str] = None  # Added for AI check result passing to next step
    variables: Dict[str, Any] = field(default_factory=dict)  # Storage for function return values and variables
    
    def has_check_point(self, check_point_name: str) -> bool:
        """Check if a specific check point is enabled in test suite configuration
        
        Args:
            check_point_name: Name of check point (e.g., 'Performance', 'Focus Ring', 'Keyboard Navigation')
            
        Returns:
            bool: True if check point is enabled, False otherwise
            
        Note:
            - When check_points is None: all check points enabled by default (backward compatibility)
            - When check_points is [] (empty list): no check points enabled (explicit disable)
            - Otherwise: only check points in the list are enabled
        """
        if self.check_points is None:
            return True  # All check points enabled by default when not specified
        if len(self.check_points) == 0:
            return False  # Empty list = explicitly disable all check points
        return check_point_name in self.check_points
    
    def set_variable(self, name: str, value: Any) -> None:
        """Store a variable value for later use in subsequent steps
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value stored in execution context
        
        Args:
            name: Variable name
            default: Default value if variable not found
            
        Returns:
            Variable value or default
        """
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable exists in execution context
        
        Args:
            name: Variable name
            
        Returns:
            bool: True if variable exists, False otherwise
        """
        return name in self.variables
    
    def resolve_variables(self, value: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
        """Resolve variable references in value (supports ${var_name} or $var_name syntax)
        
        This method can handle:
        - String values with variable references
        - Dictionary values (recursively resolves all string values)
        - List values (recursively resolves all elements)
        - Other types (returns as-is)
        
        Args:
            value: Value to resolve (can be str, dict, list, or any other type)
            
        Returns:
            Resolved value with variables replaced by their actual values
            
        Examples:
            >>> context.set_variable('meeting_id', 'MTG-123')
            >>> context.resolve_variables('Join ${meeting_id}')
            'Join MTG-123'
            >>> context.resolve_variables({'id': '$meeting_id', 'name': 'test'})
            {'id': 'MTG-123', 'name': 'test'}
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve_variables(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_variables(item) for item in value]
        else:
            return value
    
    def _resolve_string(self, value: str) -> str:
        """Resolve variable references in a string
        
        Supports two formats:
        - ${variable_name}: Clear and recommended
        - $variable_name: Simplified version
        
        Args:
            value: String value to resolve
            
        Returns:
            String with variables replaced
        """
        # Pattern matches ${var_name} or $var_name
        pattern = r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)'
        
        def replacer(match):
            # Get variable name from either capture group
            var_name = match.group(1) or match.group(2)
            
            if self.has_variable(var_name):
                var_value = self.get_variable(var_name)
                LOGGER_INFO(f"[ExecutionContext] Resolving variable ${{{var_name}}} = {var_value}", "CYAN")
                return str(var_value)
            else:
                LOGGER_WARNING(f"[ExecutionContext] Variable '{var_name}' not found, keeping original reference", "YELLOW")
                return match.group(0)  # Keep original if variable not found
        
        return re.sub(pattern, replacer, value)

"""
Function Loader Module

This module provides functionality to dynamically load and execute functions
based on configuration from function.json.
"""

import json
import importlib
import inspect
import os
import sys
from typing import Dict, Any, Callable, Optional, Union
from pathlib import Path

# Import centralized path configuration
from config.paths import FUNCTION_CONFIG_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING, LOGGER_DEBUG


class FunctionLoader:
    """Dynamic function loader for test functions"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize function loader with configuration file"""
        if config_path is None:
            # Use centralized path configuration
            config_path = str(FUNCTION_CONFIG_PATH)
        
        self.config_path = config_path
        self._function_registry = {}
        self._load_function_config()
    
    def _load_function_config(self):
        """Load function configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.function_config = json.load(f)
            
            LOGGER_DEBUG(f"[FunctionLoader] Loaded {len(self.function_config)} function definitions")
            
            # Build function registry for quick lookup
            for func_def in self.function_config:
                self._function_registry[func_def['name']] = func_def
                
        except FileNotFoundError:
            LOGGER_ERROR(f"[FunctionLoader] Configuration file not found: {self.config_path}")
            self.function_config = []
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"[FunctionLoader] Invalid JSON in configuration file: {e}")
            self.function_config = []
        except Exception as e:
            LOGGER_ERROR(f"[FunctionLoader] Error loading configuration: {e}")
            self.function_config = []
    
    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get function information by name"""
        return self._function_registry.get(function_name)
    
    def load_function(self, function_name: str) -> Optional[Callable]:
        """Dynamically load a function by name"""
        func_info = self.get_function_info(function_name)
        if not func_info:
            LOGGER_ERROR(f"[FunctionLoader] Function '{function_name}' not found in configuration")
            return None
        
        try:
            module_path = func_info['module_path']
            function_name_in_module = func_info['function_name']
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the function from the module
            if not hasattr(module, function_name_in_module):
                LOGGER_ERROR(f"[FunctionLoader] Function '{function_name_in_module}' not found in module '{module_path}'")
                return None
            
            func = getattr(module, function_name_in_module)
            
            # Verify it's a callable
            if not callable(func):
                LOGGER_ERROR(f"[FunctionLoader] '{function_name_in_module}' is not callable in module '{module_path}'")
                return None
            
            LOGGER_INFO(f"[FunctionLoader] Successfully loaded function '{function_name}' from '{module_path}'")
            return func
            
        except ImportError as e:
            LOGGER_ERROR(f"[FunctionLoader] Failed to import module '{func_info['module_path']}': {e}")
            return None
        except Exception as e:
            LOGGER_ERROR(f"[FunctionLoader] Error loading function '{function_name}': {e}")
            return None
    
    def execute_function(self, function_name: str, **kwargs) -> Any:
        """Execute a function with provided parameters"""
        func_info = self.get_function_info(function_name)
        if not func_info:
            raise ValueError(f"Function '{function_name}' not found in configuration")
        
        # Load the function
        func = self.load_function(function_name)
        if not func:
            raise RuntimeError(f"Failed to load function '{function_name}'")
        
        try:
            # Get function signature for parameter validation
            sig = inspect.signature(func)
            
            # Prepare parameters based on function signature and configuration
            prepared_params = self._prepare_parameters(func_info, kwargs, sig)
            
            LOGGER_INFO(f"[FunctionLoader] Executing function '{function_name}' with parameters: {prepared_params}")
            
            # Execute the function
            result = func(**prepared_params)
            
            LOGGER_INFO(f"[FunctionLoader] Function '{function_name}' executed successfully")
            return result
            
        except Exception as e:
            LOGGER_ERROR(f"[FunctionLoader] Error executing function '{function_name}': {e}")
            raise
    
    def _prepare_parameters(self, func_info: Dict[str, Any], provided_params: Dict[str, Any], 
                          func_signature: inspect.Signature) -> Dict[str, Any]:
        """Prepare and validate parameters for function execution"""
        config_params = func_info.get('parameters', {}).get('properties', {})
        required_params = func_info.get('parameters', {}).get('required', [])
        
        prepared = {}
        
        # Check required parameters
        for param_name in required_params:
            if param_name not in provided_params:
                # Check if there's a default value in configuration
                param_config = config_params.get(param_name, {})
                if 'default' in param_config:
                    prepared[param_name] = param_config['default']
                    LOGGER_INFO(f"[FunctionLoader] Using default value for parameter '{param_name}': {param_config['default']}")
                else:
                    raise ValueError(f"Required parameter '{param_name}' not provided for function '{func_info['name']}'")
            else:
                prepared[param_name] = provided_params[param_name]
        
        # Add optional parameters if provided
        for param_name, value in provided_params.items():
            if param_name not in prepared and param_name in config_params:
                prepared[param_name] = value
        
        # Validate parameters against function signature
        try:
            bound = func_signature.bind(**prepared)
            bound.apply_defaults()
            return bound.arguments
        except TypeError as e:
            LOGGER_WARNING(f"[FunctionLoader] Parameter binding warning: {e}, proceeding with prepared parameters")
            return prepared
    
    def list_available_functions(self) -> Dict[str, str]:
        """List all available functions with their descriptions"""
        return {
            func['name']: func.get('description', 'No description available')
            for func in self.function_config
        }

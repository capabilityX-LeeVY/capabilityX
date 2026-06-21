"""
Function Manager Module

This module provides comprehensive management functionality for test functions,
including configuration validation, function discovery, and diagnostics.
"""

import json
import importlib
import inspect
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Import centralized path configuration
from config.paths import FUNCTION_CONFIG_PATH, TEST_FUNCTIONS_PATH, SRC_PATH, PROJECT_ROOT_PATH


class FunctionManager:
    """Comprehensive function management for test functions"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize function manager with configuration file"""
        if config_path is None:
            # Use centralized path configuration
            config_path = str(FUNCTION_CONFIG_PATH)
        
        self.config_path = config_path
        self.errors = []
        self.warnings = []
        self.function_cache = {}
        self._load_config()
    
    def _load_config(self):
        """Load function configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print(f"[FunctionManager] Loaded {len(self.config)} function definitions")
            
            # Build function registry for quick lookup
            self.function_registry = {}
            for func_def in self.config:
                self.function_registry[func_def['name']] = func_def
                
        except FileNotFoundError:
            print(f"[FunctionManager] Configuration file not found: {self.config_path}")
            self.config = []
            self.function_registry = {}
        except json.JSONDecodeError as e:
            print(f"[FunctionManager] Invalid JSON in configuration file: {e}")
            self.config = []
            self.function_registry = {}
        except Exception as e:
            print(f"[FunctionManager] Error loading configuration: {e}")
            self.config = []
            self.function_registry = {}
    
    def validate_configuration(self) -> bool:
        """Validate the configuration file and return success status"""
        print(f"Validating function configuration: {self.config_path}")
        self.errors.clear()
        self.warnings.clear()
        
        # Check if config file exists
        if not Path(self.config_path).exists():
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False
        
        # Validate configuration structure
        if not isinstance(self.config, list):
            self.errors.append("Configuration must be a list of function definitions")
            return False
        
        # Validate each function definition
        success = True
        for i, func_def in enumerate(self.config):
            if not self._validate_function_definition(func_def, i):
                success = False
        
        # Print results
        self._print_validation_results()
        
        return success and len(self.errors) == 0
    
    def _validate_function_definition(self, func_def: Dict[str, Any], index: int) -> bool:
        """Validate a single function definition"""
        success = True
        
        # Check required fields
        required_fields = ['name', 'module_path', 'function_name']
        for field in required_fields:
            if field not in func_def:
                self.errors.append(f"Function {index}: Missing required field '{field}'")
                success = False
        
        if not success:
            return False
        
        name = func_def['name']
        module_path = func_def['module_path']
        function_name = func_def['function_name']
        
        # Check if module can be imported
        try:
            module = importlib.import_module(module_path)
            print(f"✓ Module '{module_path}' imported successfully")
        except ImportError as e:
            self.errors.append(f"Function '{name}': Cannot import module '{module_path}': {e}")
            return False
        except Exception as e:
            self.errors.append(f"Function '{name}': Error importing module '{module_path}': {e}")
            return False
        
        # Check if function exists in module
        if not hasattr(module, function_name):
            self.errors.append(f"Function '{name}': Function '{function_name}' not found in module '{module_path}'")
            return False
        
        func = getattr(module, function_name)
        if not callable(func):
            self.errors.append(f"Function '{name}': '{function_name}' is not callable in module '{module_path}'")
            return False
        
        print(f"✓ Function '{name}' validated successfully")
        
        # Validate parameters schema (optional)
        if 'parameters' in func_def:
            self._validate_parameters_schema(func_def['parameters'], name)
        
        return True
    
    def _validate_parameters_schema(self, params_schema: Dict[str, Any], function_name: str):
        """Validate parameters schema format"""
        if not isinstance(params_schema, dict):
            self.warnings.append(f"Function '{function_name}': Parameters should be a dictionary")
            return
        
        if 'type' in params_schema and params_schema['type'] != 'object':
            self.warnings.append(f"Function '{function_name}': Parameters type should be 'object'")
        
        if 'properties' in params_schema:
            properties = params_schema['properties']
            if not isinstance(properties, dict):
                self.warnings.append(f"Function '{function_name}': Properties should be a dictionary")
        
        if 'required' in params_schema:
            required = params_schema['required']
            if not isinstance(required, list):
                self.warnings.append(f"Function '{function_name}': Required should be a list")
    
    def _print_validation_results(self):
        """Print validation results"""
        print("\n" + "="*50)
        print("VALIDATION RESULTS")
        print("="*50)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print("\n✅ Validation passed with warnings")
        else:
            print("\n❌ Validation failed")
    
    def list_functions(self) -> Dict[str, str]:
        """List all available functions with their descriptions"""
        return {
            func['name']: func.get('description', 'No description available')
            for func in self.config
        }
    
    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific function"""
        return self.function_registry.get(function_name)
    
    def discover_functions(self, search_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover functions in the filesystem that aren't in configuration"""
        if search_path is None:
            # Use centralized path configuration
            search_path = str(TEST_FUNCTIONS_PATH)
        
        discovered = []
        search_dir = Path(search_path)
        
        # Get functions already in config
        configured_functions = {func['module_path'] for func in self.config}
        
        # Search for Python files
        for py_file in search_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            # Convert file path to module path using centralized src path
            relative_path = py_file.relative_to(SRC_PATH)
            module_path = str(relative_path.with_suffix("")).replace("\\", ".").replace("/", ".")
            
            if module_path in configured_functions:
                continue
            
            try:
                module = importlib.import_module(module_path)
                functions = [name for name, obj in inspect.getmembers(module, inspect.isfunction)
                           if not name.startswith("_")]
                
                if functions:
                    discovered.append({
                        "module_path": module_path,
                        "file_path": str(py_file),
                        "functions": functions
                    })
            except Exception:
                # Skip modules that can't be imported
                continue
        
        return discovered
    
    def generate_function_template(self, function_name: str, module_path: str, 
                                 actual_function_name: str, description: str = "") -> Dict[str, Any]:
        """Generate a template configuration for a new function"""
        return {
            "name": function_name,
            "description": description or f"Description for {function_name}",
            "module_path": module_path,
            "function_name": actual_function_name,
            "parameters": {
                "type": "object",
                "properties": {
                    "example_param": {
                        "type": "string",
                        "description": "Example parameter description"
                    }
                },
                "required": []
            }
        }
    
    def add_function(self, function_config: Dict[str, Any]) -> bool:
        """Add a new function to the configuration"""
        try:
            # Validate the new function config
            if not self._validate_function_definition(function_config, len(self.config)):
                return False
            
            # Add to configuration
            self.config.append(function_config)
            self.function_registry[function_config['name']] = function_config
            
            # Save to file
            self._save_config()
            
            print(f"✓ Successfully added function '{function_config['name']}'")
            return True
            
        except Exception as e:
            print(f"✗ Error adding function: {e}")
            return False
    
    def remove_function(self, function_name: str) -> bool:
        """Remove a function from the configuration"""
        try:
            # Find and remove from config
            self.config = [func for func in self.config if func['name'] != function_name]
            
            # Remove from registry
            if function_name in self.function_registry:
                del self.function_registry[function_name]
            
            # Save to file
            self._save_config()
            
            print(f"✓ Successfully removed function '{function_name}'")
            return True
            
        except Exception as e:
            print(f"✗ Error removing function: {e}")
            return False
    
    def _save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about configured functions"""
        total_functions = len(self.config)
        modules = set(func['module_path'] for func in self.config)
        
        # Count functions by type (based on module path)
        function_types = {}
        for func in self.config:
            module_parts = func['module_path'].split('.')
            if len(module_parts) >= 2:
                func_type = module_parts[-2]  # Parent directory name
                function_types[func_type] = function_types.get(func_type, 0) + 1
        
        return {
            "total_functions": total_functions,
            "total_modules": len(modules),
            "function_types": function_types,
            "modules": list(modules)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        print("Performing function health check...")
        
        results = {
            "config_valid": True,
            "all_functions_accessible": True,
            "issues": [],
            "statistics": self.get_statistics()
        }
        
        # Validate configuration
        if not self.validate_configuration():
            results["config_valid"] = False
            results["issues"].extend(self.errors)
        
        # Test function accessibility
        for func_def in self.config:
            try:
                module = importlib.import_module(func_def['module_path'])
                if not hasattr(module, func_def['function_name']):
                    results["all_functions_accessible"] = False
                    results["issues"].append(f"Function {func_def['function_name']} not accessible in {func_def['module_path']}")
            except Exception as e:
                results["all_functions_accessible"] = False
                results["issues"].append(f"Cannot access {func_def['name']}: {e}")
        
        return results


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Function Manager for test functions")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--list", action="store_true", help="List all functions")
    parser.add_argument("--discover", action="store_true", help="Discover unconfigured functions")
    parser.add_argument("--health-check", action="store_true", help="Perform health check")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    manager = FunctionManager()
    
    if args.validate:
        success = manager.validate_configuration()
        if not success:
            sys.exit(1)
        print("\n🎉 Configuration is valid and ready to use!")
    
    elif args.list:
        functions = manager.list_functions()
        print("\n📋 Available Functions:")
        for name, desc in functions.items():
            print(f"  • {name}: {desc}")
    
    elif args.discover:
        discovered = manager.discover_functions()
        print("\n🔍 Discovered Functions (not in config):")
        for item in discovered:
            print(f"  📁 {item['module_path']}")
            for func in item['functions']:
                print(f"    • {func}")
    
    elif args.health_check:
        results = manager.health_check()
        print(f"\n🏥 Health Check Results:")
        print(f"  Config Valid: {'✅' if results['config_valid'] else '❌'}")
        print(f"  All Functions Accessible: {'✅' if results['all_functions_accessible'] else '❌'}")
        if results['issues']:
            print(f"  Issues Found: {len(results['issues'])}")
            for issue in results['issues']:
                print(f"    • {issue}")
    
    elif args.stats:
        stats = manager.get_statistics()
        print("\n📊 Function Statistics:")
        print(f"  Total Functions: {stats['total_functions']}")
        print(f"  Total Modules: {stats['total_modules']}")
        print(f"  Function Types: {stats['function_types']}")
    
    else:
        # Default: run validation
        success = manager.validate_configuration()
        if not success:
            sys.exit(1)
        print("\n🎉 Configuration is valid and ready to use!")


if __name__ == "__main__":
    main()

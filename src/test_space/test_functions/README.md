# Function Action Strategy User Guide

## Overview

The refactored `FunctionActionStrategy` supports dynamic function loading and execution while maintaining backward compatibility with existing code.

## Architecture Design

```
test_case (YAML) 
    ↓ Define functions to call
function.json 
    ↓ Configure module paths and parameters
function_loader.py 
    ↓ Dynamically load functions
function_action_strategy.py 
    ↓ Execute function calls
actual_function.py 
    ↓ Actual function implementation
```

## File Structure

```
src/
├── core/windows/strategies/
│   └── function_action_strategy.py     # Refactored strategy class
├── test_space/
│   ├── test_functions/
│   │   ├── function.json              # Function configuration file
│   │   ├── function_loader.py         # Dynamic loader
│   │   ├── functions_manager.py       # Function management tool
│   │   ├── ui_controls/               # UI control utility functions
│   │   │   └── window_control.py      # Window control utilities
│   │   └── webex_bot/
│   │       └── send_message.py        # Concrete function implementation
│   └── test_cases/sample/
│       ├── sample05.yaml              # Webex bot test case
│       └── sample06.yaml              # UI control test case
└── final_test.py                      # Test script
```

## Configuration Format

### function.json Configuration Format

```json
[
    {
        "name": "send_message_to_webex",
        "description": "Send message to Webex teams using bot",
        "module_path": "test_space.test_functions.webex_bot.send_message",
        "function_name": "send_message_to_webex",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message content to send",
                    "default": "Test message from automated test"
                }
            },
            "required": ["message"]
        }
    }
]
```

### Test Case Format

```yaml
steps:
  - name: "test send message"
    action:
      type: function
      value: send_message_to_webex
      parameters:
        message: "Custom test message"
    expect_state: ""
```

## Key Features

### 1. Backward Compatibility

- Preserve all existing hardcoded function logic
- Existing test cases continue to work without modification
- Automatic fallback to legacy mode on errors

### 2. Dynamic Function Loading

- Support for defining new functions through configuration files
- Runtime dynamic import and execution
- Support for parameter validation and default values

### 3. Flexible Parameter Passing

- Support for passing parameters from test cases
- Automatic injection of execution context information
- Support for parameter default values and validation

### 4. Error Handling

- Comprehensive exception handling mechanisms
- Detailed logging
- Automatic fallback strategies

## Usage

### 1. Adding New Functions

1. Create function files under `test_space/test_functions`
2. Add function configuration in `function.json`
3. Use the function in test cases

### 2. Running Tests

```python
# Use test script for validation
python src/final_test.py
```

### 3. Managing Functions

```python
# Validate configuration
python src/test_space/test_functions/functions_manager.py --validate

# List all functions
python src/test_space/test_functions/functions_manager.py --list

# Show statistics
python src/test_space/test_functions/functions_manager.py --stats

# Perform health check
python src/test_space/test_functions/functions_manager.py --health-check

# Discover unconfigured functions
python src/test_space/test_functions/functions_manager.py --discover
```

### 4. Debugging and Monitoring

```python
# Get list of available functions
strategy = FunctionActionStrategy(control_handler)
functions = strategy.list_available_functions()

# Reload configuration
strategy.reload_function_config()
```

## Extensibility

### Adding New Function Types

1. Create function modules in the appropriate directory
2. Update `function.json` configuration
3. Functions will be automatically discovered and loaded

### Custom Parameter Processing

You can add custom parameter processing logic in the `_prepare_function_parameters` method.

### Adding New Validation Rules

You can extend parameter validation functionality in the `FunctionLoader`.

## Important Notes

1. **Module Paths**: Ensure `module_path` uses correct Python import paths
2. **Parameter Naming**: Keep parameter names in configuration files consistent with function signatures
3. **Error Handling**: Functions should have appropriate error handling to avoid interrupting the entire test flow
4. **Logging**: Use the unified logging system to record function execution information

## Examples

### Complete Function Addition Example

1. **Create Function File** (`test_space/test_functions/webex_bot/new_function.py`):

```python
def my_new_function(param1, param2="default_value"):
    """My new test function"""
    return f"Executed with {param1} and {param2}"
```

2. **Update Configuration** (`function.json`):

```json
{
    "name": "my_new_function",
    "description": "My new test function",
    "module_path": "test_space.test_functions.webex_bot.new_function",
    "function_name": "my_new_function",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "string", "description": "Second parameter", "default": "default_value"}
        },
        "required": ["param1"]
    }
}
```

3. **Use in Test Cases**:

```yaml
action:
  type: function
  value: my_new_function
  parameters:
    param1: "test_value"
```

This design ensures system extensibility and maintainability while maintaining compatibility with existing code.

---

# API Configuration Guide

## 📁 API Configuration File

**Location**: `src/test_space/test_functions/api_config.json`

This file contains configurations for API calls used in test cases, similar to how `function.json` manages function calls.

## 🔧 API Configuration Structure

Each API configuration contains:
- **url**: API endpoint URL
- **method**: HTTP method (GET, POST, PUT, DELETE, etc.)
- **headers**: HTTP headers
- **body**: Request body (for POST/PUT requests)  
- **expected_status**: Expected HTTP status code
- **timeout**: Request timeout in seconds
- **description**: Human-readable description

### Template Variables
Use `{{variable_name}}` for dynamic values:
```json
{
  "run_test_case_api": {
    "url": "http://localhost:9909/api/run_test_case",
    "method": "POST",
    "body": {
      "test_case_name": "{{test_case_name}}",
      "platform": "{{platform}}"
    }
  }
}
```

### Usage in Test Cases
Reference APIs in YAML test cases:
```yaml
steps:
  - name: "test api call"
    action:
      type: api
      value: run_test_case_api
      parameters:
        test_case_name: "sign_in"
        platform: "windows"
```

## 🎯 Available APIs

### Internal APIs
- **run_test_case_api** - Execute test cases via API
- **get_functions_api** - Get available functions  
- **health_check_api** - API health check
- **start_meeting_api** - Start Webex meetings

### External APIs  
- **webex_login_api** - Webex OAuth login
- **webex_create_space_api** - Create Webex spaces
- **webex_send_message_api** - Send messages to Webex

### Utility APIs
- **custom_api_call** - Flexible API call template

## 📝 Adding New APIs

1. Add configuration to `api_config.json`
2. Use template variables for dynamic content
3. Test the configuration via test cases
4. Update this documentation

This API configuration system provides the same flexibility and maintainability as the function system, but specifically for API interactions.

# Test Case API Usage Guide

## 🎯 **Overview**

A new API endpoint has been created to run individual test cases using the `TestCaseRunner` from `src\core\test_case_runner.py`.

## 📋 **API Endpoint**

### **POST /run_test_case**

Execute a specific test case by name.

#### **Request Body**
```json
{
    "test_case_name": "sign_in",
    "platform": "windows"
}
```

#### **Parameters**
- `test_case_name` (required): Name of the test case to execute (e.g., "sign_in")
- `platform` (optional): Platform to run on. Defaults to "windows" if not specified

#### **Response**
```json
{
    "status": "success",
    "message": "Test case 'sign_in' executed successfully",
    "test_case_name": "sign_in",
    "navigate_report_path": "/path/to/navigation/report.json",
    "performance_report_path": "/path/to/performance/report.json"
}
```

## 🚀 **Usage Examples**

### **Example 1: Run Sign-in Test Case**
```bash
curl -X POST "http://localhost:8000/run_test_case" \
     -H "Content-Type: application/json" \
     -d '{
       "test_case_name": "sign_in",
       "platform": "windows"
     }'
```

### **Example 2: Run Test Case with Default Platform**
```bash
curl -X POST "http://localhost:8000/run_test_case" \
     -H "Content-Type: application/json" \
     -d '{
       "test_case_name": "sign_in"
     }'
```

### **Example 3: Using Python Requests**
```python
import requests

url = "http://localhost:8000/run_test_case"
payload = {
    "test_case_name": "sign_in",
    "platform": "windows"
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Navigation Report: {result['navigate_report_path']}")
```

## 📂 **File Changes Made**

### **1. API Schema (`src/functions/schemas/api_schemas.py`)**
Added new request and response models:
- `RunTestCaseRequest`: For API request parameters
- `RunTestCaseResponse`: For API response data

### **2. Handler Function (`src/functions/handlers/meetings_functions.py`)**
Added new function:
- `run_test_case_function()`: Handles the test case execution logic

### **3. API Routes (`src/functions/api/routes.py`)**
Added new endpoint:
- `POST /run_test_case`: Main API endpoint for test case execution

## 🔧 **How It Works**

1. **API Request**: Client sends POST request with test case name
2. **Handler Function**: `run_test_case_function()` creates a `TestCaseRunner` instance
3. **Test Execution**: Calls `test_runner.run_test_case()` method
4. **Response**: Returns execution results including report paths

## 📊 **Response Status**

### **Success Response**
```json
{
    "status": "success",
    "message": "Test case 'sign_in' executed successfully",
    "test_case_name": "sign_in",
    "navigate_report_path": "/path/to/nav_report.json",
    "performance_report_path": "/path/to/perf_report.json"
}
```

### **Error Response**
```json
{
    "status": "error",
    "message": "Test case 'sign_in' execution failed: Error details here",
    "test_case_name": "sign_in",
    "navigate_report_path": null,
    "performance_report_path": null
}
```

## 🎯 **Available Test Cases**

You can run any test case by name, for example:
- `"sign_in"` - Sign in test case
- `"start_meeting"` - Start meeting test case
- `"join_meeting"` - Join meeting test case
- Any other test case name defined in your test cases directory

## ⚙️ **Platform Options**

- `"windows"` (default)
- `"web"`
- `"mac"`

## 🚨 **Error Handling**

The API includes comprehensive error handling:
- Invalid test case names
- Platform setup failures
- Test execution errors
- Network/system issues

All errors are returned with appropriate HTTP status codes and descriptive messages.

## 🔗 **Integration**

This API can be easily integrated into:
- CI/CD pipelines
- Test automation frameworks
- External monitoring systems
- Manual testing workflows

The API follows RESTful principles and returns structured JSON responses for easy consumption by various clients.

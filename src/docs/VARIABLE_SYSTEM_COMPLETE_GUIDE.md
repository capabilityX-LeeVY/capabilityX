# Variable System Complete Guide - Comprehensive Documentation

**Version**: 2.1  
**Date**: January 30, 2026  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Core Features](#core-features)
3. [Variable Syntax](#variable-syntax)
4. [Supported Action Types](#supported-action-types)
5. [AI Check Integration](#ai-check-integration)
6. [Complete Examples](#complete-examples)
7. [Technical Implementation](#technical-implementation)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)
10. [Related Files](#related-files)

---

## 🚀 Quick Start

### What Can You Do?

**Yes!** You can use function return values across all action types including AI check:

```yaml
steps:
  # Step 1: Get data with function
  - name: "Get meeting ID"
    action:
      type: function
      value: get_meeting_id
      save_to: meeting_id  # ← Save to variable
    expect_state: ""
  
  # Step 2: Use in input
  - name: "Input meeting ID"
    action:
      type: input
      value: "${meeting_id}"  # ← Use in input
  
  # Step 3: Use in AI check
  - name: "Verify meeting title"
    action:
      type: key
      value: default
    expect_state: ""
    ai_check:
      prompt: "Check if meeting title contains ${meeting_id}. ✅Success or ❌Failed"
```

---

## 🎯 Core Features

### 1. Save Return Values

Use `save_to` parameter to save function return values:

```yaml
- name: "Get current time"
  action:
    type: function
    value: get_current_time
    save_to: current_timestamp  # Save to variable
```

### 2. Reference Variables

Variables can be used in:
- ✅ **function** parameters
- ✅ **input** values
- ✅ **key** values
- ✅ **ai_check** prompts ⭐ NEW
- ✅ Any action type that supports parameters

### 3. Cross Action Type Support

Variables flow seamlessly between different action types:

```yaml
# function → input → function → ai_check
- name: "Get username"
  action:
    type: function
    value: get_username
    save_to: username

- name: "Input username"
  action:
    type: input
    value: "${username}"

- name: "Print message"
  action:
    type: function
    value: print_message
    parameters:
      message: "User: ${username}"

- name: "Verify display"
  ai_check:
    prompt: "Check if ${username} is displayed correctly"
```

---

## 💡 Variable Syntax

### Two Supported Formats

| Syntax | Example | Description | Recommendation |
|--------|---------|-------------|----------------|
| `${variable_name}` | `${username}` | Clear and explicit | ✅ Recommended |
| `$variable_name` | `$username` | Simplified version | ✅ Also supported |

### Usage Examples

```yaml
# Method 1: ${variable} (Recommended)
value: "${meeting_id}"
prompt: "Verify meeting ${meeting_id} is displayed"

# Method 2: $variable (Simplified)
value: "$username"
prompt: "Check if $username is visible"

# Method 3: Embedded in strings
value: "Meeting ${meeting_id} hosted by ${username}"
prompt: "Verify panel shows: ID: ${meeting_id}, Host: ${username}, Count: ${participant_count}"
```

---

## 📊 Supported Action Types

### Complete Support Matrix

| Action Type | Save Variable | Reference Variable | Example File |
|-------------|---------------|-------------------|--------------|
| **function** | ✅ | ✅ | function_return_value_example.yaml |
| **input** | ❌ | ✅ | cross_action_type_variables.yaml |
| **key** | ❌ | ✅ | cross_action_type_variables.yaml |
| **api** | ❌ | ✅ | (To be added) |
| **ai_check** | ❌ | ✅ | ai_check_with_variables.yaml ⭐ |

### Variable Scope

```
Test Case Start
  ↓
pre_conditions (✅ Can use variables)
  ↓
steps (✅ Can save and use variables)
  ↓
post_conditions (✅ Can use variables)
  ↓
Test Case End (❌ Variables destroyed)
```

**Note**: Variables do NOT persist across different test cases.

---

## 🤖 AI Check Integration

### Overview

AI check prompts now support variable substitution, enabling dynamic AI-powered verification based on runtime data.

### Basic Usage

```yaml
steps:
  - name: "Get meeting ID"
    action:
      type: function
      value: get_current_meeting_id
      save_to: meeting_id
    expect_state: ""
  
  - name: "Verify meeting title"
    action:
      type: key
      value: default
    expect_state: ""
    ai_check:
      prompt: "Check if the meeting title contains meeting ID ${meeting_id}. The ID should be clearly visible. Output format: ✅Success or ❌Failed"
```

### Multi-Variable AI Verification

```yaml
steps:
  - name: "Get meeting info"
    action:
      type: function
      value: get_meeting_id
      save_to: meeting_id
  
  - name: "Get username"
    action:
      type: function
      value: get_current_username
      save_to: username
  
  - name: "Get participant count"
    action:
      type: function
      value: get_participant_count
      save_to: participant_count
  
  - name: "Verify meeting info panel"
    ai_check:
      prompt: "Verify the meeting information panel displays: Meeting ID: ${meeting_id}, Host: ${username}, Participants: ${participant_count}. All information should be clearly visible. ✅Success or ❌Failed"
```

### With Reference Images

```yaml
steps:
  - name: "Get selected background name"
    action:
      type: function
      value: get_selected_background_name
      save_to: bg_name
  
  - name: "Apply virtual background"
    ai_check:
      prompt: "Verify that the virtual background '${bg_name}' is correctly applied and matches the reference image."
      reference: executive_office.jpg
```

### Backward Compatibility

Old formats `{uuid}`, `{timestamp}`, `{last_sent_message}` are still supported:

```yaml
# ✅ New syntax (Recommended)
ai_check:
  prompt: "Verify message ${message_id} appears"

# ✅ Old syntax (Still supported)
ai_check:
  prompt: "Verify message {uuid} appears"

# ✅ Mixed usage (Both work)
ai_check:
  prompt: "Verify message ${custom_id} with UUID {uuid} appears"
```

---

## 📖 Complete Examples

### Example 1: Basic Function Return Value

```yaml
test_case:
  name: basic_return_value_example
  
  steps:
    - name: "Get meeting ID"
      action:
        type: function
        value: get_meeting_id
        save_to: meeting_id
        wait_time: 1
      expect_state: ""
    
    - name: "Join meeting with ID"
      action:
        type: function
        value: join_meeting
        parameters:
          meeting_id: "${meeting_id}"
        wait_time: 2
      expect_state: ""
```

### Example 2: Cross Action Type Usage

```yaml
test_case:
  name: cross_action_type_example
  
  steps:
    # Step 1: function returns username
    - name: "Get username"
      action:
        type: function
        value: get_current_user_name
        save_to: username
        wait_time: 1
      expect_state: ""
    
    # Step 2: function returns timestamp
    - name: "Get timestamp"
      action:
        type: function
        value: get_current_timestamp
        save_to: timestamp
        wait_time: 1
      expect_state: ""
    
    # Step 3: function returns meeting ID
    - name: "Generate meeting ID"
      action:
        type: function
        value: get_meeting_id
        save_to: meeting_id
        wait_time: 1
      expect_state: ""
    
    # Step 4: Use input to enter meeting ID (function → input)
    - name: "Input meeting ID"
      action:
        type: input
        value: "Meeting: ${meeting_id}"
        wait_time: 1
      expect_state: ""
    
    # Step 5: Mix multiple variables
    - name: "Print summary"
      action:
        type: function
        value: print_message
        parameters:
          message: "User: ${username}, Meeting: ${meeting_id}, Time: ${timestamp}"
        wait_time: 1
      expect_state: ""
```

### Example 3: AI Check with Variables

```yaml
test_case:
  name: ai_check_with_variables_example
  
  steps:
    # Scenario 1: Basic AI check variable usage
    - name: "Get meeting ID"
      action:
        type: function
        value: get_current_meeting_id
        save_to: meeting_id
      expect_state: ""
    
    - name: "Verify meeting title"
      action:
        type: key
        value: default
      expect_state: ""
      ai_check:
        prompt: "Check if the meeting title contains meeting ID ${meeting_id}. ✅Success or ❌Failed"
    
    # Scenario 2: Virtual background verification
    - name: "Get virtual background name"
      action:
        type: function
        value: get_selected_background_name
        save_to: bg_name
      expect_state: ""
    
    - name: "Apply virtual background"
      action:
        type: key
        value: default
      expect_state: ""
      ai_check:
        prompt: "Verify that the virtual background '${bg_name}' is correctly applied. The background should match the reference image."
        reference: executive_office.jpg
    
    # Scenario 3: Multiple variables in AI check
    - name: "Get participant count"
      action:
        type: function
        value: get_participant_count
        save_to: participant_count
      expect_state: ""
    
    - name: "Verify meeting status panel"
      action:
        type: key
        value: default
      expect_state: ""
      ai_check:
        prompt: "Verify the meeting status panel shows: Participants: ${participant_count}, Meeting ID: ${meeting_id}. All information should be clearly visible. ✅Success or ❌Failed"
```

---

## 🔧 Technical Implementation

### 1. ExecutionContext Variable Storage

All variables are stored in `ExecutionContext`'s `variables` dictionary:

```python
@dataclass
class ExecutionContext:
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Save variable"""
        self.variables[name] = value
        LOGGER_INFO(f"Variable saved: {name} = {value}", "CYAN")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get variable"""
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """Check if variable exists"""
        return name in self.variables
```

### 2. Unified Variable Resolution

Centralized `resolve_variables()` method in ExecutionContext:

```python
def resolve_variables(self, value: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
    """Unified variable resolution for all types"""
    if isinstance(value, str):
        return self._resolve_string(value)
    elif isinstance(value, dict):
        return {k: self.resolve_variables(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [self.resolve_variables(item) for item in value]
    else:
        return value

def _resolve_string(self, value: str) -> str:
    """Resolve variables in string using regex"""
    pattern = r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)'
    
    def replace_variable(match):
        var_name = match.group(1) or match.group(2)
        if var_name in self.variables:
            return str(self.variables[var_name])
        else:
            LOGGER_WARNING(f"Variable '{var_name}' not found", "YELLOW")
            return match.group(0)
    
    return re.sub(pattern, replace_variable, value)
```

### 3. FunctionActionStrategy - Save Return Values

```python
def execute(self, ctrl_action, execution_context, dependencies):
    # Execute function
    result = self._execute_dynamic_function(...)
    
    # Save return value if save_to specified
    save_to = ctrl_action.get("save_to")
    if save_to and execution_context:
        execution_context.set_variable(save_to, result)
        LOGGER_INFO(f"Saved function return value to '{save_to}'", "GREEN")
    
    return result
```

### 4. InputActionStrategy - Resolve Variables

```python
def execute(self, ctrl_action, execution_context, dependencies):
    value = ctrl_action.get("value")
    
    # Resolve variables
    if execution_context and hasattr(execution_context, 'resolve_variables'):
        original_value = value
        value = execution_context.resolve_variables(value)
        if value != original_value:
            LOGGER_INFO(f"Resolved variable: '{original_value}' -> '{value}'", "CYAN")
    
    # Execute input action with resolved value
    # ...
```

### 5. KeyActionStrategy - Resolve Variables

```python
def execute(self, ctrl_action, execution_context, dependencies):
    value = ctrl_action.get("value")
    
    # Resolve variables
    if execution_context and hasattr(execution_context, 'resolve_variables'):
        value = execution_context.resolve_variables(value)
    
    # Execute key action with resolved value
    # ...
```

### 6. AI Check Integration

In `control_verification_processor.py`:

```python
def perform_ai_check(self, ctrl, image_path, navigate_report_path, execution_context):
    ctrl_ai_check_prompt = ctrl.get("ai_check", {}).get("prompt")
    
    # Unified variable resolution
    if ctrl_ai_check_prompt and execution_context:
        if hasattr(execution_context, 'resolve_variables'):
            ctrl_ai_check_prompt = execution_context.resolve_variables(ctrl_ai_check_prompt)
            LOGGER_INFO(f"[AI check] Applied unified variable resolution", "CYAN")
        
        # Backward compatibility - legacy {uuid}, {timestamp}, {last_sent_message}
        # ... legacy format handling ...
    
    # Use resolved prompt for AI verification
    # ...
```

### Variable Resolution Flow

```
┌─────────────────────────────────────────────────────────┐
│                   Variable Resolution Flow               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. Action receives ctrl_action with variable reference  │
│     (e.g., value: "${meeting_id}")                       │
│                          ↓                                │
│  2. Strategy calls execution_context.resolve_variables() │
│                          ↓                                │
│  3. ExecutionContext._resolve_string() performs regex    │
│     - Pattern: \$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)  │
│     - Matches ${var} and $var                            │
│                          ↓                                │
│  4. Look up variable in variables dictionary             │
│     - Found: Replace with value                          │
│     - Not found: Log warning, keep original              │
│                          ↓                                │
│  5. Return resolved value to action strategy             │
│                          ↓                                │
│  6. Action executes with resolved value                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Best Practices

### Recommended Practices

#### 1. Clear Variable Names

```yaml
# ✅ Good - Descriptive names
save_to: username
save_to: meeting_id
save_to: timestamp
save_to: participant_count

# ❌ Avoid - Vague names
save_to: data
save_to: x
save_to: temp
save_to: val
```

#### 2. Use ${} Syntax

```yaml
# ✅ Recommended - Clear and explicit
value: "${username}"
prompt: "Verify ${meeting_id} is displayed"

# ⚠️ Acceptable - But less clear
value: "$username"
prompt: "Verify $meeting_id is displayed"
```

#### 3. String Embedding

```yaml
# ✅ Good - Multiple variables in context
value: "User ${username} joined meeting ${meeting_id} at ${timestamp}"
prompt: "Verify panel shows: ID: ${meeting_id}, Host: ${username}, Count: ${participant_count}"

# ❌ Avoid - Confusing concatenation
value: "$username${meeting_id}"  # Unclear separation
```

#### 4. AI Check Prompt Design

```yaml
# ✅ Good - Clear verification criteria
ai_check:
  prompt: "Verify the meeting title displays meeting ID ${meeting_id}, format should be 'Meeting: XXX-XXX'. ✅Success or ❌Failed"

# ❌ Avoid - Too vague
ai_check:
  prompt: "Check ${meeting_id}"  # Not clear what to verify
```

#### 5. Variable Existence Checks

```yaml
# ✅ Good - Ensure variable exists before using
steps:
  - name: "Get data"
    action:
      type: function
      value: get_data
      save_to: data  # Save first
  
  - name: "Use data"
    action:
      type: input
      value: "${data}"  # Use after saving

# ❌ Avoid - Using undefined variables
steps:
  - name: "Use undefined data"
    action:
      type: input
      value: "${undefined_data}"  # Variable not defined yet
```

### What to Avoid

```yaml
# ❌ Vague variable names
save_to: x
save_to: temp
save_to: data

# ❌ Unclear variable references
value: "$user$id"  # Ambiguous

# ❌ Missing variable context in AI prompts
ai_check:
  prompt: "Check ${id}"  # Too vague

# ❌ Overwriting important variables
- name: "Get user"
  action:
    save_to: result  # result = "Alice"

- name: "Get meeting"
  action:
    save_to: result  # result = "123" (overwrites "Alice")
```

---

## 🔍 FAQ

### Q1: Do variables persist across test cases?
**A**: No. Each test case has its own independent variable space. Variables are destroyed when the test case ends.

### Q2: What happens if I reference a non-existent variable?
**A**: The system logs a warning message, keeps the original reference unchanged (e.g., `${undefined_var}`), and continues execution. The test does not fail.

### Q3: Can I use multiple variables in one string?
**A**: Yes! You can embed multiple variables in a single string:
```yaml
value: "User: ${username}, Meeting: ${meeting_id}, Time: ${timestamp}"
```

### Q4: Do all action types support variables?
**A**: Yes! Any action type whose strategy class calls `execution_context.resolve_variables()` supports variables. Currently supported:
- ✅ function (parameters)
- ✅ input (value)
- ✅ key (value)
- ✅ ai_check (prompt)

### Q5: Can I save variables in input or key actions?
**A**: No. Only function actions can save return values using `save_to`. However, input and key actions can reference variables.

### Q6: What's the difference between ${var} and $var?
**A**: Both work the same way. `${var}` is recommended as it's more explicit and prevents ambiguity, especially when embedding variables in strings.

### Q7: Are the old {uuid}, {timestamp} formats still supported?
**A**: Yes! The system maintains backward compatibility with legacy formats. Both new (`${var}`) and old (`{uuid}`) formats work in AI check prompts.

### Q8: Can variables be used in pre_conditions and post_conditions?
**A**: Yes! Variables can be used throughout the entire test case lifecycle:
- pre_conditions ✅
- steps ✅
- post_conditions ✅

### Q9: How do I debug variable issues?
**A**: Check the execution logs. Variable operations are logged with CYAN color:
```
[INFO] Variable saved: meeting_id = 123-456
[INFO] Resolved variable: '${meeting_id}' -> '123-456'
[WARNING] Variable 'undefined_var' not found
```

### Q10: Can I use variables in reference image paths?
**A**: Currently, the reference field in ai_check primarily supports static file names. Dynamic reference paths are possible but not fully tested:
```yaml
# Supported (static)
ai_check:
  reference: executive_office.jpg

# Experimental (dynamic)
ai_check:
  reference: "${bg_name}.jpg"  # May work but not guaranteed
```

---

## 📁 Related Files

### Core Implementation

| File | Description |
|------|-------------|
| `src/core/windows/data_models/execution_context.py` | Variable storage and resolution |
| `src/core/windows/strategies/function_action_strategy.py` | Function return value capture |
| `src/core/windows/strategies/input_action_strategy.py` | Input variable resolution |
| `src/core/windows/strategies/key_action_strategy.py` | Key variable resolution |
| `src/core/windows/processors/control_verification_processor.py` | AI check variable resolution |

### Example Files

| File | Description |
|------|-------------|
| `src/test_space/test_cases/examples/function_return_value_example.yaml` | Basic function return values |
| `src/test_space/test_cases/examples/cross_action_type_variables.yaml` | Cross action type usage |
| `src/test_space/test_cases/examples/ai_check_with_variables.yaml` | AI check with variables |

### Documentation

| File | Description |
|------|-------------|
| `docs/FUNCTION_RETURN_VALUE_GUIDE.md` | Comprehensive guide (bilingual) |
| `docs/CROSS_ACTION_TYPE_VARIABLES.md` | Cross action type documentation |
| `docs/AI_CHECK_VARIABLES.md` | AI check variable implementation |
| `docs/AI_CHECK_VARIABLES_QUICKSTART.md` | Quick start guide |
| `docs/FUNCTION_RETURN_VALUE_IMPLEMENTATION.md` | Technical implementation details |
| `src/test_space/docs/AICHECK_README.md` | Example file documentation |

### How to Run Examples

```bash
# Basic function return value example
uv run python src/run_test_case_job.py --test_case "examples/function_return_value_example"

# Cross action type variables example
uv run python src/run_test_case_job.py --test_case "examples/cross_action_type_variables"

# AI check with variables example
uv run python src/run_test_case_job.py --test_case "examples/ai_check_with_variables"
```

---

## 🎓 Learning Path

### For Beginners

1. **Start with basics**: Read this Quick Start section
2. **Run basic example**: Execute `function_return_value_example.yaml`
3. **Understand syntax**: Learn `${variable}` and `$variable` formats
4. **Practice**: Create a simple test case with one variable

### For Intermediate Users

1. **Cross action type**: Study `cross_action_type_variables.yaml`
2. **Multiple variables**: Practice using multiple variables in one test
3. **String embedding**: Learn to embed variables in strings
4. **Complex workflows**: Chain multiple functions together

### For Advanced Users

1. **AI check integration**: Study `ai_check_with_variables.yaml`
2. **Dynamic verification**: Implement AI checks with runtime data
3. **Complex scenarios**: Build complete test workflows
4. **Optimization**: Follow best practices to optimize variable usage

---

## 🎉 Summary

### Key Takeaways

✅ **What You Can Do:**
- Save function return values to variables
- Use variables across all action types (function, input, key, ai_check)
- Reference multiple variables in a single string
- Create dynamic AI verification with runtime data
- Build complex test workflows with variable chaining

✅ **Two Variable Syntaxes:**
- `${variable_name}` - Recommended, clear and explicit
- `$variable_name` - Simplified, also supported

✅ **Supported Everywhere:**
- Function parameters
- Input values
- Key values
- AI check prompts
- Pre-conditions and post-conditions

✅ **Backward Compatible:**
- Old formats (`{uuid}`, `{timestamp}`) still work
- No breaking changes to existing test cases

✅ **Production Ready:**
- Comprehensive error handling
- Detailed logging
- Complete documentation
- Multiple working examples

---

## 📞 Support

For questions or issues:
- **Team**: Test Automation Team
- **Repository**: [webex-regress-shield](https://sqbu-github.cisco.com/binbiwan/webex-regress-shield)
- **Test Space**: [wrs_test_space](https://sqbu-github.cisco.com/binbiwan/wrs_test_space)

---

## 📝 Change Log

### Version 2.1 (2026-01-30)

**New Features:**
- ✅ AI check prompt variable support
- ✅ Cross action type variable usage (input, key)
- ✅ Unified variable resolution in ExecutionContext
- ✅ Complete example files and documentation

**Technical Improvements:**
- 📝 Comprehensive documentation
- 🔍 Enhanced logging for variable operations
- 🎯 Support for multiple variables in strings
- ⚡ Backward compatibility with legacy formats

### Version 2.0

**Initial Features:**
- ✅ Function return value capture with `save_to`
- ✅ Variable reference in function parameters
- ✅ Basic variable resolution system

---

**Happy Testing with Variables! 🚀**

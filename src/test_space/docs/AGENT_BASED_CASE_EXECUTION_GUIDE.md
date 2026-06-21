# Remote Agent Case Execution Guide

Execute test cases and test suites on remote agent nodes with parameters.

---

## Use in Test Case YAML
### Example: Call Remote Test Cases via API

```yaml
test_case:
  name: my_test_case
  steps:
    - name: "Stop screen sharing on agent"
      action:
        type: api
        value: "run_agent_api"
        agent_node: "meeting_agent_01"
        parameters:
          test_case_name: "meetings/share/stop_screen_sharing"
          platform: "windows"
```

---

## Use in Test Suite YAML

### Example: Mix Local and Agent Execution

```yaml
test_suite:
  name: my_test_suite
  platform: windows
  language: [en]
  test_cases:
    # Local execution
    - navigations/basic/uninstall_app
    
    # Agent execution with parameters
    - navigations/basic/install_app:
        agent_node: "meeting_agent_01"
        parameters:
          installOptions/version: "eft"
          language: "en_US"
    
    # Agent execution without parameters
    - navigations/basic/agree:
        agent_node: "meeting_agent_01"
```

---

## Parameters

### Required
- **`agent_node`**: Agent identifier (e.g., "meeting_agent_01")

### Optional Parameters
All parameters under `parameters:` are passed to the agent. Only use parameters defined in `settingsInitializer.py`:

#### 1. Application Installation (installOptions)
```yaml
- **`installOptions/version`**: Webex version - Default: "latest"; Options: "latest", "eft", "45.8.0.12345", etc.
- **`installOptions/source`**: Build source - Default: "shanghai"; Options: "shanghai", "galway", "sym"
- **`installOptions/qtversion`**: Qt version - Default: "6"; Options: "5", "6", "6.8"
- **`installOptions/arch`**: Architecture - Default: "x64"; Options: "x64", "arm64"
- **`installOptions/cdntoken`**: CDN toke
- **`installOptions/http2`**: Use http2 builds - Default: false
- **`installOptions/notResetDB`**: Do not reset database - Default: false
```

#### 2. Feature Toggles
```yaml
- **`openai`**: Enable OpenAI analysis - Default: false
- **`jira`**: Enable JIRA reporting - Default: false
- **`recording`**: Enable video recording - Default: false
- **`cleanupAllVersions`**: Cleanup all versions - Default: false 
```

#### 3. Test Configuration
```yaml
- **`account`**: Account name (refer to account.json)
- **`botRoomId`**: Bot room ID for messaging
- **`language`**: Language code - Default: "en_US"; Options: "en_US", "zh_CN", "ja_JP", "ko_KR", "de_DE", "es_ES", "fr_FR", "it_IT", "pt_BR"
- **`platform`**: Platform - Default: auto-detect; Options: "windows", "mac"
- **`fileNBugs`**: Number of bugs to report - Default: 5
```

### Parameter Format Options

**Option 1: Slash Format** (recommended for single nested parameter)
```yaml
parameters:
  installOptions/version: "eft"
  language: "en_US"
```

**Option 2: Nested Format** (recommended for multiple nested parameters)
```yaml
parameters:
  installOptions:
    version: "eft"
    qtversion: "6"
    source: "shanghai"
  language: "en_US"
```

Both formats are supported. Use slash format for simplicity, nested format for clarity when setting multiple related parameters.

---

## Agent Configuration

Agents are defined in `src/test_space/test_functions/agent_nodes.json`:

```json
{
  "meeting_agent_01": {
    "base_url": "http://10.224.118.133:8001",
    "description": "Meeting agent for video/audio operations"
  }
}
```

---
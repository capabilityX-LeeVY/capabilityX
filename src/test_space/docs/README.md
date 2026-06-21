# Test Case Creation Guide

This guide provides step-by-step instructions for creating test cases for accessibility testing in the Webex Regress Shield framework.

---

## Table of Contents
1. [Prepare and Create Dataset for Your App or Site](#1-prepare-and-create-dataset-for-your-app-or-site)
2. [Review and Validate Dataset](#2-review-and-validate-dataset)
3. [Create Test Cases](#3-create-test-cases)
4. [Check Reports](#4-check-reports)

---

## 1. Prepare and Create Dataset for Your App or Site

### 1.1 Edit the Navigate Template

Edit the file: `src\test_space\test_cases\accessibility\sequence\navigate.yaml`

This file is used to collect all controls from the current page or window by navigating through them.

#### Example 1: Collect Controls from Main Page

If "navigate" is the **first step**, it represents opening the site and then traversing and recording all controls on the main page:

```yaml
- name: "navigate"
  action:
    type: key
    value: tab
  expect_state: ""
```

**Explanation:** The system will press TAB key repeatedly to traverse all focusable controls on the main page and record them.

#### Example 2: Navigate After an Action

If "navigate" is the **second step**, it means first locate the control from the previous step, perform the action, and then traverse all controls on the resulting page:

```yaml
- name: "Sign in for webex web page"
  action:
    type: key
    value: enter
  expect_state: ""

- name: "navigate"
  action:
    type: key
    value: tab
  expect_state: ""
```

**Explanation:** 
1. First step: Find and activate the "Sign in for webex web page" button by pressing ENTER
2. Second step: After the page loads, traverse and record all controls on the new page

#### Example 3: Handle Blocked Navigation

If navigation stops at a certain control (e.g., a dialog or popup), you need to perform an appropriate action on that control before continuing navigation:

```yaml
- name: "Upcoming"
  action:
    type: key
    value: tab
  expect_state: ""

- name: "navigate"
  action:
    type: key
    value: tab
  expect_state: ""
```

**Explanation:** Navigate to "Upcoming" control first, then continue with the general navigation to capture remaining controls.

### 1.2 Run the Navigation Test

Execute the following command to traverse and record all controls:

```bash
uv run python src/run_test_case_job.py --test_suite "navigate"
```

#### Results Location

**Collected controls will be saved to:**
- **Specific metadata**: `src\test_space\datasets\control_specific_metadata.json`
  - Contains controls collected from the current navigation session
  
- **Final dataset**: `src\test_space\datasets\control_datasets.json`
  - The merged dataset used by the framework for control identification
  - Combines base metadata, specific metadata, and custom metadata

---

## 2. Review and Validate Dataset

### 2.1 Verify Control Recording

After running the navigation test, perform the following checks:

1. **Review `control_specific_metadata.json`**
   - Check if all expected controls are recorded
   - Verify control names and IDs are correct
   - Example structure:
     ```json
     {
         "name": "Sign In",
         "metadata": {
             "web": {
                 "control_name": "Sign In",
                 "control_id": "IDButton2"
             }
         }
     }
     ```

2. **Verify Merge to `control_datasets.json`**
   - Confirm that controls from `control_specific_metadata.json` have been merged
   - Check that metadata is properly structured with platform-specific information

### 2.2 Ensure Control Name Uniqueness and Readability

**Important:** Control names must be unique and descriptive across your entire application suite.

#### Problem Example:
Multiple applications may have a "Sign In" button, which creates ambiguity:
```json
{"name": "Sign In"}  // Which app does this belong to?
```

#### Solution:
Modify control names in `control_datasets.json` to be more specific and descriptive:
```json
{"name": "Sign in for webex web page"}  // Clear and unique
{"name": "Sign in for admin portal"}     // Clear and unique
```

**Best Practices:**
- ✅ Use descriptive names that include context (e.g., page/app name)
- ✅ Ensure case-sensitive uniqueness
- ✅ Make names human-readable
- ❌ Avoid generic names like "Button", "OK", "Submit" without context

3. manual create control datasets

```bash
uv run python src/test_space/datasets/datasets_generator.py --mode reset --platform 'windows' --project 'webex_app'

python src/test_space/datasets/datasets_generator.py \
  --mode reset \
  --platform web \
  --project control_hub \
  --skip-main-db \
  --skip-custom-metadata
```

---

## 3. Create Test Cases

### 3.1 Choose the Appropriate Directory

Create test cases in the appropriate directory based on functionality:

**Directory Structure Examples:**
```
src/test_space/test_cases/
├── web/
│   ├── j2ee/           # Java-based web applications
│   └── react/          # React-based applications
├── windows/
│   └── meetings/       # Windows desktop app features
└── accessibility/
    └── sequence/       # Accessibility navigation tests
```

### 3.2 Test Case Template

Use the following template and customize for your workflow:

**Example:** `src\test_space\test_cases\web\j2ee\sign_in.yaml`

```yaml
test_case:
  name: sign_in
  account: allianz8                           # Account to use for testing
  site_url: "https://testprod.webex.com"     # Target site URL
  description: Verify that a user can successfully sign in with valid credentials
  expect_result: The user is signed in successfully and focus is on the main page
  
  steps:
    # Step 1: Activate sign in button
    - name: "Sign in for webex web page"
      action:
        type: key
        value: enter
      expect_state: ""

    # Step 2: Input email address
    - name: "Email address for webex web page"
      action:
        type: input
        value: ${email}                       # Variable from account config
      expect_state: ""

    # Step 3: Submit email
    - name: "Sign in with email address for webex web page"
      action:
        type: key
        value: enter
      expect_state: ""

    # Step 4: Input password
    - name: "Password for webex web page"
      action:
        type: input
        value: ${password}                    # Variable from account config
      expect_state: ""

    # Step 5: Submit password and sign in
    - name: "Sign in with password for webex web page"
      action:
        type: key
        value: enter
      expect_state: ""

  check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Untranslated&Truncated, Performance]
```

### 3.3 Configuration Parameters

#### Required Fields:
- **name**: Unique identifier for the test case
- **account**: Account name from `src\config\account.json`
- **site_url**: Target URL for web applications (optional for desktop apps)
- **description**: What the test case validates
- **expect_result**: Expected outcome after test execution
- **steps**: Array of test steps (see below)

#### Step Configuration:

Each step must have:
- **name**: Must match exactly (case-sensitive) with control names in `control_datasets.json`
- **action.type**: Type of action to perform
- **action.value**: The specific action value
- **expect_state**: Expected control to be focused after action (optional, use "" if unknown)

#### Action Types:

| Type | Description | Value Examples | Reference |
|------|-------------|----------------|-----------|
| `key` | Keyboard key press | `enter`, `tab`, `escape`, `space` | `src\config\key_map.py` |
| `input` | Text input | `${email}`, `${password}`, `"literal text"` | Use `${}` for variables |
| `shortcut` | Keyboard shortcut | `ctrl+s`, `alt+f4`, `ctrl+shift+t` | Combination keys |
| `function` | Custom function | `run_datasets_generator`, `send_message_to_webex` | `src\test_space\test_functions\` |
| `api` | API call | API endpoint configurations | API handlers |

**View all available keys:** Check `src\config\key_map.py` for complete key mapping

#### Using Account Variables:

For credentials and sensitive data, use variables from the account configuration:

```yaml
- name: "Email address"
  action:
    type: input
    value: ${email}        # Reads from account.json

- name: "Password"
  action:
    type: input
    value: ${password}     # Reads from account.json
```

**Account Configuration:** `src\config\account.json`

### 3.4 Checkpoint Types

Configure which aspects to validate in your test:

```yaml
check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Untranslated&Truncated, Performance]
```

**Available Checkpoints:**
- **KB**: Keyboard navigation accessibility
- **SR**: Screen reader compatibility
- **FR**: Focus ring visibility
- **Untranslated&Truncated**: Text translation and truncation issues
- **Performance**: UI response time and performance metrics
- **Stress**: System performance under load (requires additional configuration)

### 3.5 Important Notes

#### ⚠️ Control Name Consistency
- Step names **MUST match exactly** (case-sensitive) with control names in `control_datasets.json`
- This ensures proper accessibility sequence validation
- Example:
  ```yaml
  # ✅ Correct (matches dataset)
  - name: "Sign in for webex web page"
  
  # ❌ Wrong (case mismatch)
  - name: "sign in for webex web page"
  
  # ❌ Wrong (different text)
  - name: "Sign In Button"
  ```

#### Optional Configuration
```yaml
test_case:
  retry_enabled: false          # Disable retry on failure for faster validation
  record_traversal: true        # Record all controls during traversal
  execution_duration: 1         # Test duration in minutes (for stress tests)
  execution_count: 5            # Number of times to repeat test
```

### 3.6 Interactive Case Design Flow

The following animation demonstrates how test cases interact with agent nodes and API configurations in the WebexRegressShield system:

![Interactive Case Design Flow](test_functions/interactive_case_design_flow.gif)

This flow illustrates the complete interaction path:
- **VM List**: Agent node definitions and IP addresses
- **agent_nodes.json**: Agent connection configurations  
- **Test Case (YAML)**: Test case referencing agent node and API
- **API Config (JSON)**: API endpoint configuration with base_url
- **Registry (Python)**: Function registration mechanism
- **Routes (FastAPI)**: API endpoint implementation
- **Agent Server**: Final execution on the agent server

---

## 4. Check Reports

### 4.1 Execution

Run your test case or test suite:

```bash
# Run a specific test case
uv run python src/run_test_case_job.py --test_suite "your_test_case"

# Run in case mode
uv run python src/run_test_case_job.py --mode case --case "web/j2ee/sign_in"
```

### 4.2 Notifications

After execution completes, you will receive:
- **Webex Space Notification**: Summary of test results with links to detailed reports
- **Console Output**: Real-time execution logs

### 4.3 Report Locations

All test outputs are stored in the **`wrs-output`** directory at the same level as the project root:

```
wrs-output/
└── {MACHINE_NAME}_{MACHINE_ID}/
    └── {TIMESTAMP}/
        ├── log/                    # Execution logs
        │   └── wrs_YYYY-MM-DD.log
        ├── report/                 # Test reports
        │   ├── navigate/          # Navigation reports (HTML)
        │   ├── performance/       # Performance metrics (JSON)
        │   └── stress/            # Stress test results (if applicable)
        ├── db/                     # Control databases
        │   └── ControlINFO.db
        └── screenshots/            # Screenshots (if captured)
```

#### Report Types:

1. **Navigation Report** (`report/navigate/`)
   - HTML visualization of control navigation flow
   - Accessibility validation results
   - Focus order and keyboard navigation paths

2. **Performance Report** (`report/performance/`)
   - JSON metrics for UI response times
   - Control interaction latency
   - Performance benchmarks

3. **Logs** (`log/`)
   - Detailed execution logs
   - Debug information
   - Error traces

4. **Database** (`db/`)
   - Collected control information
   - Metadata for analysis

### 4.4 Viewing Reports

**Local Viewing:**
1. Navigate to the output directory
2. Open HTML reports in a web browser
3. Review JSON files for detailed metrics

**Remote Viewing:**
- Click the links in the Webex Space notification
- Access centralized report dashboard (if configured)

---

## Quick Start Example

Here's a complete workflow to create your first test case:

### Step 1: Collect Controls
```bash
# Edit navigate.yaml to define your navigation path
# Then run:
uv run python src/run_test_case_job.py --test_suite "navigate"
```

### Step 2: Review Dataset
```bash
# Check the collected controls
code src/test_space/datasets/control_specific_metadata.json

# Verify merge to final dataset
code src/test_space/datasets/control_datasets.json
```

### Step 3: Create Test Case
```bash
# Create your test case file
code src/test_space/test_cases/web/j2ee/my_test.yaml

# Add configuration and steps (use template above)
```

### Step 4: Run Test
```bash
uv run python src/run_test_case_job.py --test_suite "my_test"
```

### Step 5: Check Results
```bash
# Results will be in wrs-output directory
# Notification sent to Webex Space
```

---

## Troubleshooting

### Common Issues:

1. **Control Not Found**
   - Verify control name in `control_datasets.json` matches exactly (case-sensitive)
   - Re-run navigation test to collect missing controls
   - Check platform-specific metadata (windows/web/mac)

2. **Navigation Stops Unexpectedly**
   - Add intermediate steps to handle dialogs/popups
   - Use escape key or close actions before continuing navigation
   - Check logs for specific error messages

3. **Account Variables Not Working**
   - Verify account exists in `src\config\account.json`
   - Check variable syntax: `${variable_name}`
   - Ensure account is specified in test case YAML

4. **Site URL Not Loading**
   - Confirm `site_url` is specified in test case for web apps
   - Check network connectivity
   - Verify URL format includes protocol (https://)

---

## Best Practices

1. ✅ **Always run navigation test first** to collect controls before creating test cases
2. ✅ **Use descriptive control names** that include context and are unique
3. ✅ **Test incrementally** - create simple test cases and gradually add complexity
4. ✅ **Review datasets regularly** to ensure data quality and consistency
5. ✅ **Use variables for credentials** - never hardcode passwords
6. ✅ **Add meaningful descriptions** to test cases for documentation
7. ✅ **Organize test cases logically** in appropriate directories
8. ✅ **Check reports after each run** to catch issues early

---

## Additional Resources

- **Key Mappings**: `src\config\key_map.py`
- **Account Configuration**: `src\config\account.json`
- **Function Registry**: `src\test_space\test_functions\function.json`
- **Test Case Examples**: `src\test_space\test_cases\sample\`
- **Dataset Generation Prompt**: `src\test_space\datasets\TEST_CASE_GENERATION_PROMPT.md`

---

## Support

For questions or issues:
1. Check the logs in `wrs-output/{machine}/{timestamp}/log/`
2. Review existing test cases in `src\test_space\test_cases\sample\`
3. Contact the RegressShield team in Webex Space

---

**Version:** 1.0  
**Last Updated:** October 30, 2025

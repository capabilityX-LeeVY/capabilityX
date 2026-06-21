# Test Case Architecture Design

## Overview

The WebexRegressShield framework adopts a layered architecture design that supports three test execution modes: **Test Case**, **Test Batch**, and **Test Suite**. This design ensures both atomicity and reusability of test cases while supporting complex scenario combinations and validations.

**Version:** 2.0  
**Last Updated:** January 7, 2026

---

## Table of Contents

1. [Architecture Diagram](#architecture-diagram)
2. [File Organization](#file-organization)
3. [Test Execution Modes](#test-execution-modes)
   - [Test Case Mode](#1-test-case-mode)
   - [Test Batch Mode](#2-test-batch-mode)
   - [Test Suite Mode](#3-test-suite-mode)
4. [Test Case Directory Structure](#test-case-directory-structure)
   - [Directory 1: navigations/](#directory-1-navigations---atomic-operations-layer)
   - [Directory 2: acc_regression/](#directory-2-acc_regression---complete-workflow-layer)
   - [Directory 3: release_graduation/](#directory-3-release_graduation---release-validation-layer)
   - [Directory 4: feature_test/](#directory-4-feature_test---feature-validation-layer)
   - [Shared Test Case Convention](#shared-test-case-convention-navigationsbasic)
5. [Test Batch Structure](#test-batch-structure)
6. [Test Suite Structure](#test-suite-structure)
7. [Comparison: Batch vs Suite](#comparison-batch-vs-suite)
8. [Design Principles](#design-principles)
9. [Best Practices](#best-practices)
10. [Execution Commands](#execution-commands)
11. [Migration Guide](#migration-guide)
12. [Version History](#version-history)
13. [Related Documentation](#related-documentation)
14. [Support](#support)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Execution Modes                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │   Test Case    │  │   Test Batch   │  │  Test Suite    │     │
│  │   (Atomic Ops) │  │  (Batch Exec)  │  │  (Combined)    │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            Test Case Directory Structure             │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │  1. navigations/        (Atomic Operations)          │       │
│  │  2. acc_regression/     (Complete Workflow)          │       │
│  │  3. release_graduation/ (Release Validation)         │       │
│  │  4. feature_test/       (Feature Validation)         │       │
│  │  5. stress/             (Stress Testing)             │       │
│  │  6. performance/        (Performance Testing)        │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## File Organization

### Complete Directory Structure
```text
src/test_space/
├── test_cases/                          # Test Case directory
│   ├── navigations/                     # Atomic operations layer
│   │   ├── preconditions/               # Pre-conditions
│   │   │   ├── app_entry/
│   │   │   │   └── sign_in_to_app.yaml
│   │   │   └── app_core/
│   │   │       └── start_a_webex_meeting.yaml
│   │   ├── functional/                  # Functional operations
│   │   │   └── in_meeting/
│   │   │       ├── audio/
│   │   │       ├── video/
│   │   │       │   └── change_virtual_background.yaml
│   │   │       └── share/
│   │   ├── postconditions/              # Post-conditions
│   │   │   └── end_meeting.yaml
│   │   └── basic/                       # Shared test cases
│   │       └── guest_join_PMR.yaml
│   │
│   ├── acc_regression/                  # Complete workflow layer
│   │   └── meetings/
│   │       └── video/
│   │           └── vbg_static.yaml
│   │
│   ├── release_graduation/              # Release validation layer
│   │   ├── smoke_test/
│   │   ├── critical_path/
│   │   └── regression/
│   │
│   └── feature_test/                    # Feature validation layer
│       ├── audio_team/
│       ├── video_team/
│       ├── share_team/
│       └── chat_team/
│
├── test_batches/                        # Test Batch directory
│   ├── acc_regression/                  # Accessibility regression batches
│   │   └── video_vbg_batch.yaml
│   ├── release_graduation/              # Release validation batches
│   │   └── smoke_batch.yaml
│   └── feature_test/                    # Feature validation batches
│       ├── audio_batch.yaml
│       └── video_batch.yaml
│
└── test_suites/                         # Test Suite directory
    ├── acc_regression/                  # Accessibility regression suites
    │   └── video_vbg_suite.yaml
    ├── release_graduation/              # Release validation suites
    │   └── smoke_suite.yaml
    ├── feature_test/                    # Feature validation suites
    │   ├── audio_suite.yaml
    │   └── video_suite.yaml
    └── promote_blue_channel.yaml        # Blue channel promotion suite
```

---

## Test Execution Modes

### 1. Test Case Mode

**Purpose:** Execute individual test cases, supporting both atomic operations and complete workflows

**Characteristics:**
- Can be a single atomic operation
- Can be a complete business workflow
- Supports pre-conditions and post-conditions
- Can be referenced and combined by other modes

**Execution Command:**
```bash
python src/run_test_case_job.py --test_case 'case_name'
```

---

### 2. Test Batch Mode

**Purpose:** Execute multiple test cases with complete workflows in batch

**Characteristics:**
- Each test case is an independent complete workflow
- Each execution includes complete preparation (uninstall, install, sign in)
- Suitable for regression testing and large-scale verification
- Supports parallel execution

**Execution Command:**
```bash
python src/run_test_case_job.py --test_batch 'batch_name'
```

**Use Cases:**
- Daily automated regression testing
- Complete verification before version release
- Repeated execution of same workflow to ensure stability

---

### 3. Test Suite Mode

**Purpose:** Combine multiple test cases in a single session to verify multiple features

**Characteristics:**
- Verify multiple features in one meeting/session
- Share the same test environment (no repeated installation and login)
- Optimize execution time
- Suitable for feature integration verification

**Execution Command:**
```bash
python src/run_test_case_job.py --test_suite 'suite_name'
```

**Use Cases:**
- Verify audio + video + share in one meeting
- Blue channel promotion verification
- Feature interaction testing


---

## Test Case Directory Structure

### Directory 1: `navigations/` - Atomic Operations Layer

**Responsibility:** Provide basic test case atomic operations for single functionality

**Design Principles:**
- Each test case is responsible for only one single function
- Highly reusable and can be referenced by other test cases
- Follow DRY (Don't Repeat Yourself) principle

**Directory Structure:**

```text
navigations/
├── preconditions/          # Pre-conditions (preparation work)
│   ├── app_entry/          # Application entry related
│   │   └── sign_in_to_app.yaml
│   └── app_core/           # Core application operations
│       └── start_a_webex_meeting.yaml
├── functional/             # Functional operations
│   └── in_meeting/         # In-meeting operations
│       └── video/
│           └── change_virtual_background.yaml
├── postconditions/         # Post-conditions (cleanup work)
│   └── end_meeting.yaml
└── basic/                  # Shared operations (can be used by multiple teams)
    └── guest_join_PMR.yaml
```

**Examples:**
- `src/test_space/test_cases/navigations/preconditions/app_entry/sign_in_to_app.yaml`
  - **Function:** Sign in to application
  - **Responsibility:** Only complete the sign-in operation
  
- `src/test_space/test_cases/navigations/preconditions/app_core/start_a_webex_meeting.yaml`
  - **Function:** Start a meeting
  - **Responsibility:** Only complete the start meeting operation
  
- `src/test_space/test_cases/navigations/functional/in_meeting/video/change_virtual_background.yaml`
  - **Function:** Change virtual background
  - **Responsibility:** Only complete the change virtual background operation

**Usage:**
```yaml
# Reference in other test cases
test_case:
  name: vbg_static
  pre_conditions:
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_a_webex_meeting
  steps:
    - navigations/functional/in_meeting/video/change_virtual_background
  post_conditions:
    - navigations/postconditions/end_meeting
```

---

### Directory 2: `acc_regression/` - Complete Workflow Layer

**Responsibility:** Each test case contains a complete workflow, composed of multiple cases from navigations

**Design Principles:**
- Complete end-to-end verification
- Can run independently
- Built by combining atomic operations from navigations
- Primarily used for accessibility regression testing

**Directory Structure:**
```
acc_regression/
└── meetings/
    └── video/
        └── vbg_static.yaml
```

**Example:**
`src/test_space/test_cases/acc_regression/meetings/video/vbg_static.yaml`

**Characteristics:**
- Contains complete test flow: Install → Sign In → Start Meeting → Change Background → End Meeting
- Can be referenced by test batch
- Verifies complete accessibility-related scenarios

**Workflow Example:**
```yaml
test_case:
  name: vbg_static
  description: Complete virtual background static image accessibility verification
  
  pre_conditions:
    - navigations/basic/install_app
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_a_webex_meeting
  
  steps:
    - name: "Verify virtual background accessibility"
      action:
        - navigations/functional/in_meeting/video/change_virtual_background
        - navigations/functional/in_meeting/video/select_static_background
  
  post_conditions:
    - navigations/postconditions/end_meeting
    - navigations/basic/uninstall_app
  
  check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Untranslated&Truncated]
```

---

### Directory 3: `release_graduation/` - Release Validation Layer

**Responsibility:** Test cases that the Graduation team needs to run for each release

**Design Principles:**
- **Single Responsibility Principle**
- Each test case focuses on one release verification scenario
- If needed by other teams, the test case should be placed in `navigations/basic/`

**Directory Structure:**
```
release_graduation/
├── smoke_test/
├── critical_path/
└── regression/
```

**Use Cases:**
- Critical path verification before release
- Smoke testing
- Release checklist verification

**Creation Guidelines:**
1. **Follow Single Responsibility:** Each test case validates only one release key point
2. **Complete Independence:** Can run independently without depending on specific environment
3. **Sharing Principle:** If test case needs to be used by other teams, must move to `navigations/basic/`

**Example:**
```yaml
# release_graduation/smoke_test/basic_meeting_flow.yaml
test_case:
  name: basic_meeting_flow
  description: Release validation - Basic meeting flow
  team: graduation
  
  steps:
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_a_webex_meeting
    - navigations/functional/in_meeting/audio/verify_audio
    - navigations/postconditions/end_meeting
```

---

### Directory 4: `feature_test/` - Feature Validation Layer

**Responsibility:** Test cases that various feature teams need to run

**Design Principles:**
- **Single Responsibility Principle**
- Each test case focuses on one feature verification
- If needed by other teams, the test case should be placed in `navigations/basic/`

**Directory Structure:**
```
feature_test/
├── audio_team/
├── video_team/
├── share_team/
└── chat_team/
```

**Use Cases:**
- New feature development verification
- Feature team's CI/CD
- Feature-specific testing

**Creation Guidelines:**
1. **Follow Single Responsibility:** Each test case validates only one feature
2. **Organize by Team:** Facilitate each team to manage their own test cases
3. **Sharing Principle:** If test case needs to be used by other teams, must move to `navigations/basic/`

**Example:**
```yaml
# feature_test/video_team/new_filter_effect.yaml
test_case:
  name: new_filter_effect
  description: Verify new video filter effect
  team: video_team
  
  pre_conditions:
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_a_webex_meeting
  
  steps:
    - name: "Apply new filter"
      action: apply_new_filter
    - name: "Verify filter effect"
      action: verify_filter_effect
  
  post_conditions:
    - navigations/postconditions/end_meeting
```

---

### Shared Test Case Convention: `navigations/basic/`

**Responsibility:** Store test cases that need to be shared and used by multiple teams

**Use Cases:**
- Test cases developed by feature teams need to be used by other teams
- Test cases from graduation team need to be referenced by feature teams
- Shared business process verification

**Example:**
`src/test_space/test_cases/navigations/basic/guest_join_PMR.yaml`

**Migration Rule:**
```
feature_test/video_team/guest_join_PMR.yaml  (Original location)
         ↓ (Needs to be used by other teams)
navigations/basic/guest_join_PMR.yaml        (Shared location)
```

---

## Test Batch Structure

### Directory Location: `test_batches/`

**Responsibility:** Execute test cases with complete workflows in batch

**Directory Structure:**
```text
test_batches/
├── acc_regression/          # Accessibility regression batches
│   └── video_vbg_batch.yaml
├── release_graduation/      # Release validation batches
│   └── smoke_batch.yaml
└── feature_test/            # Feature validation batches
    ├── audio_batch.yaml
    └── video_batch.yaml
```

**Characteristics:**
- Each test case is a complete workflow verification
- Each execution includes complete environment preparation and cleanup
- Supports multiple repeated executions of the same workflow

**Batch Execution Example:**
`src/test_space/test_batches/acc_regression/video_vbg_batch.yaml`

```yaml
test_batch:
  name: video_vbg_batch
  description: Batch execute virtual background tests, each time with complete workflow verification
  
  test_cases:
    - acc_regression/meetings/video/vbg_static
    - acc_regression/meetings/video/vbg_blur
    - acc_regression/meetings/video/vbg_dynamic
  
  execution_mode: sequential  # or parallel
  repeat_count: 3             # Execute each test case 3 times
```

**Execution Flow (using vbg_static as example, repeated 3 times):**
```
Iteration 1:
  1. Uninstall application
  2. Install application
  3. Sign in
  4. Start meeting
  5. Change virtual background to static image
  6. Verify
  7. End meeting

Iteration 2:
  1. Uninstall application
  2. Install application
  3. Sign in
  4. Start meeting
  5. Change virtual background to static image
  6. Verify
  7. End meeting

Iteration 3:
  1. Uninstall application
  2. Install application
  3. Sign in
  4. Start meeting
  5. Change virtual background to static image
  6. Verify
  7. End meeting
```

**Applicable Scenarios:**
- Daily automated regression testing
- Stability testing
- Large-scale feature verification

---

## Test Suite Structure

### Directory Location: `test_suites/`

**Responsibility:** Combine multiple test cases in a single session to verify multiple features

**Characteristics:**
- Share the same test environment (one installation, one sign-in, one meeting start)
- Verify multiple features in the same meeting
- Optimize execution time
- Suitable for feature integration verification

**Combined Verification Example:**
`src/test_space/test_suites/promote_blue_channel.yaml`

```yaml
test_suite:
  name: promote_blue_channel
  description: Verify audio, video, and share features in one meeting
  account: promote_account
  
  # Pre-conditions executed only once
  pre_conditions:
    - navigations/basic/install_app
    - navigations/preconditions/app_entry/sign_in_to_app
    - navigations/preconditions/app_core/start_a_webex_meeting
  
  # Verify sequentially in the same meeting
  test_cases:
    - name: check_audio
      steps:
        - navigations/functional/in_meeting/audio/unmute
        - navigations/functional/in_meeting/audio/verify_audio_working
        - navigations/functional/in_meeting/audio/mute
    
    - name: check_video
      steps:
        - navigations/functional/in_meeting/video/start_video
        - navigations/functional/in_meeting/video/change_virtual_background
        - navigations/functional/in_meeting/video/stop_video
    
    - name: check_share
      steps:
        - navigations/functional/in_meeting/share/start_screen_share
        - navigations/functional/in_meeting/share/verify_sharing
        - navigations/functional/in_meeting/share/stop_share
  
  # Post-conditions executed only once
  post_conditions:
    - navigations/postconditions/end_meeting
    - navigations/basic/uninstall_app
  
  check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Performance]
```

**Execution Flow:**
```
1. Uninstall application (once)
2. Install application (once)
3. Sign in (once)
4. Start meeting (once)
5. ├─ Verify Audio features
   ├─ Verify Video features
   └─ Verify Share features
6. End meeting (once)
7. Uninstall application (once)
```

**Applicable Scenarios:**
- Blue channel promotion verification
- Feature integration testing
- Demo demonstrations
- Quick smoke testing

---

## Comparison: Batch vs Suite

| Feature | Test Batch | Test Suite |
|---------|------------|------------|
| **Execution Mode** | Each test case executes independently and completely | Multiple test cases execute in same session |
| **Environment Preparation** | Complete preparation each time (install, sign in) | Prepare only once |
| **Execution Time** | Longer (repeated environment preparation) | Shorter (shared environment) |
| **Isolation** | High (independent environment each time) | Low (shared environment) |
| **Applicable Scenarios** | Regression, Stability testing | Feature integration, Quick verification |
| **Test Case Requirements** | Must be complete workflow | Can be atomic operations or combinations |

**Selection Recommendations:**
- **Use Test Batch:** Need to verify independent stability of each feature
- **Use Test Suite:** Need to quickly verify integration of multiple features

---

## Design Principles

### 1. Single Responsibility Principle

**Application Scenarios:**
- Atomic operations in `navigations/`
- Test cases in `release_graduation/`
- Test cases in `feature_test/`

**Rules:**
- Each test case is responsible for only one single function
- If a test case does multiple things, it should be split into multiple test cases

### 2. DRY Principle (Don't Repeat Yourself)

**Application Scenarios:**
- Avoid repetition through atomic operations in `navigations/`
- Avoid repetition through `pre_conditions` references
- Share test cases through `navigations/basic/`

**Rules:**
- Don't write the same test steps repeatedly
- Prioritize referencing existing atomic operations

### 3. Reusability

**Application Scenarios:**
- Design goal of `navigations/` layer
- Purpose of `basic/` directory

**Rules:**
- Consider reusability when designing test cases
- Place test cases needed by multiple teams in `basic/`

### 4. Isolation

**Application Scenarios:**
- Test Batch design
- Independent test case execution

**Rules:**
- Test cases should not depend on each other
- Complete environment preparation each time in Test Batch

### 5. Composability

**Application Scenarios:**
- Test Suite design
- `acc_regression/` built by combining `navigations/`

**Rules:**
- Build complex workflows by combining atomic operations
- Support flexible test case combinations

---

## Best Practices

### Creating Test Cases

1. **Determine test case type:**
   - Is it an atomic operation? → Place in `navigations/`
   - Is it a complete workflow? → Place in `acc_regression/`
   - Is it release validation? → Place in `release_graduation/`
   - Is it feature validation? → Place in `feature_test/`

2. **Follow naming conventions:**
   - Use lowercase and underscores: `guest_join_PMR.yaml`
   - Name should describe functionality: `change_virtual_background.yaml`
   - Avoid abbreviations, maintain readability

3. **Write clear descriptions:**
   ```yaml
   test_case:
     name: vbg_static
     description: Verify accessibility of static virtual background
     team: video_team
     owner: user@example.com
   ```

4. **Use pre/post conditions properly:**
   ```yaml
   pre_conditions:
     - navigations/preconditions/app_entry/sign_in_to_app
   post_conditions:
     - navigations/postconditions/end_meeting
   ```

### Creating Test Batch

1. **Select test cases with complete workflow:**
   ```yaml
   test_cases:
     - acc_regression/meetings/video/vbg_static
     - acc_regression/meetings/video/vbg_blur
   ```

2. **Set reasonable repeat_count:**
   - Stability testing: 3-5 times
   - Quick verification: 1 time

3. **Choose execution mode:**
   - `sequential`: Serial execution (default)
   - `parallel`: Parallel execution (requires sufficient resources)

### Creating Test Suite

1. **Select functionally related test cases:**
   - Features that can be verified in the same meeting
   - Features have correlation

2. **Optimize execution order:**
   - Verify basic features first (audio)
   - Then verify advanced features (share)

3. **Use check_point properly:**
   ```yaml
   check_point: [Keyboard Navigation, Screen Reader, Focus Ring, Performance]
   ```

---

## Related Documentation

- **Test Case Creation Guide**: [TEST_CASE_CREATION_GUIDE.md](TEST_CASE_CREATION_GUIDE.md)
- **Navigation Generation**: `datasets/core/README_GENERATE_TEST_CASES.md`
- **Test Case Structure**: `test_cases/README_TEST_CASE_STRUCTURE.md`
- **Database Management**: `management/tools/README_DB_MANAGER.md`

---

## Support

- **Test Automation Team**
- **Repository**: sqbu-github.cisco.com:binbiwan/wrs_test_space
- **Documentation**: src/test_space/

---

**END OF DOCUMENT**

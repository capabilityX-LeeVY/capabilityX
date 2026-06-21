# Vibe Coding — Examples by Prompt

## Which Prompt to Use?

| What you want to do | Prompt | Tier |
|---|---|---|
| Generate a YAML test case | `/add-test-case` | — |
| Generate an `acc_regression/meetings` **in-meeting** test case (video, audio, chat…) | `/add-test-case-in-meetings` | — |
| Generate a **join-meeting** test case (join meeting, guest join PMR) | `/add-test-case-join-meetings` | — |
| Generate a **schedule-meeting** test case | `/add-test-case-schedule-meetings` | — |
| Generate a YAML test suite | `/add-suite` | — |
| **Find and run an existing test case by name** | `/run-test-case` | — |
| **Find and run an existing test suite by name** | `/run-test-suite` | — |
| Add a new `action.type` (runtime UI action) | `/add-strategy` | Tier 2 / 3 |
| Add a new YAML keyword (load-time transform) | `/extend-workflow-parser` | Tier 1 |

> All prompts live in `.github/prompts/` — type `/` in Copilot Chat to see them.

---

## Part 1 — `/add-test-case`

Generate a YAML test case file from a natural language description.

---

## How to Run

### Method 1 — Slash command (recommended, no `#` needed)

Because the files use the `.prompt.md` extension, VS Code registers them as slash commands automatically.

In VS Code Copilot Chat input box, just type your request directly — VS Code will prompt you to pick the mode:

```
/add-test-case Create "Show in floating window" test case.
account: allianz8
file directory: acc_regression meeting video
pre_conditions: start meeting, open video settings
steps:
  1. enable/check "Show in floating window"
  2. click save button, AI check prompt: "Verify that the Show in floating window effect is visually applied to the video. Output format: ✅Success or ❌Failed", reference: show_in_floating_window.jpg
post_conditions: end meeting, sign out
```

> `/add-test-case` loads the prompt rules automatically — no need to reference the file with `#`.

### Method 2 — Use the prompt file as context via `#file:`

Alternatively, attach the file manually:

```
#file:.github/prompts/add-test-case.prompt.md

Create "Show in floating window" test case.
account: allianz8
file directory: acc_regression meeting video
pre_conditions: start meeting, open video settings
steps:
  1. enable/check "Show in floating window"
post_conditions: end meeting, sign out
```

### Which method to use?

| Situation | Method |
|---|---|
| Normal usage | Method 1 — type `/add-test-case` directly in chat |
| Slash command not showing up | Method 2 — `#file:.github/prompts/add-test-case.prompt.md` |

---

## Input Format

```
Create "<feature name>" test case.
account: <account_name>                      # optional, omit if using default
file directory: <category> <area>            # e.g. acc_regression meeting video
pre_conditions: <comma-separated steps>      # e.g. start meeting, open video settings
steps:
  1. <action> "<control name>"
  2. <action> "<control name>", AI check prompt: "<verification>. Output format: ✅Success or ❌Failed", reference: <image>.jpg
post_conditions: <teardown steps>            # e.g. end meeting, sign out
check_points: <optional list>                # defaults to Keyboard Navigation
```

**Field descriptions:**

| Field | Required | Description |
|---|---|---|
| `"<feature name>"` | ✅ | Feature name — becomes the `snake_case` YAML file name |
| `account` | Optional | Test account name (e.g. `bts1`, `bts2`). Omit to use default |
| `file directory` | ✅ | Category path: e.g. `acc_regression meeting video` |
| `pre_conditions` | ✅ | Comma-separated navigation steps before the test |
| `steps` | ✅ | Numbered test actions; any step can include `AI check prompt:` |
| `post_conditions` | ✅ | Teardown steps (e.g. `end meeting, sign out`) |
| `check_points` | Optional | Defaults to `Keyboard Navigation` if omitted |

---

## Example 1 — Simple (keyboard navigation only)

```
Create "Mute microphone" test case.
account: bts1
file directory: acc_regression meeting audio
pre_conditions: start meeting
steps:
  1. click "Mute"
post_conditions: end meeting, sign out
```

---

## Example 2 — With AI check (video enhancement)

```
Create "Show in floating window" test case.
account: bts1
file directory: acc_regression meeting video
pre_conditions: start meeting, open video settings
steps:
  1. enable/check "Show in floating window"
  2. click save button, AI check prompt: "Verify that the Show in floating window effect is visually applied to the video. Output format: ✅Success or ❌Failed", reference: show_in_floating_window.jpg
post_conditions: end meeting, sign out
```

---

## Available Check Points

| Value | When to use |
|---|---|
| `Keyboard Navigation` | Always include — validates KB accessibility |
| `Screen Reader` | Include when testing ARIA/screen reader compatibility |
| `Focus Ring` | Include when testing visible focus indicators |
| `Performance` | Include when `ui_response: true` is used |

> `ai_check` is a step-level property, **not** a check point value. Do not add it to `check_points`.

---

## Available Setup Keywords

| Keyword | Maps to |
|---|---|
| `uninstall` | `navigations/basic/uninstall_app` |
| `install` | `navigations/basic/install_app` |
| `agree` | `navigations/basic/agree` |
| `sign in` | `navigations/preconditions/app_entry/sign_in_to_app` |
| `start meeting` | `navigations/preconditions/app_core/start_meeting` |
| `open settings` | `navigations/preconditions/app_core/settings` |
| `open video settings` | `navigations/functional/in_meeting/video/video_settings` |
| `open video options` | `navigations/functional/in_meeting/video/video_options` |
| `open change virtual background panel` | `navigations/functional/in_meeting/video/change_virtual_background` |
| `open audio options` | `navigations/functional/in_meeting/audio/audio_options` |
| `open audio settings` | `navigations/functional/in_meeting/audio/audio_settings` |

## Available Teardown Keywords

| Keyword | Maps to |
|---|---|
| `end meeting` | `navigations/postconditions/end_meeting` |
| `end meeting for all` | `navigations/postconditions/end_meeting_for_all` |
| `leave meeting` | `navigations/postconditions/leave_meeting` |
| `sign out` | `navigations/postconditions/sign_out` |


---

## Part 2 — `/add-test-case-in-meetings`

Specialized prompt for `acc_regression/meetings` **in-meeting** test cases with **minimal input**.
Covers features accessed *inside* a running meeting: video, audio, chat, share, meeting controls, captions, AI assistant, etc.
Defaults are applied automatically — no need to specify account, pre/post conditions, or file path.

| Field | Default |
|---|---|
| `account` | `allianz8` |
| `file directory` | `acc_regression/meetings/<auto-detected area>` |
| `pre_conditions` | `uninstall_app → install_app → agree → sign_in_to_app → start_meeting` |
| `post_conditions` | `end_meeting → sign_out` |
| `check_points` | `[Keyboard Navigation]` |

> Area is auto-detected from your step descriptions by matching against `src/test_space/test_functions/navigation_mappings.json`.

### How to Run

```
/add-test-case-in-meetings Create "<feature name>" test case.
steps:
  1. <navigation description>
  2. enable/check "<control name>"
  3. save it and AI check prompt: "<verification>. Output format: ✅Success or ❌Failed", reference: <image>.jpg
```

### Example 1 — Video setting with AI check

```
/add-test-case-in-meetings Create "Show in floating window" test case.
steps:
  1. open video settings
  2. enable/check "Show in floating window"
  3. save it and AI check prompt: "Verify that the Show in floating window effect is visually applied to the video. Output format: ✅Success or ❌Failed", reference: show_in_floating_window.jpg
```

Output: `test_cases/acc_regression/meetings/video/show_in_floating_window.yaml`

### Optional Overrides

Any default can be overridden by explicitly providing it:

```
/add-test-case-in-meetings Create "<feature name>" test case.
account: bts1
check_points: [Keyboard Navigation, Screen Reader]
steps:
  ...
```

---

## Part 2b — `/add-test-case-join-meetings`

Specialized prompt for **join-meeting** test cases (`acc_regression/meetings/actions/`).
Covers joining a meeting from various entry points. `post_conditions` are **omitted by default**.

| Field | Default |
|---|---|
| `account` | `allianz8` |
| `file directory` | `acc_regression/meetings/actions/` |
| `pre_conditions` | `uninstall_app → install_app → agree` (no `start_meeting`, no sign-in for guest/app-entry) |
| `post_conditions` | **Omitted** unless explicitly provided |
| `check_points` | `[Keyboard Navigation]` |

### Supported Scenarios

| Keyword | Path | Needs sign-in? |
|---|---|---|
| `guest join a meeting`, `guest join meeting`, `join as guest` | `navigations/preconditions/app_entry/guest_join_a_meeting` | No (parameterized: `meeting_link`, `name`) |
| `guest join pmr`, `guest join meeting room` | `navigations/basic/guest_join_PMR` | No |
| `join a meeting webex`, `join webex meeting` | `navigations/preconditions/app_core/join_a_meeting_webex` | Yes (adds `sign_in_to_app`) |

### How to Run

#### Mode 1 — Generate only (review before running)

Generate the test case and review it manually before execution:

```
/add-test-case-join-meetings Create "guest join meeting" test case.
steps:
  1. guest join a meeting, meeting_link: "binbiwan@cisco.webex.com", name: "tony"
```

Output: `test_cases/acc_regression/meetings/actions/guest_join_meeting.yaml`

Then run manually (or use `/run-test-case` to search and run interactively):
```powershell
uv run python src\run_test_case_job.py --test_case "acc_regression\meetings\actions\guest_join_meeting"
```

#### Mode 2 — Generate and auto-run

Generate the test case and automatically execute it without manual intervention:

```
/add-test-case-join-meetings Create "guest join meeting" test case.
steps:
  1. guest join a meeting, meeting_link: "binbiwan@cisco.webex.com", name: "tony"
after create test case finished, please run it.
```

> Adding "after create test case finished, please run it" (or "run it after", "then run it", "and run it") will automatically execute the test immediately after creation.

The generated step will include a `parameters` block:

```yaml
# local_api: the referenced YAML's steps are loaded and executed inline.
# Both ${key} and {key} placeholder styles are supported.
- name: "guest join a meeting"
  action:
    type: local_api
    value: "navigations/preconditions/app_entry/guest_join_a_meeting"
    parameters:
      meeting_link: "binbiwan@cisco.webex.com"
      name: "tony"
```

---

## Part 2c — `/add-test-case-schedule-meetings`

Specialized prompt for **schedule-meeting** test cases (`acc_regression/meetings/schedule/`).
Requires sign-in. No `start_meeting` in pre_conditions. Default post_condition is `sign_out` only.

| Field | Default |
|---|---|
| `account` | `allianz8` |
| `file directory` | `acc_regression/meetings/schedule/` |
| `pre_conditions` | `uninstall_app → install_app → agree → sign_in_to_app` |
| `post_conditions` | `sign_out` |
| `check_points` | `[Keyboard Navigation]` |

### How to Run

```
/add-test-case-schedule-meetings Create "schedule meeting recurrence" test case.
steps:
  1. schedule a meeting
  2. enable/check "Recurrence"
  3. save it and AI check prompt: "Verify that the Recurrence option is enabled. Output format: ✅Success or ❌Failed", reference: schedule_recurrence.jpg
```

Output: `test_cases/acc_regression/meetings/schedule/schedule_meeting_recurrence.yaml`

---

## Part 3 — `/extend-workflow-parser`

Extend `workflow_loader.py` to support a new **load-time** YAML keyword (Tier 1).  
Use this when you want a new `action.type` that **transforms or expands steps when the YAML is loaded** — not at runtime.

> ⚠️ **Not the same as `/add-strategy`.**  
> `/add-strategy` = new runtime UI action (click, type, verify).  
> `/extend-workflow-parser` = new YAML keyword that rewrites steps at load time (like `local_api`, `include`).

### Example — `local_api` (already implemented, use as reference)

**What it does:** Inline-expands a referenced sub-workflow YAML and substitutes runtime parameters before execution starts.

**Input to Copilot:**

```
/extend-workflow-parser

Keyword name:    local_api
Trigger:         action.type == "local_api"
Behavior:        Load the referenced YAML file's steps and expand them inline at load time.
                 Sub-workflow YAMLs use ${key} placeholders (canonical style — do NOT use {key}).
Parameters:
  - value:       path to the sub-workflow YAML (relative to test_cases/, no .yaml extension)
  - parameters:  dict of placeholder name -> runtime value
Example YAML:
  - name: "run join meeting"
    action:
      type: local_api
      value: "navigations/preconditions/app_entry/guest_join_a_meeting"
      parameters:
        meeting_link: "binbiwan@cisco.webex.com"
        name: "tony"
```

**What Copilot will do:**
1. Read `workflow_loader.py` → find `_expand_includes()`
2. Add an `elif` branch that detects `action.type == 'local_api'`
3. Load the referenced YAML's steps via `_load_included_steps()`
4. Call `_replace_params()` to substitute `${meeting_link}` and `${name}` in the loaded steps
5. Extend the expanded steps list — no strategy class, no `action_strategy_manager.py` change needed

**How the referenced YAML uses the parameters** (`guest_join_a_meeting.yaml`):

```yaml
steps:
  - name: "Meeting link or personal room ID input field"
    action:
      type: input
      value: "${meeting_link}"    # substituted at load time

  - name: "Your name"
    action:
      type: input
      value: "${name}"            # substituted at load time
```

### When to use `/add-strategy` instead

If your feature needs to **interact with the live Webex UI at runtime** (locate a control, click it, read its state), use `/add-strategy` — that creates a new `<type>_action_strategy.py` file.

| Feature | Load time? | UI interaction? | Prompt |
|---|---|---|---|
| `local_api` — expand sub-workflow | yes | no | `/extend-workflow-parser` |
| `clipboard_paste` — Ctrl+V a value | no | yes | `/add-strategy` (Tier 2) |
| `screenshot_verify` — capture + compare | no | yes | `/add-strategy` (Tier 3) |


---

## Part 5 — `/run-test-case`

Find and run an existing test case by natural language name — no need to remember exact paths.

### How it works

1. **Extract keywords** from your input (strips filler words like `run`, `test`, `case`)
2. **Search** `src/test_space/test_cases/` recursively for matching YAML files (excludes `navigations/` sub-workflows)
3. **Present** a numbered list of matches for you to choose from
4. **Run** the selected test case automatically

### How to Use

```
/run-test-case run guest join meeting test case
```

**Copilot output:**
```
I found the following matching test cases:

1. acc_regression/meetings/actions/guest_join_meeting.yaml
2. acc_regression/jmt/guest_join_pmr.yaml
3. feature_test/Merak&Apptastic/join_meeting/Commercial_guest_join/guest_join_PMR.yaml

Which one would you like to run? (Enter the number)
```

**You reply:** `1`

**Copilot runs:**
```powershell
uv run python src\run_test_case_job.py --test_case "acc_regression\meetings\actions\guest_join_meeting"
```

### More Examples

```
/run-test-case run vbg static
/run-test-case execute show in floating window
/run-test-case run forward navigation in meetings
/run-test-case run acc_regression/meetings/video/vbg_static
```

### Auto-Run (skip confirmation)

If only one match is found and you add `just run it` or `run directly`:
```
/run-test-case run vbg static, just run it
```
→ Runs immediately without asking for confirmation.

---

## Part 6 — `/run-test-suite`

Find and run an existing test suite by natural language name — no need to remember exact paths.

### How it works

1. **Extract keywords** from your input (strips filler words like `run`, `test`, `suite`)
2. **Search** `src/test_space/test_suites/` recursively for matching YAML files (includes all subdirectories)
3. **Present** a numbered list of matches for you to choose from
4. **Run** the selected suite using its bare file stem name

### How to Use

```
/run-test-suite run video vbg test suite
```

**Copilot output:**
```
I found the following matching test suites:

1. video_vbg.yaml
2. web/web_video_vbg.yaml
3. mac_video_vbg.yaml

Which one would you like to run? (Enter the number)
```

**You reply:** `1`

**Copilot runs:**
```powershell
uv run python src\run_test_case_job.py --test_suite "video_vbg"
```

> **Key difference from `/run-test-case`:** The `--test_suite` argument always uses the **bare file stem** (no directory prefix), e.g. `video_vbg` not `web/video_vbg`.

### More Examples

```
/run-test-suite run meetings comprehensive
/run-test-suite run jmt suite
/run-test-suite run schedule meetings
/run-test-suite run web video vbg, just run it
```

### Auto-Run (skip confirmation)

If only one match is found and you add `just run it` or `run directly`:
```
/run-test-suite run mac video vbg, just run it
```
→ Runs immediately without asking for confirmation.

### Available Test Suites (reference)

| File | Suite name (`--test_suite`) |
|---|---|
| `video_vbg.yaml` | `video_vbg` |
| `web/web_video_vbg.yaml` | `web_video_vbg` |
| `mac_video_vbg.yaml` | `mac_video_vbg` |
| `meetings_comprehensive.yaml` | `meetings_comprehensive` |
| `acc_regression/jmt.yaml` | `jmt` |
| `schedule_meetings.yaml` | `schedule_meetings` |
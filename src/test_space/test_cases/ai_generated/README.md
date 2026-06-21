# AI Generated Test Cases

This directory contains test cases created by GitHub Copilot (mode-8-create-test-case) when the user does **not** specify a project or team target.

## Sub-directories

Test cases are organised by scenario type to keep auto-generated files tidy and separate from hand-authored regression suites:

| Sub-directory | Contents |
|---|---|
| `join_meeting/` | Guest join and user join flows auto-generated without a target project |
| `in_meeting/` | In-meeting feature flows auto-generated without a target project |
| `schedule_meeting/` | Schedule meeting flows auto-generated without a target project |
| `general/` | Calling, settings, and other flows auto-generated without a target project |

## Promotion

Once a generated test case is reviewed and validated, move it to the appropriate `acc_regression/` or `feature_test/` directory and remove it from here.

## Workflow Generator

Use the generator script to build a workflow test case from natural-language steps and
auto-insert `scan window` steps between business actions:

```bash
uv run python .github/skills/acc-ai-automation/scripts/create_workflow_test_case.py \
	--name sign_up_workflow \
	--steps-text "step 1: click sign up\nstep 2: Email address required input 111@1.com\nstep 3: click next button"
```

Generated business steps default to semantic locate mode:

- `match_mode: semantic`
- `similarity_threshold: 0.55`

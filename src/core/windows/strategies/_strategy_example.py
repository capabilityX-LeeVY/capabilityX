"""
_strategy_example.py — WRS Strategy Architecture Reference

This file lives in the real strategies directory so it stays in sync with actual
implementations. It is NOT executed — it is a readable, annotated reference for
Copilot and developers.

────────────────────────────────────────────────────────────────────────────────
ARCHITECTURE QUICK-REFERENCE
────────────────────────────────────────────────────────────────────────────────
Three tiers of extensibility — pick the right one:

  Tier 1 ─ YAML-level transform (load time)
            Where:  workflow_loader._expand_includes()
            When:   You need to expand/transform YAML steps before execution
            Adds:   An elif branch — no strategy class required
            Example: local_api, include

  Tier 2 ─ Simple action strategy (runtime UI action)
            Where:  New file in this directory + register in action_strategy_manager.py
            When:   New action.type that does something but result NOT in report
            Adds:   1 file + 1 registration line
            Example: key, input, shortcut, direct_key

  Tier 3 ─ Full pipeline action type (runtime + report + DB)
            Where:  Strategy + ActionResult field + 7-file pipeline chain
            When:   Result must appear in markdown report table AND MySQL DB
            Adds:   1 strategy + ActionResult field + processor + report + DB
            Example: verify, ai_check

────────────────────────────────────────────────────────────────────────────────
ENTRY FLOW (read these files to understand how execution reaches a strategy)
────────────────────────────────────────────────────────────────────────────────
  run_test_case_job.py
    → test_job_orchestrator.py
      → suite_case_runner.py / test_case_runner.py
        → workflow_loader.py          (YAML parsed; Tier 1 runs here)
          → action_strategy_manager.py
            → <type>_action_strategy.py  (Tier 2 or 3 execute() called here)
              → ControlActionProcessor  (captures ActionResult)
                → ReportProcessor       (Tier 3 result written to report)
                  → test_case_db_handler (Tier 3 result persisted to DB)
"""

# ─────────────────────────────────────────────────────────────────────────────
# TIER 1 — YAML-level (no strategy class)
# ─────────────────────────────────────────────────────────────────────────────
# There is NO Python class for Tier 1. The feature is an elif branch inside
# workflow_loader._expand_includes(). See the local_api implementation for the
# canonical pattern:
#
#   # File: src/rs_sdk/utils/workflow_loader.py
#   # Method: _expand_includes(self, steps, base_path)
#
#   elif (isinstance(step, dict)
#         and isinstance(step.get('action'), dict)
#         and step['action'].get('type') == 'local_api'):
#       yaml_path = step['action'].get('value', '')
#       params = step['action'].get('parameters', {})
#       included_steps = self._load_included_steps(yaml_path, base_path)
#       if params and included_steps:
#           included_steps = self._replace_params(included_steps, params)
#       expanded_steps.extend(included_steps)
#
# YAML usage:
#   steps:
#     - name: "sign in with test account"
#       action:
#         type: local_api
#         value: "navigations/preconditions/app_entry/sign_in_to_app"
#         parameters:
#           username: "${account_user}"
#           password: "${account_pass}"


# ─────────────────────────────────────────────────────────────────────────────
# TIER 2 — Simple strategy: KeyActionStrategy (real implementation)
# ─────────────────────────────────────────────────────────────────────────────
from typing import Dict, Any, Optional
from core.windows.strategies.action_strategy import ActionStrategy
from config.key_map import KEY_MAP
from common.utils.logger import LOGGER_INFO
import uiautomation as auto


class KeyActionStrategy(ActionStrategy):
    """
    Tier 2 example — handles action.type == "key".

    Reads a logical key name (e.g. "default", "enter", "space") from the YAML
    action.value field, maps it through KEY_MAP to the actual sendkeys string,
    then fires it with uiautomation.SendKeys().

    No ActionResult field needed — the return value is a plain string consumed
    by the calling processor but NOT written to a separate report column.
    """

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "{SPACE}")

        # Resolve ${var_name} / {var_name} variables injected from ExecutionContext
        if execution_context and hasattr(execution_context, 'resolve_variables'):
            value = execution_context.resolve_variables(value)

        send_value = KEY_MAP.get(value.lower(), "{SPACE}")
        auto.SendKeys(send_value)
        LOGGER_INFO(f"[operator][Locate][action][key][{send_value}]!", "CYAN")
        return send_value

    def get_action_type(self) -> str:
        return "key"   # Must match the string used in YAML action.type


class InputActionStrategy(ActionStrategy):
    """
    Tier 2 example — handles action.type == "input".

    Types a literal string (e.g. a username or URL) into the currently focused
    control using uiautomation.SendKeys with raw-string mode.
    """

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        value = ctrl_action.get("value", "")

        if execution_context and hasattr(execution_context, 'resolve_variables'):
            value = execution_context.resolve_variables(value)

        auto.SendKeys(value, waitTime=0)
        LOGGER_INFO(f"[operator][Locate][action][input][{value}]!", "CYAN")
        return value

    def get_action_type(self) -> str:
        return "input"


# ─────────────────────────────────────────────────────────────────────────────
# TIER 3 — Full pipeline strategy: VerifyActionStrategy (real implementation)
# ─────────────────────────────────────────────────────────────────────────────
from common.utils.logger import LOGGER_ERROR


class VerifyActionStrategy(ActionStrategy):
    """
    Tier 3 example — handles action.type == "verify".

    The return value ("✅Success" / "❌Failed") is captured in
    ActionResult.verification_result and flows through the full 7-step pipeline:

      VerifyActionStrategy.execute()
        → ControlActionProcessor   captures result into ActionResult.verification_result
          → ReportProcessor        writes it to the markdown report table column
            → test_case_db_handler inserts it into TestCaseNavigateReport row

    Pipeline touch-points for a new Tier 3 feature:
      1. Add field to   src/core/windows/data_models/action_result.py
      2. Create         src/core/windows/strategies/<type>_action_strategy.py   ← this file
      3. Add/extend     src/core/windows/processors/control_verification_processor.py
      4. Capture in     src/core/windows/processors/control_action_processor.py
      5. Extract in     src/core/windows/processors/report_processor.py
      6. Write column   src/rs_sdk/utils/report_handler.py
      7. Persist row    src/test_space/management/handlers/test_case_db_handler.py
    """

    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        expected_value = ctrl_action.get("value", "")

        # Tier 3 strategies obtain their processor from execution_context — they
        # do NOT instantiate processors directly (that would break dependency injection).
        verification_processor = getattr(execution_context, 'verification_processor', None)
        if not verification_processor:
            LOGGER_ERROR("[operator][Locate][action][verify] No verification_processor in execution context", "RED")
            return "❌Failed (No Processor)"

        result = verification_processor.verify_control_value(expected_value)

        # Normalize to canonical result strings used across ALL Tier 3 features
        status = result['status']
        if 'Success' in status:
            display_result = "✅Success"
        elif 'Failed' in status:
            display_result = "❌Failed"
        else:
            display_result = status

        LOGGER_INFO(f"[operator][Locate][action][verify] {display_result}", "CYAN")
        return display_result

    def get_action_type(self) -> str:
        return "verify"


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRATION SNIPPET
# ─────────────────────────────────────────────────────────────────────────────
# After creating a Tier 2 or Tier 3 strategy, register it in:
#   src/core/windows/strategies/action_strategy_manager.py
#
# Step 1 — add import at the top of that file:
#   from core.windows.strategies.<type>_action_strategy import <Type>ActionStrategy
#
# Step 2 — add to the strategies list in _register_default_strategies():
#   strategies = [
#       KeyActionStrategy(),
#       DirectKeyActionStrategy(),
#       ...
#       <Type>ActionStrategy(),   # ← add here
#       DefaultActionStrategy()   # DefaultActionStrategy must always be last
#   ]


# ─────────────────────────────────────────────────────────────────────────────
# ActionResult FIELD CONVENTION (Tier 3 only)
# ─────────────────────────────────────────────────────────────────────────────
# File: src/core/windows/data_models/action_result.py
#
# @dataclass
# class ActionResult:
#     navigate_status: str = ""
#     ...
#     verification_result:  Optional[str] = None  # existing Tier 3 field
#     your_feature_result:  Optional[str] = None  # ← new field: "<feature>_result"
#
# Allowed values (enforced by convention, not an enum):
#   "✅Success"  — feature executed and produced expected output
#   "❌Failed"   — feature executed but output did not match expected
#   "N/A"        — feature not applicable to this step (default fill-in)

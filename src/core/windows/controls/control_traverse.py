"""
ControlTraverser — Simple full-circle TAB / SHIFT+TAB traversal for test cases.

This class is used exclusively by `acc_sequence` action steps in test-case YAML.
It performs one complete keyboard navigation circle (TAB or SHIFT+TAB), records
control info and a screenshot at every step, and stops automatically when focus
returns to the starting control.

Anchor fallback strategy:
  The initial focused control (a) may not be a real Tab stop (e.g. a container
  group that receives programmatic focus but is skipped by Tab). When (a) is not
  encountered again, the traverser promotes the next control (b) as the anchor.
  If (b) is seen a second time, the circle is complete. Up to 3 levels of
  fallback are attempted before forcing a stop.

It intentionally has no smart-traversal logic (no flag_tree, flag_tab, combox
direction reversal, etc.) — that complexity lives in ControlNavigator and is only
needed for the accessibility database exploration workflow.
"""

from typing import List

from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.utils.control_recorder import ControlRecorder
from rs_sdk.utils.control_metadata import ControlMetadata
from rs_sdk.utils import control_db

from core.windows.controls.control_navigator_handler import ControlNavigatorHandler
from core.windows.controls.control_validator_handler import ControlValidatorHandler
from core.windows.data_models.action_result import TraverseRecord
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING

_MAX_STEPS = 300  # safety guard against runaway loops
_MAX_ANCHOR_LEVELS = 3  # max fallback anchor promotions


class ControlTraverser:
    """Simple full-circle traversal for test-case acc_sequence steps."""

    @staticmethod
    def _normalize_meta_value(value):
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _match_meta(cls, meta_a: dict, meta_b: dict):
        """Check if two control metadata dicts refer to the same control.

        Returns:
            (is_match, matched_by, value_a, value_b)
        """
        id_a = cls._normalize_meta_value(meta_a.get("id"))
        id_b = cls._normalize_meta_value(meta_b.get("id"))
        if id_a and id_b:
            return (id_a == id_b), "id", id_a, id_b

        hash_a = cls._normalize_meta_value(meta_a.get("path_hash"))
        hash_b = cls._normalize_meta_value(meta_b.get("path_hash"))
        if hash_a and hash_b:
            return (hash_a == hash_b), "path_hash", hash_a, hash_b

        name_a = cls._normalize_meta_value(meta_a.get("name"))
        name_b = cls._normalize_meta_value(meta_b.get("name"))
        if name_a and name_b:
            return (name_a == name_b), "name", name_a, name_b
        return False, "name", name_a, name_b

    @classmethod
    def _get_focus_return_reason(cls, init_meta: dict, current_meta: dict):
        """Determine if focus has returned to the starting control.

        Matching priority:
        1) automation id (most stable)
        2) path_hash
        3) control name (fallback only)
        """
        return cls._match_meta(init_meta, current_meta)

    def __init__(self):
        self.current_control   = ControlFactory().create_control()
        self.control_recorder  = ControlRecorder()
        self.navigator_handler = ControlNavigatorHandler()
        self.control_metadata  = ControlMetadata()
        self.validator_handler = ControlValidatorHandler()
        self.control_db        = control_db.ControlDB()

    def traverse(
        self,
        direction: str,
        from_control=None,
        level: int = 1,
        is_validated: int = 0,
    ) -> List[TraverseRecord]:
        """
        Perform one full-circle TAB or SHIFT+TAB traversal.

        Uses a progressive anchor fallback strategy:
          - Level 0: anchor = initial focused control (a)
          - Level 1: anchor = first Tab-visited control (b)
          - Level 2: anchor = second Tab-visited control (c)
        When the current anchor is seen a second time, the circle is complete.
        If it's never seen again, promote the next candidate and try once more.

        Args:
            direction:    "tab" (press TAB) or "shift_tab" (press SHIFT+TAB).
            from_control: Control name token used by ControlMetadata to read
                          the currently focused element.
            level:        Recording level passed to record_control_info.
            is_validated: Initial validation status passed to record_control_info.

        Returns:
            List of TraverseRecord objects visited during the traversal (in order).
        """
        key = "TAB" if direction == "tab" else "SHIFT_TAB"

        # Force-query the real OS-focused element via UIA GetFocusedElement().
        self.current_control.refresh(force_update=True)

        init_meta = self.control_metadata.get_control_metadata(from_control)
        init_path_hash = init_meta.get("path_hash")

        # ── Fallback anchor tracking ─────────────────────────────────────────
        # anchor_candidates[0] = init control (may not be a real Tab stop)
        # anchor_candidates[1..N] = first N distinct Tab stops (collected after
        #   pressing Tab, skipping any that match init)
        anchor_candidates: list[dict] = [init_meta]
        anchor_first_seen: list[int] = [0]
        anchor_level = 0  # active anchor index

        traverse_all: List[TraverseRecord] = []
        order = 0

        while True:
            order += 1

            current_meta = self.control_metadata.get_control_metadata(from_control)
            current_name = current_meta.get("name")
            current_id   = current_meta.get("id")

            # ── Full-circle exit: focus returned to the active anchor ─────────
            active_anchor = anchor_candidates[anchor_level]
            is_returned, matched_by, start_value, current_value = self._match_meta(
                active_anchor, current_meta
            )

            if order > 1 and is_returned:
                # Must have gone enough steps to constitute a real circle
                min_steps_for_circle = anchor_first_seen[anchor_level] + 3
                if order > min_steps_for_circle:
                    LOGGER_INFO(
                        f"[ControlTraverser] Full circle completed "
                        f"[direction={direction}][steps={order - 1}]"
                        f"[anchor_level={anchor_level}]"
                        f"[matched_by={matched_by}]"
                        f"[start={start_value}]"
                        f"[current={current_value}]", "GREEN"
                    )
                    break

            # ── Fallback: check if current matches a higher-level candidate ───
            # If we haven't matched the primary anchor (level 0) and we see a
            # fallback candidate for the second time, that means we've completed
            # a full circle from that candidate's perspective.
            if anchor_level == 0 and len(anchor_candidates) > 1:
                for lvl in range(1, len(anchor_candidates)):
                    is_match, _, _, _ = self._match_meta(
                        anchor_candidates[lvl], current_meta
                    )
                    if is_match and order > anchor_first_seen[lvl] + 3:
                        anchor_level = lvl
                        LOGGER_INFO(
                            f"[ControlTraverser] Full circle completed via "
                            f"anchor fallback "
                            f"[direction={direction}][steps={order - 1}]"
                            f"[anchor_level={anchor_level}]"
                            f"[matched_by=fallback]"
                            f"[anchor_id={self._normalize_meta_value(anchor_candidates[lvl].get('id'))}]"
                            f"[anchor_name={self._normalize_meta_value(anchor_candidates[lvl].get('name'))}]",
                            "GREEN"
                        )
                        break
                if anchor_level > 0:
                    break

            # ── Safety guard against runaway loop ─────────────────────────────
            if order > _MAX_STEPS:
                LOGGER_WARNING(
                    f"[ControlTraverser] Max steps ({_MAX_STEPS}) reached, stopping. "
                    f"[direction={direction}][last={current_name}]"
                )
                break

            # ── Record current control info and screenshot ────────────────────
            self.control_recorder.record_control_info(
                level, from_control, init_path_hash, is_validated, direction
            )
            control_image_path, _, _, _ = self.control_recorder.record_control_image()

            LOGGER_INFO(
                f"[{order}][ControlTraverser] [{current_name}] | [{current_id}]", "CYAN"
            )

            # ── Move focus to the next control ────────────────────────────────
            self.navigator_handler.traverse_control(key)
            new_meta = self.control_metadata.get_control_metadata(from_control)
            traverse_all.append(TraverseRecord(
                order=order,
                control_name=current_name or "",
                control_id=current_id or "",
                control_image_path=control_image_path,
                control_type=current_meta.get("type_name"),
                full_description=current_meta.get("full_description"),
                access_key=current_meta.get("accesskey"),
                legacy_value=current_meta.get("legacy_value"),
                legacy_role=current_meta.get("legacy_role"),
                legacy_state=current_meta.get("legacy_state"),
                parent_name=current_meta.get("parent_name"),
                parent_type=current_meta.get("parent_type"),
                window_level1=current_meta.get("window_name"),
                window_level2=current_meta.get("level2_window_name"),
                default_action=current_meta.get("default_action"),
            ))

            # ── Collect fallback anchor candidates AFTER Tab press ─────────────
            # Only collect if: different from init AND not already collected
            if len(anchor_candidates) <= _MAX_ANCHOR_LEVELS:
                is_same_as_init, _, _, _ = self._match_meta(init_meta, new_meta)
                if not is_same_as_init:
                    # Check it's not already in candidates
                    already_collected = False
                    for existing in anchor_candidates[1:]:
                        is_dup, _, _, _ = self._match_meta(existing, new_meta)
                        if is_dup:
                            already_collected = True
                            break
                    if not already_collected:
                        anchor_candidates.append(dict(new_meta))
                        anchor_first_seen.append(order + 1)  # will be seen at next iteration start
                        LOGGER_INFO(
                            f"[ControlTraverser] Registered fallback anchor "
                            f"level {len(anchor_candidates) - 1}: "
                            f"[{self._normalize_meta_value(new_meta.get('name'))}]"
                            f"[id={self._normalize_meta_value(new_meta.get('id'))}]"
                        )

        return traverse_all

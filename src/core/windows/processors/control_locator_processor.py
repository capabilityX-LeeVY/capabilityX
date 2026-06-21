"""
Control Locator Processor

This module contains the ControlLocatorProcessor for handling control location 
and navigation with flexible retry strategies.
"""

import os
import time
from difflib import SequenceMatcher
import uiautomation as auto
from typing import Tuple, Optional
from core.windows.data_models.locate_target import LocateTarget
from core.windows.data_models.focused_control_metadata import FocusedControlMetadata
from core.windows.data_models.locate_result import LocateResult
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING
from common.handler.imageHandler import capture_and_save_screenshot
from rs_sdk.utils.event_listener import FocusListener
from rs_sdk.utils.control_datasets_loader import get_complete_control_metadata_by_name
from config.config import NO_LOCATE_CONTROLS, NO_LOCATE_CONTROLS_ACTION_TYPE
from config.paths import WINDOW_IMAGE_PATH
from models.openai_client import OpenAIClient
from prompts.prompt_loader import load_prompt, OCRPrompts


class ControlLocatorProcessor:
    """Control locator processor - handles control location and navigation with flexible retry strategies"""
    
    def __init__(self, control_navigator, metadata_processor):
        self.control_navigator = control_navigator
        self.metadata_processor = metadata_processor
        self.max_retry_attempts = 3
        self.retry_delay = 1
        
        # Store control name sequence for intelligent retry
        self.control_name_sequence = []
        
        # Store control name UI path for intelligent retry (actual control names from UI)
        self.control_name_ui_path = []
        
        self.current_step_index = 0
        
        # Global retry enable/disable flag
        # Set to False when validating test case steps sequence (no retry needed)
        # Set to True for exploration mode (retry enabled for robustness)
        self.enable_retry = True
        
        # Record traversal flag - controls whether to record all controls during traversal
        # Set to True to record controls (for exploration/data collection)
        # Set to False to skip recording (for test case validation)
        # This value is passed to test_case_flag in control_navigator
        # Default to False (test validation mode, better performance)
        self.record_traversal = False
        
        # Retry strategy configuration
        self.retry_strategies_enabled = {
            "stale_data": True,      # Reset FocusListener for identical controls
            "corrupted_data": True,  # Reset FocusListener for ?? characters
            "empty_controls": True,  # Press ESC for empty control lists
            "control_not_found": True,  # Press ESC when target control not found despite having controls
            "intelligent_backtrack": True,  # Backtrack to intersection and retry sequence
            "ai_fuzzy_match": True,  # Use OpenAI to find closest semantic match in control_name_ui_path
            "reopen_parent": True,   # Re-navigate to predecessor step to reopen parent panel (e.g. after combobox ESC closes it)
        }
    
    def set_control_name_sequence(self, control_names_list):
        """Set the control name sequence for intelligent retry mechanism"""
        self.control_name_sequence = control_names_list
        self.current_step_index = 0
        LOGGER_DEBUG(f"[operator][Locate][sequence] Set control name sequence: {control_names_list}", "CYAN")
    
    def set_enable_retry(self, enable: bool):
        """
        Enable or disable retry mechanism for control location
        
        Args:
            enable: True to enable retry (exploration mode), False to disable (test case validation mode)
        """
        self.enable_retry = enable
        mode = "ENABLED" if enable else "DISABLED"
        LOGGER_INFO(f"[operator][Locate][retry][config] Retry mechanism {mode}", "CYAN")
        if not enable:
            LOGGER_INFO(f"[operator][Locate][retry][config] Running in TEST CASE VALIDATION mode - no retries", "YELLOW")
        else:
            LOGGER_INFO(f"[operator][Locate][retry][config] Running in EXPLORATION mode - retries enabled", "GREEN")
    
    def set_record_traversal(self, record: bool):
        """
        Enable or disable recording of all controls during traversal
        
        Args:
            record: True to record controls (exploration/data collection), False to skip recording (test case validation)
        """
        self.record_traversal = record
        mode = "ENABLED" if record else "DISABLED"
        LOGGER_INFO(f"[operator][Locate][record][config] Control traversal recording {mode}", "CYAN")
        if not record:
            LOGGER_INFO(f"[operator][Locate][record][config] Running in TEST CASE VALIDATION mode - no recording", "YELLOW")
        else:
            LOGGER_INFO(f"[operator][Locate][record][config] Running in EXPLORATION mode - recording enabled", "GREEN")
    
    def set_control_name_ui_path(self, control_name_ui_path):
        """Set control name UI path for intelligent retry mechanism (actual UI control names)"""
        self.control_name_ui_path = control_name_ui_path
        LOGGER_INFO(f"[backtrack][ui_path] Control name UI path set: {control_name_ui_path}", "CYAN")
        LOGGER_INFO(f"[backtrack][ui_path] UI path length: {len(control_name_ui_path)} controls", "GREEN")
    
    def set_current_step_index(self, index):
        """Set the current step index in the control sequence"""
        self.current_step_index = index
        LOGGER_DEBUG(f"[operator][Locate][sequence] Set current step index: {index}", "CYAN")
    
    def find_intersection_and_backtrack_index(self, traverse_all_controls, target_control_name):
        """Find intersection between available controls and control UI path, return backtrack index"""
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Starting intersection analysis for '{target_control_name}'", "CYAN")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Control name UI path: {self.control_name_ui_path}", "CYAN")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Control name sequence: {self.control_name_sequence}", "CYAN")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Current step index: {self.current_step_index}", "CYAN")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Traversed controls: {traverse_all_controls}", "CYAN")
        
        # PRIORITY 1: Use control_name_ui_path if available (actual UI control names)
        primary_sequence = self.control_name_ui_path if self.control_name_ui_path else self.control_name_sequence
        
        if not primary_sequence or not traverse_all_controls:
            LOGGER_DEBUG(f"[backtrack][intersection][analysis] Missing data - primary_sequence: {bool(primary_sequence)}, controls: {bool(traverse_all_controls)}", "YELLOW")
            return None
        
        LOGGER_INFO(f"[backtrack][intersection][analysis] Using primary sequence (UI path): {primary_sequence}", "GREEN" if self.control_name_ui_path else "YELLOW")
        
        # Clean and normalize control names for comparison
        available_controls = [ctrl.strip() for ctrl in traverse_all_controls if ctrl and ctrl.strip()]
        sequence_controls = [ctrl.strip() for ctrl in primary_sequence if ctrl and ctrl.strip()]
        
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Available controls (cleaned): {available_controls}", "CYAN")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Sequence controls (cleaned): {sequence_controls}", "CYAN")
        
        # Find intersection
        intersection = []
        intersection_indices = []
        
        for i, seq_ctrl in enumerate(sequence_controls):
            if seq_ctrl in available_controls:
                intersection.append(seq_ctrl)
                intersection_indices.append(i)
                LOGGER_DEBUG(f"[backtrack][intersection][analysis] Found match: '{seq_ctrl}' at index {i}", "GREEN")
        
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Final intersection: {intersection}", "GREEN" if intersection else "YELLOW")
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] Intersection indices: {intersection_indices}", "GREEN" if intersection_indices else "YELLOW")
        
        if not intersection:
            LOGGER_DEBUG(f"[backtrack][intersection][analysis] No intersection found between available controls and sequence", "YELLOW")
            return None
        
        # Find the earliest intersection point that's before or at current target
        target_index = None
        if target_control_name:
            target_name_clean = target_control_name.strip()
            try:
                target_index = sequence_controls.index(target_name_clean)
                LOGGER_DEBUG(f"[backtrack][intersection][analysis] Target '{target_name_clean}' found at sequence index {target_index}", "CYAN")
            except ValueError:
                LOGGER_DEBUG(f"[backtrack][intersection][analysis] Target control '{target_name_clean}' not found in sequence", "YELLOW")
        
        # Select the best backtrack point
        backtrack_index = None
        if target_index is not None:
            # Find the latest intersection point that's before the target
            valid_indices = [idx for idx in intersection_indices if idx < target_index]
            LOGGER_DEBUG(f"[backtrack][intersection][analysis] Valid indices before target: {valid_indices}", "CYAN")
            if valid_indices:
                backtrack_index = max(valid_indices)
                LOGGER_DEBUG(f"[backtrack][intersection][analysis] Using latest valid index: {backtrack_index}", "GREEN")
            else:
                # If no intersection before target, use the earliest intersection
                backtrack_index = min(intersection_indices)
                LOGGER_DEBUG(f"[backtrack][intersection][analysis] No valid indices before target, using earliest: {backtrack_index}", "YELLOW")
        else:
            # If target not in sequence, use the earliest intersection
            backtrack_index = min(intersection_indices)
            LOGGER_DEBUG(f"[backtrack][intersection][analysis] Target not in sequence, using earliest: {backtrack_index}", "YELLOW")
        
        if backtrack_index is not None:
            backtrack_control = sequence_controls[backtrack_index]
            LOGGER_INFO(f"[backtrack][intersection][analysis] Found intersection: {intersection}", "GREEN")
            LOGGER_INFO(f"[backtrack][intersection][analysis] Backtrack to index {backtrack_index}: '{backtrack_control}'", "GREEN")
            return backtrack_index
        
        LOGGER_DEBUG(f"[backtrack][intersection][analysis] No valid backtrack index found", "YELLOW")
        return None
    
    def _should_retry_location(self, traverse_all_controls, result, target_control_name=None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Determine if location should be retried based on result patterns and return retry action type
        
        User-requested priority logic:
        1. ABSOLUTE PRIORITY 1: Intelligent backtrack - When locate fails, immediately check if control_name_ui_path has intersection with traverse_all_controls
        2. PRIORITY 2: If no intersection, press ESC and search again
        3. PRIORITY 3: If still fails after ESC, check again for intersection
        """
        
        # Check global retry enable flag first
        if not self.enable_retry:
            LOGGER_DEBUG(f"[operator][Locate][retry][disabled] Retry mechanism is disabled (test case validation mode)", "YELLOW")
            return False, None, "Retry disabled by configuration"
        
        # ABSOLUTE PRIORITY 1: Intelligent backtrack check - User's first priority requirement
        if self.retry_strategies_enabled.get("intelligent_backtrack", True) and not result:
            # Use control_name_ui_path as primary matching sequence (actual UI control names)
            primary_sequence = self.control_name_ui_path if self.control_name_ui_path else self.control_name_sequence
            
            if primary_sequence:
                backtrack_index = self.find_intersection_and_backtrack_index(traverse_all_controls, target_control_name)
                if backtrack_index is not None:
                    LOGGER_INFO(f"[backtrack][priority_1] ABSOLUTE PRIORITY: Intelligent backtrack triggered", "GREEN")
                    LOGGER_INFO(f"[backtrack][priority_1] Found intersection between traverse_all_controls and control_name_ui_path", "GREEN")
                    return True, "intelligent_backtrack", f"PRIORITY 1: Found intersection in UI path, can backtrack to index {backtrack_index}"
                else:
                    LOGGER_DEBUG(f"[backtrack][priority_1] No intersection found between traverse_all_controls and UI path", "YELLOW")
            else:
                LOGGER_DEBUG(f"[backtrack][priority_1] No control UI path available for intersection check", "YELLOW")
        
        # PRIORITY 1.5: AI fuzzy match - when no exact intersection found in P1,
        # use OpenAI to find the closest semantic match in control_name_ui_path
        if self.retry_strategies_enabled.get("ai_fuzzy_match", True) and not result:
            primary_sequence = self.control_name_ui_path if self.control_name_ui_path else self.control_name_sequence
            if primary_sequence and target_control_name:
                LOGGER_INFO(
                    f"[ai_fuzzy_match][priority_1_5] No exact intersection found, "
                    f"triggering AI fuzzy match for '{target_control_name}' "
                    f"({len(primary_sequence)} candidates in UI path)",
                    "CYAN"
                )
                return True, "ai_fuzzy_match", (
                    f"PRIORITY 1.5: No exact intersection, using AI to find closest match "
                    f"to '{target_control_name}' ({len(primary_sequence)} candidates)"
                )
            else:
                LOGGER_DEBUG(f"[ai_fuzzy_match][priority_1_5] No UI path or target available for AI fuzzy match", "YELLOW")

        # PRIORITY 2: If no intersection found, use ESC strategy
        if not result:
            # Check for repeated identical controls (indicates stale data)
            if self.retry_strategies_enabled.get("stale_data", True) and len(traverse_all_controls) > 0:
                all_equal = all(item == traverse_all_controls[0] for item in traverse_all_controls)
                if all_equal:
                    LOGGER_DEBUG(f"[backtrack][priority_2] Using stale_data strategy (all controls identical)", "YELLOW")
                    return True, "stale_data", "All controls are identical, possible stale data"
        
        # PRIORITY 3: Check for ?? characters (indicates missing or corrupted control data)
        if self.retry_strategies_enabled.get("corrupted_data", True):
            contains_question_marks = any('??' in str(item) for item in traverse_all_controls)
            if contains_question_marks:
                LOGGER_DEBUG(f"[backtrack][priority_3] Using corrupted_data strategy", "YELLOW")
                return True, "corrupted_data", "Found ?? characters in controls, possible corrupted data"
        
        # PRIORITY 4: Check for empty control list when expecting results
        if self.retry_strategies_enabled.get("empty_controls", True):
            if not traverse_all_controls and not result:
                LOGGER_DEBUG(f"[backtrack][priority_4] Using empty_controls strategy", "YELLOW")
                return True, "empty_controls", "Empty control list returned"
        
        # PRIORITY 5: General ESC strategy - Used when no intersection found (User's second priority requirement)
        if self.retry_strategies_enabled.get("control_not_found", True):
            if not result and traverse_all_controls and len(traverse_all_controls) > 0:
                LOGGER_INFO(f"[backtrack][priority_5] Using ESC strategy (no intersection found)", "YELLOW")
                return True, "control_not_found", f"PRIORITY 2: No intersection found, will press ESC. Target control not found despite {len(traverse_all_controls)} controls available"
        
        return False, None, None
    
    def _perform_retry_reset(self, retry_reason):
        """Perform standard retry reset operations for stale_data and corrupted_data"""
        LOGGER_DEBUG(f"[operator][Locate][retry][reset] {retry_reason}, resetting FocusListener", "YELLOW")
        
        listener = FocusListener()
        listener.stop()
        listener.start()
        time.sleep(self.retry_delay)

    def _try_reopen_parent(self, target_control_name: str, traverse_all_controls: Optional[list] = None) -> bool:
        """
        Try to reopen the parent panel/dialog by navigating to and activating its opener control.

        Primary strategy: use intersection analysis to find the backtrack/opener control
        (does NOT require target to be in control_name_sequence).
        Fallback: use the predecessor step in control_name_sequence.

        Args:
            target_control_name: The control we are trying to locate
            traverse_all_controls: Currently visible controls (used for intersection analysis)

        Returns:
            True if the opener was found and activated (parent likely reopened), False otherwise
        """
        if not target_control_name:
            LOGGER_DEBUG(f"[reopen_parent] No target available", "YELLOW")
            return False

        opener_name = None

        # Primary strategy: intersection analysis - finds the parent control directly
        # from what's currently visible (does not need target in sequence)
        if traverse_all_controls is not None:
            backtrack_index = self.find_intersection_and_backtrack_index(traverse_all_controls, target_control_name)
            if backtrack_index is not None:
                primary_sequence = self.control_name_ui_path if self.control_name_ui_path else self.control_name_sequence
                if primary_sequence and backtrack_index < len(primary_sequence):
                    opener_name = primary_sequence[backtrack_index].strip()
                    LOGGER_INFO(f"[reopen_parent] Found opener via intersection analysis: '{opener_name}' at index {backtrack_index}", "CYAN")

        # Fallback: use predecessor step from control_name_sequence (requires target in sequence)
        if not opener_name and self.control_name_sequence:
            clean_sequence = [ctrl.strip() for ctrl in self.control_name_sequence]
            try:
                target_index = clean_sequence.index(target_control_name.strip())
                if target_index > 0:
                    opener_name = clean_sequence[target_index - 1]
                    LOGGER_INFO(f"[reopen_parent] Found opener via sequence predecessor: '{opener_name}' (index {target_index - 1})", "CYAN")
            except ValueError:
                LOGGER_DEBUG(f"[reopen_parent] Target '{target_control_name}' not in sequence, predecessor fallback unavailable", "YELLOW")

        if not opener_name:
            LOGGER_DEBUG(f"[reopen_parent] Cannot determine opener for '{target_control_name}'", "YELLOW")
            return False

        LOGGER_INFO(f"[reopen_parent] Locating opener '{opener_name}' to reopen parent panel", "CYAN")

        complete_metadata = get_complete_control_metadata_by_name(opener_name, platform='windows')
        control_type = complete_metadata.get('control_type') if complete_metadata else None
        control_type_name = complete_metadata.get('control_type_name') if complete_metadata else None
        opener_meta = {
            "name": opener_name,
            "id": "",
            "test_case_step_description": opener_name,
            "control_type": control_type,
            "control_type_name": control_type_name
        }

        _, _, nav_result, _ = self.control_navigator.control_navigator(
            is_recorded=False, is_located=True, locate_control_meta=opener_meta,
            close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
        )

        if nav_result:
            LOGGER_INFO(f"[reopen_parent] ✅ Found opener '{opener_name}', activating with SPACE to reopen parent", "GREEN")
            auto.SendKeys("{SPACE}")
            time.sleep(1.0)
            return True
        else:
            LOGGER_WARNING(f"[reopen_parent] ❌ Could not locate opener '{opener_name}', cannot reopen parent", "YELLOW")
            return False

    def _ai_find_closest_in_ui_path(self, target_control_name: str, traverse_all_controls: list) -> Optional[str]:
        """
        Use OpenAI to find the closest semantic match to target_control_name
        within traverse_all_controls (the controls currently visible in the UI).

        Args:
            target_control_name: The control name we are trying to locate
            traverse_all_controls: The list of control names currently visible in the UI

        Returns:
            The exact control name string from traverse_all_controls that best matches the target,
            or None if no suitable match is found or the AI call fails.
        """
        if not traverse_all_controls or not target_control_name:
            LOGGER_DEBUG(f"[ai_fuzzy_match][find] Missing data - traverse_all_controls: {bool(traverse_all_controls)}, target: {bool(target_control_name)}", "YELLOW")
            return None

        candidates = [ctrl.strip() for ctrl in traverse_all_controls if ctrl and ctrl.strip()]
        if not candidates:
            LOGGER_DEBUG(f"[ai_fuzzy_match][find] No valid candidates in traverse_all_controls", "YELLOW")
            return None

        candidates_text = "\n".join(f"- {name}" for name in candidates)
        prompt = (
            f'I am trying to navigate to a UI control named: "{target_control_name}".\n'
            f'From the following list of available UI controls:\n'
            f'{candidates_text}\n\n'
            f'Which control name from the list is the closest semantic match to "{target_control_name}"?\n'
            f'Rules:\n'
            f'- Reply with ONLY the exact control name from the list above.\n'
            f'- If no control is similar enough, reply with "NONE".\n'
            f'- Do not add any explanation or extra text.'
        )

        LOGGER_INFO(f"[ai_fuzzy_match][find] Calling OpenAI for '{target_control_name}' with {len(candidates)} candidates", "CYAN")
        LOGGER_DEBUG(f"[ai_fuzzy_match][find] Candidates: {candidates}", "CYAN")

        try:
            client = OpenAIClient()
            response = client.chat(prompt)
            if not response:
                LOGGER_WARNING(f"[ai_fuzzy_match][find] OpenAI returned empty response", "YELLOW")
                return None

            matched = response.strip()
            LOGGER_INFO(f"[ai_fuzzy_match][find] OpenAI raw response: '{matched}'", "CYAN")

            if matched.upper() == "NONE":
                LOGGER_DEBUG(f"[ai_fuzzy_match][find] OpenAI found no suitable match", "YELLOW")
                return None

            # Validate: the response must be one of the candidates (exact or case-insensitive)
            matched_candidate = None
            for candidate in candidates:
                if candidate == matched:
                    matched_candidate = candidate
                    break
            if not matched_candidate:
                for candidate in candidates:
                    if candidate.lower() == matched.lower():
                        matched_candidate = candidate
                        break

            if not matched_candidate:
                LOGGER_WARNING(f"[ai_fuzzy_match][find] ⚠️ AI response '{matched}' is not in candidate list, ignoring", "YELLOW")
                return None

            # Similarity gate: reject matches below 80% text similarity
            # This prevents wildly wrong AI matches (e.g. 'Video options' → 'Resolution and frame rate')
            target_lower = target_control_name.strip().lower()
            matched_lower = matched_candidate.strip().lower()
            similarity = SequenceMatcher(None, target_lower, matched_lower).ratio()
            # Also check containment (e.g. 'Mute' in 'Mute button')
            is_contained = target_lower in matched_lower or matched_lower in target_lower

            if similarity >= 0.8 or is_contained:
                LOGGER_INFO(f"[ai_fuzzy_match][find] ✅ Match accepted: '{matched_candidate}' (similarity={similarity:.2f}, contained={is_contained})", "GREEN")
                return matched_candidate
            else:
                LOGGER_WARNING(
                    f"[ai_fuzzy_match][find] ⚠️ Match rejected: '{matched_candidate}' "
                    f"(similarity={similarity:.2f} < 0.80, contained={is_contained}), ignoring",
                    "YELLOW"
                )
                return None

        except Exception as e:
            LOGGER_WARNING(f"[ai_fuzzy_match][find] OpenAI call failed: {e}", "YELLOW")
            return None

    def _ai_is_direct_target(self, target_control_name: str, ai_matched_name: str) -> bool:
        """
        Ask OpenAI whether ai_matched_name IS the target control itself
        (possibly with a different wording / state suffix), or whether it is
        a parent/opener control that needs to be activated first to reveal
        the actual target.

        Returns:
            True  → ai_matched_name IS the target (navigate directly or via opener lookup)
            False → ai_matched_name is a parent opener (press SPACE to reveal the target)
        """
        prompt = (
            f'I am navigating a UI. I want to reach a control named: "{target_control_name}".\n'
            f'The UI currently shows a control named: "{ai_matched_name}".\n\n'
            f'Question: Is "{ai_matched_name}" the SAME control as "{target_control_name}" '
            f'(possibly with a different wording, extra state text like "selected", "1 of 3", '
            f'or minor phrasing difference), '
            f'OR is "{ai_matched_name}" a PARENT / OPENER control that you must activate first '
            f'(e.g. press SPACE) to open a panel or dropdown where "{target_control_name}" will appear?\n\n'
            f'Reply with ONLY one word: SAME or OPENER.'
        )
        LOGGER_INFO(
            f"[ai_fuzzy_match][is_direct] Asking AI: is '{ai_matched_name}' the same as or opener for '{target_control_name}'",
            "CYAN"
        )
        try:
            client = OpenAIClient()
            response = client.chat(prompt)
            if not response:
                LOGGER_WARNING(f"[ai_fuzzy_match][is_direct] Empty response, defaulting to OPENER", "YELLOW")
                return False
            answer = response.strip().upper()
            LOGGER_INFO(f"[ai_fuzzy_match][is_direct] AI answered: '{answer}'", "CYAN")
            return answer == "SAME"
        except Exception as e:
            LOGGER_WARNING(f"[ai_fuzzy_match][is_direct] AI call failed: {e}, defaulting to OPENER", "YELLOW")
            return False

    def _check_control_visible_by_ocr(self, target_control_name: str) -> bool:
        """
        Capture a screenshot of the current window and use AI OCR to determine
        whether the target control is visually present.

        Args:
            target_control_name: The control name to search for in the screenshot

        Returns:
            True if the AI confirms the control is visible, False otherwise
        """
        try:
            # Ensure the screenshot directory exists
            screenshot_dir = str(WINDOW_IMAGE_PATH)
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, "ocr_visibility_check.png")

            # Capture current screen
            LOGGER_DEBUG(f"[ocr_visibility] Capturing screenshot to '{screenshot_path}'", "CYAN")
            capture_and_save_screenshot(screenshot_path)

            if not os.path.exists(screenshot_path):
                LOGGER_WARNING(f"[ocr_visibility] Screenshot capture failed", "YELLOW")
                return False

            # Load prompt template and inject the target control name
            prompt_template = load_prompt(OCRPrompts.CONTROL_VISIBILITY_CHECK)
            prompt = prompt_template.replace("{target_control_name}", target_control_name)

            # Call AI vision analysis
            LOGGER_INFO(f"[ocr_visibility] Asking AI: is '{target_control_name}' visible on screen?", "CYAN")
            client = OpenAIClient()
            result = client.ai_analyze_image(screenshot_path, message=prompt)

            if not result:
                LOGGER_WARNING(f"[ocr_visibility] AI returned empty response, assuming not visible", "YELLOW")
                return False

            answer = result.strip().upper()
            is_visible = answer == "YES"
            LOGGER_INFO(
                f"[ocr_visibility] AI answer: '{answer}' → control "
                f"{'IS' if is_visible else 'is NOT'} visible",
                "GREEN" if is_visible else "YELLOW"
            )
            return is_visible

        except Exception as e:
            LOGGER_WARNING(f"[ocr_visibility] OCR check failed: {e}, assuming not visible", "YELLOW")
            return False

    def _perform_retry_action(self, action_type, retry_reason, traverse_all_controls=None, target_control_name=None):
        """Perform specific retry actions based on the failure condition"""
        LOGGER_DEBUG(f"[operator][Locate][retry][action] {action_type}: {retry_reason}", "YELLOW")
        
        if action_type == "intelligent_backtrack":
            # Perform intelligent backtrack and retry sequence
            LOGGER_DEBUG(f"[backtrack][action][retry] Starting intelligent backtrack action", "YELLOW")
            backtrack_index = self.find_intersection_and_backtrack_index(traverse_all_controls, target_control_name)
            if backtrack_index is not None:
                LOGGER_INFO(f"[backtrack][action][retry] Starting intelligent backtrack from index {backtrack_index}", "GREEN")
                return self._execute_backtrack_sequence(backtrack_index, target_control_name)
            else:
                # No valid backtrack point - return False without pressing ESC so the caller
                # can fall back to ai_fuzzy_match cleanly without disrupting UI state
                LOGGER_DEBUG(f"[backtrack][action][retry] No valid backtrack point found, returning False for fallback handling", "YELLOW")
                return False
                
        elif action_type == "ai_fuzzy_match":
            # Use OpenAI to find the closest semantic match in traverse_all_controls,
            # then either navigate directly (if it IS the target) or open parent first.
            LOGGER_INFO(f"[ai_fuzzy_match][action] Calling OpenAI to find closest match for '{target_control_name}'", "CYAN")
            if not target_control_name:
                LOGGER_DEBUG(f"[ai_fuzzy_match][action] No target control name provided", "YELLOW")
                # auto.SendKeys("{ESC}")
                time.sleep(self.retry_delay)
                return False
            ai_matched_name = self._ai_find_closest_in_ui_path(target_control_name, traverse_all_controls or [])
            if ai_matched_name:
                LOGGER_INFO(f"[ai_fuzzy_match][action] ✅ AI matched '{target_control_name}' → '{ai_matched_name}'", "GREEN")

                # Ask AI: is ai_matched_name the same control as target (SAME)
                # or a parent/opener that must be activated first (OPENER)?
                is_direct_target = self._ai_is_direct_target(target_control_name, ai_matched_name)
                LOGGER_DEBUG(
                    f"[ai_fuzzy_match][action] is_direct_target={is_direct_target} "
                    f"(AI judgment: {'SAME' if is_direct_target else 'OPENER'}) "
                    f"('{ai_matched_name}' vs '{target_control_name}')",
                    "CYAN"
                )

                complete_metadata = get_complete_control_metadata_by_name(ai_matched_name, platform='windows')
                control_type = complete_metadata.get('control_type') if complete_metadata else None
                control_type_name = complete_metadata.get('control_type_name') if complete_metadata else None
                ctrl_meta = {
                    "name": ai_matched_name,
                    "id": "",
                    "test_case_step_description": ai_matched_name,
                    "control_type": control_type,
                    "control_type_name": control_type_name
                }

                if is_direct_target:
                    # AI says SAME: ai_matched_name IS the target control (possibly with different
                    # wording or a state suffix like 'Not selected 2 of 3').
                    # ai_matched_name was selected from traverse_all_controls (the controls the
                    # navigator traversed), but the traversal may have briefly opened a parent
                    # panel that has since closed (e.g. combobox ESC). So first try direct
                    # navigation; if that fails, find the opener via intersection analysis
                    # (using ai_matched_name as target, since it IS in control_name_ui_path)
                    # and reopen the parent before navigating again.
                    LOGGER_INFO(
                        f"[ai_fuzzy_match][action] SAME: '{ai_matched_name}' is the target "
                        f"— trying direct navigation first", "CYAN"
                    )
                    _, _, nav_result, _ = self.control_navigator.control_navigator(
                        is_recorded=False, is_located=True, locate_control_meta=ctrl_meta,
                        close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                    )
                    if nav_result:
                        LOGGER_INFO(f"[ai_fuzzy_match][action] ✅ Located '{ai_matched_name}' directly", "GREEN")
                        return True
                    else:
                        # Direct navigation failed — the parent panel is likely closed.
                        # Use ai_matched_name (exact UI name) as lookup target for opener search,
                        # because ai_matched_name exists in control_name_ui_path and
                        # intersection analysis can find the opener control before it.
                        LOGGER_INFO(
                            f"[ai_fuzzy_match][action] Direct navigation failed — "
                            f"parent panel likely closed. Searching opener for '{ai_matched_name}' "
                            f"via intersection analysis", "YELLOW"
                        )
                        reopen_success = self._try_reopen_parent(ai_matched_name, traverse_all_controls)
                        if reopen_success:
                            _, _, retry_result, _ = self.control_navigator.control_navigator(
                                is_recorded=False, is_located=True, locate_control_meta=ctrl_meta,
                                close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                            )
                            if retry_result:
                                LOGGER_INFO(
                                    f"[ai_fuzzy_match][action] ✅ Located '{ai_matched_name}' "
                                    f"after reopening parent", "GREEN"
                                )
                                return True
                            else:
                                LOGGER_WARNING(
                                    f"[ai_fuzzy_match][action] ⚠️ '{ai_matched_name}' still not found "
                                    f"after reopening parent, pressing ESC", "YELLOW"
                                )
                        else:
                            LOGGER_WARNING(
                                f"[ai_fuzzy_match][action] ⚠️ Could not find opener for "
                                f"'{ai_matched_name}', pressing ESC", "YELLOW"
                            )
                else:
                    # ai_matched_name is a parent opener:
                    # 1. Navigate to the opener
                    # 2. Press SPACE to open the parent panel
                    # 3. Locate the original target inside it - but use the EXACT UI name
                    #    (e.g. 'Best for text and images Not selected 2 of 3') so the navigator
                    #    matches by rule 1 (exact) and breaks before reaching any combobox.
                    LOGGER_INFO(f"[ai_fuzzy_match][action] 🔓 '{ai_matched_name}' is parent opener for '{target_control_name}' — navigating to opener first", "CYAN")
                    _, _, opener_nav_result, _ = self.control_navigator.control_navigator(
                        is_recorded=False, is_located=True, locate_control_meta=ctrl_meta,
                        close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                    )
                    if opener_nav_result:
                        LOGGER_INFO(f"[ai_fuzzy_match][action] Pressing SPACE to open parent via '{ai_matched_name}'", "CYAN")
                        auto.SendKeys("{SPACE}")
                        time.sleep(1.0)

                        # First attempt: navigate with the YAML target name.
                        # This may fail if the UI control name has extra suffix
                        # (e.g. 'Not selected 2 of 3'), causing partial-match rule 6.1
                        # but not rule 6.3 break, leading to combobox ESC closing the panel.
                        # We still capture fresh_controls to resolve the exact UI name.
                        target_meta = {
                            "name": target_control_name,
                            "id": "",
                            "test_case_step_description": target_control_name,
                            "control_type": None,
                            "control_type_name": None
                        }
                        _, fresh_controls, target_result, _ = self.control_navigator.control_navigator(
                            is_recorded=False, is_located=True, locate_control_meta=target_meta,
                            close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                        )
                        if target_result:
                            LOGGER_INFO(f"[ai_fuzzy_match][action] ✅ Located target '{target_control_name}' after opening parent '{ai_matched_name}'", "GREEN")
                            return True

                        # First attempt failed - try to resolve exact UI name from fresh_controls
                        # (e.g. 'Best for text and images Not selected 2 of 3')
                        exact_ui_name = None
                        for ctrl in (fresh_controls or []):
                            if ctrl and target_control_name.lower() in ctrl.lower():
                                exact_ui_name = ctrl
                                LOGGER_INFO(f"[ai_fuzzy_match][action] 🔍 Resolved exact UI name: '{exact_ui_name}' for target '{target_control_name}'", "CYAN")
                                break

                        if exact_ui_name and exact_ui_name != target_control_name:
                            # Re-navigate to opener and reopen the panel
                            LOGGER_INFO(f"[ai_fuzzy_match][action] Retrying with exact UI name '{exact_ui_name}', re-opening parent '{ai_matched_name}'", "CYAN")
                            _, _, opener_retry, _ = self.control_navigator.control_navigator(
                                is_recorded=False, is_located=True, locate_control_meta=ctrl_meta,
                                close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                            )
                            if opener_retry:
                                auto.SendKeys("{SPACE}")
                                time.sleep(1.0)
                                exact_meta = {
                                    "name": exact_ui_name,
                                    "id": "",
                                    "test_case_step_description": exact_ui_name,
                                    "control_type": None,
                                    "control_type_name": None
                                }
                                _, _, exact_result, _ = self.control_navigator.control_navigator(
                                    is_recorded=False, is_located=True, locate_control_meta=exact_meta,
                                    close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
                                )
                                if exact_result:
                                    LOGGER_INFO(f"[ai_fuzzy_match][action] ✅ Located via exact UI name '{exact_ui_name}' after reopening parent", "GREEN")
                                    return True
                                else:
                                    LOGGER_WARNING(f"[ai_fuzzy_match][action] ⚠️ Exact UI name '{exact_ui_name}' also failed after reopening parent, pressing ESC", "YELLOW")
                            else:
                                LOGGER_WARNING(f"[ai_fuzzy_match][action] ⚠️ Could not re-navigate to opener '{ai_matched_name}' for retry, pressing ESC", "YELLOW")
                        else:
                            LOGGER_WARNING(f"[ai_fuzzy_match][action] ⚠️ Target '{target_control_name}' not found after opening parent '{ai_matched_name}', pressing ESC", "YELLOW")
                    else:
                        LOGGER_WARNING(f"[ai_fuzzy_match][action] ⚠️ Could not navigate to opener '{ai_matched_name}', pressing ESC", "YELLOW")
            else:
                LOGGER_DEBUG(f"[ai_fuzzy_match][action] AI returned no match for '{target_control_name}'", "YELLOW")
            # Fallback: press ESC
            # auto.SendKeys("{ESC}")
            time.sleep(self.retry_delay)
            return False

        elif action_type in ("empty_controls", "control_not_found"):
            # Use OCR to check if the target control is visually present before pressing ESC
            is_visible = self._check_control_visible_by_ocr(target_control_name) if target_control_name else False
            if is_visible:
                # Control is visible on screen but keyboard traversal missed it — retry without ESC
                LOGGER_INFO(f"[operator][Locate][retry][ocr] OCR confirms '{target_control_name}' is visible, retrying without ESC", "GREEN")
            else:
                # Control is NOT visible — press ESC to dismiss potential overlay/dialog, then retry
                LOGGER_DEBUG(f"[operator][Locate][retry][ocr_esc] OCR confirms '{target_control_name}' is NOT visible, pressing ESC", "YELLOW")
                auto.SendKeys("{ESC}")
            time.sleep(self.retry_delay)
            
        else:
            # Default action for unknown types
            LOGGER_DEBUG(f"[operator][Locate][retry][default] Unknown action type, using default ESC", "YELLOW")
            auto.SendKeys("{ESC}")
            time.sleep(self.retry_delay)
        
        return False
    
    def _execute_backtrack_sequence(self, start_index, target_control_name):
        """Execute the backtrack sequence from start_index to target"""
        LOGGER_INFO(f"[backtrack][sequence][execute] Starting backtrack sequence execution", "GREEN")
        LOGGER_DEBUG(f"[backtrack][sequence][execute] Start index: {start_index}, Target: '{target_control_name}'", "CYAN")
        
        if not self.control_name_sequence:
            LOGGER_DEBUG(f"[backtrack][sequence][execute] No control sequence available", "RED")
            return False
        
        # Find target index
        target_index = None
        if target_control_name:
            target_name_clean = target_control_name.strip()
            try:
                target_index = [ctrl.strip() for ctrl in self.control_name_sequence].index(target_name_clean)
                LOGGER_DEBUG(f"[backtrack][sequence][execute] Target '{target_name_clean}' found at index {target_index}", "CYAN")
            except ValueError:
                LOGGER_DEBUG(f"[backtrack][sequence][execute] Target '{target_name_clean}' not found in sequence", "YELLOW")
                return False
        
        if target_index is None or start_index >= target_index:
            LOGGER_DEBUG(f"[backtrack][sequence][execute] Invalid sequence: start_index={start_index}, target_index={target_index}", "YELLOW")
            return False
        
        # Execute sequence from start_index to target_index
        LOGGER_INFO(f"[backtrack][sequence][execute] Executing sequence from {start_index} to {target_index}", "GREEN")
        LOGGER_DEBUG(f"[backtrack][sequence][execute] Total steps to execute: {target_index - start_index + 1}", "CYAN")
        
        for i in range(start_index, target_index + 1):
            control_name = self.control_name_sequence[i].strip()
            if not control_name:
                LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Skipping empty control name", "YELLOW")
                continue
                
            LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Locating control: '{control_name}'", "CYAN")
            LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Step type: {'INTERMEDIATE' if i < target_index else 'TARGET'}", "CYAN")
            
            # Get control type information from datasets
            # control_name here comes from YAML which should already be cleaned
            complete_metadata = get_complete_control_metadata_by_name(control_name, platform='windows')
            control_type = complete_metadata.get('control_type') if complete_metadata else None
            control_type_name = complete_metadata.get('control_type_name') if complete_metadata else None
            
            ctrl_meta = {
                "name": control_name,
                "id": "",  # Use empty ID for backtrack sequence
                "test_case_step_description": control_name,
                "control_type": control_type,
                "control_type_name": control_type_name
            }
            
            LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Control type: {control_type} ({control_type_name})", "CYAN")
            
            # Perform location without retry to avoid infinite loops
            LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Calling control_navigator for: '{control_name}'", "CYAN")
            _traverse_record_controls, traverse_all_controls, result, _control_metadata = self.control_navigator.control_navigator(
                is_recorded=False, is_located=True, locate_control_meta=ctrl_meta, 
                close_flag=False, locate_id_flag=True, test_case_flag=self.record_traversal
            )
            
            if result:
                LOGGER_INFO(f"[backtrack][sequence][execute][step {i}] ✅ Successfully located: '{control_name}'", "GREEN")
                
                # Execute action for intermediate steps (not the target step)
                if i < target_index:
                    LOGGER_INFO(f"[backtrack][sequence][execute][step {i}] Executing intermediate action for: '{control_name}'", "CYAN")
                    try:
                        # Execute default action (SPACE key) for intermediate steps
                        LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Sending SPACE key action", "CYAN")
                        auto.SendKeys("{SPACE}")
                        LOGGER_INFO(f"[backtrack][sequence][execute][step {i}] ✅ Executed SPACE action for: '{control_name}'", "GREEN")
                        # Delay to allow UI response
                        LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Waiting 1.0s for UI response", "CYAN")
                        time.sleep(1.0)
                    except Exception as e:
                        LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] ❌ Action execution failed for '{control_name}': {e}", "YELLOW")
                
                if i == target_index:
                    LOGGER_INFO(f"[backtrack][sequence][execute] 🎯 Successfully reached target: '{control_name}'", "GREEN")
                    LOGGER_INFO(f"[backtrack][sequence][execute] ✅ Backtrack sequence completed successfully", "GREEN")
                    return True
            else:
                LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] ❌ Failed to locate: '{control_name}'", "RED")
                LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Available controls: {traverse_all_controls}", "RED")
                LOGGER_INFO(f"[backtrack][sequence][execute] ❌ Backtrack sequence failed at step {i}", "RED")
                return False
            
            # Small delay between steps
            if i < target_index:
                LOGGER_DEBUG(f"[backtrack][sequence][execute][step {i}] Inter-step delay 0.5s", "CYAN")
                time.sleep(0.5)
        
        LOGGER_DEBUG(f"[backtrack][sequence][execute] ❌ Sequence completed but target not reached", "RED")
        
        return False
    
    def locate_control_handler_for_operator(self, control_meta, close_flag=False, locate_id_flag=True, is_optional=False):
        """Core control location logic with intelligent retry mechanism"""
        target_control_name = control_meta.get('name', 'Unknown')
        LOGGER_DEBUG(f"[operator][Locate][navigate][step 2]: [{target_control_name}]", "YELLOW")
        LOGGER_INFO(f"[operator][Locate][control_meta]: {control_meta}", "CYAN")
        LOGGER_DEBUG(f"[operator][Locate][sequence] Current sequence: {self.control_name_sequence}", "CYAN")
        LOGGER_DEBUG(f"[operator][Locate][sequence] Current step index: {self.current_step_index}", "CYAN")
        LOGGER_DEBUG(f"[operator][Locate][retry] Retry enabled: {self.enable_retry}", "CYAN")
        
        # For optional steps, only try once without retries
        # For disabled retry mode (test case validation), also only try once
        if is_optional or not self.enable_retry:
            max_attempts = 1
            if is_optional:
                LOGGER_DEBUG(f"[operator][Locate][navigate][optional]: Step is optional, limiting to single attempt", "CYAN")
            if not self.enable_retry:
                LOGGER_INFO(f"[operator][Locate][navigate][no_retry]: Retry disabled, using single attempt for validation", "YELLOW")
        else:
            max_attempts = self.max_retry_attempts
        
        for attempt in range(max_attempts):
            if attempt > 0:
                LOGGER_DEBUG(f"[operator][Locate][navigate][retry attempt {attempt + 1}/{max_attempts}]", "YELLOW")
            
            # OPTIMIZATION: Try intelligent backtrack BEFORE lengthy navigation if we have sequence
            # Only do pre-check if retry is enabled (not in test case validation mode)
            if attempt == 0 and self.control_name_sequence and not is_optional and self.enable_retry:
                # Pre-check: if we know we're in wrong place, try backtrack first
                LOGGER_DEBUG(f"[operator][Locate][pre_check] Checking if intelligent backtrack is viable before navigation", "CYAN")
                
                # Get current control state for quick assessment
                try:
                    # Quick control check to see current position
                    _traverse_record_controls, traverse_all_controls_quick, result_quick, _control_metadata = self.control_navigator.control_navigator(
                        is_recorded=False, is_located=True, locate_control_meta=control_meta, 
                        close_flag=close_flag, locate_id_flag=locate_id_flag, test_case_flag=self.record_traversal
                    )
                    
                    # If quick check fails and we have many controls, consider backtrack immediately
                    if not result_quick and len(traverse_all_controls_quick) >= 3:
                        should_retry, action_type, retry_reason = self._should_retry_location(
                            traverse_all_controls_quick, result_quick, target_control_name
                        )
                        
                        if should_retry and action_type == "intelligent_backtrack":
                            LOGGER_INFO(f"[operator][Locate][pre_backtrack] Pre-navigation backtrack triggered for '{target_control_name}'", "GREEN")
                            backtrack_success = self._perform_retry_action(action_type, retry_reason, 
                                                                         traverse_all_controls_quick, target_control_name)
                            if backtrack_success:
                                # Try again after backtrack
                                _traverse_record_controls, traverse_all_controls, result, _control_metadata = self.control_navigator.control_navigator(
                                    is_recorded=False, is_located=True, locate_control_meta=control_meta, 
                                    close_flag=close_flag, locate_id_flag=locate_id_flag, test_case_flag=self.record_traversal
                                )
                                if result:
                                    LOGGER_INFO(f"[operator][Locate][pre_backtrack][success] Target '{target_control_name}' located after pre-navigation backtrack", "GREEN")
                                    return traverse_all_controls, result
                            else:
                                # Backtrack failed in pre-check - try ai_fuzzy_match first, then reopen_parent
                                if self.retry_strategies_enabled.get("ai_fuzzy_match", True):
                                    LOGGER_INFO(f"[operator][Locate][pre_backtrack->ai_fuzzy_match] Backtrack failed, trying AI fuzzy match in pre-check", "YELLOW")
                                    fuzzy_success = self._perform_retry_action(
                                        "ai_fuzzy_match", "Fallback from failed pre-check backtrack",
                                        traverse_all_controls_quick, target_control_name
                                    )
                                    if fuzzy_success:
                                        # ai_fuzzy_match already located the target — do NOT re-navigate with original meta
                                        LOGGER_INFO(f"[operator][Locate][pre_backtrack][ai_fuzzy_match success] Target '{target_control_name}' located via AI fuzzy match", "GREEN")
                                        return traverse_all_controls_quick, True
                                    else:
                                        # AI fuzzy match failed — fallback to OCR + ESC in pre-check
                                        LOGGER_INFO(f"[operator][Locate][pre_backtrack->ocr_esc] AI fuzzy match failed in pre-check, falling back to OCR visibility check", "YELLOW")
                                        self._perform_retry_action("control_not_found", "Fallback from failed pre-check ai_fuzzy_match",
                                                                   traverse_all_controls_quick, target_control_name)
                                # [DISABLED] reopen_parent after ai_fuzzy_match failure
                                # if self.retry_strategies_enabled.get("reopen_parent", True):
                                #     LOGGER_INFO(f"[operator][Locate][pre_backtrack->reopen_parent] AI fuzzy match failed, trying to reopen parent for '{target_control_name}'", "YELLOW")
                                #     reopen_success = self._try_reopen_parent(target_control_name, traverse_all_controls_quick)
                                #     if reopen_success:
                                #         _, fresh_controls, fresh_result, _ = self.control_navigator.control_navigator(
                                #             is_recorded=False, is_located=True, locate_control_meta=control_meta,
                                #             close_flag=close_flag, locate_id_flag=locate_id_flag, test_case_flag=self.record_traversal
                                #         )
                                #         if fresh_result:
                                #             LOGGER_INFO(f"[operator][Locate][pre_backtrack][reopen_parent success] Target '{target_control_name}' located after reopening parent", "GREEN")
                                #             return fresh_controls, fresh_result

                        elif should_retry and action_type == "ai_fuzzy_match":
                            # P1 found no intersection, P1.5 triggered ai_fuzzy_match directly in pre-check
                            LOGGER_INFO(f"[operator][Locate][pre_check][ai_fuzzy_match] AI fuzzy match triggered in pre-check for '{target_control_name}'", "GREEN")
                            fuzzy_success = self._perform_retry_action(
                                "ai_fuzzy_match", retry_reason,
                                traverse_all_controls_quick, target_control_name
                            )
                            if fuzzy_success:
                                # ai_fuzzy_match already located the target — do NOT re-navigate with original meta
                                LOGGER_INFO(f"[operator][Locate][pre_check][ai_fuzzy_match success] Target '{target_control_name}' located via AI fuzzy match in pre-check", "GREEN")
                                return traverse_all_controls_quick, True
                            else:
                                # AI fuzzy match failed — fallback to OCR + ESC in pre-check
                                LOGGER_INFO(f"[operator][Locate][pre_check->ocr_esc] AI fuzzy match failed in pre-check, falling back to OCR visibility check", "YELLOW")
                                self._perform_retry_action("control_not_found", "Fallback from failed pre-check ai_fuzzy_match",
                                                           traverse_all_controls_quick, target_control_name)
                except Exception as e:
                    LOGGER_DEBUG(f"[operator][Locate][pre_check] Pre-check failed: {e}", "YELLOW")
            
            # Standard navigation attempt
            _traverse_record_controls, traverse_all_controls, result, _control_metadata = self.control_navigator.control_navigator(
                is_recorded=False, is_located=True, locate_control_meta=control_meta, 
                close_flag=close_flag, locate_id_flag=locate_id_flag, test_case_flag=self.record_traversal
            )
            
            # Log current traverse_all_controls for debugging
            LOGGER_DEBUG(f"[operator][Locate][traverse] Current controls: {traverse_all_controls}", "CYAN")
            
            # If successful, return immediately
            if result:
                LOGGER_DEBUG(f"[operator][Locate][navigate][success on attempt {attempt + 1}]", "GREEN")
                return traverse_all_controls, result
            
            # For optional steps, don't retry - return immediately after first attempt
            if is_optional:
                LOGGER_DEBUG(f"[operator][Locate][navigate][optional][no_retry]: Optional step failed on first attempt, not retrying", "CYAN")
                return traverse_all_controls, result
            
            # For disabled retry mode, don't retry - return immediately
            if not self.enable_retry:
                LOGGER_DEBUG(f"[operator][Locate][navigate][no_retry][disabled]: Retry disabled, returning result without retry", "YELLOW")
                return traverse_all_controls, result
            
            # Check if retry is needed (only for non-optional steps with retry enabled)
            should_retry, action_type, retry_reason = self._should_retry_location(traverse_all_controls, result, target_control_name)
            
            LOGGER_DEBUG(f"[operator][Locate][retry][check] should_retry: {should_retry}, action_type: {action_type}, reason: {retry_reason}", "YELLOW")
            
            if not should_retry:
                # No retry condition detected, return failure
                LOGGER_DEBUG(f"[operator][Locate][navigate][no retry needed on attempt {attempt + 1}]", "YELLOW")
                return traverse_all_controls, result
            
            # If this is the last attempt, don't perform retry actions
            if attempt == max_attempts - 1:
                LOGGER_DEBUG(f"[operator][Locate][navigate][max attempts reached]", "RED")
                return traverse_all_controls, result
            
            # Perform appropriate retry action based on the failure type
            if action_type in ["stale_data", "corrupted_data"]:
                # Use standard reset for these conditions
                self._perform_retry_reset(retry_reason or "Unknown retry condition")
            elif action_type == "intelligent_backtrack":
                # Use intelligent backtrack mechanism
                LOGGER_INFO(f"[operator][Locate][backtrack] Attempting intelligent backtrack for '{target_control_name}'", "GREEN")
                backtrack_success = self._perform_retry_action(action_type, retry_reason or "Unknown retry condition", 
                                                             traverse_all_controls, target_control_name)
                if backtrack_success:
                    # If backtrack was successful, the target should now be located
                    LOGGER_INFO(f"[operator][Locate][navigate][backtrack success]: Target '{target_control_name}' located via backtrack", "GREEN")
                    return traverse_all_controls, True
                else:
                    LOGGER_DEBUG(f"[operator][Locate][navigate][backtrack failed]: Backtrack unsuccessful for '{target_control_name}', falling back to ai_fuzzy_match then reopen_parent", "YELLOW")
                    # First try ai_fuzzy_match with currently visible controls
                    if self.retry_strategies_enabled.get("ai_fuzzy_match", True):
                        LOGGER_INFO(f"[operator][Locate][backtrack->ai_fuzzy_match] Trying AI fuzzy match as fallback after failed backtrack", "GREEN")
                        fuzzy_match_success = self._perform_retry_action(
                            "ai_fuzzy_match", "Fallback from failed intelligent_backtrack",
                            traverse_all_controls, target_control_name
                        )
                        if fuzzy_match_success:
                            LOGGER_INFO(f"[operator][Locate][navigate][ai_fuzzy_match fallback success]: Target located via AI fuzzy match", "GREEN")
                            return traverse_all_controls, True
                        else:
                            LOGGER_DEBUG(f"[operator][Locate][navigate][ai_fuzzy_match fallback failed]: AI fuzzy match also failed, trying reopen_parent", "YELLOW")
                    # If ai_fuzzy_match failed, try to reopen the parent panel (e.g. combobox ESC closed it)
                    if self.retry_strategies_enabled.get("reopen_parent", True):
                        LOGGER_INFO(f"[operator][Locate][backtrack->reopen_parent] Trying to reopen parent for '{target_control_name}'", "YELLOW")
                        reopen_success = self._try_reopen_parent(target_control_name, traverse_all_controls)
                        if reopen_success:
                            _, fresh_controls, fresh_result, _ = self.control_navigator.control_navigator(
                                is_recorded=False, is_located=True, locate_control_meta=control_meta,
                                close_flag=close_flag, locate_id_flag=locate_id_flag, test_case_flag=self.record_traversal
                            )
                            if fresh_result:
                                LOGGER_INFO(f"[operator][Locate][navigate][reopen_parent success]: Target '{target_control_name}' located after reopening parent", "GREEN")
                                return fresh_controls, fresh_result
                            else:
                                LOGGER_DEBUG(f"[operator][Locate][navigate][reopen_parent failed]: Could not locate target after reopening parent", "RED")
            elif action_type == "ai_fuzzy_match":
                # Use AI to find closest semantic match in control_name_ui_path
                LOGGER_INFO(f"[operator][Locate][ai_fuzzy_match] Attempting AI fuzzy match for '{target_control_name}'", "GREEN")
                fuzzy_match_success = self._perform_retry_action(action_type, retry_reason or "Unknown retry condition",
                                                                 traverse_all_controls, target_control_name)
                if fuzzy_match_success:
                    LOGGER_INFO(f"[operator][Locate][navigate][ai_fuzzy_match success]: Target located via AI fuzzy match", "GREEN")
                    return traverse_all_controls, True
                else:
                    # AI fuzzy match failed (e.g. similarity too low) — fallback to OCR + ESC
                    LOGGER_INFO(f"[operator][Locate][ai_fuzzy_match->ocr_esc] AI fuzzy match failed, falling back to OCR visibility check for '{target_control_name}'", "YELLOW")
                    self._perform_retry_action("control_not_found", "Fallback from failed ai_fuzzy_match",
                                               traverse_all_controls, target_control_name)
            else:
                # Use specific retry action for other conditions
                self._perform_retry_action(action_type, retry_reason or "Unknown retry condition", 
                                         traverse_all_controls, target_control_name)
        
        # Return the last attempt's result
        return traverse_all_controls, result
    
    def locate_control(self, locate_target: LocateTarget, locate_id_flag: bool, current_control) -> LocateResult:
        """Locate control based on target and return result"""
        ctrl_name = locate_target.name
        test_case_step_description = locate_target.test_case_step_description
        
        LOGGER_INFO(f"[operator][locate][start][step 0]: [{locate_target}]", "BLUE")
        LOGGER_DEBUG(f"[operator][locate][metadata][step 1]: [locate_id_flag:{locate_id_flag}] [{ctrl_name}], [{locate_target.id}]", "BLUE")

        # Check if navigated is False - if so, skip locate but extract current control metadata
        if not locate_target.navigated:
            LOGGER_INFO(f"[operator][locate][skip][navigated:false]: Skipping control location for '{test_case_step_description}' (navigated=false)", "CYAN")
            LOGGER_DEBUG(f"[operator][locate][skip][navigated:false]: Will execute action directly but extract current control metadata", "CYAN")
            
            # Extract current control metadata even when navigated is false
            # The extract_focused_control() method internally calls refresh(), so no need to call it here
            result = True
            control_metadata = self.metadata_processor.extract_focused_control()
            
            LOGGER_INFO(f"[operator][locate][result][{result}]: [skipped - navigated:false, extracted current control: {control_metadata.current_control_name}]", "YELLOW")
            
            return LocateResult(
                success=result,
                metadata=control_metadata,
                control_name=ctrl_name
            )

        if test_case_step_description in NO_LOCATE_CONTROLS or locate_target.action_type in NO_LOCATE_CONTROLS_ACTION_TYPE:
            result = True
            # Still extract current control metadata for function/api/shortcut actions
            control_metadata = self.metadata_processor.extract_focused_control()
            if locate_target.action_type == "function":
                LOGGER_DEBUG(f"[operator][locate][skip][function]: Skipping control location for function action_type, extracted current control: {control_metadata.current_control_name}", "CYAN")
            elif locate_target.action_type == "api":
                LOGGER_DEBUG(f"[operator][locate][skip][api]: Skipping control location for api action_type, extracted current control: {control_metadata.current_control_name}", "CYAN")
            elif locate_target.action_type == "shortcut":
                LOGGER_DEBUG(f"[operator][locate][skip][shortcut]: Skipping control location for shortcut action_type, extracted current control: {control_metadata.current_control_name}", "CYAN")
            elif locate_target.action_type == "acc_sequence":
                LOGGER_DEBUG(f"[operator][locate][skip][acc_sequence]: Skipping control location for acc_sequence action_type, extracted current control: {control_metadata.current_control_name}", "CYAN")
        else:
            # Get control type information from datasets
            # Use test_case_step_description (cleaned name) for lookup, not ctrl_name (which may have spaces)
            # test_case_step_description is the cleaned version from YAML, ctrl_name may come from UI with spaces
            lookup_name = test_case_step_description if test_case_step_description else ctrl_name
            complete_metadata = get_complete_control_metadata_by_name(lookup_name, platform='windows')
            control_type = complete_metadata.get('control_type') if complete_metadata else None
            control_type_name = complete_metadata.get('control_type_name') if complete_metadata else None
            
            if complete_metadata:
                LOGGER_DEBUG(f"[operator][locate][metadata][found]: '{lookup_name}' -> type={control_type} ({control_type_name})", "GREEN")
            else:
                LOGGER_DEBUG(f"[operator][locate][metadata][not_found]: No metadata found for '{lookup_name}'", "YELLOW")
            
            ctrl_meta = {
                "name": ctrl_name,
                "id": locate_target.id,
                "test_case_step_description": test_case_step_description,
                "control_type": control_type,
                "control_type_name": control_type_name,
                "match_mode": locate_target.match_mode,
                "similarity_threshold": locate_target.similarity_threshold
            }
            
            LOGGER_DEBUG(f"[operator][locate][metadata][control_type]: {control_type} ({control_type_name})", "CYAN")
            
            control_visited, result = self.locate_control_handler_for_operator(
                ctrl_meta, locate_id_flag=locate_id_flag, is_optional=locate_target.optional
            )
            
            # Refresh current control information
            current_control.refresh()
            
            if result:
                control_metadata = self.metadata_processor.extract_focused_control()
            else:
                # For optional controls or failed locate, still extract current control metadata
                if locate_target.optional:
                    LOGGER_INFO(f"[operator][locate][optional][failed]: Optional control '{ctrl_name}' not found, extracting current control metadata", "YELLOW")
                    control_metadata = self.metadata_processor.extract_focused_control()
                else:
                    control_metadata = FocusedControlMetadata()

        LOGGER_DEBUG(f"[operator][locate][result][{result}]: [current focus on control]", "YELLOW")
        
        return LocateResult(
            success=result,
            metadata=control_metadata,
            control_name=ctrl_name
        )

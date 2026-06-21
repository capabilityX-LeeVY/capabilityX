"""
Linux Control Handler - Platform-specific implementation for Linux/AT-SPI

This module provides control handling functionality for Linux
using AT-SPI (Assistive Technology Service Provider Interface).

Implementation uses pyatspi for accessibility control access and manipulation,
similar to how uiautomation works on Windows.
"""

import hashlib
import time
import pyatspi
from gi.repository import Atspi
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils.control_db import ControlDB


class ControlHandler:
    """
    Linux-specific control handler using AT-SPI.
    
    This class provides control handling functionality for Linux applications
    using the AT-SPI accessibility framework. It mirrors the Windows ControlHandler
    functionality but uses pyatspi for control access.
    
    Key Features:
    - Access controls via AT-SPI accessibility tree
    - Query control properties (name, role, description, accessible_id)
    - Generate control hashes and paths
    - Database integration for control tracking
    
    Note: Works with applications that expose AT-SPI accessibility interface.
    """
    
    def __init__(self):
        """Initialize the Linux control handler."""
        self.control_db = ControlDB()
        self.max_level = 100000
        LOGGER_INFO("[ControlHandler] Initialized with AT-SPI support", "GREEN")

    def is_control_unique(self, hash_value):
        """
        Check if a control hash is unique in the database.
        
        Args:
            hash_value (str): The hash value to check
            
        Returns:
            bool: True if unique, False if already exists
        """
        controls_hash = self.control_db.fetch_all_control_hashes()
        if hash_value in controls_hash:
            return False
        else:
            return True
    
    def close_fte_window(self):
        """
        Close FTE (First Time Experience) window using ESC key.
        
        On Linux, this simulates pressing the ESC key using AT-SPI.
        """
        try:
            # Generate ESC key event
            pyatspi.Registry.generateKeyboardEvent(
                pyatspi.KEY_SYM,  # Key symbol type
                'Escape',         # Key name
                pyatspi.KEY_PRESS # Key press action
            )
            time.sleep(0.1)
            pyatspi.Registry.generateKeyboardEvent(
                pyatspi.KEY_SYM,
                'Escape',
                pyatspi.KEY_RELEASE
            )
            LOGGER_INFO("[ControlHandler] Sent ESC key to close FTE window", "CYAN")
        except Exception as e:
            LOGGER_ERROR(f"[ControlHandler] Error sending ESC key: {e}")
    
    def get_control_Level(self, control_name):
        """
        Get the level of a control by its name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            int: Control level or max_level if not found
        """
        results = self.control_db.fetch_control_level_by_name(control_name)
        if results and results[0]:
            return results[0][0]
        return self.max_level
    
    def get_control_level2_window_name(self, control_name):
        """
        Get the WindowLevel2Name for a control.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: WindowLevel2Name if available, otherwise None
        """
        results = self.control_db.fetch_control_level2_window_name(control_name)
        return results[0][0] if results else None
    
    def get_control_id_by_name(self, control_name):
        """
        Get the automation/accessible ID by control name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: Accessible ID if available, otherwise None
        """
        results = self.control_db.fetch_control_automation_id_by_name(control_name)
        return results[0][0] if results else None

    def get_control_name_by_id(self, control_id):
        """
        Get control name by its accessible ID.
        
        Args:
            control_id (str): Accessible ID of the control
            
        Returns:
            str or None: Control name if available, otherwise None
        """
        results = self.control_db.fetch_control_name_by_id(control_id)
        return results[0][0] if results else None
    
    def get_control_toggle_state_by_control_path_hash(self, control_path_hash):
        """
        Get the toggle state of a control by its path hash.
        
        Args:
            control_path_hash (str): Hash of the control path
            
        Returns:
            bool or None: Toggle state if available, otherwise None
        """
        results = self.control_db.fetch_control_toggle_state_by_control_path_hash(control_path_hash)
        return results[0][0] if results else None
    
    def get_from_control_name(self, control_name):
        """
        Get the first FromControl name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: FromControl if available, otherwise None
        """
        results = self.control_db.fetch_from_control_name(control_name)
        return results[0][0] if results else None
    
    def get_last_from_control_name(self, control_name):
        """
        Get the last FromControl name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: FromControl if available, otherwise None
        """
        results = self.control_db.fetch_from_control_name(control_name)
        return results[-1][0] if results else None
    
    def get_process_id_by_control_name(self, control_name):
        """
        Get process ID by control name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            int or None: Process ID if available, otherwise None
        """
        results = self.control_db.fetch_process_id_by_contorl_name(control_name)
        return results[0][0] if results else None

    def get_control_level_by_control_id_hash(self, control_id_hash):
        """
        Get control level by control ID hash.
        
        Args:
            control_id_hash (str): Hash of the control ID
            
        Returns:
            int: Control level or max_level if not found
        """
        results = self.control_db.fetch_control_level_by_id_hash(control_id_hash)
        return results[0][0] if results else self.max_level
    
    def get_control_level_by_runtime_id(self, runtime_id):
        """
        Get control level by runtime ID (AT-SPI path).
        
        Args:
            runtime_id (list): Runtime ID components
            
        Returns:
            int: Control level or 100000 if not found
        """
        runtime_id_str = ",".join(map(str, runtime_id))
        LOGGER_DEBUG(f"runtime_id_str: {runtime_id_str}", "RED")
        results = self.control_db.fetch_control_level_by_runtime_id(runtime_id_str)
        if results is not None and len(results) > 0:
            return results[0][0]
        else:
            return 100000
    
    def get_control_runtime_id_by_automation_id(self, control_id):
        """
        Get runtime ID by accessible ID.
        
        Args:
            control_id (str): Accessible ID
            
        Returns:
            str or None: Runtime ID if available, otherwise None
        """
        results = self.control_db.fetch_runtime_id_by_control_id(control_id)
        return results[0][0] if results else None
    
    def get_control_level_by_name_prefix(self, prefix_name):
        """
        Get control level by name prefix.
        
        Args:
            prefix_name (str): Prefix of the control name
            
        Returns:
            int: Control level or 100000 if not found
        """
        results = self.control_db.fetch_control_level_by_name_prefix(prefix_name)
        if results is not None and len(results) > 0:
            return results[0][0]
        else:
            return 100000

    def get_control_is_validated(self, control_name):
        """
        Check if a control is validated.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            bool or None: Validation status, or None if not found
        """
        results = self.control_db.fetch_control_is_validated(control_name)
        return results[0][0] if results else None
    
    def get_control_is_validated_prefix(self, control_name):
        """
        Check if controls with name prefix are validated.
        
        Args:
            control_name (str): Control name prefix
            
        Returns:
            list or None: List of validation statuses, or None if not found
        """
        results = self.control_db.fetch_control_is_validated_prefix(control_name)
        return results if results else None
    
    def get_control_is_validated_by_control_id(self, control_id):
        """
        Check if a control is validated by its ID.
        
        Args:
            control_id (str): Accessible ID
            
        Returns:
            bool or None: Validation status, or None if not found
        """
        results = self.control_db.fetch_control_is_validated_by_control_id(control_id)
        return results[0][0] if results else None
    
    def get_control_is_validated_by_runtime_id(self, runtime_id):
        """
        Check if a control is validated by its runtime ID.
        
        Args:
            runtime_id (list): Runtime ID components
            
        Returns:
            bool or None: Validation status, or None if not found
        """
        runtime_id_str = ",".join(map(str, runtime_id))
        results = self.control_db.fetch_control_is_validated_by_runtime_id(runtime_id_str)
        return results[0][0] if results else None
    
    def get_control_is_validated_by_control_path_hash(self, control_path_hash):
        """
        Check if a control is validated by its path hash.
        
        Args:
            control_path_hash (str): Hash of the control path
            
        Returns:
            bool or None: Validation status, or None if not found
        """
        results = self.control_db.fetch_control_is_validated_by_control_path_hash(control_path_hash)
        return results[0][0] if results else None
    
    def get_control_type_by_name(self, control_name):
        """
        Get control type (role) by name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: Control type/role, or None if not found
        """
        results = self.control_db.fetch_control_type_by_name(control_name)
        return results[0][0] if results else None
    
    def get_control_name_by_window(self, control_name):
        """
        Get all control names in a window.
        
        Args:
            control_name (str): Window name
            
        Returns:
            list: List of control names
        """
        results = self.control_db.fetch_control_name_by_window(control_name)
        return [row[0] for row in results]
    
    def get_control_window_name(self, control_name):
        """
        Get window name for a control.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: Window name, or None if not found
        """
        results = self.control_db.fetch_control_window_name_by_name(control_name)
        return results[-1][0] if results else None

    def get_control_window_automation_id(self, control_name):
        """
        Get window accessible ID.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: Window accessible ID, or None if not found
        """
        results = self.control_db.fetch_control_window_automation_id_by_control_name(control_name)
        return results[0][0] if results else None

    def get_control_id_hash(self, control_name):
        """
        Get control ID hash by name.
        
        Args:
            control_name (str): Name of the control
            
        Returns:
            str or None: Control ID hash, or None if not found
        """
        results = self.control_db.fetch_control_id_hash_by_name(control_name)
        # Special handling for certain controls
        from config.config import MORE
        if control_name in ["More options", "Share", "Record"]:
            return results[0][0] if results else None
        if control_name in MORE:
            return results[0][0] if results else None
        return results[-1][0] if results else None
    
    def get_control_Level_by_prefix_name(self, control_name):
        """
        Get control level by prefix name with special logic.
        
        Args:
            control_name (str): Control name prefix
            
        Returns:
            int: Control level or 100000 if not found
        """
        results = self.control_db.fetch_control_level_by_name_prefix(control_name)
        automationid_results = self.control_db.fetch_control_automation_id_by_name(control_name)

        LOGGER_DEBUG(f"get_control_Level_prefix:[{len(results) > 1 and automationid_results == 1}][{len(results)}][{len(automationid_results)}] [{control_name}] [{results}] [{automationid_results}]", "RED")
        if len(results) > 1 and len(automationid_results) == 1:
            LOGGER_DEBUG(f"get_control_Level_prefix [0][0]:[{results[0][0]}]", "RED")
            return results[0][0]
        if results is not None and len(results) > 0:
            LOGGER_DEBUG(f"get_control_Level_prefix [-1][0]:[{results[-1][0]}]", "RED")
            return results[-1][0]
        else:
            return 100000
    
    def get_control_Level_by_prefix_name_and_id(self, control_name, control_id):
        """
        Get control level by prefix name and ID.
        
        Args:
            control_name (str): Control name prefix
            control_id (str): Accessible ID
            
        Returns:
            int: Control level or 1 if not found
        """
        if control_id is not None:
            results = self.control_db.fetch_control_level_by_name_prefix_and_id(control_name, control_id)
        else:
            results = self.control_db.fetch_control_level_by_name_prefix(control_name)
        
        if results is not None and len(results) > 0:
            LOGGER_DEBUG(f"get_control_Level_prefix results[0][0]:[{results[0][0]}]", "RED")
            return results[0][0]
        else:
            return 1
    
    def get_control_Level_by_control_id(self, control_name):
        """
        Get control level by control ID.
        
        Args:
            control_name (str): Control ID
            
        Returns:
            int or None: Control level, or None if not found
        """
        results = self.control_db.fetch_control_level_by_control_id(control_name)
        LOGGER_DEBUG(f"get_control_Level_by_control_id:[{results}]", "RED")
        return results[0][0] if results else None
    
    def get_root_control_pid(self):
        """
        Get the root control process ID.
        
        Returns:
            int or None: Process ID, or None if not found
        """
        results = self.control_db.fetch_root_process_id()
        return results[0][0] if results else None
   
    def is_all_Control_is_validated_in_window(self, window_name):
        """
        Check if all controls in a window are validated.
        
        Args:
            window_name (str): Name of the window
            
        Returns:
            bool: True if all controls are validated, False otherwise
        """
        results = self.control_db.fetch_is_validated_by_window_name(window_name)
        return all(row[0] != 0 for row in results) if results else True

    def is_all_control_is_validated_in_window_level2(self, window_name):
        """
        Check if all controls in a WindowLevel2 are validated.
        
        Args:
            window_name (str): Name of the window level 2
            
        Returns:
            bool: True if all controls are validated, False otherwise
        """
        results = self.control_db.fetch_control_is_validated_by_window_level2(window_name)
        return all(row[0] != 0 for row in results) if results else True

    def get_control_window_name_by_control_id_hash(self, control_id_hash):
        """
        Get window name by control ID hash.
        
        Args:
            control_id_hash (str): Hash of the control ID
            
        Returns:
            str or None: Window name, or None if not found
        """
        results = self.control_db.fetch_control_window_name_by_control_id_hash(control_id_hash)
        return results[0][0] if results else None
    
    def get_control_level2_window_name_by_control_id_hash(self, control_id_hash):
        """
        Get WindowLevel2Name by control ID hash.
        
        Args:
            control_id_hash (str): Hash of the control ID
            
        Returns:
            str or None: WindowLevel2Name, or None if not found
        """
        results = self.control_db.fetch_control_level2_window_name_by_control_id_hash(control_id_hash)
        return results[0][0] if results else None
    
    def generate_control_path_hash(self, control_name, from_control):
        """
        Generate a hash for the control path.
        
        Args:
            control_name (str): Name of the control
            from_control (str): Parent control name
            
        Returns:
            str: SHA-256 hash of the control path
        """
        combined_string = f"{control_name}:{from_control}"
        hash_object = hashlib.sha256(combined_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        return hash_hex
    
    def generate_optimal_control_path(self, current_control_level, target_control_name):
        """
        Generate optimal path to reach a target control.
        
        Args:
            current_control_level (int): Current control level
            target_control_name (str): Target control name
            
        Returns:
            list: Optimal control path
        """
        optimal_control_path = self.control_db.fetch_control_optimal_path(current_control_level, target_control_name)
        return optimal_control_path
    
    def generate_optimal_control_second_path(self, current_control_level, target_control_name):
        """
        Generate second optimal path to reach a target control.
        
        Args:
            current_control_level (int): Current control level
            target_control_name (str): Target control name
            
        Returns:
            list: Second optimal control path
        """
        optimal_control_path = self.control_db.fetch_control_optimal_second_path(current_control_level, target_control_name)
        return optimal_control_path
    
    def generate_ui_path_by_index(self, control_index, start_level):
        """
        Generate UI path by control index and start level.
        
        Args:
            control_index (int): Control index
            start_level (int): Start level for the path
            
        Returns:
            list: UI path from start_level
        """
        optimal_control_path = self.control_db.fetch_ui_path_by_index(control_index)
        
        LOGGER_DEBUG(f"generate_ui_path_by_index: [{control_index}][{start_level}][{optimal_control_path}]", "RED")
        LOGGER_DEBUG(f"generate_ui_path_by_index: FULL PATH [{optimal_control_path}]", "RED")
        LOGGER_DEBUG(f"generate_ui_path_by_index: optimal_control_path [{optimal_control_path[start_level-1:]}]", "RED")

        if start_level < 0 or start_level > len(optimal_control_path):
            LOGGER_ERROR(f"Invalid start_level: {start_level}. Return Full Path: [{optimal_control_path}].", "RED")
            return optimal_control_path
        return optimal_control_path[start_level-1:]
    
    def generate_optimal_control_all_path(self, current_control_level, target_control_name):
        """
        Generate all possible paths to reach a target control.
        
        Args:
            current_control_level (int): Current control level
            target_control_name (str): Target control name
            
        Returns:
            list: All UI paths
        """
        optimal_control_path = self.control_db.fetch_all_ui_paths_any_level(target_control_name)
        return optimal_control_path
    
    def generate_optimal_control_min_path(self, current_control_level, target_control_name):
        """
        Generate minimum level UI path to reach a target control.
        
        Args:
            current_control_level (int): Current control level
            target_control_name (str): Target control name
            
        Returns:
            list: Minimum level UI path
        """
        optimal_control_path = self.control_db.fetch_min_level_ui_path(target_control_name)
        return optimal_control_path
    
    def extract_prefix(self, string):
        """
        Extract prefix from a control name string.
        
        Args:
            string (str): Control name string
            
        Returns:
            str: Extracted prefix
        """
        parts = string.split(', ')
        if len(parts) >= 2:
            prefix = ', '.join(parts[:2])
        else:
            prefix = ', '.join(parts[:-1])
        if prefix == '':
            return string
        return prefix

    def are_controls_same(self, control1, control2):
        """
        Check if two controls are the same based on their key parts.
        
        Args:
            control1 (str): First control name
            control2 (str): Second control name
            
        Returns:
            bool: True if controls are the same, False otherwise
        """
        key_part1 = self.extract_up_to_second_comma(control1)
        key_part2 = self.extract_up_to_second_comma(control2)
        return key_part1 == key_part2

    def extract_key_part(self, control_name):
        """
        Extract key part from control name (Level to Tab).
        
        Args:
            control_name (str): Control name
            
        Returns:
            str: Extracted key part or empty string
        """
        try:
            start_index = control_name.find("Level")
            end_index = control_name.find("Tab") + len("Tab")
            if start_index != -1 and end_index != -1 and start_index < end_index:
                return control_name[start_index:end_index].strip()
            return ""
        except Exception as e:
            LOGGER_ERROR(f"[ERROR] Failed to extract key part: {e}")
            return ""
    
    def extract_up_to_second_comma(self, text: str) -> str:
        """
        Extract text up to the second comma.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text up to second comma
        """
        if not text:
            return ""
        if "、" not in text and ", " not in text:
            return text
        text = text.replace("、", ", ")
        parts = text.split(", ")
        if len(parts) < 2:
            return text
        return ", ".join(parts[:2])
    
    def normalize_control_tree_name(self, control_name):
        """
        Normalize control tree name to first three words.
        
        Args:
            control_name (str): Control name
            
        Returns:
            str or None: Normalized name or None
        """
        first_three_words = self.extract_first_three_words(control_name)
        if first_three_words and first_three_words.strip() and len(first_three_words.split()) == 3:
            return first_three_words
        return None
    
    def normalize_control_tree_name_back(self, control_name):
        """
        Normalize control tree name backwards (up to four parts, remove last word).
        
        Args:
            control_name (str): Control name
            
        Returns:
            str: Normalized name
        """
        key_part = self.extract_up_to_four_parts(control_name)
        key_part_trimmed = self.remove_last_word(key_part)
        return key_part_trimmed if key_part_trimmed.strip() else key_part

    def extract_first_three_words(self, text):
        """
        Extract the first three words from a text string.
        
        Args:
            text (str): Input text
            
        Returns:
            str: First three words or less if fewer words available
        """
        if not text:
            return ""
        words = text.split()
        if len(words) >= 3:
            return " ".join(words[:3])
        elif len(words) >= 2:
            return " ".join(words[:2])
        elif len(words) == 1:
            return words[0]
        return ""

    def are_controls_tree_same(self, control1, control2):
        """
        Check if two controls are the same based on their first three words.
        
        Args:
            control1 (str): First control name
            control2 (str): Second control name
            
        Returns:
            bool: True if controls are the same, False otherwise
        """
        first_three_words1 = self.extract_first_three_words(control1)
        first_three_words2 = self.extract_first_three_words(control2)
        return first_three_words1 == first_three_words2
    
    def extract_up_to_four_parts(self, text):
        """
        Extract up to four comma-separated parts.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with up to four parts
        """
        if not text:
            return ""
        parts = text.split(", ")
        if len(parts) > 4:
            return ", ".join(parts[:4])
        return text
    
    def remove_last_word(self, text):
        """
        Remove the last word from text.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text without last word
        """
        if not text:
            return ""
        words = text.split()
        if len(words) > 1:
            return " ".join(words[:-1])
        return text

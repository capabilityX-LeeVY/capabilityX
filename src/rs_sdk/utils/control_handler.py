import hashlib
import uiautomation as auto
import time
import psutil
import re

from config.config import *
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils.control_db import ControlDB

class ControlHandler:
    def __init__(self):
        self.control_db = ControlDB()
        self.max_level = 100000

    def is_control_unique(self, hash_value):
        controls_hash = self.control_db.fetch_all_control_hashes()
        if hash_value in controls_hash:
            return False
        else:
            return True
        
    def close_fte_window(self):
        auto.SendKeys("{ESC}")
        
    def get_control_Level(self, control_name):   
        results = self.control_db.fetch_control_level_by_name(control_name)
        if results and results[0]:  
            return results[0][0]
        return self.max_level
        
    def get_control_level2_window_name(self, control_name):
        """Return the first WindowLevel2Name if available, otherwise None."""
        results = self.control_db.fetch_control_level2_window_name(control_name)
        return results[0][0] if results else None
        
    def get_control_id_by_name(self, control_name):
        """Return the first AutomationId if available, otherwise None."""
        results = self.control_db.fetch_control_automation_id_by_name(control_name)
        return results[0][0] if results else None

    def get_control_name_by_id(self, control_id):
        """Return the first ControlName if available, otherwise None."""
        results = self.control_db.fetch_control_name_by_id(control_id)
        return results[0][0] if results else None
    
    def get_control_toggle_state_by_control_path_hash(self, control_path_hash):
        """Return the first AutomationId if available, otherwise None."""
        results = self.control_db.fetch_control_toggle_state_by_control_path_hash(control_path_hash)
        return results[0][0] if results else None
        
    def get_from_control_name(self, control_name):
        """Return the first FromControl if available, otherwise None."""
        results = self.control_db.fetch_from_control_name(control_name)
        return results[0][0] if results else None
    
    def get_last_from_control_name(self, control_name):
        """Return the last FromControl if available, otherwise None."""
        results = self.control_db.fetch_from_control_name(control_name)
        return results[-1][0] if results else None
    
    def get_process_id_by_control_name(self, control_name):
        """Return the first ProcessId if available, otherwise None."""
        results = self.control_db.fetch_process_id_by_contorl_name(control_name)
        return results[0][0] if results else None

    def get_control_level_by_control_id_hash(self, control_id_hash):
        """Return the Level based on control_id_hash, or 100000 if not found."""
        results = self.control_db.fetch_control_level_by_id_hash(control_id_hash)
        return results[0][0] if results else self.max_level
    
    def get_control_level_by_runtime_id(self, runtime_id):
        runtime_id_str = ",".join(map(str, runtime_id))
        LOGGER_DEBUG(f"runtime_id_str: {runtime_id_str}", "RED")
        results = self.control_db.fetch_control_level_by_runtime_id(runtime_id_str)
        if results is not None and len(results) > 0:
            return results[0][0]
        else:
            return 100000
        
    def get_control_runtime_id_by_automation_id(self, control_id):
        """Return the RuntimeId based on control_id, or None if not found."""
        results = self.control_db.fetch_runtime_id_by_control_id(control_id)
        return results[0][0] if results else None
        
    def get_control_level_by_name_prefix(self, prefix_name):
        results = self.control_db.fetch_control_level_by_name_prefix(prefix_name)
        if results is not None and len(results) > 0:
            return results[0][0]
        else:
            return 100000

    def get_control_is_validated(self, control_name):
        """Return the is_validated status, or None if not found."""
        results = self.control_db.fetch_control_is_validated(control_name)
        return results[0][0] if results else None
    
    def get_control_is_validated_prefix(self, control_name):
        """Return the is_validated status, or None if not found."""
        results = self.control_db.fetch_control_is_validated_prefix(control_name)
        # return results[0][0] if results else None
        return results if results else None
    
    def get_control_is_validated_by_control_id(self, control_id):
        """Return the is_validated status, or None if not found."""
        results = self.control_db.fetch_control_is_validated_by_control_id(control_id)
        return results[0][0] if results else None
    
    def get_control_is_validated_by_runtime_id(self, runtime_id):
        """Return the is_validated status, or None if not found."""
        runtime_id_str = ",".join(map(str, runtime_id))
        results = self.control_db.fetch_control_is_validated_by_runtime_id(runtime_id_str)
        return results[0][0] if results else None
    
    def get_control_is_validated_by_control_path_hash(self, control_path_hash):
        """Return the is_validated status based on control_path_hash, or None if not found."""
        results = self.control_db.fetch_control_is_validated_by_control_path_hash(control_path_hash)
        return results[0][0] if results else None
        
    def get_control_type_by_name(self, control_name):
        """Return the ControlType based on control_name, or None if not found."""
        results = self.control_db.fetch_control_type_by_name(control_name)
        return results[0][0] if results else None
        
    def get_control_name_by_window(self, control_name):
        results = self.control_db.fetch_control_name_by_window(control_name)
        return [row[0] for row in results]
    
    def get_control_window_name(self, control_name):
        results = self.control_db.fetch_control_window_name_by_name(control_name)
        return results[-1][0] if results else None

    def get_control_window_automation_id(self, control_name):
        """Return the WindowAutomationId based on control_name, or None if not found."""
        results = self.control_db.fetch_control_window_automation_id_by_control_name(control_name)
        return results[0][0] if results else None

    def get_control_id_hash(self, control_name):
        """Return the control_id_hash based on control_name, or None if not found."""
        results = self.control_db.fetch_control_id_hash_by_name(control_name)
        if control_name in ["More options", "Share", "Record"]:
            return results[0][0] if results else None
        if control_name in MORE:
            return results[0][0] if results else None
        return results[-1][0] if results else None
    
    def get_control_Level_by_prefix_name(self, control_name):
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
        results = self.control_db.fetch_control_level_by_control_id(control_name)
        LOGGER_DEBUG(f"get_control_Level_by_control_id:[{results}]", "RED")
        return results[0][0] if results else None
        
    
    def get_root_control_pid(self):
        results = self.control_db.fetch_root_process_id()
        return results[0][0] if results else None
   
    def is_all_Control_is_validated_in_window(self, window_name):
        results = self.control_db.fetch_is_validated_by_window_name(window_name)
        # LOGGER_DEBUG(f"{window_name} is_validated is {results}, {all(row[0] != 0 for row in results)}", "RED")
        return all(row[0] != 0 for row in results) if results else True

    def is_all_control_is_validated_in_window_level2(self, window_name):
        """Check if all controls in a WindowLevel2 are validated (i.e., no is_validated = 0)."""
        results = self.control_db.fetch_control_is_validated_by_window_level2(window_name)
        return all(row[0] != 0 for row in results) if results else True

    def get_control_window_name_by_control_id_hash(self, control_id_hash):
        """Return the WindowName based on control_id_hash, or None if not found."""
        results = self.control_db.fetch_control_window_name_by_control_id_hash(control_id_hash)
        return results[0][0] if results else None
        
    def get_control_level2_window_name_by_control_id_hash(self, control_id_hash):
        """Return the WindowLevel2Name based on control_id_hash, or None if not found."""
        results = self.control_db.fetch_control_level2_window_name_by_control_id_hash(control_id_hash)
        return results[0][0] if results else None
        
    def generate_control_path_hash(self, control_name, from_control):
        combined_string = f"{control_name}:{from_control}"
        hash_object = hashlib.sha256(combined_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        return hash_hex
    
    def generate_optimal_control_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_db.fetch_control_optimal_path(current_control_level, target_control_name)
        return optimal_control_path
    
    def generate_optimal_control_second_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_db.fetch_control_optimal_second_path(current_control_level, target_control_name)
        return optimal_control_path
    
    def generate_ui_path_by_index(self, control_index, start_level):
        optimal_control_path = self.control_db.fetch_ui_path_by_index(control_index)
        
        LOGGER_DEBUG(f"generate_ui_path_by_index: [{control_index}][{start_level}][{optimal_control_path}]", "RED")
        LOGGER_DEBUG(f"generate_ui_path_by_index: FULL PATH [{optimal_control_path}]", "RED")
        LOGGER_DEBUG(f"generate_ui_path_by_index: optimal_control_path [{optimal_control_path[start_level-1:]}]", "RED")

        if start_level < 0 or start_level > len(optimal_control_path):
            LOGGER_ERROR(f"Invalid start_level: {start_level}. Return Full Path: [{optimal_control_path}].", "RED")
            return optimal_control_path
        return optimal_control_path[start_level-1:]
    
    def generate_optimal_control_all_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_db.fetch_all_ui_paths_any_level(target_control_name)
        return optimal_control_path
    
    def generate_optimal_control_min_path(self, current_control_level, target_control_name):
        optimal_control_path = self.control_db.fetch_min_level_ui_path(target_control_name)
        return optimal_control_path
    
    def extract_prefix(self, string):
        parts = string.split(', ')
        if len(parts) >= 2:
            prefix = ', '.join(parts[:2])
        else:
            prefix = ', '.join(parts[:-1])
        if prefix == '':
            return string
        return prefix

    def are_controls_same(self, control1, control2):
        key_part1 = self.extract_up_to_second_comma(control1)
        key_part2 = self.extract_up_to_second_comma(control2)
        return key_part1 == key_part2

    def extract_key_part(self, control_name):
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
        first_three_words = self.extract_first_three_words(control_name)
        if first_three_words and first_three_words.strip() and len(first_three_words.split()) == 3:
            return first_three_words
    
    def normalize_control_tree_name_back(self, control_name):
        key_part = self.extract_up_to_four_parts(control_name)
        key_part_trimmed = self.remove_last_word(key_part)
        return key_part_trimmed if key_part_trimmed.strip() else key_part

    def extract_first_three_words(self, text):
        """Extract the first three words from a text string."""
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
        first_three_words1 = self.extract_first_three_words(control1)
        first_three_words2 = self.extract_first_three_words(control2)
        
        if first_three_words1 == first_three_words2 and first_three_words1.strip():
            return True
        
        return False
    
    def are_controls_tree_same_bak(self, control1, control2):
        key_part1 = self.extract_up_to_four_parts(control1)
        key_part2 = self.extract_up_to_four_parts(control2)
        
        if key_part1 == key_part2:
            return True
        
        if key_part1 and key_part2:
            key_part1_trimmed = self.remove_last_word(key_part1)
            key_part2_trimmed = self.remove_last_word(key_part2)
            
            if key_part1_trimmed == key_part2_trimmed and key_part1_trimmed.strip():
                return True
        
        return False
    
    def remove_last_word(self, text: str) -> str:
        if not text:
            return ""
        
        text = text.strip()
        if not text:
            return ""
        
        import re
        match = re.search(r'\s+\S+$', text)
        
        if match:
            return text[:match.start()]
        else:
            return ""
        
    def extract_up_to_four_parts(self, text: str) -> str:
        if not text:
            return ""
        if "、" not in text and ", " not in text:
            return text
        text = text.replace("、", ", ")
        parts = text.split(", ")
        if len(parts) < 4:
            return text
        return ", ".join(parts[:4])

    
    def remove_first_segment(self, text):
        first_dot_index = text.find('.')
        if first_dot_index != -1:
            return text[first_dot_index + 1:]
        return text
        
    def focus_on_meeting_main_window(self):
        auto.SendKeys("{Esc}")
        time.sleep(1)
        auto.SendKeys("{Esc}")
        time.sleep(1)
        main_meeting_window = auto.WindowControl(searchDepth=1, AutomationId=CALLWINDOWAUTOID)
        children = main_meeting_window.GetChildren()
        # time.sleep(2)

        for child in children:
            if child.AutomationId == CALLCONTROLBARAUTOID:
                child.SetFocus()
                # focused_control = auto.GetFocusedControl()
                subchildrens = child.GetChildren()
                for subchild in subchildrens:
                    if subchild.AutomationId == AUDIOCONTROLAUTOID:
                        subchild.SetFocus()
                        time.sleep(2)
                        break
                break

    def focus_on_webex_agreement_window(self, window_autoids=None, target_automation_ids=None):
        if window_autoids is None:
            window_autoids = ["EulaAgreementWindow", "SparkApp.EulaAgreementWindow"]
        if target_automation_ids is None:
            target_automation_ids = ["EulaAgreementWindow.applyButton", "SparkApp.EulaAgreementWindow.applyButton"]

        for window_autoid in window_autoids:
            main_meeting_window = auto.WindowControl(searchDepth=1, AutomationId=window_autoid)
            if not main_meeting_window.Exists(3):
                print(f"Window with AutomationId '{window_autoid}' not found.")
                continue

            main_meeting_window.SetActive()
            time.sleep(2)
            for i in range(10):
                current_control = auto.GetFocusedControl()
                if current_control and current_control.AutomationId in target_automation_ids:
                    current_control.SetFocus()
                    auto.SendKeys("{Space}")
                    time.sleep(2)
                    return
                print(f"Focused Control: {current_control.Name if current_control else 'None'}")
                auto.SendKeys("{Tab}")
                time.sleep(1)

        LOGGER_INFO("Failed to find the agreement button in any of the candidate windows.")

    def focus_on_webex_app_window(self, target_automation_id, window_automation_id=MAINWINDOW, searchDepth=1):
        main_meeting_window = auto.WindowControl(searchDepth=searchDepth, window_automation_id=window_automation_id)
        LOGGER_INFO(f"Main Meeting Window: {main_meeting_window.Name}", "RED")
        main_meeting_window.SetActive()
        target_control = self.find_nested_control(main_meeting_window, target_automation_id)
        LOGGER_INFO(f"Target Control: {target_control}", "RED")
        if target_control:
            target_control.SetFocus()
            time.sleep(2)
        else:
            print(f"Control with AutomationId {target_automation_id} not found.")

    def get_pid_by_name(self, process_name= "CiscoCollabHost.exe"):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == process_name:
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def focus_on_window_by_pid(self, pid, target_automation_id, window_automation_id= MAINWINDOW, searchDepth=1):
        window = auto.WindowControl(searchDepth=searchDepth, AutomationId=window_automation_id, ProcessId=pid)

        if not window.Exists():
            print(f"cannot find PID={pid} and AutomationId={window_automation_id}")
            return

        LOGGER_INFO(f"Main Meeting Window: {window.Name}", "RED")
        window.SetActive()

        target_control = self.find_nested_control(window, target_automation_id)
        LOGGER_INFO(f"Target Control: {target_control}", "RED")

        if target_control:
            target_control.SetFocus()
            time.sleep(2)
        else:
            print(f"Control with AutomationId {target_automation_id} not found.")

    def focus_on_window_by_pid_autoid(self, pid, window_automation_id= MAINWINDOW, searchDepth=1):
        window = auto.WindowControl(searchDepth=searchDepth, AutomationId=window_automation_id, ProcessId=pid)

        if not window.Exists():
            LOGGER_ERROR(f"cannot find PID={pid} and AutomationId={window_automation_id}")
            return

        LOGGER_INFO(f"Connect pid automation id window: {window.Name}, and the auto id is {window_automation_id}", "RED")
        window.SetActive()

    def focus_on_window_by_pid_autoid_contains(self, pid, window_automation_id= MAINWINDOW, searchDepth=1):
        root = auto.GetRootControl()
        windows = root.GetChildren()
        
        target_window = None
        for window in windows:
            if window.ProcessId == pid:
                if window.AutomationId and window_automation_id in window.AutomationId:
                    target_window = window
                    break
        
        if not target_window:
            LOGGER_ERROR(f"cannot find PID={pid} with AutomationId containing '{window_automation_id}'")
            return

        LOGGER_INFO(f"Connect pid automation id window: {target_window.Name}, and the auto id is {target_window.AutomationId}", "RED")
        window_control = auto.WindowControl(searchDepth=searchDepth, AutomationId=target_window.AutomationId, ProcessId=pid)
        if window_control.Exists():
            window_control.SetActive()
        else:
            LOGGER_ERROR(f"Failed to activate window with AutomationId={target_window.AutomationId}, PID={pid}")

    def get_main_window_info_by_pid(self, pid, searchDepth=1):
        """
        Returns a tuple (window_name, automation_id) for the main window of the given pid.
        If not found, returns (None, None).
        """
        root = auto.GetRootControl()
        windows = root.GetChildren()
        found = False

        for window in windows:
            if window.ProcessId == pid:
                found = True
                LOGGER_DEBUG(f"Found window: Name='{window.Name}', ClassName='{window.ClassName}', IsTopLevel={window.IsTopLevel}", "YELLOW")

        if not found:
            LOGGER_WARNING(f"No windows found for PID={pid}", "YELLOW")
            return None, None

        target_windows = []
        for window in windows:
            if window.ProcessId == pid:
                target_windows.append(window)

        if not target_windows:
            LOGGER_ERROR(f"Cannot find any window for PID={pid}")
            return None, None

        for window in target_windows:
            if window.IsTopLevel and window.Name and len(window.Name.strip()) > 0:
                LOGGER_INFO(f"Found main window: {window.Name}, AutomationId: {window.AutomationId}", "GREEN")
                return window.Name, window.AutomationId

        for window in target_windows:
            if window.Name and len(window.Name.strip()) > 0:
                LOGGER_INFO(f"Found named window: {window.Name}, AutomationId: {window.AutomationId}", "YELLOW")
                return window.Name, window.AutomationId

        first_window = target_windows[0]
        window_name = first_window.Name if first_window.Name else "Unnamed Window"
        automation_id = first_window.AutomationId if hasattr(first_window, "AutomationId") else None
        LOGGER_WARNING(f"Using first available window: {window_name}, AutomationId: {automation_id}", "YELLOW")
        return window_name, automation_id

    def focus_on_active_window_by_pid(self, pid, searchDepth=1):
        """
        Print all windows for the given pid, get the first available window,
        extract its automation ID, and then properly focus and activate it.
        """
        root = auto.GetRootControl()
        windows = root.GetChildren()
        found = False
        for window in windows:
            if window.ProcessId == pid:
                found = True
                LOGGER_INFO(f"[Window][Found]: Name='{window.Name}', ClassName='{window.ClassName}', IsTopLevel={window.IsTopLevel}", "YELLOW")
        if not found:
            LOGGER_WARNING(f"No windows found for PID={pid}", "YELLOW")
            return None
        
        target_windows = []
        for window in windows:
            if window.ProcessId == pid:
                LOGGER_DEBUG(f"[Window][Found]: {window.Name}, ClassName: {window.ClassName}", "YELLOW")
                target_windows.append(window)
        
        if not target_windows:
            LOGGER_ERROR(f"[Window][Error]: Cannot find any window for PID={pid}")
            return None

        LOGGER_DEBUG(f"[Window][Total]: {len(target_windows)} found for PID={pid}: {target_windows}", "YELLOW")
        first_window = target_windows[0]
        LOGGER_WARNING(f"[Window][Using First]: {first_window.Name}", "YELLOW")

        # Get the window automation ID
        window_automation_id = first_window.AutomationId
        LOGGER_INFO(f"[Window][AutomationId]: {window_automation_id}", "CYAN")

        # Use WindowControl with proper parameters to get the window and set it active
        if window_automation_id:
            window = auto.WindowControl(searchDepth=searchDepth, AutomationId=window_automation_id, ProcessId=pid)
            if window.Exists():
                window.SetActive()
                LOGGER_INFO(f"[Window][Activated]: {window_automation_id}", "GREEN")
                return window
            else:
                LOGGER_ERROR(f"[Window][Error]: Failed to find window with AutomationId: {window_automation_id} and PID: {pid}")
        else:
            # Fallback: if no automation ID, use the original approach
            first_window.SetActive()
            LOGGER_WARNING(f"[Window][No AutomationId]: using direct SetActive on first window", "YELLOW")

        return first_window

    def focus_on_window_by_name(self, Name='Webex - Profile 1 - Microsoft​ Edge'):
        window = auto.WindowControl(searchDepth=1, Name=Name)
        if window.Exists(0):
            window.SetFocus()
            window.SetActive()
        else:
            print(f"Window with name not found.")

    def find_nested_control(self, control, automation_id):
        if control.AutomationId == automation_id:
            return control
        for child in control.GetChildren():
            found = self.find_nested_control(child, automation_id)
            if found:
                return found
        return None


    def find_first_window_with_children(self, windows, process_id):
            for window in windows:
                if window.ProcessId == process_id:
                    children = window.GetChildren()
                    if children:
                        return window
            return None
    
    def ensure_focus(self, window):
        if not window.Exists(0):
            raise Exception("Window not found")
        window.SetFocus()
        window.SetActive()
    
    def get_focus_by_processId(self, process_id):
        process_id = process_id
        root = auto.GetRootControl()
        windows = root.GetChildren()
        target_window = None
        while not target_window:
            target_window = self.find_first_window_with_children(windows, process_id)
            if target_window:
                self.ensure_focus(target_window)
                try:
                    auto.SendKeys("{Tab}")
                except Exception as e:
                    LOGGER_ERROR(f"Error in window: {e}")
            else:
                LOGGER_ERROR("No window with children found.")
            time.sleep(1)

    def get_foreground_window(self):
        try:
            foreground_window = auto.GetForegroundControl()
            LOGGER_INFO(f"Foreground Window control: {foreground_window}, the class name is {foreground_window.ClassName}", "YELLOW")
            if foreground_window:
                return foreground_window
        except Exception as e:
            LOGGER_ERROR(f"Error getting foreground window: {e}")
                      

    def normalize_control_id(self, control_id: str, patterns_to_strip: list[str]) -> str:
        """
         control_id contain '_QML_123' can change to '_QML_'
        :param control_id: original control_id string
        :param patterns_to_strip: ["_QML_", "_QMLTYPE_"]
        
        """
        if not control_id:
            return ""
        
        for prefix in patterns_to_strip:
            escaped_prefix = re.escape(prefix)
            pattern = rf'{escaped_prefix}\d+'
            control_id = re.sub(pattern, prefix, control_id)
        return control_id
    
    def get_control_default_action(self, control):
        legacy_pattern = control.GetLegacyIAccessiblePattern()
        
        try:
            default_action = legacy_pattern.DefaultAction if legacy_pattern else "N/A"
        except Exception:
            default_action = "N/A"
        
        try:
            legacy_value = legacy_pattern.Value if legacy_pattern else "N/A"
        except Exception:
            legacy_value = "N/A"
        
        try:
            legacy_role = legacy_pattern.Role if legacy_pattern else "N/A"
        except Exception:
            legacy_role = "N/A"
        
        try:
            legacy_state = legacy_pattern.State if legacy_pattern else "N/A"
        except Exception:
            legacy_state = "N/A"
        
        return default_action, legacy_value, legacy_role, legacy_state
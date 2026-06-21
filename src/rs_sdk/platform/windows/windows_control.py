import comtypes.client
import hashlib
import psutil
import time
import uiautomation as auto
import pyautogui as autogui

from comtypes.client import GetModule
GetModule('oleacc.dll')
GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient
from rs_sdk.framework.abstract_control import BaseControl
from rs_sdk.utils.control import Control
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils.control_handler import ControlHandler
from rs_sdk.utils.control_db import ControlDB
from rs_sdk.utils.event_listener import FocusListener

class WindowsControl(BaseControl):
    def __init__(self):
        """Initialize and get the currently focused self.control."""
        self.automation = comtypes.client.CreateObject(UIAutomationClient.CUIAutomation)
        self.control_handler = ControlHandler()
        self.control_db = ControlDB()
        self.control = Control()
        if self.control.toggle_listener:
            self.element = self.control.current_focus
            self.pre_element = self.control.previous_focus
        else:
            self.element = self.automation.GetFocusedElement()
        if not self.element:
            LOGGER_ERROR("Failed to initialize: No focused element found.", "RED")
    
    def refresh(self, force_update=False):
        """Refresh the control element. If invalid, attempt to change focus and restore.
        
        Args:
            force_update: If True, force get the focused element from system instead of cache
        """
        if force_update:
            # Force update from system - but don't modify global state
            forced_element = self.automation.GetFocusedElement()
            if forced_element:
                try:
                    _ = forced_element.CurrentName  # Test if valid
                    self.element = forced_element
                    # Update global state only if element is valid
                    self.control.current_focus = forced_element
                    LOGGER_DEBUG(f"[Force Refresh] Updated element")
                    return forced_element
                except Exception as e:
                    LOGGER_WARNING(f"[Force Refresh] Forced element invalid: {e}")
                    # Fall through to use cached element
        
        self.element = self.control.current_focus
        if self.element:
            try:
                _ = self.element.CurrentName
                return self.element
            except Exception:
                LOGGER_WARNING("Current element is invalid, attempting to recover focus.", "YELLOW")
        reverse_keys = {
            "{DOWN}": "{UP}",
            "{LEFT}": "{RIGHT}",
            "{RIGHT}": "{LEFT}"
        }

        for key in ["{DOWN}", "{LEFT}", "{RIGHT}", "{TAB}"]:
            auto.SendKeys(key) 
            time.sleep(1) 

            new_element = self.control.current_focus 

            if new_element and new_element != self.element:
                LOGGER_INFO(f"Focus changed using key {key}, attempting to restore previous focus...", "CYAN")
                if key == "{TAB}":
                    autogui.hotkey('shift', 'TAB')
                else:
                    auto.SendKeys(reverse_keys[key])
                time.sleep(1) 

                self.element = self.control.current_focus 
                try:
                    if self.element:
                        _ = self.element.CurrentName 
                        LOGGER_INFO(f"Focus restored and control is valid. current {self.element.CurrentName}", "GREEN")
                        return self.element
                except Exception:
                    LOGGER_ERROR("Restored element is still invalid.", "RED")
        
        LOGGER_INFO("Restarting focus listener to recover focus tracking.", "YELLOW")
        listener = FocusListener()
        listener.stop()
        listener.start()

        new_element = self.control.current_focus 

        if new_element:
            try:
                _ = new_element.CurrentName 
                self.element = new_element
                LOGGER_INFO(f"Focus listener recovered a valid control. current {self.element.CurrentName}", "GREEN")
                return self.element
            except Exception:
                LOGGER_ERROR("Recovered element is still invalid.", "RED")

        LOGGER_ERROR("Failed to restore a valid control.", "RED")
        return None

    def get_previous_element_raw(self):
        """Return the previous focused control element."""
        return self.control.previous_focus
    
    def get_current_element_raw(self):
        """Return the current focused control element."""
        return self.control.current_focus

    @property
    def ControlName(self):
        """Return the name of the control as a property."""
        return self.get_control_name()
    
    @property
    def ControlID(self):
        """Return the automation id of the control as a property."""
        return self.get_control_id()
    
    @property
    def ControlIDHash(self):
        """Return the id hash of the control as a property."""
        return self.get_control_id_hash()
    
    @property
    def ControlType(self):
        """Return the localized control type of the control as a property."""
        return self.get_control_type()
    
    @property
    def ControlTypeName(self):
        """Return the localized control type name of the control as a property."""
        return self.get_control_type_name()
    
    @property
    def ControlBoundingRectangle(self):
        """Return the bounding rectongle of the control as a property."""
        return self.get_control_bounding_rect()
    
    @property
    def ControlHelpText(self):
        """Return the help text of the control as a property."""
        return self.get_control_help_text()
    
    @property
    def ControlFullDescription(self):
        """Return the full description of the control as a property."""
        return self.get_fulldescription()
    
    @property
    def ControlToggleState(self):
        """Return the toggle state of the control as a property."""
        return self.get_toggle_state()
    
    @property
    def ControlLegacyProperties(self):
        """Return the legacy properties (default_action, legacy_value, legacy_role, legacy_state) of the control as a property."""
        return self.get_control_legacy_properties()
    
    @property
    def ControlCollapseState(self):
        """Return the collapse properties (collapsed, expand) of the control as a property."""
        return self.get_expand_collapse_state()
    
    @property
    def ControlAncestorElement(self):
        """Return the ancestor element of the control as a property."""
        return self.get_control_ancestor_element()
    
    @property
    def ControlAllAncestorElements(self):
        """Return all ancestor elements of the control as a property."""
        return self.get_control_all_ancestor_elements()
    
    @property
    def ControlAncestorLevelsElements(self):
        """Return ancestor elements level of the control as a property."""
        return self.get_control_ancestor_levels_elements()
    
    @property
    def ControlFirstAncestorWindow(self):
        """Return the first ancestor window of the control as a property."""
        return self.get_control_first_ancestor_window()
    
    @property
    def ControlPreviousSibling(self):
        """Return the previous sibling element of the control as a property."""
        return self.get_control_previous_sibling()
    
    @property
    def ControlNextSibling(self):
        """Return the next sibling element of the control as a property."""
        return self.get_control_next_sibling()
    
    @property
    def ControlParent(self):
        """Return the parent of the control as a property."""
        return self.get_control_parent()
    
    @property
    def ControlExpandCollapse(self):
        """Return the expand or collapse state of the control as a property."""
        return self.get_control_expand_collapse()
    
    @property
    def ControlProcessID(self):
        """Return the process id of the control as a property."""
        return self.get_control_process_id()
    
    @property
    def ControlRuntimeID(self):
        """Return the process id of the control as a property."""
        return self.get_control_runtime_id()
    
    @property
    def ControlAccessKey(self):
        """Return the access key of the control as a property."""
        return self.get_control_accesskey()
    
    @property
    def ControlClassName(self):
        """Return the class name of the control as a property."""
        return self.get_class_name()
    
    @property
    def ControlValue(self):
        """Return the value of the control as a property (for edit/text controls)."""
        return self.get_control_value()

    def get_control_name(self):
        """Return the name of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            name = self.element.CurrentName
            return name 
        except Exception as e:
            LOGGER_ERROR(f"Error getting control name: {e}", "RED")
            return None

    @classmethod
    def from_element(cls, element):
        instance = cls()
        instance.element = element
        return instance

    def get_control_id(self):
        """Return the automation id of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            id = self.element.CurrentAutomationId
            return id if id else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control id: {e}", "RED")
            return None
    
    def get_class_name(self):
        """Return the class name of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            class_name = self.element.CurrentClassName
            return class_name if class_name else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control class name: {e}", "RED")
            return None
        
    def get_control_id_hash(self):
        try:
            focused_element = self.element
            
            if focused_element.CurrentControlType in [50023, 50024]:
                control_identifier = focused_element.CurrentName
                # current_control_ancestor  = self.get_control_ancestor_element()
                # current_control_window_name = current_control_ancestor.get("name", None)
                # controls_tree = self.control_handler.get_control_name_by_window(current_control_window_name)
                # LOGGER_DEBUG(f"[id_hash] controls_tree: {controls_tree}", "RED")
                # for control in controls_tree:
                #     LOGGER_DEBUG(f"[id_hash] control: {control} [{type(control)}], current control: {focused_element.CurrentName} [{type(focused_element.CurrentName)}]", "RED")
                #     result = self.control_handler.are_controls_tree_same(focused_element.CurrentName, control)
                #     if result:
                #         LOGGER_DEBUG(f"[id_hash] Found matching control: {control} [{type(control)}]", "RED")
                #         control_identifier = control
                #         break
            
                control_hash = hashlib.sha256(control_identifier.encode("utf-8")).hexdigest()
            
                return control_hash

            if not focused_element:
                LOGGER_ERROR("No focused element found.", "RED")
                return None
            
            # reassigned_ancestors = self.get_control_ancestor_levels_elements(type=50032, levels=2)          
            # current_control_level1_window_name = reassigned_ancestors.get("level1", {}).get("name", None)
            # current_control_level2_window_name = reassigned_ancestors.get("level2", {}).get("name", None)

            parent_name = self.get_control_parent().get("name", None)

            control_identifier = (
                f"Focused:{focused_element.CurrentName}:"
                f"{focused_element.CurrentAutomationId}:"
                f"{focused_element.CurrentControlType}\n"
                f"{parent_name}\n"
            )

            control_hash = hashlib.sha256(control_identifier.encode("utf-8")).hexdigest()
            # LOGGER_DEBUG(f"control_hash: [{control_hash}] [{control_identifier}]", "RED")
            return control_hash

        except Exception as e:
            LOGGER_ERROR(f"Error occurred: {e}", "RED")
            return None
        
    def get_control_path_hash(self, control_name, from_control):

        combined_string = f"{control_name}:{from_control}"
        hash_object = hashlib.sha256(combined_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        return hash_hex

    def get_control_type(self):
        """Return the localized control type."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            type = self.element.CurrentControlType
            return type 
        except Exception as e:
            LOGGER_ERROR(f"Error getting control type: {e}", "RED")
            return None
        
    def get_control_type_name(self):
        """Return the localized control type."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            type = self.element.CurrentLocalizedControlType
            # Strip zero-width characters (U+200B, U+200C, U+200D, U+FEFF) that
            # Qt accessibility bridge may inject into localized type strings
            if type:
                type = type.strip('\u200b\u200c\u200d\ufeff').strip()
            return type if type else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control type: {e}", "RED")
            return None
        
    def get_control_bounding_rect(self):
        """Return the bounding rectangle of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            bounding_rect = self.element.CurrentBoundingRectangle
            return bounding_rect if bounding_rect else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control bounding rectangle: {e}", "RED")
            return None
        
    def get_control_help_text(self):
        """Return the help text of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            help_text = self.element.CurrentHelpText
            return help_text if help_text else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control help text: {e}")
            return None

    def get_fulldescription(self):
        """Return the full description of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            control = self.element.QueryInterface(UIAutomationClient.IUIAutomationElement6)
            return control.CurrentFullDescription if control else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control full description: {e}", "RED")
            return
    
    def get_control_value(self):
        """Return the value of the control (for edit/text controls that support Value Pattern)."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            # Try to get Value pattern for edit/text controls
            value_pattern = self.element.GetCurrentPattern(UIAutomationClient.UIA_ValuePatternId)
            if value_pattern:
                value_interface = value_pattern.QueryInterface(UIAutomationClient.IUIAutomationValuePattern)
                return value_interface.CurrentValue if value_interface.CurrentValue else ""
            return None
        except Exception as e:
            # If Value pattern is not supported, return None (not all controls support it)
            LOGGER_DEBUG(f"Control does not support Value pattern: {e}", "YELLOW")
            return None
    
    def get_toggle_state(self):
        """Return the toggle state of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            toggle_pattern = self.element.GetCurrentPattern(UIAutomationClient.UIA_TogglePatternId)
            toggle_interface = toggle_pattern.QueryInterface(UIAutomationClient.IUIAutomationTogglePattern)
            return toggle_interface.CurrentToggleState

        except Exception as e:
            LOGGER_ERROR(f"Error getting control toggle state: {e}", "RED")
            return
        
    def get_expand_collapse_state(self):
        try:
            expand_collapse_pattern = self.element.GetCurrentPattern(UIAutomationClient.UIA_ExpandCollapsePatternId)
            expand_collapse_interface = expand_collapse_pattern.QueryInterface(
                UIAutomationClient.IUIAutomationExpandCollapsePattern
            )
            LOGGER_DEBUG(f"ExpandCollapse pattern available: {expand_collapse_interface is not None}")
            if expand_collapse_interface:
                state = expand_collapse_interface.CurrentExpandCollapseState
                return state
        except Exception as e:
            LOGGER_ERROR(f"Error getting control collapse state: {e}", "RED")
        return "None"

    def get_control_legacy_properties(self):
        """Return default_action, legacy_value, legacy_role, legacy_state of the control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None, None, None, None
        
        try:
            # Convert UIAutomation element to uiautomation control
            control = auto.GetFocusedControl()
            if not control:
                LOGGER_ERROR("Failed to get focused control for legacy properties.", "RED")
                return None, None, None, None
            
            # Use ControlHandler to get legacy properties
            default_action, legacy_value, legacy_role, legacy_state = self.control_handler.get_control_default_action(control)
            
            return default_action, legacy_value, legacy_role, legacy_state
            
        except Exception as e:
            LOGGER_ERROR(f"Error getting control legacy properties: {e}", "RED")
            return None, None, None, None
        
    def get_control_ancestor_element(self):
        """Return the ancestor element of the focused control as a dictionary."""
        try:
            focused_element = self.element
            if not focused_element:
                LOGGER_ERROR("No focused element found.", "RED")
                return {}

            current_process_id = focused_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)

            tree_walker = self.automation.ControlViewWalker
            ancestor_element = focused_element

            while True:
                parent_element = tree_walker.GetParentElement(ancestor_element)
                if not parent_element:
                    break

                parent_process_id = parent_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)
                if parent_process_id != current_process_id:
                    break

                ancestor_element = parent_element

            control_info = {
                "name": ancestor_element.CurrentName,
                "id": ancestor_element.CurrentAutomationId,
                "type": ancestor_element.CurrentControlType,
                "type_name": ancestor_element.CurrentLocalizedControlType
            }

        except Exception as e:
            LOGGER_ERROR(f"Error occurred: {e}", "RED")
            control_info = {}

        return control_info
    
    def get_control_all_ancestor_elements(self):
        """Return all ancestor elements of the focused control as a list of dictionaries."""
        try:
            focused_element = self.element
            if not focused_element:
                LOGGER_ERROR("No focused element found.", "RED")
                return []

            current_process_id = focused_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)

            tree_walker = self.automation.ControlViewWalker
            ancestor_element = focused_element

            ancestors = []
            level = 0
            while True:
                parent_element = tree_walker.GetParentElement(ancestor_element)
                if not parent_element:
                    break

                parent_process_id = parent_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)
                if parent_process_id != current_process_id:
                    break

                ancestor_element = parent_element
                level += 1

                ancestors.append({
                    "level": level,
                    "name": ancestor_element.CurrentName,
                    "id": ancestor_element.CurrentAutomationId,
                    "type": ancestor_element.CurrentControlType,
                    "type_name": ancestor_element.CurrentLocalizedControlType,
                    "process_id": parent_process_id
                })

            return ancestors

        except Exception as e:
            LOGGER_ERROR(f"Error occurred: {e}", "RED")
            return []
        
    def get_control_ancestor_levels_elements(self, type=50032, levels=2):
        """Return the ancestor elements of the focused control up to the specified level as a dictionary."""
        def _get_filtered_ancestor_elements(type):
            ancestors_info = self.get_control_all_ancestor_elements()
            filtered_ancestors = [ancestor for ancestor in ancestors_info if ancestor['type'] == type]
            filtered_ancestors.sort(key=lambda x: x['level'], reverse=True)
            return filtered_ancestors

        def _log_filtered_ancestor_elements(type):
            filtered_ancestors = _get_filtered_ancestor_elements(type)
            reassigned_ancestors = []
            for idx, ancestor in enumerate(filtered_ancestors):
                reassigned_ancestor = {
                    "level": idx + 1,
                    "name": ancestor['name'],
                    "id": ancestor['id'],
                    "type": ancestor['type']
                }
                reassigned_ancestors.append(reassigned_ancestor)
            return reassigned_ancestors

        reassigned_ancestors = _log_filtered_ancestor_elements(type=type)
        
        result = {}
        for level in range(1, levels + 1):
            if len(reassigned_ancestors) >= level:
                result[f"level{level}"] = {
                    "name": reassigned_ancestors[level - 1]['name'],
                    "id": reassigned_ancestors[level - 1]['id'],
                    "type": reassigned_ancestors[level - 1]['type']
                }
            else:
                result[f"level{level}"] = {
                    "name": None,
                    "id": None,
                    "type": None
                }

        return result
    
    def get_control_first_ancestor_window(self):
        """Return the topmost ancestor window (type=50032) of the control."""
        try:
            focused_element = self.element
            if not focused_element:
                LOGGER_ERROR("No focused element found.", "RED")
                return None

            current_process_id = focused_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)

            tree_walker = self.automation.ControlViewWalker
            ancestor_element = focused_element
            topmost_window = None
            nearest_window = None

            while True:
                parent_element = tree_walker.GetParentElement(ancestor_element)
                if not parent_element:
                    break

                parent_process_id = parent_element.GetCurrentPropertyValue(UIAutomationClient.UIA_ProcessIdPropertyId)
                # if parent_process_id != current_process_id:
                #     break

                if parent_element.CurrentControlType == 50032:
                    if nearest_window is None:
                        nearest_window = parent_element
                    topmost_window = parent_element

                ancestor_element = parent_element

            # Prefer topmost window (full app window); fall back to nearest window
            # (e.g. popup menu, dialog) when topmost is not found in the UIA tree
            return topmost_window or nearest_window
            
        except Exception as e:
            LOGGER_ERROR(f"Error occurred: {e}", "RED")
            return None


    def get_control_previous_sibling(self):
        """Return the previous sibling element of the focused control as a dictionary."""
        try:
            focused_element = self.element
            if not focused_element:
                return {}

            tree_walker = self.automation.ControlViewWalker
            previous_sibling = tree_walker.GetPreviousSiblingElement(focused_element)

            if previous_sibling:
                control_info = {
                    "name": previous_sibling.CurrentName,
                    "id": previous_sibling.CurrentAutomationId,
                    "type": previous_sibling.CurrentControlType,
                    "type_name": previous_sibling.CurrentLocalizedControlType
                }
            else:
                control_info = {}

        except Exception as e:
            LOGGER_ERROR(f"An error occurred: {e}", "RED")
            control_info = {}

        return control_info
    
    def get_control_next_sibling(self):
        """Return the next sibling element of the focused control as a dictionary."""
        try:
            focused_element = self.element
            if not focused_element:
                return {}

            tree_walker = self.automation.ControlViewWalker
            next_sibling = tree_walker.GetNextSiblingElement(focused_element)

            if next_sibling:
                control_info = {
                    "name": next_sibling.CurrentName,
                    "id": next_sibling.CurrentAutomationId,
                    "type": next_sibling.CurrentControlType,
                    "type_name": next_sibling.CurrentLocalizedControlType
                }
            else:
                control_info = {}

        except Exception as e:
            LOGGER_ERROR(f"An error occurred: {e}", "RED")
            control_info = {}

        return control_info

    def get_control_parent(self):
        """Return the parent element of the focused control as a dictionary."""
        try:
            focused_element = self.element
            if not focused_element:
                LOGGER_ERROR("No focused element found.", "RED")
                return {}

            tree_walker = self.automation.ControlViewWalker
            parent_element = tree_walker.GetParentElement(focused_element)

            if parent_element:
                control_info = {
                    "name": parent_element.CurrentName,
                    "id": parent_element.CurrentAutomationId,
                    "type": parent_element.CurrentControlType,
                    "type_name": parent_element.CurrentLocalizedControlType
                }
            else:
                LOGGER_ERROR("No parent element found.", "RED")
                control_info = {}

        except Exception as e:
            LOGGER_ERROR(f"An error occurred: {e}", "RED")
            control_info = {}

        return control_info
    
    def get_control_expand_collapse(self):  
        element = self.automation.GetFocusedElement()
        
        try:
            pattern_obj = element.GetCurrentPattern(UIAutomationClient.UIA_ExpandCollapsePatternId)
            expand_collapse_pattern = pattern_obj.QueryInterface(UIAutomationClient.IUIAutomationExpandCollapsePattern)

            state = expand_collapse_pattern.CurrentExpandCollapseState
            
        except Exception as e:
            state = None
        
        return state

    def get_control_process_id(self):
        """Return the process id of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            CurrentProcessId = self.element.CurrentProcessId
            return CurrentProcessId
        except Exception as e:
            LOGGER_ERROR(f"Error getting control name: {e}")
            return None
    
    def get_control_runtime_id(self):
        """Return the runtime id of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            runtime_id = self.element.GetRuntimeId()
            return runtime_id if runtime_id else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control runtime id: {e}")
            return None
        
    def get_control_accesskey(self):
        """Return the access key of the self.control."""
        if not self.element:
            LOGGER_ERROR("Control element is not available.", "RED")
            return None
        try:
            access_key = self.element.CurrentAccessKey
            return access_key if access_key else None
        except Exception as e:
            LOGGER_ERROR(f"Error getting control access key: {e}")
            return None
    
    def get_control_Level(self, control_name):   

        results = self.control_db.fetch_control_level_by_name(control_name)
        if results is not None and len(results) > 0:
            return results[0][0]
        else:
            return 100000
        
    def get_control_Level_prefix(self, control_name):   
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
        
    def get_control_from_name(self, control_name):
        results = self.control_db.fetch_from_control_name(control_name)
        if results is not None:
            for row in results:
                return row[0]
        else:
            return None
        
    def get_control_toggle_state(self, control_name):
        pass
        return None
    
    def get_children_pid(self, parent_pid):
        """get children PID"""
        try:
            parent = psutil.Process(parent_pid)
        except psutil.NoSuchProcess:
            return []
        return [child.pid for child in parent.children(recursive=True)]

    def get_parent_pid(self, child_pid):
        """get parent PID"""
        try:
            child_process = psutil.Process(child_pid)
            return child_process.ppid()
        except psutil.NoSuchProcess:
            return None

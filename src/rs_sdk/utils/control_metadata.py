import platform as platform_module
from dataclasses import dataclass
from config.config import *

# Platform-specific import for control handler
if platform_module.system() == "Windows":
    from rs_sdk.utils.control_handler import ControlHandler
elif platform_module.system() == "Linux":
    from rs_sdk.platform.linux.linux_control_handler import ControlHandler

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils.control_db import ControlDB
from tools.webexApp import appHandler
from typing import Optional
from comtypes.client import GetModule
GetModule('oleacc.dll')
GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient


# Conditional imports for platform-specific modules
if platform_module.system() == "Windows":
    from rs_sdk.platform.windows.windows_control import WindowsControl as Control
    from ctypes.wintypes import RECT
elif platform_module.system() == "Linux":
    from rs_sdk.platform.linux.linux_control import LinuxControl as Control
    RECT = None


@dataclass
class ControlImageMetadata:
    control_rect: Optional[RECT]
    pre_control_rect: Optional[RECT]
    root_window_rect: Optional[RECT]
    pre_control_type: Optional[int]
    is_window_without_title: bool = False

class ControlMetadata:
    def __init__(self):
        self.control_db = ControlDB()
        self.current_control = Control()
        self.control_handler = ControlHandler()
        # self.app_pids = appHandler.get_pids()
    
    def get_control_metadata(self, from_control=None):
        control = self.current_control
        control.refresh()
        control_name = control.ControlName
        control_type = control.ControlType
        control_type_name = control.ControlTypeName
        control_id = control.ControlID
        control_id_hash = control.ControlIDHash
        control_runtime_id = control.ControlRuntimeID
        control_class_name = control.ControlClassName
        control_accesskey = control.ControlAccessKey
        control_full_description = control.ControlFullDescription
        control_path_hash = self.control_handler.generate_control_path_hash(control_name, from_control)
        control_level = self.control_handler.get_control_level_by_control_id_hash(control_id_hash)
        reassigned_ancestors = control.ControlAncestorLevelsElements
        control_window_name = reassigned_ancestors["level1"]["name"]
        control_window_automation_id = reassigned_ancestors["level1"]["id"]
        control_level2_window_name = reassigned_ancestors["level2"]["name"]
        control_level2_window_automation_id = reassigned_ancestors["level2"]["id"]
        control_parent = control.ControlParent
        control_parent_name = control_parent.get("name", "None")
        control_parent_type = control_parent.get("type", "None")
        control_parent_id = control_parent.get("id","None")
        control_process_id = control.ControlProcessID

        # Get legacy properties
        default_action, legacy_value, legacy_role, legacy_state = control.ControlLegacyProperties
        
        return {
            "name": control_name,
            "type": control_type,
            "type_name": control_type_name,
            "id": control_id,
            "id_hash": control_id_hash,
            "runtime_id": control_runtime_id,
            "class_name": control_class_name,
            "accesskey": control_accesskey,
            "full_description": control_full_description,
            "path_hash": control_path_hash,
            "level": control_level,
            "window_name": control_window_name,
            "window_automation_id": control_window_automation_id,
            "level2_window_name": control_level2_window_name,
            "level2_window_automation_id": control_level2_window_automation_id,
            "parent": control_parent,
            "parent_name": control_parent_name,
            "parent_type": control_parent_type,
            "parent_id": control_parent_id,
            "default_action": default_action,
            "legacy_value": legacy_value,
            "legacy_role": legacy_role,
            "legacy_state": legacy_state,
            "from control": from_control,
            "process_id": control_process_id
        }
    
    def get_control_image_metadata(self) -> ControlImageMetadata:
        is_crop_currentControl = True
        is_crop_preControl = True
        is_crop_rootWindow = True
        is_window_without_title = False

        control = self.current_control
        control.refresh()

        pre_control = None
        root_window = None
        pre_control_rect = None
        root_window_rect = None

        try:
            pre_control = control.from_element(control.get_previous_element_raw())
        except Exception:
            is_crop_preControl = False

        if self._is_invalid_control(control):
            is_crop_currentControl = False
            is_crop_rootWindow = False
        # elif control.ControlProcessID not in self.app_pids:
        #     self.app_pids = appHandler.get_pids()
        #     if control.ControlProcessID not in self.app_pids:
        #         is_crop_currentControl = False
        #         is_crop_rootWindow = False
        else:
            # root_window = control.from_element(control.ControlFirstAncestorWindow)
            # root_window_rect = root_window.ControlBoundingRectangle
            root_window = control.ControlFirstAncestorWindow
            if root_window is not None:
                root_window_rect = root_window.CurrentBoundingRectangle
                window = root_window.QueryInterface(UIAutomationClient.IUIAutomationElement9)
                if window.CurrentIsDialog and root_window.CurrentClassName != "WquickView":
                    is_window_without_title = True
            else:
                is_crop_rootWindow = False

        if is_crop_currentControl:
            control_rect = control.ControlBoundingRectangle
        
        invalid_control_types = {50030, 50032, 50033, 50025, 50026, 50019}
        if self._is_invalid_control(pre_control):
            is_crop_preControl = False
        else:
            assert pre_control is not None           
            # if pre_control.ControlProcessID not in self.app_pids:
            #     is_crop_preControl = False
            if (
                pre_control.ControlID == control.ControlID
                or pre_control.ControlType in invalid_control_types
            ):
                is_crop_preControl = False
            else:
                pre_control_rect = pre_control.ControlBoundingRectangle
                pre_control_type = pre_control.ControlType
                if (
                    control_rect is not None and
                    pre_control_rect is not None and
                    pre_control_rect.left == control_rect.left and
                    pre_control_rect.top == control_rect.top and
                    pre_control_rect.right == control_rect.right and
                    pre_control_rect.bottom == control_rect.bottom
                ):
                    is_crop_preControl = False
                
        return ControlImageMetadata(
            control_rect=control_rect if is_crop_currentControl else None,
            pre_control_rect=pre_control_rect if is_crop_preControl else None,
            root_window_rect=root_window_rect if is_crop_rootWindow else None,
            pre_control_type=pre_control_type if is_crop_preControl else None,
            is_window_without_title=is_window_without_title if is_crop_rootWindow else False
        )

    
    def _is_invalid_control(self, control):
        try:
            _ = control.ControlProcessID
            return False
        except:
            return True

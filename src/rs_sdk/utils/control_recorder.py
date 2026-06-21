import shutil
import datetime
import json
from pathlib import Path
import imagehash
from PIL import Image

from config.paths import CONTROL_IMAGE_PATH, WINDOW_IMAGE_PATH, SESSION_OUTPUT_PATH
from config.config import NO_RECORD_CONTROLS_ID
from rs_sdk.utils.control_metadata import ControlMetadata
from common.handler.textHandler import preProcessString
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.utils.control_db import ControlDB
from rs_sdk.utils import image_handler
from common.handler.report_id_generator import report_id_generator
from config.paths import SETTINGS_PATH
from common.utils import deviceInfo


class ControlRecorder:
    def __init__(self):
        self.current_focus_control = ControlFactory()  
        self.control_db = ControlDB()
        self.control_metadata = ControlMetadata()
        self.control_image_directory_path = Path(CONTROL_IMAGE_PATH) / "currentControls"
        self.pre_control_image_directory_path = Path(CONTROL_IMAGE_PATH) / "preControls"
        self.window_image_directory_path = Path(WINDOW_IMAGE_PATH)
        self._load_settings_from_file()
        
    def _load_settings_from_file(self):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self._appVersion = settings.get('appVersion', 'Unknown')
            self._workflow = settings.get('workflow', 'sign_in')
            self._language = settings.get('language', 'en')
            self._environment = settings.get('environment','ATS')
            self._installOptions = settings.get('installOptions',{})
            self._qtversion = self._installOptions.get('qtversion', '6')
            self._arch = self._installOptions.get('arch', 'x64')  # Default to x64 if not specified

            LOGGER_DEBUG(f"Loaded from file - appVersion: {self._appVersion}, workflow: {self._workflow}, language: {self._language}, environment: {self._environment}, installOptions: {self._installOptions}, qtversion: {self._qtversion}, arch: {self._arch}", "CYAN")

        except Exception as e:
            LOGGER_ERROR(f"Failed to load settings from file: {e}")
            self._appVersion = 'Unknown'
            self._workflow = 'sign_in'
            self._language = 'en'
    
    def _get_machine_info(self):
        try:
            hostname = deviceInfo.getHostName()
            sn = deviceInfo.getSerialNumber()
            machine_name = f"{hostname}_{sn}" if hostname and sn else hostname or sn or "Unknown"
            
            return {
                'hostname': hostname,
                'serial_number': sn,
                'machine_name': machine_name
            }
        except Exception as e:
            LOGGER_ERROR(f"Failed to get machine info: {e}", "RED")
            return {
                'hostname': 'Unknown',
                'serial_number': 'Unknown', 
                'machine_name': 'Unknown'
            }

    def reset_image_directory(self):
        shutil.rmtree(SESSION_OUTPUT_PATH, ignore_errors=True)

    def record_control_info(self, level, from_control, control_path_hash, is_validated, rule, keyboard_action=None, result=None, project_id = "3"):
        
        try:
            current_focus_control = self.current_focus_control.create_control()
            # LOGGER_INFO(f"[Record][SDK]: [ControlName: {current_focus_control.ControlName}],[ControlType: {current_focus_control.ControlType}],[ControlTypeName: {current_focus_control.ControlTypeName}],[ControlID: {current_focus_control.ControlID}],[ControlIDHash: {current_focus_control.ControlIDHash}],[ControlPreviousSibling: {current_focus_control.ControlPreviousSibling}],[ControlNextSibling: {current_focus_control.ControlNextSibling}],[ControlParent: {current_focus_control.ControlParent}],[ControlAncestorElement: {current_focus_control.ControlAncestorElement}],[ControlAncestorLevelsElements: {current_focus_control.ControlAncestorLevelsElements}],[ControlFullDescription: {current_focus_control.ControlFullDescription}],[ControlHelpText: {current_focus_control.ControlHelpText}]", "RED")

            control_name = current_focus_control.ControlName
            control_type = current_focus_control.ControlType
            control_LocalizedControlType = current_focus_control.ControlTypeName
            AutomationId = current_focus_control.ControlID
            control_id_hash = current_focus_control.ControlIDHash
            fulldescription = current_focus_control.ControlFullDescription
            process_id = current_focus_control.ControlProcessID
            runtime_id = current_focus_control.ControlRuntimeID
            runtime_id = ','.join(map(str, runtime_id)) # type: ignore
            control_accesskey = current_focus_control.ControlAccessKey
            control_ClassName = current_focus_control.ControlClassName
            HelpText = current_focus_control.ControlHelpText

            parent_control = current_focus_control.ControlParent
            parent_name = parent_control.get("name", "None")
            parent_type = parent_control.get("type", "None")
            previous_sibling_control = current_focus_control.ControlPreviousSibling
            previous_sibling = previous_sibling_control.get("name", "None")
            next_sibling_control = current_focus_control.ControlNextSibling
            next_sibling = next_sibling_control.get("name", "None")

            level = level
            
            process_name = from_control
            
            if current_focus_control.ControlType == 50002:
                togglestate = current_focus_control.ControlToggleState
            else:
                togglestate = "None"
                            
            # reassigned_ancestors = accUIA.get_ancestors_elements_level1_to_level2()
            reassigned_ancestors = current_focus_control.ControlAncestorLevelsElements
            current_control_level1_window_name = reassigned_ancestors["level1"]["name"]
            current_control_level1_AutomationId = reassigned_ancestors["level1"]["id"]
            current_control_level1_type = reassigned_ancestors["level1"]["type"]
            current_control_level2_window_name = reassigned_ancestors["level2"]["name"]
            current_control_level2_AutomationId = reassigned_ancestors["level2"]["id"]
            current_control_level2_type = reassigned_ancestors["level2"]["type"]
            

            if control_type in [50023, 50024] and current_control_level1_window_name == None and current_control_level2_window_name == None:
                current_control_level1_window_name = parent_name

            # record default_action, legacy_value, legacy_role, legacy_state
            default_action, legacy_value, legacy_role, legacy_state = current_focus_control.ControlLegacyProperties
            if control_type == 50025 and parent_type == 50008:
                legacy_value = "None"
            
            if current_focus_control.ControlType in [50003]:
                expand_collapse_state = current_focus_control.ControlCollapseState
            else:
                expand_collapse_state = "None"

            IsEnabled = "None"
            IsKeyboardFocusable = "None"
            HasKeyboardFocus = "None"
            control_bounding_rectangles = "None"
            HierarchicalLevel = "None"
            image, pre_control_image, window_image = "None", "None", "None"

            # Get all ancestor elements and serialize to JSON
            ancestors_list = current_focus_control.ControlAllAncestorElements
            ancestors_json = json.dumps(ancestors_list) if ancestors_list else None
            LOGGER_DEBUG(f"Ancestors data: {ancestors_json}", "CYAN")

            if AutomationId in NO_RECORD_CONTROLS_ID:
                control_name = "Disclaimer Content View"

            app_version = self._appVersion
            workflow = self._workflow
            qt_version = self._qtversion
            environment = self._environment
            arch = self._arch
            if workflow == "":
                workflow = "sign_in"
            language = self._language
            jenkins_job = workflow + "_" + environment + "_" + qt_version + "_" + language
            machine_info = self._get_machine_info()
            machine_name = machine_info.get('machine_name', 'Unknown')
            report_id = report_id_generator.global_report_id
            self.control_db.insert_control_info(report_id, control_name, level, from_control, HierarchicalLevel, rule, control_path_hash, control_id_hash, runtime_id, is_validated, current_control_level1_window_name, current_control_level1_AutomationId, current_control_level1_type, current_control_level2_window_name, current_control_level2_AutomationId, current_control_level2_type, parent_name, parent_type, previous_sibling, next_sibling, 
                                control_LocalizedControlType, control_type, togglestate, AutomationId, fulldescription, control_accesskey, app_version, workflow, language, qt_version, arch, jenkins_job, machine_name, control_bounding_rectangles, control_ClassName,
                                default_action, legacy_value, expand_collapse_state, IsEnabled, IsKeyboardFocusable, HasKeyboardFocus,
                                HelpText, legacy_role, legacy_state, image, pre_control_image, window_image, process_id, process_name, project_id, keyboard_action, ancestors_json)
        
            LOGGER_INFO(f"[Record][Success]: [name: ({control_name})][is_validated: ({is_validated})]", "GREEN")

        except Exception as e:
            LOGGER_ERROR(f"Record control error: {e}", "RED")
            pass

    def record_control_image(self):
        try:
            info_metadata = self.control_metadata.get_control_metadata()
            image_metadata = self.control_metadata.get_control_image_metadata()
            description = info_metadata.get('name')
            control_type = info_metadata.get('type')
            control_id = info_metadata.get('id')
            pre_control_image = None
            pre_control_image_bytes = None
            control_image_path = None
            previous_control_image_path = None
            ignore_pre_control_image = False
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{timestamp}_{preProcessString(description)}"
            margin_left = 0
            margin_right = 0
            margin_top = 0
            margin_bottom = 0
            img_hash = None  # Initialize image hash

            if image_metadata.control_rect:
                if control_type == 50004: # Inputbox
                    margin_left = 70
                    margin_right = 60
                    margin_top = 10
                    margin_bottom = 50
                control_image_output = image_handler.capture_image_from_currentBoundingRectangle(image_metadata.control_rect, left_extra=margin_left, right_extra=margin_right, top_extra=margin_top, bottom_extra=margin_bottom)
                control_image = control_image_output.img
                control_image_bytes = control_image_output.byte_data
                control_image_path = str(Path(self.control_image_directory_path) / f"{image_name}.jpg")
                image_handler.save_image(image_name, img=control_image, output_path=self.control_image_directory_path.as_posix())
                
                # Calculate image hash using perceptual hash (phash)
                if control_image is not None:
                    img_hash = str(imagehash.phash(control_image))
                    LOGGER_DEBUG(f"Calculated image hash: {img_hash}", "CYAN")

            if image_metadata.pre_control_rect:
                if image_metadata.pre_control_type == 50004: # Inputbox
                    margin_left = 30
                    if image_metadata.pre_control_rect and image_metadata.control_rect:
                        if (
                            image_metadata.pre_control_rect.left - margin_left <= image_metadata.control_rect.left and
                            image_metadata.pre_control_rect.top <= image_metadata.control_rect.top and
                            image_metadata.pre_control_rect.right + margin_right >= image_metadata.control_rect.right and
                            image_metadata.pre_control_rect.bottom - margin_bottom >= image_metadata.control_rect.bottom
                        ):
                            LOGGER_DEBUG(f"Control rectangle is within the pre-control rectangle. Skipping pre-control image capture.", "YELLOW")
                            ignore_pre_control_image = True
                if not ignore_pre_control_image:
                    pre_control_image_output = image_handler.capture_image_from_currentBoundingRectangle(image_metadata.pre_control_rect, left_extra=margin_left)
                    pre_control_image = pre_control_image_output.img
                    pre_control_image_bytes = pre_control_image_output.byte_data
                    previous_control_image_path = str(Path(self.pre_control_image_directory_path) / f"{image_name}.jpg") if pre_control_image else None
                    image_handler.save_image(image_name, img=pre_control_image, output_path=self.pre_control_image_directory_path.as_posix())

            # Insert control action history with image hash
            self.control_db.insert_control_action_history(description, control_type, control_id, image_name, control_image_bytes, None, None, img_hash)
            return control_image_path, previous_control_image_path, control_image_bytes, pre_control_image_bytes
            
        except Exception as e:
            LOGGER_ERROR(f"Record image error: {e}", "RED")
            return None, None, None, None

    def record_window_image(self):
        try:
            window_image_path = None
            window_image_bytes = None  # Initialize to None
            rect_metadata = self.control_metadata.get_control_image_metadata()
            if not rect_metadata or not rect_metadata.root_window_rect:
                LOGGER_INFO("Refresh the rect_metadata", "YELLOW")
                rect_metadata = self.control_metadata.get_control_image_metadata()
            info_metadata = self.control_metadata.get_control_metadata()
            description = info_metadata.get('name')
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{timestamp}_{preProcessString(description)}"

            if rect_metadata.root_window_rect:
                if rect_metadata.is_window_without_title:
                    window_image_output = image_handler.capture_image_from_currentBoundingRectangle(rect_metadata.root_window_rect, top_extra=27)
                else:
                    window_image_output = image_handler.capture_image_from_currentBoundingRectangle(rect_metadata.root_window_rect)
                window_image = window_image_output.img
                window_image_bytes = window_image_output.byte_data
                window_image_path = str(Path(self.window_image_directory_path) / f"{image_name}.jpg")
                image_handler.save_image(image_name, img=window_image, output_path=WINDOW_IMAGE_PATH.as_posix())
            else:
                LOGGER_WARNING(f"No root_window_rect available for window image capture", "YELLOW")

            # self.control_db.update_control_image(control_id_hash, window_image_bytes, 'control_id_hash')
            return window_image_path, window_image_bytes
            
        except Exception as e:
            LOGGER_ERROR(f"Record image error: {e}", "RED")
            return None, None

    def capture_foreground_window_image(self):
        """Fallback window capture using Win32 GetForegroundWindow.

        Called when UIA ancestor traversal cannot resolve root_window_rect (e.g. during
        a window transition, after a popup closes, or when the UIA element is stale).
        Uses the Win32 foreground window rect — the same bounding-rectangle approach as
        the normal UIA path — so the captured image is scoped to the current window,
        not the full screen.

        Returns (image_path, image_bytes), or (None, None) on failure.
        """
        try:
            import win32gui
            from ctypes.wintypes import RECT

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                LOGGER_WARNING("[window fallback] No foreground window found", "YELLOW")
                return None, None

            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            fg_rect = RECT(left, top, right, bottom)
            window_image_output = image_handler.capture_image_from_currentBoundingRectangle(fg_rect)
            if not window_image_output or not window_image_output.img:
                LOGGER_WARNING("[window fallback] Foreground window capture returned empty image", "YELLOW")
                return None, None

            window_title = win32gui.GetWindowText(hwnd) or "foreground_window"
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{timestamp}_{preProcessString(window_title)}"
            window_image_path = str(Path(self.window_image_directory_path) / f"{image_name}.jpg")
            image_handler.save_image(image_name, img=window_image_output.img, output_path=WINDOW_IMAGE_PATH.as_posix())
            LOGGER_INFO(f"[window fallback] Foreground window image saved: {image_name}", "YELLOW")
            return window_image_path, window_image_output.byte_data

        except Exception as e:
            LOGGER_WARNING(f"[window fallback] Foreground window capture failed: {e}", "YELLOW")
            return None, None


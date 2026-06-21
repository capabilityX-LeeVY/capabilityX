from core.mac.RSApplication import CRSApplication
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
import pandas as pd
from core.mac.RSKeyboard import CRSKeyboard
from typing import Optional
from config.paths import FULLSCREEN_IMAGE_PATH, SETTINGS_PATH
from core.structsDef import TestCase, TestSuite,TestCaseBatch,Step, StepAction
import os
import time
import datetime
import subprocess
from core.mac.GTMetaData import GTMetaDataMgr,GTMetaDataItem
from common.handler.settingsHandler import DynamicConfig
from config.paths import CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH,report_path,SESSION_OUTPUT_PATH
from core.processor.focus_processor import FocusRingProcessor
from typing import Optional
from core.mac.AXClasses import NativeUIElement
import threading
import re

class CRSActionResult(object):
    _instance_lock = threading.Lock()
    def __init__(self) -> None:
        pass

    def __new__(cls, *args, **kwargs):
        _instance_lock = threading.Lock()
        if not hasattr(CRSActionResult, "_instance"):
            with CRSActionResult._instance_lock:
                if not hasattr(CRSActionResult, "_instance"):
                    CRSActionResult._instance = object.__new__(cls)
                    CRSActionResult._instance.init()
                    
        return CRSActionResult._instance
    
    def init(self):
        self.result = {}

    def set_result(self, key: str, value):
        self.result[key] = value

    def get_result(self, key: str):
        return self.result.get(key, None)
    
    @staticmethod
    def GetInstance():
        return CRSActionResult()
    
    @staticmethod
    def SetActionResult(key: str, value):
        instance = CRSActionResult.GetInstance()
        instance.set_result(key, value)
    
    @staticmethod
    def GetActionResult(key: str):
        instance = CRSActionResult.GetInstance()
        return instance.get_result(key)
    
class CRSTestCase(object):
    pass

class CRSGTReport(object):
    def __init__(self):
        self.reportFolder = report_path
        if not os.path.exists(self.reportFolder):
            os.makedirs(self.reportFolder)
    

    def formatTestCaseReport(self, caseName:str,reportData:pd.DataFrame) -> str:
        columns = reportData.columns.tolist()
        report = f""
        tableHead = "|" + "|".join(columns) + "|\n"
        tableSeparator = "|" + "|".join(["---"] * len(columns)) + "|\n"
        markdown_table = tableHead + tableSeparator

        for _,row in reportData.iterrows():
            markdown_table += "|"
            for col in columns:
                value = row[col]
                markdown_table += f"{value}|"
            markdown_table += "\n"
        return report + markdown_table + "\n\n"
    

    def writeTestSuiteReport(self, suiteName:str, caseReports: list) -> str:
        reportPath = os.path.join(self.reportFolder,f"GT_Mac_{suiteName}_report_{int(time.time())}.md")
        report = f"# Test Suite: [{suiteName}]\n\n"
        for caseReport in caseReports:
            report += caseReport
        with open(reportPath, "w", encoding="utf-8") as f:
            f.write(report)
        return reportPath

    def write_report(self,caseName:str,reportData:pd.DataFrame,stream=False) -> str:
        reportPath = os.path.join(self.reportFolder,f"GT_Mac_{caseName}_report_{int(time.time())}.md")
        columns = reportData.columns.tolist()
        tableHead = "|" + "|".join(columns) + "|\n"
        tableSeparator = "|" + "|".join(["---"] * len(columns)) + "|\n"
        markdown_table = tableHead + tableSeparator

        for _,row in reportData.iterrows():
            markdown_table += "|"
            for col in columns:
                value = row[col]
                markdown_table += f"{value}|"
            markdown_table += "\n"
        
        if stream == True:
            print(f"Report for test case [{caseName}]:\n")
            #print(markdown_table)
            return markdown_table
        
        with open(reportPath, "w", encoding="utf-8") as f:
            f.write(markdown_table)

        LOGGER_INFO(f"Test case report written to: {reportPath}")

        return reportPath

class CRSApplicationGT(CRSApplication):
    def __init__(self,dbConnection = None) -> None:
        super().__init__(dbConnection)
        self.metadataMgr = None
        # Initialize FocusRingProcessor for focus ring validation
        self.focus_ring_processor = FocusRingProcessor(
            image_output_path=CONTROL_IMAGE_PATH,
            results_output_path=FOCUS_RING_RESULT_PATH
        )        
    
    def loadControlMetadata(self):
        self.metadataMgr = GTMetaDataMgr()
        self.metadataMgr.LoadAndSaveGTMetaData()

    def initGTApplication(self):
        self.loadControlMetadata()
        settings = DynamicConfig(SETTINGS_PATH)
        bundleID = settings.get("bundleID") or "Cisco-Systems.Spark"
        LOGGER_INFO(f"Initializing GT application with bundleID: {bundleID}")
        self.RaiseFirstWindow(bundleID=bundleID)
        time.sleep(1)

class CRSGTAction(object):
    def __init__(self, stepName: Optional[str], stepAction: StepAction) -> None:
        self.action = stepAction
        self.lastAICheckResult = None
        self.step_name = stepName

    def DoAction(self, application=None):
        if self.action.type == "key":
            if self.action.value == "default":
                CRSKeyboard.SpaceKeyPressed()
            elif self.action.value == "tab":
                CRSKeyboard.TabKeyPressed()
            elif self.action.value == "esc":
                CRSKeyboard.ESCPressed()
            else:
                message = f"Unsupported key action value: {self.action.value}"
                LOGGER_ERROR(message)
                raise Exception(message)
            
        elif self.action.type == "input":
            from config.account_config import account_config
            
            settings = DynamicConfig(SETTINGS_PATH)
            account = settings.get("account")
            if self.action.value is not None:
                input_text = self.action.value
                if self.action.value == "${email}":
                    input_text = account_config.get_email(account)
                    if input_text is None:
                        message = f"Account '{account}' does not have an email configured."
                        LOGGER_ERROR(message)
                        raise Exception(message)
                elif self.action.value == "${password}":
                    input_text = account_config.get_password(account)
                    if input_text is None:
                        message = f"Account '{account}' does not have a password configured."
                        LOGGER_ERROR(message)
                        raise Exception(message)
                elif self.action.value == "{ai_check_result}":
                    input_text = self.lastAICheckResult
                    if input_text is None:
                        message = f"No AI check result available for input action."
                        LOGGER_ERROR(message)
                        raise Exception(message)
                else:
                    groups = re.findall(r"\$\{([^{}]*?)\}", self.action.value)
                    for group in groups:
                        value = CRSActionResult.GetActionResult(group)
                        if value is not None:
                            input_text = value
                            break
                    
                subprocess.run("pbcopy", text=True, input=str(input_text))
                CRSKeyboard.CommandV()
            else:
                message = "Input action requires a value."
                LOGGER_ERROR(message)
                raise Exception(message)
            
        elif self.action.type == "shortcut" or self.action.type == "direct_key":
            from common.utils.shortcuts import ShortcutsHandler
            shutcutsHandler = ShortcutsHandler()
            shortcut = shutcutsHandler.get_shortcut(self.action.value, platform='mac')
            if shortcut is not None:
                CRSKeyboard.SendKeys(shortcut)
            else:
                message = f"Shortcut '{self.action.value}' not found for mac."
                LOGGER_ERROR(message)
                raise Exception(message)
        elif self.action.type == "function":
            from core.mac.GTFunction import GTFunction
            f = GTFunction()
            if self.action.value is None:
                message = "required function name is missing in action parameters."
                LOGGER_ERROR(message)
                raise Exception(message)
            
            parameters = {}
            parameters["step_name"] = self.step_name
            if self.action.parameters is not None:
                parameters.update(self.action.parameters)
            
            # Auto-inject app_ref from application context (like Windows injects webex_main_pid)
            if application is not None and hasattr(application, 'nativeUIElement') and application.nativeUIElement is not None:
                parameters["app_ref"] = application.nativeUIElement

            result = f.call_by_name(self.action.value, **parameters)
            if self.action.save_to is not None:
                CRSActionResult.SetActionResult(self.action.save_to, result)

            if self.action.wait_time and self.action.wait_time > 0:
                time.sleep(float(self.action.wait_time))

            return result
        elif self.action.type == "api":
            from core.mac.GTAPI import GTAPI
            api = GTAPI()
            if self.action.value is None:
                message = "GTAPI,required function name is missing in action parameters."
                LOGGER_ERROR(message)
                raise Exception(message)
            
            parameters = {}
            parameters["step_name"] = self.step_name
            if self.action.parameters is not None:
                parameters.update(self.action.parameters)
            
            if self.action.agent_node is None:
                message = "GTAPI,required agent_node is missing in action parameters for api action type."
                LOGGER_ERROR(message)
                raise Exception(message)
            
            parameters["agent_node"] = self.action.agent_node
            parameters["parameters"] = self.action.parameters
            result = api.call_by_name(self.action.value, **parameters)
            if self.action.save_to is not None:
                CRSActionResult.SetActionResult(self.action.save_to, result)

            return result
        
        elif self.action.type == "local_api":
            if self.action.value is None:
                message = "required function name is missing in action parameters."
                LOGGER_ERROR(message)
                raise Exception(message)
            
            if self.action.parameters is not None:
                for key, value in self.action.parameters.items():
                    CRSActionResult.SetActionResult(key, value)
            
            from core.mac.GTManager import GTManager
            settings = DynamicConfig(SETTINGS_PATH)
            language = settings.get("language") or "en_US"
            return GTManager.run_by_file(self.action.value, language=language) 

        elif self.action.type == "acc_sequence":
            _VALUE_MAP = {
                "tab":       ("tab",       CRSKeyboard.TabKeyPressed),
                "shift+tab": ("shift_tab", CRSKeyboard.ShiftTabPressed),
                "shift_tab": ("shift_tab", CRSKeyboard.ShiftTabPressed),
            }
            raw_value = (self.action.value or "tab").strip().lower()
            direction_name, press_fn = _VALUE_MAP.get(raw_value, ("tab", CRSKeyboard.TabKeyPressed))

            LOGGER_INFO(f"[acc_sequence] Starting full-circle traversal [direction={direction_name}]", "CYAN")

            if application is None:
                message = "[acc_sequence] application context is required but was not provided."
                LOGGER_ERROR(message)
                raise Exception(message)

            def _get_focused():
                return application.GetFocusedUIElement()

            def _elem_id(el):
                try:
                    parts = [el.avaliableInfo or "", el.role or "", el.identifier or ""]
                    combined = "|".join(parts)
                    return combined if any(p.strip() for p in parts) else ""
                except Exception:
                    return ""

            start_el = _get_focused()
            if start_el is None:
                press_fn()
                start_el = _get_focused()
            start_id = _elem_id(start_el) if start_el else ""
            start_name = (start_el.avaliableInfo or "(unknown)") if start_el else "(none)"
            LOGGER_INFO(f"[acc_sequence] Start element: [{start_name}]", "CYAN")

            _MAX_STEPS = 300
            controls_visited = 0
            order = 0
            while True:
                order += 1
                current_el = _get_focused()
                current_id = _elem_id(current_el) if current_el is not None else ""
                current_name = (current_el.avaliableInfo or "(unknown)") if current_el is not None else "(none)"

                if order > 1 and start_id and current_id and current_id == start_id:
                    LOGGER_INFO(
                        f"[acc_sequence] Full circle completed "
                        f"[direction={direction_name}][steps={order - 1}]", "GREEN"
                    )
                    break

                # Safety guard
                if order > _MAX_STEPS:
                    LOGGER_WARNING(
                        f"[acc_sequence] Max steps ({_MAX_STEPS}) reached, stopping "
                        f"[direction={direction_name}]"
                    )
                    break

                LOGGER_INFO(f"[acc_sequence][{order}] current: [{current_name}] → pressing {direction_name}", "CYAN")
                press_fn()
                controls_visited += 1
                after_el = _get_focused()
                after_name = (after_el.avaliableInfo or "(unknown)") if after_el is not None else "(none)"
                LOGGER_INFO(f"[acc_sequence][{order}] after:   [{after_name}]", "CYAN")

            LOGGER_INFO(
                f"[acc_sequence] Full-circle traversal completed "
                f"[direction={direction_name}][controls visited={controls_visited}]", "GREEN"
            )
            return direction_name

        else:
            message = f"Unsupported action type: {self.action.type}"
            LOGGER_ERROR(message)
            raise Exception(message)

        if self.action.wait_time and self.action.wait_time > 0:
            time.sleep(float(self.action.wait_time))

        if self.action.parameters is not None:
            message = f"Unsupported parameter key: { self.action.parameters}"
            LOGGER_ERROR(message)
            raise Exception(message)

        if self.action.agent_node is not None:
            message = f"Unsupported agent_node key: { self.action.agent_node}"
            LOGGER_ERROR(message)
            raise Exception(message)

class CRSGTStep(object):
    def __init__(self, step: Step, language = "en_US") -> None:
        self.step = step
        self.language = language
        self.b_ai_check = True
        self.b_navigate_check = True
        self.b_focus_ring_check = True
        self.controlImagePath = None
        self.windowImagePath = None
        self.verifyResult = {}
        self.lastAICheckResult = None

    def _absolute_To_Relative_path(self, path: str) -> str:
        return os.path.relpath(path, start=report_path)
    

    def _toImageRelativePath(self, image_full_path: str) -> str:
        if image_full_path is None:
            return "N/A"
        path = self._absolute_To_Relative_path(image_full_path)
        file_name = os.path.basename(image_full_path)
        image_html = f'<img src="{path}" alt="{file_name}" style="max-width: 300px; height: auto;">'
        return image_html

    def _verifyResultInit(self): 
        self.verifyResult["caseName"] = "N/A"
        self.verifyResult["Steps"] = "N/A"
        self.verifyResult["step_name"] = self.step.name
        self.verifyResult["control_Name"] = "N/A"
        self.verifyResult["control_image_path"] = "N/A"
        self.verifyResult["window_image_path"] = "N/A"
        self.verifyResult["focus_ring"] = "N/A"
        self.verifyResult["Next focusedUI"] = "N/A"
        self.verifyResult["KB Navigate"] = "N/A"
        self.verifyResult["UI Response"] = "N/A"
        self.verifyResult["AI Check"] = "N/A"
        self.verifyResult["Memory"] = "N/A"

    def _run_normal_step(self, application: CRSApplicationGT):
        real_control = GTMetaDataMgr().get_metadata_item_by_name(self.step.name)
        
        finded = False
        if real_control is not None and real_control.isEmpty() == False:
            self.verifyResult["step_name"] = real_control.name
            name = GTMetaDataMgr.getL18NMetadataByName(real_control.control_name, self.language)
            regex_name = GTMetaDataMgr.getL18NMetadataByName(real_control.control_name_regex, self.language)

            if real_control.control_name is not None:
                if name is None:
                    LOGGER_ERROR(f"Control name for step '{self.step.name}' is None after localization.")
                    raise Exception(f"Control name for step '{self.step.name}' is None after localization.")
                
                LOGGER_INFO(f"Finding control by name: {name}")
                finded,uiElement = application.FindControlBy(controlName=name)

            if not finded and real_control.control_name_regex is not None:
                if regex_name is None:
                    LOGGER_ERROR(f"Control name regex for step '{self.step.name}' is None after localization.")
                    raise Exception(f"Control name regex for step '{self.step.name}' is None after localization.")
                
                LOGGER_INFO(f"Finding control by name regex: {regex_name}")
                finded,uiElement = application.FindControlBy(controlNameReg=regex_name)

            if finded:
                res = self.Verify_FocusRing(application,uiElement)
                if res == False:
                    message = f"Focus ring verification failed for step '{self.step.name}'."
                    LOGGER_ERROR(message)
                    #raise Exception(message)
                
                if self.step.action is not None:
                    action = CRSGTAction(self.step.name, self.step.action)
                    action.lastAICheckResult = self.lastAICheckResult
                    action.DoAction(application)
                    if self.step.wait_time and self.step.wait_time > 0:
                        time.sleep(float(self.step.wait_time))

                    self.Verify_KB_Navigate(application=application)
            else:
                if self.step.optional and self.step.optional == True:
                    LOGGER_WARNING(f"Optional step '{name}' not found. Continuing to next step.")
                    self.verifyResult["Next focusedUI"] = "NA"
                    return

                # try again after 5 seconds
                time.sleep(5)
                if real_control.control_name is not None:
                    if name is None:
                        LOGGER_ERROR(f"Control name for step '{self.step.name}' is None after localization.")
                        raise Exception(f"Control name for step '{self.step.name}' is None after localization.")
                    
                    LOGGER_INFO(f"Finding control by name: {name}")
                    finded,uiElement = application.FindControlBy(controlName=name)

                if not finded and real_control.control_name_regex is not None:
                    if regex_name is None:
                        LOGGER_ERROR(f"Control name regex for step '{self.step.name}' is None after localization.")
                        raise Exception(f"Control name regex for step '{self.step.name}' is None after localization.")
                    
                    LOGGER_INFO(f"Finding control by name regex: {regex_name}")
                    finded,uiElement = application.FindControlBy(controlNameReg=regex_name)

                if finded:
                    res = self.Verify_FocusRing(application,uiElement)
                    if res == False:
                        message = f"Focus ring verification failed for step '{self.step.name}'."
                        LOGGER_ERROR(message)
                        #raise Exception(message)
                    
                    if self.step.action is not None:
                        action = CRSGTAction(self.step.name, self.step.action)
                        action.lastAICheckResult = self.lastAICheckResult
                        action.DoAction(application)

                    self.Verify_KB_Navigate(application=application)
                else:
                    message = f"Step [{name}] not found and is not optional. Aborting test case."
                    LOGGER_ERROR(message)
                    raise Exception(message)
        else:
            message = f"Control metadata for step '{self.step.name}' not found."
            LOGGER_ERROR(message)
            raise Exception(message)

    def Verify_AI_Check(self,application: CRSApplicationGT) -> bool:
        if self.b_ai_check == False:
            self.verifyResult["AI Check"] = "N/A"
            return True
        
        if self.step.ai_check is None or self.step.ai_check == "":
            self.verifyResult["AI Check"] = "N/A"
            return True
        
        prompt = self.step.ai_check.get("prompt", None)
        reference = self.step.ai_check.get("reference", None)
        image_name = self.step.ai_check.get("image_name", None)
        source = self.step.ai_check.get("source", None)
        if prompt is None:
            return False
        
        groups = re.findall(r"\$\{([^{}]*?)\}", prompt)
        for group in groups:
            value = CRSActionResult.GetActionResult(group)
            if value is not None:
                prompt = prompt.replace(f"${{{group}}}", str(value))

        imagePath = self.windowImagePath
        if source is None:
            imagePath = self.windowImagePath  
        elif source == "control":
            imagePath = self.controlImagePath
        elif source == "window":
            imagePath = self.windowImagePath
        elif source == "fullscreen":
            if image_name is not None:
                imagePath = os.path.join(FULLSCREEN_IMAGE_PATH, f'''{image_name}.jpg''')
            else:
                raise Exception("Image name must be provided for fullscreen source in AI check.")
            
        if imagePath is None or os.path.exists(imagePath) == False:
            message = f"No window image available for AI check: {imagePath}"
            LOGGER_ERROR(message)
            self.verifyResult["AI Check"] = "❌ Failed - No window image available"
            return False
        
        LOGGER_INFO(f"Performing AI check with prompt: {prompt}, reference: {reference}, imagePath: {imagePath}")
        result = "N/A"
        if reference is not None:
            from config.paths import DATASET_IMG_FOLDER_PATH
            fullPath = os.path.join(DATASET_IMG_FOLDER_PATH, reference)
            result = application.ai_processor.handle_ai_check_report(fullPath, imagePath, prompt)
        else:
            result = application.ai_processor.handle_ai_check_report(None, imagePath, prompt)
        
        self.verifyResult["AI Check"] = result

    def Verify_KB_Navigate(self, application: CRSApplicationGT) -> bool:
        if self.step.expect_state is None or self.step.expect_state == "":
            self.verifyResult["Next focusedUI"] = "N/A"
            self.verifyResult["KB Navigate"] = "N/A"
            return True
        
        if self.b_navigate_check == False:
            self.verifyResult["Next focusedUI"] = "N/A"
            self.verifyResult["KB Navigate"] = "N/A"
            return True
        
        focuse = application.GetFocusedUIElement()
        if focuse is None:
            message = "No focused UI element found."
            self.verifyResult["Next focusedUI"] = "No focused UI element"
            self.verifyResult["KB Navigate"] = "❌ Failed"
            LOGGER_ERROR(message)
            return False
        
        # AXWindow role is not supported by compiled code — skip verification
        if focuse.role == "AXWindow":
            LOGGER_WARNING(f"Focused element is AXWindow during KB navigate check, skipping.")
            self.verifyResult["Next focusedUI"] = "AXWindow"
            self.verifyResult["KB Navigate"] = "N/A"
            return True
        
        if focuse.isVerifyable() == False:
            message = "Focused UI element is not verifyable."
            self.verifyResult["Next focusedUI"] = "Focused UI element is not verifyable."
            self.verifyResult["KB Navigate"] = "N/A"
            LOGGER_ERROR(message)
            return True
        
        focuseInfo = focuse.avaliableInfo
        if isinstance(self.step.expect_state, str) == True:
            self.step.expect_state = GTMetaDataMgr.getL18NMetadataByName(self.step.expect_state, self.language)
            if focuseInfo == self.step.expect_state:
                self.verifyResult["KB Navigate"] = "✅Success"
                return True
            else:
                self.verifyResult["KB Navigate"] = f"❌Failed. Expected: [{self.step.expect_state}], Actual: [{focuseInfo}]"
                #raise Exception(f"Verification failed. Expected: [{self.step.expect_state}], Actual: [{focuseInfo}]")

        if isinstance(self.step.expect_state, (list, tuple)) == True:
            if focuseInfo in self.step.expect_state:
                self.verifyResult["KB Navigate"] = "✅Success"
                return True
            else:
                self.verifyResult["KB Navigate"] = f"❌Failed. Expected: [{self.step.expect_state}], Actual: [{focuseInfo}]"
                #raise Exception(f"Verification failed. Expected: [{self.step.expect_state}], Actual: [{focuseInfo}]")

    def Verify_FocusRing(self, application: CRSApplicationGT,currentElement:Optional['NativeUIElement']) -> bool:
        # verify focus ring
        if currentElement is None:
            message = "Current element is None for focus ring verification."
            LOGGER_ERROR(message)
            self.verifyResult["focus_ring"] = "Element is None"
            self.verifyResult["control_image_path"] = "N/A"
            self.verifyResult["control_Name"] = "N/A"
            self.verifyResult["window_image_path"] = "N/A"
            self.verifyResult["Memory"] = "N/A"
            return False
        
        # AXWindow role is not supported by compiled code — skip verification
        if currentElement.role == "AXWindow":
            LOGGER_WARNING(f"Focused element is AXWindow for step '{self.step.name}', skipping focus ring verification.")
            self.verifyResult["focus_ring"] = "N/A (AXWindow)"
            self.verifyResult["control_image_path"] = "N/A"
            self.verifyResult["control_Name"] = "AXWindow"
            self.verifyResult["window_image_path"] = "N/A"
            self.verifyResult["Memory"] = "N/A"
            return True
        
        memory = currentElement.getMemoryUsage()
        self.verifyResult["Memory"] = f"{memory} MB"
        self.verifyResult["control_Name"] = currentElement.avaliableInfo
        currentWin = application._findTopWindow(currentElement)
        imagesPath = application.controlRecorder.cropControlImage(currentElement=currentElement, preElement=None)
        window_image_path = application.controlRecorder.cropWindowImage(windowElement=currentWin)
        self.controlImagePath = imagesPath
        self.windowImagePath = window_image_path
        if imagesPath is None or len(imagesPath) == 0:
            message = f"Failed to capture control image for focus ring verification of control '{self.step.name}'."
            LOGGER_ERROR(message)
            self.verifyResult["focus_ring"] = "Failed to capture control image or image capture not enabled"
            self.verifyResult["control_image_path"] = "N/A"
            self.verifyResult["window_image_path"] = "N/A"
            return False
    
        if self.b_focus_ring_check == False:
            self.verifyResult["focus_ring"] = "N/A"
            self.verifyResult["control_image_path"] = "N/A"
            self.verifyResult["window_image_path"] = "N/A"
            self.verifyResult["Memory"] = "N/A"
            return True
        
        res = application.focus_ring_processor.validate_image_focused_status(image_full_path=imagesPath[0])
        self.verifyResult["focus_ring"] = res
        self.verifyResult["control_image_path"] = self._toImageRelativePath(imagesPath[0])
        self.verifyResult["window_image_path"] = self._toImageRelativePath(window_image_path)
        if res.find("✅Success") == -1:
            LOGGER_ERROR(f"Focus ring validation failed for control '{self.step.name}': {res}")
            return False    
        
        return True

    def getCurrentFocusedElement(self, application: CRSApplicationGT) -> Optional['NativeUIElement']:
        focused = application.GetFocusedUIElement()
        if focused is None:
            message = "No focused UI element found."
            LOGGER_ERROR(message)
            return None
        
        # If focus is on AXWindow, press Tab to move focus to an actual control
        if focused.role == "AXWindow":
            LOGGER_INFO(f"Focused element is AXWindow, pressing Tab to move focus to a child control.")
            CRSKeyboard.TabKeyPressed()
            focused = application.GetFocusedUIElement()
            if focused is None:
                LOGGER_ERROR("No focused UI element found after Tab from AXWindow.")
                return None
        
        return focused

    def _capture_fullscreen_for_report(self):
        """Capture a fallback screenshot for report rows that have no focused UI element."""
        try:
            from rs_sdk.utils.image_handler import capture_full_screen, save_image

            safe_step_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(self.step.name or "unknown_step")).strip("_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{timestamp}_{safe_step_name or 'unknown_step'}"
            result = capture_full_screen(1)
            if result.img is None:
                LOGGER_ERROR(f"Failed to capture fallback fullscreen image for step '{self.step.name}'.")
                return

            image_path = save_image(image_name, img=result.img, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
            if image_path is None:
                LOGGER_ERROR(f"Failed to save fallback fullscreen image for step '{self.step.name}'.")
                return

            self.windowImagePath = image_path
            self.verifyResult["window_image_path"] = self._toImageRelativePath(image_path)
            self.verifyResult["control_image_path"] = "N/A"
            self.verifyResult["focus_ring"] = "N/A"
            LOGGER_INFO(f"Fallback fullscreen image saved for step '{self.step.name}': {image_path}")
        except Exception as exc:
            LOGGER_ERROR(f"Exception while capturing fallback fullscreen image for step '{self.step.name}': {exc}")
    
    def Run(self, application: CRSApplicationGT):
        self._verifyResultInit()
        if self.step is None:
            message = "Step is None."
            LOGGER_ERROR(message)
            raise Exception(message)
        if self.step.action is None or self.step.action.type is None:
            message = "Action type is None in step."
            LOGGER_ERROR(message)
            raise Exception(message)
        elif self.step.action.type in ["shortcut", "direct_key", "function", "local_api", "api", "acc_sequence"]:
            if self.step.action is not None:
                action = CRSGTAction(self.step.name, self.step.action)
                action.DoAction(application)
        else:
            self._run_normal_step(application)

        if getattr(application, "gt_initialized", True) is False:
            self._capture_fullscreen_for_report()
            self.Verify_AI_Check(application)
            return

        currentElement = self.getCurrentFocusedElement(application)
        if currentElement is not None:
            self.Verify_FocusRing(application, currentElement)
            self.Verify_AI_Check(application)
        else:
            self._capture_fullscreen_for_report()

class CRSTestCase(object):
    def __init__(self, case: TestCase, language = "en_US") -> None:
        self.case = case
        self.flag_do_post_condition = True
        self.flag_do_pre_condition = True
        self.flag_write_report = True
        self.language = language
        self.reportData = []
        self.lastAICheckResult = None
    
    def GetTestCaseName(self):
        from config.paths import TEST_CASES_PATH
        testName = os.path.relpath(self.case.case_full_path, start=str(TEST_CASES_PATH))
        if testName.endswith(".yaml"):
            testName = testName[:-5]

        return testName

    def WriteReport(self,stream=False):
        if self.case.is_specific_case():
            LOGGER_INFO(f"Skipping report generation for special case: {self.case.name}")
            return
        
        df = pd.DataFrame(self.reportData)
        desired_order = ["caseName", "Steps","step_name", "control_Name","window_image_path", "control_image_path", "UI Response", "KB Navigate","focus_ring","AI Check","Next focusedUI", "Memory"]
        df = df[desired_order]
        nameMap = {
            "caseName":"Test Case",
            "Steps":"Step Num",
            "step_name":"Step Name",
            "control_Name":"Control Description	",
            "control_image_path":"Control Image",
            "window_image_path":"Window Image",
            "focus_ring":"Focus Ring",
            "Next focusedUI":"Next Focused UI",
            "UI Response":"UI Response Time",
            "KB Navigate":"KB Navigate",
            "Memory":"Total Memory"
            }
        df = df.rename(columns=nameMap)
        report = CRSGTReport()
        reportPath = report.write_report(self.case.name, df, stream=stream)

        #print(df)
        LOGGER_INFO(f"Test case report written to: {reportPath}")

    def _run_special_case(self,progress_callback=None):
        if self.case.name == "uninstall Webex app":
            from tools.webexApp import appHandler
            appHandler.uninstallWebex()
            LOGGER_INFO("Webex application uninstalled successfully.")
        elif self.case.name == "install Webex app":
            from tools.webexApp import appHandler
            appHandler.installWebex()
            LOGGER_INFO("Webex application installed successfully.")
        elif self.case.name == "re-install Webex app":
            from tools.webexApp import appHandler
            appHandler.installWebex()
            LOGGER_INFO("Webex application re-installed successfully.")
        else:
            message = f"Unsupported special case: {self.case.name}"
            LOGGER_ERROR(message)
            raise Exception(message)
        if progress_callback is not None:
            progress_callback({
            "step": self.case.name,
            "status": "skipped",
            "message": f"Test case [{self.case.name}] skipped."
            })
            
    def Run(self,progress_callback=None):
        if self.case.is_specific_case():
            self._run_special_case(progress_callback=progress_callback)
            return
        
        if self.flag_do_pre_condition == True and self.flag_do_post_condition == True:
            LOGGER_WARNING(f"Starting test case: {self.case.name} (from file: {self.case.case_full_path})")
            
        if self.case.is_platform_supported("mac") == False:
            LOGGER_INFO(f"Skipping test case '{self.case.name}' as it is not supported on mac platform.")
            
            if progress_callback is not None:
                progress_callback({
                "step": self.case.name,
                "status": "skipped",
                "message": f"Test case [{self.case.name}] skipped."
                })

            return

        settings = DynamicConfig(SETTINGS_PATH)
        oldaccount = settings.get("account")
        #checkPoints = self.case.check_points
        if self.case.account is not None:
            settings.set("account", self.case.account)

        if self.case.pre_conditions is not None  and self.flag_do_pre_condition:
            for condition in self.case.pre_conditions:
                LOGGER_INFO(f"run the pre-condition case:[{condition.name}] for {self.case.name}")
                preCase = CRSTestCase(condition, self.language)
                preCase.flag_write_report = False
                preCase.flag_do_pre_condition = False
                preCase.Run()
                self.reportData.extend(preCase.reportData)
        
        application = CRSApplicationGT()
        application.gt_initialized = self.case.need_initialization is not False
        if application.gt_initialized:
            application.initGTApplication()
        else:
            LOGGER_INFO(f"Skipping GT application initialization for test case: {self.case.name}")
        lastTimeStamp = datetime.datetime.now()
        index = 1
        for _, step in enumerate(self.case.steps):
            if step.is_platform_supported("mac") == False:
                LOGGER_INFO(f"Skipping step '{step.name}' as it is not supported on mac platform.")
                continue
            crs_step = CRSGTStep(step, self.language)
            crs_step.lastAICheckResult = self.lastAICheckResult
            crs_step.Run(application)
            currentTimeStamp = datetime.datetime.now()
            stepDuration = currentTimeStamp - lastTimeStamp
            lastTimeStamp = currentTimeStamp
            crs_step.verifyResult["UI Response"] = f'{stepDuration.total_seconds():.2f}s'
            crs_step.verifyResult["caseName"] = self.GetTestCaseName()
            crs_step.verifyResult["Steps"] = index
            self.lastAICheckResult = crs_step.verifyResult.get("AI Check", None)
            self.reportData.append(crs_step.verifyResult)
            index = index + 1

        settings.set("account", oldaccount)
        
        if self.case.post_conditions is not None and self.flag_do_post_condition:
            for condition in self.case.post_conditions:
                LOGGER_INFO(f"run the post-condition case:[{condition.name}] for {self.case.name}") 
                postCase = CRSTestCase(condition,self.language)
                postCase.flag_write_report = False
                postCase.flag_do_post_condition = False
                postCase.flag_do_pre_condition = False
                postCase.Run()
                self.reportData.extend(postCase.reportData)

        if self.flag_write_report:
            self.WriteReport()

        if progress_callback is not None:
            progress_callback({
            "step": self.case.name,
            "status": "completed",
            "message": f"Test case [{self.case.name}] executed successfully."
            })
        time.sleep(5) # wait for 5 seconds after test case
        LOGGER_INFO(f"Finished test case: {self.case.name}")

class CRSGTTestSuite(object):
    def __init__(self, suite: TestSuite, language = "en_US") -> None:
        self.suite = suite
        self.language = language
        self.reportData = []
        self.lastAICheckResult = None

    def GetTestCaseName(self,case: TestCase):
        from config.paths import TEST_CASES_PATH
        testName = os.path.relpath(case.case_full_path, start=str(TEST_CASES_PATH)) # type: ignore
        if testName.endswith(".yaml"):
            testName = testName[:-5]

        return testName
    
    def WriteReport(self):
        reportFolder = report_path
        if not os.path.exists(reportFolder):
            os.makedirs(reportFolder)

        reportPath = os.path.join(reportFolder,f"GT_Mac_{self.suite.name}_report_{int(time.time())}.md")
        with open(reportPath, "w", encoding="utf-8") as f:
            f.writelines(self.reportData)
        LOGGER_INFO(f"Test case report written to: {reportPath}")

    def Run(self, progress_callback=None):
        LOGGER_WARNING(f"Starting test suite: {self.suite.name} (from file: {self.suite.suite_full_path})")
        # if self.suite.account is not None:
        #     settings = DynamicConfig(SETTINGS_PATH)
        #     settings.set("account", self.suite.account)

        for case in self.suite.test_cases:
            if case.is_platform_supported("mac") == False:
                LOGGER_INFO(f"Skipping test case '{case.name}' as it is not supported on mac platform.")

            if case.is_specific_case():
                case_special = CRSTestCase(case, self.language)
                case_special.Run(progress_callback=progress_callback)
      
        application = CRSApplicationGT()
        application.initGTApplication()
        
        lastTimeStamp = datetime.datetime.now()
        for case in self.suite.test_cases:
            index = 1
            if case.is_platform_supported("mac") == False:
                LOGGER_INFO(f"Skipping test case '{case.name}' as it is not supported on mac platform.")
            
                if progress_callback is not None:
                    progress_callback({
                    "step": case.name,
                    "status": "skipped",
                    "message": f"Test case [{case.name}] in suite [{self.suite.name}] skipped."
                    })
                continue

            if case.is_specific_case(): 
                continue
            self.reportData.append(f"## Test Case: [{self.GetTestCaseName(case)}]\n\n")
            stepResults = []
            for step in case.steps:
                if step.is_platform_supported("mac") == False:
                    LOGGER_INFO(f"Skipping step '{step.name}' as it is not supported on mac platform.")
                    continue
                crs_step = CRSGTStep(step, self.language)
                crs_step.lastAICheckResult = self.lastAICheckResult
                crs_step.Run(application)
                currentTimeStamp = datetime.datetime.now()
                stepDuration = currentTimeStamp - lastTimeStamp
                lastTimeStamp = currentTimeStamp
                crs_step.verifyResult["Steps"] = index
                crs_step.verifyResult["UI Response"] = f'{stepDuration.total_seconds():.2f}s'
                crs_step.verifyResult["caseName"] = self.GetTestCaseName(case)
                
                stepResults.append(crs_step.verifyResult)
                self.lastAICheckResult = crs_step.verifyResult.get("AI Check", None)
                index = index + 1
            
            reportHandel = CRSGTReport()
            df = pd.DataFrame(stepResults)
            nameMap = {
                "caseName":"Test Case",
                "Steps":"Step Num",
                "step_name":"Step Name",
                "control_Name":"Control Description	",
                "control_image_path":"Control Image",
                "window_image_path":"Window Image",
                "focus_ring":"Focus Ring",
                "Next focusedUI":"Next Focused UI",
                "UI Response":"UI Response Time",
                "KB Navigate":"KB Navigate",
                "Memory":"Total Memory"
                }
            df = df.rename(columns=nameMap)
            report = reportHandel.formatTestCaseReport(case.name, df)
            self.reportData.append(report)
            if progress_callback is not None:
                progress_callback({
                "step": case.name,
                "status": "completed",
                "message": f"Test case [{case.name}] in suite [{self.suite.name}] executed successfully."
                })

        time.sleep(3) # wait for 2 seconds after test case
        self.WriteReport()
        LOGGER_INFO(f"Finished test suite: {self.suite.name}")

class CRSGTTestCaseBatch(object):
    def __init__(self, batch: TestCaseBatch, language = "en_US") -> None:
        self.batch = batch
        self.language = language
    
    def Run(self, progress_callback=None):
        LOGGER_WARNING(f"Starting test batch cases: {self.batch.name} (from file: {self.batch.batch_full_path})")
        results = {
            "passed": [],
            "failed": [],
            "skipped": []
        }
        for case in self.batch.test_cases:
            try:
                if case.is_platform_supported("mac") == False:
                    LOGGER_INFO(f"Skipping test case '{case.name}' as it is not supported on mac platform.")
                    
                    if progress_callback is not None:
                        progress_callback({
                        "step": case.name,
                        "status": "skipped",
                        "message": f"Test case [{case.name}] in batch [{self.batch.name}] skipped."
                        })
                    results["skipped"].append(case.name)
                    continue
                        
                CRSTestCase(case, self.language).Run(progress_callback=progress_callback)
                results["passed"].append(case.name)    
            except Exception as e:
                LOGGER_ERROR(f"Error while checking platform support for test case '{case.name}': {e}")
                failedInfo = {
                    "case": case.name,
                    "error": str(e),
                    "owner": case.owner
                }
                results["failed"].append(failedInfo)
                continue
            

        time.sleep(3) # wait for 2 seconds after test case
        LOGGER_INFO(f"Finished test batch cases: {self.batch.name}")


    
            
            


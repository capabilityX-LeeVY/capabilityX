import time
import sys
import AppKit
import core.mac as acchelp

from db.cloudMySQL import accData
from config.config import WAIT_CONTROLER_ACTION_TIME, ACCOUNT
from config.paths import FEATURE_TOGGLE_CONFIG_PATH
from core.mac._input import Keyboard
from core.mac.AXClasses import NativeUIElement
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from common.utils.featureToggle import FeatureToggle
from common.utils import deviceInfo
from tools.webexApp import appHandler
from common.handler import textHandler
import subprocess

FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)

def handleProcesses():
    language_code = deviceInfo.getSystemLanguageCode()
    results = accData.selectProcessSteps(language_code,processIDs = [0,1,2,3,4])
    processesNavigator = ProcessesNavigation()
    
    if results is not None:
        for _, row in results.iterrows():
            processesNavigator.navigateByTabForProcesses(row['controlName'], row['controlType'], row['controlIdentifier'], row['controlAction'], row['processName'], row['processID'], row['projectID'], row['controlActionWaitTime'])
    else:
        LOGGER_ERROR("No results found or an error occurred.")

class ProcessesNavigation:
    def __init__(self):
        frontmost_app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
        pid = frontmost_app.processIdentifier()
        self.AXApp = NativeUIElement.get_app_ref_by_pid(pid)
        self.controls_id = []

    def navigateByTabForProcesses(self, control_name, control_type, control_identifier, control_action, process_name, process_id, project_id, wait_time):
        while True:
            platform = appHandler.current_platform()
            is_found = False
            control_id = f"{control_name}|{control_type}|{control_identifier}"
            
            for control_changed_id in self.controls_id:
                if textHandler.textSimilarity(control_changed_id, control_id) > 0.8:
                    is_found = True

            control_changed = self.AXApp.focusedElement
            if control_changed is None:
                Keyboard().send_key(acchelp.Key.tab)
                control_changed = self.AXApp.focusedElement
                
            control_changed_id = f"{control_changed.avaliableInfo}|{control_changed.role}|{control_changed.identifier}"
            control_changed_avaliableInfo = control_changed.avaliableInfo

            if not self.isTraverseCompleted(control_changed_id):
                self.controls_id.append(control_changed_id)

            if textHandler.textSimilarity(control_changed_id, control_id) > 0.8:
                LOGGER_INFO(f">>>Run process via control [{control_changed_avaliableInfo}].")
                # accCore.recordControlLevel(control_changed, 0, process_name, process_id, keyboard_action=control_action, result="Pass", project_id=project_id)
                if FeatureToggle.isEnabled("devMode") and control_changed_id == ACCOUNT["control_username_id"]:
                    control_changed.set_string("AXValue", ACCOUNT["username"])
                elif FeatureToggle.isEnabled("devMode") and control_changed_id == ACCOUNT["control_password_id"]:
                    control_changed.set_string("AXValue", ACCOUNT["password"])
                elif control_action in dir(acchelp.Key):
                    Keyboard().send_key(getattr(acchelp.Key, control_action))
                else:
                    subprocess.run("pbcopy", text=True, input=str(control_action))
                    Keyboard().send_key_with_modifiers('v', [acchelp.Key.cmd_l,])
                    #control_changed.set_string("AXValue", control_action)
                
                time.sleep(wait_time)
                self.controls_id.clear()
                break
            elif self.isTraverseCompleted(control_changed_id) and not is_found:
                LOGGER_ERROR(f"Process control [{control_name}] not found.")
                if not appHandler.isActiveProcessSame(platform):
                    sys.exit("\033[1;31mNot on the correct App.\033[0m")
                break
            elif self.isTraverseCompleted(control_changed_id) and is_found and not appHandler.isActiveProcessSame(platform):
                sys.exit("\033[1;31mNot on the correct App.\033[0m")
            elif control_changed.role in ["AXRadioButton", "AXCell", "AXCheckbox", "AXTable"]:
                is_tab_action = True
                try:
                    Keyboard().send_key(acchelp.Key.up)
                    time.sleep(WAIT_CONTROLER_ACTION_TIME)
                    control_focus = self.AXApp.focusedElement
                    control_focus_id = f"{control_focus.avaliableInfo}|{control_focus.role}|{control_focus.identifier}"
                    if control_changed_id != control_focus_id:
                        is_tab_action = False
                except:
                    pass
                if is_tab_action:
                    try:
                        Keyboard().send_key(acchelp.Key.right)
                        time.sleep(WAIT_CONTROLER_ACTION_TIME)
                        control_focus = self.AXApp.focusedElement
                        control_focus_id = f"{control_focus.avaliableInfo}|{control_focus.role}|{control_focus.identifier}"
                        if control_changed_id != control_focus_id:
                            is_tab_action = False
                    except:
                        pass
                if is_tab_action:
                    LOGGER_INFO(f">>> Navigate by Tab to control [{control_name}] from control [{control_changed_avaliableInfo}] with control ID [{control_changed_id}].")
                    Keyboard().send_key(acchelp.Key.tab)
                else:
                    LOGGER_INFO(f">>> Navigate by Arrow to control [{control_name}] from control [{control_changed_avaliableInfo}] with control ID [{control_changed_id}].")
                time.sleep(WAIT_CONTROLER_ACTION_TIME)
            else:
                LOGGER_INFO(f">>> Navigate by Tab to control [{control_name}] from control [{control_changed_avaliableInfo}] with control ID [{control_changed_id}].")
                Keyboard().send_key(acchelp.Key.tab)
                time.sleep(WAIT_CONTROLER_ACTION_TIME)
    
    def isTraverseCompleted(self, control_changed_id):
            run_count = 0
            try_count = 0
            previous_control = None
            for control in self.controls_id:
                if control == control_changed_id and control != previous_control:
                    run_count += 1
                elif control == control_changed_id and control == previous_control:
                    try_count += 1
                    if try_count >= 5:
                        return True
                else:
                    try_count = 0
                previous_control = control
                if run_count > 1:
                    return True
            return False

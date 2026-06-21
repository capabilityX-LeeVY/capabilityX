import time
import sys
import core.mac as acchelp
import AppKit

from db.cloudMySQL import accData
from config.config import WAIT_CONTROLER_ACTION_TIME, ACCOUNT
from config.paths import FEATURE_TOGGLE_CONFIG_PATH
from core.mac._mixin._input import Keyboard
from core.mac.AXClasses import NativeUIElement
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG, LOGGER_WARNING
from common.utils.featureToggle import FeatureToggle
from common.utils import deviceInfo
from tools.webexApp import appHandler
from common.handler import textHandler
from db.cloudMySQL import accData
# from acc.common import accUIA
from acc.handler import accFocusRing

platform = appHandler.current_platform()

def traverseControls():
    last_control = handleNavigation()
    print("last control", last_control)
    # last_control = 'Test'
    if last_control:
        while True:
            results = accData.queryProcessControls(isProcessed=0)
            if results.empty:
                LOGGER_INFO("No new data to process. Exiting loop.")
                break
            time.sleep(2)
            for _, row in results.iterrows():
                try:
                    is_processed = Processes().run(
                        row['controlName'], row['controlType'], 
                        row['controlAutomationID'], row['controlBoundingRectangle'], 
                        row['controlNativeWindowHandle'], row['entryControl'], 
                        last_control, row['fromAction'], row['isLocationChanged'], row['isProcessed']
                    )
                    if is_processed:
                        accData.updateControl(row['navigationID'], isProcessed=1)
                except Exception as process_error:
                    LOGGER_ERROR(f"Error processing control {row['controlName']}: {process_error}")
    else:
        LOGGER_WARNING("Last control is not available.")


def handleNavigation(entry_control=None, entry_action='Tab', isNeedClose=False):
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    frontmost_app = workspace.frontmostApplication()
    pid = frontmost_app.processIdentifier()
    AXApp = NativeUIElement.get_app_ref_by_pid(pid)
    from_action = entry_action
    pre_control = None
    source_control = entry_control
    controls_id = []


    while True:
        is_found = False
        if source_control:
            source_control_id = f"{source_control.avaliableInfo}|{source_control.role}|{source_control.identifier}"
        else:
            source_control_id = None
        focused_control = AXApp.focusedElement
        if focused_control is None:
            Keyboard().send_key(acchelp.Key.tab)
            time.sleep(WAIT_CONTROLER_ACTION_TIME)
            focused_control = AXApp.focusedElement
        focused_control_id = f"{focused_control.avaliableInfo}|{focused_control.role}|{focused_control.identifier}"
        control_full_description = focused_control.description
        control_bounding_rect = (f"{focused_control.frame.x}, {focused_control.frame.y}, {focused_control.frame.width}, {focused_control.frame.height}")
        # if focused_control.role == 50004:
        #     control_focus_ring = accFocusRing.getImageFromRect(focused_control.CurrentBoundingRectangle, padding=15, isText=True)
        # else:
        #     control_focus_ring = accFocusRing.getImageFromRect(focused_control.CurrentBoundingRectangle)
        control_focus_ring = accFocusRing.getImageFromRect(focused_control.frame)
        if not pre_control and source_control:
            pre_control = source_control
        try:
            # if pre_control.role == 50004:
            #     pre_control_focus_ring = accFocusRing.getImageFromRect(pre_control.CurrentBoundingRectangle, padding=15, isText=True)
            # else:
            #     pre_control_focus_ring = accFocusRing.getImageFromRect(pre_control.CurrentBoundingRectangle)
            pre_control_focus_ring = accFocusRing.getImageFromRect(pre_control.frame)
        except:
            pre_control_focus_ring = None

        for control_id in controls_id:
            if textHandler.textSimilarity(focused_control_id, control_id) > 0.98:
                is_found = True

        if not isTraverseCompleted(focused_control_id, controls_id):
            controls_id.append(focused_control_id)
            if focused_control.avaliableInfo in ['Set a status']:
                isProcessed = 0
            else:
                isProcessed = 1
            if not isTraverseCompleted(focused_control_id, controls_id):
                data = (focused_control.avaliableInfo, focused_control.role, focused_control.identifier, control_full_description, control_bounding_rect, focused_control.CurrentNativeWindowHandle, focused_control_id, source_control_id, pre_control, from_action, control_focus_ring, pre_control_focus_ring, isProcessed)
                accData.insertDataToWindowsControls(data)
        if isTraverseCompleted(focused_control_id, controls_id) and is_found and not appHandler.isActiveProcessSame(platform):
            sys.exit("\033[1;31mNot on the correct App.\033[0m")
        elif isTraverseCompleted(focused_control_id, controls_id) and focused_control.role !=50007 and appHandler.isActiveProcessSame(platform):
            LOGGER_INFO("Traverse finished on the current layer.")
            if isNeedClose:
                Keyboard().send_key(acchelp.Key.esc)
            return pre_control
        elif focused_control.role in ["AXRadioButton", "AXCell", "AXCheckbox", "AXTable"] and not is_found:
            is_tab_action = True
            try:
                Keyboard().send_key(acchelp.Key.down)
                time.sleep(WAIT_CONTROLER_ACTION_TIME)
                control_focus_changed = AXApp.focusedElement
                control_focus_changed_id = f"{control_focus_changed.avaliableInfo}|{control_focus_changed.role}|{control_focus_changed.identifier}"
                if control_focus_changed_id != focused_control_id:
                    from_action = "Down"
                    is_tab_action = False
            except: 
                pass
            if is_tab_action:
                try:
                    Keyboard().send_key(acchelp.Key.right)
                    time.sleep(WAIT_CONTROLER_ACTION_TIME)
                    control_focus_changed = AXApp.focusedElement
                    control_focus_changed_id = f"{control_focus_changed.avaliableInfo}|{control_focus_changed.role}|{control_focus_changed.identifier}"
                    if control_focus_changed_id != focused_control_id:
                        from_action = "Right"
                        is_tab_action = False
                except:
                    pass
            if is_tab_action:
                LOGGER_INFO(f">>> Navigate to control [{focused_control_id}] by press Tab key.")
                from_action = "Tab"
                Keyboard().send_key(acchelp.Key.tab)
            else:
                LOGGER_INFO(f">>> Navigate to control [{focused_control_id}] by press arrow key.")
        else:
            time.sleep(WAIT_CONTROLER_ACTION_TIME)
            LOGGER_INFO(f">>> Navigate to control [{focused_control_id}] by press Tab key.")
            from_action = "Tab"
            Keyboard().send_key(acchelp.Key.tab)
        pre_control = focused_control


class Processes:
    def __init__(self):
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        frontmost_app = workspace.frontmostApplication()
        pid = frontmost_app.processIdentifier()
        self.AXApp = NativeUIElement.get_app_ref_by_pid(pid)
        self.controls_id = []

    def run(self, control_name, control_type, control_automationID, control_bounding_rectangle, control_native_window_handle, entry_control, pre_control, from_action, is_location_changed, is_processed):

        while True:
            is_found = False
            control_id = f"{control_name}|{control_type}|{control_automationID}"
            for focused_control_id in self.controls_id:
                if textHandler.textSimilarity(focused_control_id, control_id) > 0.98:
                    is_found = True

            try:
                focused_control = self.AXApp.focusedElement
            except:
                focused_control = None

            if focused_control is None:
                continue
            else:
                focused_control_id = f"{focused_control.avaliableInfo}|{focused_control.role}|{focused_control.identifier}"

            if not isTraverseCompleted(focused_control_id, self.controls_id):
                self.controls_id.append(focused_control_id)

            if textHandler.textSimilarity(control_id, focused_control_id) > 0.98:
                time.sleep(WAIT_CONTROLER_ACTION_TIME)
                LOGGER_INFO(f">>>Run process via control [{control_name}]")
                # recordControlLevel(control_changed, 0, process_name, process_id, keyboard_action=acc_action, result="Pass", project_id=project_id)
                # if FeatureToggle.isEnabled("devMode") and control_changed_id == ACCOUNT["control_username_id"]:
                #     auto.SendKeys(ACCOUNT["username"])
                # elif FeatureToggle.isEnabled("devMode") and control_changed_id == ACCOUNT["control_password_id"]:
                #     auto.SendKeys(ACCOUNT["password"])
                # else:
                #     auto.SendKeys(control_action)
                if focused_control.role and focused_control.role in ["AXButton", "AXRadioButton", "AXCell", "AXCheckbox", "AXTable"]:
                    # entry_control_id = focused_control_id
                    from_action = "Space"
                    Keyboard().send_key(acchelp.Key.space)
                    if is_processed == 0:
                        handleNavigation(focused_control, from_action, isNeedClose=True)

                self.controls_id.clear()
                break
            elif isTraverseCompleted(focused_control_id, self.controls_id) and focused_control.role not in [50007, 50025] and not is_found:
                LOGGER_ERROR(f"Process control [{control_name}] not found.")
                # recordControlLevel(control_name, 0, process_name, process_id, keyboard_action="Tab", result="Fail: Process control not found.")
                if not appHandler.isActiveProcessSame(platform):
                    sys.exit("\033[1;31mNot on the correct App.\033[0m")
                break
            elif isTraverseCompleted(focused_control_id, self.controls_id) and is_found and not appHandler.isActiveProcessSame(platform):
                    sys.exit("\033[1;31mNot on the correct App.\033[0m")
            elif focused_control.role in [50023, 50026, 50025, 50019, 50011, 50007] and not is_found:
                is_tab_action = True
                try:
                    Keyboard().send_key(acchelp.Key.down)           
                    time.sleep(WAIT_CONTROLER_ACTION_TIME)
                    control_focus_changed = self.AXApp.focusedElement
                    control_focus_changed_id = f"{control_focus_changed.avaliableInfo}|{control_focus_changed.role}|{control_focus_changed.identifier}"
                    if control_focus_changed_id != focused_control_id:
                        is_tab_action = False
                except: 
                    pass
                if is_tab_action:
                    try:
                        Keyboard().send_key(acchelp.Key.right)
                        time.sleep(WAIT_CONTROLER_ACTION_TIME)
                        control_focus_changed = self.AXApp.focusedElement
                        control_focus_changed_id = f"{control_focus_changed.avaliableInfo}|{control_focus_changed.role}|{control_focus_changed.identifier}"
                        if control_focus_changed_id != focused_control_id:
                            is_tab_action = False
                        if isTraverseCompleted(control_focus_changed_id, self.controls_id) and control_focus_changed.role == 50007:
                            is_tab_action = True
                    except:
                        pass
                if is_tab_action:
                    LOGGER_INFO(f">>> Navigate by Tab to control [{control_name}] from control [{focused_control_id}] with text_similarity [{textHandler.textSimilarity(control_id, focused_control_id)}].")
                    Keyboard().send_key(acchelp.Key.tab)
                else:
                    LOGGER_INFO(f">>> Navigate by arrow to control [{control_name}] from control [{focused_control_id}] with text_similarity [{textHandler.textSimilarity(control_id, focused_control_id)}].")
            else:
                time.sleep(WAIT_CONTROLER_ACTION_TIME)
                LOGGER_INFO(f">>> Navigate by Tab to control [{control_name}] from control [{focused_control_id}] with text_similarity [{textHandler.textSimilarity(control_id, focused_control_id)}].")
                Keyboard().send_key(acchelp.Key.tab)
        return True
        

def isTraverseCompleted(focused_control_id, controls_id):
    run_count = 0
    try_count = 0
    previous_control = None
    for control in controls_id:
        if control == focused_control_id and control != previous_control:
            run_count += 1
        elif control == focused_control_id and control == previous_control:
            try_count += 1
            if try_count >= 5:
                return True
        else:
            try_count = 0                                             
        previous_control = control
        if run_count > 1:
            return True
    return False

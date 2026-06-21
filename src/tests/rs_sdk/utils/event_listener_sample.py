import logging
import comtypes.client
import threading
import pythoncom
import traceback

from comtypes.client import GetModule
GetModule('oleacc.dll')
GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient
from comtypes import GUID
from comtypes.gen.UIAutomationClient import IUIAutomationFocusChangedEventHandler
from tests.rs_sdk.utils.control_sample import Control
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

UIA_CLSID = GUID('{FF48DBA4-60EF-4201-AA87-54103EEF594E}')
uia = comtypes.client.CreateObject(UIA_CLSID, interface=UIAutomationClient.IUIAutomation)

class FocusListener:
    """Class-based focus change event listener."""
    handler = None
    listener_thread = None
    running = False

    def __init__(self):
        self.current_focus = None
        self.previous_focus = None

    def _focus_change_listener(self):
        """Internal method to listen for focus change events."""
        try:
            self.handler = self.FocusChangedHandler(self)
            uia.AddFocusChangedEventHandler(None, self.handler)
            pythoncom.PumpMessages()
        except Exception as e:
            LOGGER_ERROR(f"Error in focusChangeListener: {e}")

    def start(self):
        """Start the focus change listener in a separate thread."""
        if self.running:
            LOGGER_WARNING("Focus listener is already running.")
            return
        pythoncom.CoInitialize()
        self.listener_thread = threading.Thread(target=self._focus_change_listener, daemon=True)
        self.listener_thread.start()
        self.running = True
        LOGGER_INFO("[Initialized][FocusListener] started.", "GREEN")

    def stop(self):
        """Stop the focus change listener and release resources."""
        if not self.running:
            LOGGER_WARNING("Focus listener is not running.")
            return
        try:
            if self.handler:
                uia.RemoveFocusChangedEventHandler(self.handler)
                logging.info("Focus change event handler removed.")
        except Exception as e:
            LOGGER_ERROR(f"Error in stopControlListener: {e}")
        finally:
            self.running = False
            LOGGER_INFO("Focus listener stopped.")

    class FocusChangedHandler(comtypes.COMObject):
        _com_interfaces_ = [IUIAutomationFocusChangedEventHandler]

        def __init__(self, listener):
            super().__init__()
            self.listener = listener

        def safe_get_attr(self, obj, attr, default=None):
            try:
                return getattr(obj, attr, default)
            except Exception as e:
                LOGGER_DEBUG(f"safe_get_attr failed for {attr}: {e}")
                return default

        def HandleFocusChangedEvent(self, sender):
            def _getUIAParent(control):
                tree_walker = uia.ControlViewWalker
                return tree_walker.GetParentElement(control)

            LOGGER_INFO("=== HandleFocusChangedEvent START ===")
            try:
                try:
                    name = self.safe_get_attr(sender, 'CurrentName')
                    control_type = self.safe_get_attr(sender, 'CurrentControlType')
                    LOGGER_INFO(f"[step0] Sender received: Name: {name}, Type: {control_type}")
                except Exception as e:
                    LOGGER_WARNING(f"[step0] Sender access failed, fallback needed: {e}\n{traceback.format_exc()}")
                    sender = uia.GetFocusedElement()
                    LOGGER_INFO(f"[step0-retry] Fallback to focused element: Name: {self.safe_get_attr(sender, 'CurrentName')}, Type: {self.safe_get_attr(sender, 'CurrentControlType')}")

                try:
                    control_type = self.safe_get_attr(sender, 'CurrentControlType', 0)
                    if control_type == 50026:
                        LOGGER_INFO("[step2] ControlType == 50026")
                        parent = _getUIAParent(sender)
                        parent_type = self.safe_get_attr(parent, 'CurrentControlType', 0)
                        LOGGER_INFO(f"[step2] Got parent: Name: {self.safe_get_attr(parent, 'CurrentName')}, Type: {parent_type}")

                        if parent and parent_type in [50023, 50024]:
                            LOGGER_INFO("[step2] Parent type matched, reassign sender to parent")
                            sender = parent
                        else:
                            LOGGER_INFO("[step2] Parent type not matched, fallback to GetFocusedElement()")
                            sender = uia.GetFocusedElement()

                    elif control_type == 50032:
                        LOGGER_INFO("[step2] ControlType == 50032, fallback to GetFocusedElement()")
                        sender = uia.GetFocusedElement()

                except Exception as e:
                    LOGGER_WARNING(f"[step2] Error in ControlType handling: {e}\n{traceback.format_exc()}")
                    sender = uia.GetFocusedElement()

                # refresh current_focus using singleton instance (previous_focus is updated in setter)
                try:
                    control_instance = Control()  # Get singleton instance
                    control_instance.current_focus = sender
                    LOGGER_INFO(f"[step3] current_focus updated to: Name: {self.safe_get_attr(sender, 'CurrentName')}, Type: {self.safe_get_attr(sender, 'CurrentControlType')}")
                except Exception as e:
                    LOGGER_WARNING(f"[refresh focus] Error updating focus: {e}\n{traceback.format_exc()}")

            except Exception as e:
                LOGGER_ERROR(f"[HandleFocusChangedEvent-outer-exception] {e}\n{traceback.format_exc()}")

            LOGGER_INFO("=== HandleFocusChangedEvent END ===")
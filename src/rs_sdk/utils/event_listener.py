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
from rs_sdk.utils.control import Control
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

            try:
                try:
                    name = self.safe_get_attr(sender, 'CurrentName')
                    control_type = self.safe_get_attr(sender, 'CurrentControlType')
                except Exception as e:
                    LOGGER_WARNING(f"[Failed] Sender access failed, fallback needed: {e}\n{traceback.format_exc()}")
                    try:
                        sender = uia.GetFocusedElement()
                        LOGGER_INFO(f"[retry] Fallback to focused element: Name: {self.safe_get_attr(sender, 'CurrentName')}, Type: {self.safe_get_attr(sender, 'CurrentControlType')}")
                    except Exception:
                        return

                try:
                    control_type = self.safe_get_attr(sender, 'CurrentControlType', 0)
                    if control_type == 50026:
                        parent = _getUIAParent(sender)
                        parent_type = self.safe_get_attr(parent, 'CurrentControlType', 0)

                        if parent and parent_type in [50023, 50024]:
                            sender = parent
                        else:
                            try:
                                sender = uia.GetFocusedElement()
                            except Exception:
                                return

                    elif control_type == 50032:
                        try:
                            sender = uia.GetFocusedElement()
                        except Exception:
                            return

                except Exception:
                    return

                # refresh current_focus using singleton instance (previous_focus is updated in setter)
                try:
                    control_instance = Control()  # Get singleton instance
                    control_instance.current_focus = sender
                except Exception as e:
                    LOGGER_WARNING(f"[refresh focus] Error updating focus: {e}\n{traceback.format_exc()}")

            except Exception as e:
                LOGGER_ERROR(f"[HandleFocusChangedEvent-outer-exception] {e}\n{traceback.format_exc()}")
                return

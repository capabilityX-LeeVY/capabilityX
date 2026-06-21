import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

import logging
import time

from tests.rs_sdk.utils.event_listener_sample import FocusListener
from tests.rs_sdk.utils.control_sample import Control

def test_webex_app():
    """Test and log the focused control's name and type."""
    listener = FocusListener()
    listener.start()
    control = Control()
    time.sleep(2)  # Allow time for the listener to start

    try:
        while True:
            try:
                # previous_control = control.previous_focus  
                current_control = control.current_focus

                # prev_name = previous_control.CurrentName if previous_control else "None"
                curr_name = current_control.CurrentName if current_control else "None"
                
                # Get control value (for edit controls)
                curr_value = "N/A"
                try:
                    if current_control:
                        # Try to get Value pattern for edit/text controls
                        from comtypes.gen import UIAutomationClient
                        value_pattern = current_control.GetCurrentPattern(UIAutomationClient.UIA_ValuePatternId)
                        if value_pattern:
                            value_interface = value_pattern.QueryInterface(UIAutomationClient.IUIAutomationValuePattern)
                            curr_value = value_interface.CurrentValue if value_interface.CurrentValue else ""
                except Exception as e:
                    # If Value pattern is not supported, it's fine (not all controls support it)
                    pass

                # Get top-level ancestor window (next level below Desktop)
                top_window_name = "N/A"
                top_window_id = "N/A"
                top_window_class = "N/A"
                try:
                    if current_control:
                        # Use TreeWalker to find top-level window
                        import uiautomation as auto
                        
                        try:
                            # Convert COM object to uiautomation Control
                            # Get the automation element handle
                            handle = current_control.CurrentNativeWindowHandle
                            
                            if handle and handle != 0:
                                # Get window from handle
                                top_window = auto.ControlFromHandle(handle)
                                if top_window:
                                    top_window_name = top_window.Name if top_window.Name else "N/A"
                                    top_window_id = top_window.AutomationId if top_window.AutomationId else "N/A"
                                    top_window_class = top_window.ClassName if top_window.ClassName else "N/A"
                                    LOGGER_INFO(f"[Method 1] Found via handle: [{top_window_name}]")
                            else:
                                # Fallback: walk up using TreeWalker
                                LOGGER_INFO(f"[Method 2] No handle, walking tree...")
                                from comtypes.gen import UIAutomationClient
                                from comtypes import GUID
                                
                                # Get UIA instance
                                UIA_CLSID = GUID('{FF48DBA4-60EF-4201-AA87-54103EEF594E}')
                                import comtypes.client
                                uia = comtypes.client.CreateObject(UIA_CLSID, interface=UIAutomationClient.IUIAutomation)
                                
                                # Use ControlViewWalker (filters out non-control elements)
                                walker = uia.ControlViewWalker
                                current = current_control
                                depth = 0
                                
                                while current and depth < 15:
                                    parent = walker.GetParentElement(current)
                                    if parent:
                                        parent_name = parent.CurrentName if parent.CurrentName else "(no name)"
                                        parent_class = parent.CurrentClassName if parent.CurrentClassName else "(no class)"
                                        parent_type = parent.CurrentControlType
                                        
                                        LOGGER_INFO(f"  Depth {depth}: [{parent_name}] Class:[{parent_class}] Type:[{parent_type}]")
                                        
                                        # Check if this is Desktop
                                        if parent_class == "#32769" or (parent_type == 50033 and "Desktop" in str(parent_name)):
                                            # Current is the top-level window
                                            top_window_name = current.CurrentName if current.CurrentName else "N/A"
                                            top_window_id = current.CurrentAutomationId if current.CurrentAutomationId else "N/A"
                                            top_window_class = current.CurrentClassName if current.CurrentClassName else "N/A"
                                            LOGGER_INFO(f"[Method 2] Found at depth {depth}: [{top_window_name}]")
                                            break
                                        
                                        current = parent
                                        depth += 1
                                    else:
                                        LOGGER_INFO(f"  Depth {depth}: No parent, stopping")
                                        break
                        except Exception as inner_e:
                            LOGGER_ERROR(f"Error in window detection: {inner_e}")
                            import traceback
                            LOGGER_ERROR(traceback.format_exc())
                            
                except Exception as e:
                    LOGGER_ERROR(f"Outer error getting top-level window: {e}")
                    import traceback
                    LOGGER_ERROR(traceback.format_exc())

                LOGGER_INFO(f"=====================================================================================================")
                # LOGGER_DEBUG(f"Previous Control Name:[{prev_name}], [{previous_control.CurrentAutomationId}] [{previous_control.CurrentControlType}], [{previous_control.CurrentLocalizedControlType}]")
                curr_automation_id = current_control.CurrentAutomationId if current_control else "N/A"
                curr_control_type = current_control.CurrentControlType if current_control else "N/A"
                curr_localized_type = current_control.CurrentLocalizedControlType if current_control else "N/A"
                LOGGER_INFO(f"Current Control Name: [{curr_name}] [{curr_automation_id}] [{curr_control_type}], [{curr_localized_type}]")
                LOGGER_INFO(f"Current Control Value: [{curr_value}]")
                LOGGER_INFO(f"Top-Level Window Name: [{top_window_name}]")
                LOGGER_INFO(f"Top-Level Window ID: [{top_window_id}]")
                LOGGER_INFO(f"Top-Level Window Class: [{top_window_class}]")
                LOGGER_INFO(f"=====================================================================================================")

                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()

test_webex_app()
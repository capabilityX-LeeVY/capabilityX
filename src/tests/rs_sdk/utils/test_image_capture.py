import sys
import os
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)


import time
import platform
from pathlib import Path
from rs_sdk.utils import image_handler

# Platform-specific imports for event listener and control
if platform.system() == "Windows":
    from rs_sdk.utils.event_listener import FocusListener
    from rs_sdk.utils.control import Control
elif platform.system() == "Linux":
    from rs_sdk.platform.linux import FocusListener, Control
else:
    # Default fallback for unsupported platforms
    from rs_sdk.utils.event_listener import FocusListener
    from rs_sdk.utils.control import Control
from common.handler.textHandler import preProcessString


image_path = Path(r"C:\test")
image_path.mkdir(parents=True, exist_ok=True)


def test_image_capture():
    control = Control()  # singleton, exposes current_focus via property
    listener = None
    if control.toggle_listener:
        listener = FocusListener()
        listener.start()
        time.sleep(1)

    last_control_id = None
    try:
        while True:
            try:
                current_control = control.current_focus
                if current_control is None:
                    time.sleep(0.1)
                    continue

                current_id = (current_control.CurrentAutomationId, current_control.CurrentName, current_control.CurrentClassName)
                # print(f"Current Control ID: {current_id}|| Type: {current_control.CurrentControlType}")
                if current_id != last_control_id:
                    last_control_id = current_id

                    control_rect = current_control.CurrentBoundingRectangle
                    control_name = current_control.CurrentName
                    timestamp = time.strftime("%Y%m%d%H%M%S")
                    image_name = f"{timestamp}_{preProcessString(control_name)}"
                    if current_control.CurrentControlType == 50004: # Inputbox
                        margin_left = 70
                        margin_right = 50
                        margin_top = 10
                        margin_bottom = 50
                    else:
                        margin_left = 0
                        margin_right = 0
                        margin_top = 0
                        margin_bottom = 0
                    # Capture the control
                    control_image_output = image_handler.capture_image_from_currentBoundingRectangle(control_rect, left_extra=margin_left, right_extra=margin_right, top_extra=margin_top, bottom_extra=margin_bottom)
                    control_image = control_image_output.img
                    control_image_path = str(Path(image_path) / f"{image_name}.png")
                    image_handler.save_image(image_name, img=control_image, output_path=image_path.as_posix())
                    
                    # Capture the full screen
                    # full_screenshot = image_handler.capture_full_screen(monitor_index=2)
                    # full_screenshot_img = full_screenshot.img
                    # control_image_path = str(Path(image_path) / f"{image_name}.png")               
                    # image_handler.save_image(image_name, img=full_screenshot_img, output_path=image_path.as_posix())

                    print(f"Image saved: {control_image_path}")

                time.sleep(0.1)
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt:
            pass
    finally:
        print("Stopping listener...")
        if listener:
            listener.stop()
            print("Listener stopped.")

test_image_capture()
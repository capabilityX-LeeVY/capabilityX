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
import AppKit
from core.mac.AXClasses import NativeUIElement
from pathlib import Path
from rs_sdk.utils import image_handler
from common.handler.textHandler import preProcessString


image_path = Path(r"/Users/weiqli/workF/test")
image_path.mkdir(parents=True, exist_ok=True)


def test_image_capture():
    time.sleep(2)
    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    pid = app.processIdentifier()
    AXApp = NativeUIElement.get_app_ref_by_pid(pid)
    last_control_id = None
    while True:
        try:
            current_control = AXApp.focusedElement if AXApp is not None else None
            if current_control is None:
                time.sleep(0.1)
                continue

            current_id = (current_control.avaliableInfo, current_control.role, current_control.identifier)
            if current_id != last_control_id:
                last_control_id = current_id

                control_rect = current_control.frame
                control_name = current_control.avaliableInfo
                timestamp = time.strftime("%Y%m%d%H%M%S")
                image_name = f"{timestamp}_{preProcessString(control_name)}"

                # Capture the control
                # control_image_output = image_handler.capture_image_from_currentBoundingRectangle(control_rect)
                # control_image = control_image_output.img
                # control_image_path = str(Path(control_image_directory_path) / f"{image_name}.png")
                # image_handler.save_image(image_name, img=control_image, output_path=control_image_directory_path.as_posix())
                
                # Capture the full screen
                full_screenshot = image_handler.capture_full_screen()
                full_screenshot_img = full_screenshot.img 
                control_image_path = str(Path(image_path) / f"{image_name}.png")               
                image_handler.save_image(image_name, img=full_screenshot_img, output_path=image_path.as_posix())

                print(f"Image saved: {control_image_path}")

            time.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")

test_image_capture()
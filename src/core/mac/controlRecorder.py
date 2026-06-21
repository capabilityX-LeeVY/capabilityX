import datetime
import shutil

from pathlib import Path
from config.paths import CONTROL_IMAGE_PATH, WINDOW_IMAGE_PATH, SESSION_OUTPUT_PATH
from common.utils.featureToggle import FeatureToggle
from common.handler.textHandler import preProcessString
from common.handler import fileHandler
from rs_sdk.utils.control_db import ControlDB
from rs_sdk.utils import image_handler
from core.mac.AXClasses import NativeUIElement
from common.utils.logger import LOGGER_INFO

class ControlRecorder():
    def __init__(self):
        self.control_db = ControlDB()
        self.control_image_directory_path = Path(CONTROL_IMAGE_PATH) / "currentControls"
        self.previous_control_image_directory_path = Path(CONTROL_IMAGE_PATH) / "preControls"
        self.window_image_directory_path = Path(WINDOW_IMAGE_PATH)

    def recordControlImage(self, currentElement:NativeUIElement, preElement:NativeUIElement):
        if currentElement is None:
            return
        
        description = currentElement.avaliableInfo
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"{timestamp}_{preProcessString(description)}"
        control_type = currentElement.role
        control_id = currentElement.identifier
        pre_control_image_bytes = None
        control_image_path = None
        pre_control_image_path = None
        if currentElement.role == "AXCell":
            margin_left = 30
            margin_right = 20
        else:
            margin_left = 0
            margin_right = 0

        if currentElement.frame:
            control_image_result = image_handler.capture_image_from_currentBoundingRectangle(currentElement.frame, left_extra=margin_left, right_extra=margin_right)
            control_image = control_image_result.img
            control_image_bytes = control_image_result.byte_data
            control_image_path = str(self.control_image_directory_path / f"{image_name}.jpg")
            image_handler.save_image(image_name, img=control_image, output_path=str(self.control_image_directory_path))
        if preElement and preElement.frame is not None:
            pre_control_image_result = image_handler.capture_image_from_currentBoundingRectangle(preElement.frame)
            pre_control_image = pre_control_image_result.img
            pre_control_image_bytes = pre_control_image_result.byte_data
            pre_control_image_path = str(self.previous_control_image_directory_path / f"{image_name}.jpg")
            image_handler.save_image(image_name, img=pre_control_image, output_path=str(self.previous_control_image_directory_path))

        self.control_db.insert_control_action_history(description, control_type, control_id, image_name, control_image_bytes, pre_control_image_bytes, window_image=None)
        return control_image_path, pre_control_image_path

    @staticmethod
    def recordLastWindowImage(windowElement:NativeUIElement):
        if windowElement is None:
            return
        
        image_name = f"last_window_image"
        window_image = image_handler.capture_image_from_currentBoundingRectangle(windowElement.frame, 5).img
        image_handler.save_image(image_name, img=window_image, output_path=str(SESSION_OUTPUT_PATH))

    
    def recordWindowImage(self, windowElement:NativeUIElement):
        if windowElement is None:
            return
        
        description = windowElement.avaliableInfo
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"{timestamp}_{preProcessString(description)}"
        window_image_path = str(Path(self.window_image_directory_path) / f"{image_name}.jpg")

        window_image = image_handler.capture_image_from_currentBoundingRectangle(windowElement.frame).img
        image_handler.save_image(image_name, img=window_image, output_path=str(self.window_image_directory_path))
        return window_image_path

    def cropControlImage(self, currentElement:NativeUIElement, preElement:NativeUIElement):
        if currentElement and currentElement.frame is not None:
            if FeatureToggle.isEnabled('croppedImage'):
                return self.recordControlImage(currentElement, preElement)
        
        return None

    def cropWindowImage(self, windowElement:NativeUIElement):
        if windowElement and windowElement.frame is not None:
            if FeatureToggle.isEnabled('croppedImage'):
                return self.recordWindowImage(windowElement)
            
        return None
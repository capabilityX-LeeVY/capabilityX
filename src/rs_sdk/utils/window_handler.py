import uiautomation as auto
import time

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.utils.control_db import ControlDB
from rs_sdk.factory.control_factory import ControlFactory
from config.config import SKIP_CLOSE_WINDOW,SKIP_CLOSE_WINDOW_BY_ID

class WindowHandler:
    def __init__(self):
        self.control_db = ControlDB()
        self.current_control = ControlFactory().create_control()

    def is_all_Control_is_validated_in_window(self, window_name):
        results = self.control_db.fetch_is_validated_by_window_name(window_name)
        # LOGGER_DEBUG(f"{window_name} is_validated is {results}, {all(row[0] != 0 for row in results)}", "RED")
        return all(row[0] != 0 for row in results) if results else True
    
    def is_all_control_is_validated_in_window_level2(self, window_name):
        """Check if all controls in a WindowLevel2 are validated (i.e., no is_validated = 0)."""
        results = self.control_db.fetch_control_is_validated_by_window_level2(window_name)
        return all(row[0] != 0 for row in results) if results else True

    def is_validated_all_controls_in_current_window(self):
        current_control = self.current_control
        current_control.refresh()
        reassigned_ancestors = current_control.ControlAncestorLevelsElements
        current_control_window_level1_name = reassigned_ancestors["level1"]["name"]
        current_control_window_level2_name = reassigned_ancestors["level2"]["name"]
        current_control_window_level1_id = reassigned_ancestors["level1"]["id"]
        current_control_window_level2_id = reassigned_ancestors["level2"]["id"]
        
        # control_window_name = self.get_control_window_name_by_control_id_hash(control_id_hash)
        all_controls_validated = self.is_all_Control_is_validated_in_window(current_control_window_level1_name)
        
        # control_window_level2_name = self.get_control_level2_window_name_by_control_id_hash(control_id_hash)
        all_controls_validated_in_window_level2 = self.is_all_control_is_validated_in_window_level2(current_control_window_level2_name)

        LOGGER_INFO(f"> [Close Window][checking][window level 1]: {current_control_window_level1_name} all_controls_validated: [{all_controls_validated}]][control_window_name != None: {current_control_window_level1_name != None}]", "MAGENTA")
        LOGGER_INFO(f"> [Close Window][checking][window level 2]: {current_control_window_level2_name} all_controls_validated: [{all_controls_validated_in_window_level2}] [control_window_level2_name != None: [{current_control_window_level2_name != None}]]", "MAGENTA")
        if all_controls_validated and current_control_window_level1_name != None and current_control_window_level2_id not in SKIP_CLOSE_WINDOW_BY_ID:
            auto.SendKeys("{ESC}")
            LOGGER_INFO(f"> [Close Window][ESC][Level 1]: [{current_control_window_level1_name}]]", "MAGENTA")
            return True
        elif all_controls_validated_in_window_level2 and current_control_window_level2_name != None and current_control_window_level2_id not in SKIP_CLOSE_WINDOW_BY_ID:
            auto.SendKeys("{ESC}")
            LOGGER_INFO(f"> [Close Window][ESC][Level 2]: [{current_control_window_level2_name}],[{current_control_window_level2_id}]]", "MAGENTA")
            time.sleep(1)
            return True
        return False
    
    
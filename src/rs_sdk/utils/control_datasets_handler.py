
from rs_sdk.utils.control_db import ControlDB

class ControlDatasetsHandler:
    def __init__(self):
        self.control_db = ControlDB()

    def clean_invalid_control(self):
        self.control_db.clean_control_info_db()

if __name__ == '__main__':
    handler = ControlDatasetsHandler()
    handler.clean_invalid_control()
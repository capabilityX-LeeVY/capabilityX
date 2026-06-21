from core.mac.RSApplication import CRSApplication
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR


class CRPreMeeting(CRSApplication):
    def __init__(self,dbConnection) -> None:
        super().__init__(dbConnection)
        self.tableName = None

    def StartTraversalThePreMeeting(self):
        pass
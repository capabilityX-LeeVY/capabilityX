from core.mac.RSApplication import CRSApplication
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from typing import Optional

class CRSWorkFlow(CRSApplication):
    def __init__(self,dbConnection) -> None:
        super().__init__(dbConnection)
        self.tableName = None

    def GoToElement(self,controlName = None,controlHash = None,controlNameReg = None,controlID = None) -> tuple[bool,Optional['NativeUIElement']]:
        focused = self.nativeUIElement.focusedElement
        focused.tabOrder = self.lastTabOrder
        focused.level = 1
        focused.tableName = self.tableName
        (result,ele) = focused.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        if result == True:
            return (True,ele)
        else:
            return (False,None)
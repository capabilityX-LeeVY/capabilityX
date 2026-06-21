from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXWebArea(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.needBack = False
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children
        res = []
        if children is None or len(children) == 0:
            return res
        
        return children

    def children(self)-> list['NativeUIElement']:
        if self.role not in ["AXWebArea"]:
            return []
        
        return self._traverChild(self.element)
    
    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        if len(subItems) == 0:
            return (res,tabOrder)
        
        CRSKeyboard.TabKeyPressed()
        order = tabOrder
        for index,item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.processID = self.element.processID
            item.navigationKey = "Tab"
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance
            item.CaptureControlScreenshot()
            
            if item.enabled == False:
                continue
            
            if item.roleNotFocusedable() == True:
                continue

            (skipFlag,result,newOrder) = item.Traveral(order)
            if skipFlag is True:
                continue
            else:
                res.extend(result)
                order = newOrder
            
            if index != len(subItems) -1:
                CRSKeyboard.TabKeyPressed()

        return (res,order)

    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        if len(subItems) == 0:
            return (False,None)
        
        for index,item in enumerate(subItems):
            res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                return res

            if index != len(subItems) -1:
                CRSKeyboard.TabKeyPressed()
    
        return (False,None)


    @staticmethod
    def IsAXWebArea(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXWebArea"]:
            return False
        
        return True 

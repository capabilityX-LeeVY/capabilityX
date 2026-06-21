from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXTextArea(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children

        if children is None or len(children) == 0:
            res = []
            res.append(self.element)
            return res
        
        return children

    def children(self)-> list['NativeUIElement']:
        if self.role not in ["AXTextArea"]:
            return []
        
        return self._traverChild(self.element)
    
    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        if len(subItems) == 0:
            return (res,tabOrder)
        
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

            inserted = CTraversed.InsertElement(item)
            if inserted == True:
                item.navigationKey = "Tab"
                sql = item.formatToSql()
                res.append(sql)
                order = order + 1

            if index != len(subItems) -1:
                CRSKeyboard.TabKeyPressed()

        return (res,order)

    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        if len(subItems) == 0:
            return (False,None)
        
        for index,item in enumerate(subItems):
            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
            
            if index != len(subItems) -1:
                CRSKeyboard.TabKeyPressed()
    
        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                return (True, subItems[0])
            else:
                return (False,self.element)
            
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                item.level = self.element.level 
                item.productName = self.element.productName
                item.processID = self.element.processID
                item.tabOrder = self.element.tabOrder
                item.fromControl = self.element.fromControl
                item.isDeep = self.element.isDeep
                item.tableName = self.element.tableName
                item.pathInfo = self.element.pathInfo
                item.pathInfo_Names = self.element.pathInfo_Names
                item.needValidate = self.element.needValidate
                
                return (True,item)
            
        return (False,self.element)

    @staticmethod
    def IsAXTextArea(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXTextArea"]:
            return False
        
        return True 

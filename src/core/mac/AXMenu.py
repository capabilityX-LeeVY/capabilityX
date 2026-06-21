from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXMenu(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self)-> list['NativeUIElement']:
        res = []
        if self.element is not None:
            children = self.element.children
            res.extend(children)

        return res

    def children(self)-> list['NativeUIElement']:
        return self._traverChild()
        
    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder + 1
        for index, item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.processID = self.element.processID
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance
            item.CaptureControlScreenshot()
            item.navigationKey = "DownArrow"
            inserted = CTraversed.InsertElement(item)
            if inserted == True:
                item.RecordTraversalInfo()
                sql = item.formatToSql()
                res.append(sql)
                order = order + 1

            if index != len(subItems):
                CRSKeyboard.DownArrowKeyPressed()

        CRSKeyboard.ESCPressed()
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:            
        subItems:list['NativeUIElement'] = self.children()
        for index,item in enumerate(subItems):
            enable = item.enabled
            if enable == False:
                continue

            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                CRSKeyboard.ESCPressed()
                return (True,item)
            
            if index != len(subItems):
                CRSKeyboard.DownArrowKeyPressed()
        
        return (False,None)
    
    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            return (True, self.element)
            
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
    def IsAXMenu(element:NativeUIElement) -> bool:
        if element is None:
            return False
                
        if element.role not in ["AXMenu","AXMenuBar"]:
            return False
        
        return True 

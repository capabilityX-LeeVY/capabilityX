from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXCheckBox(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        res = []
        res.append(self.element)
        return res

    def children(self)-> list['NativeUIElement']:
        if self.role not in ["AXCheckBox"]:
            return []
        
        return self._traverChild(self.element)
        

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder + 1
        self.CaptureControlScreenshot()
        
        for item in subItems:
            item.level = self.element.level
            item.productName = self.element.productName
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.needValidate = self.element.needValidate
            item.tabOrder = order
            item.navigationKey = "Tab"
            item.RecordTraversalInfo()
            sql = item.formatToSql()
            res.append(sql)
            order = order + 1
            CTraversed.InsertElement(item)
            
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None):
        if self.element.enabled == False:
            return (False,None)
        
        if self.element.roleNotFocusedable() == True:
            return (False,None)

        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            CRSKeyboard.RightArrowKeyPressed()
            return (True,self.element)
                 
        return (False,None)
    
    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                return (True, subItems[0])
            else:
                return (False,self.element)
            
        for _,item in enumerate(subItems):
            if item.enabled == False:
                continue

            if item.roleNotFocusedable() == True:
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
    def IsAXCheckBox(element:NativeUIElement) -> bool:
        if element is None:
            return False
                
        if element.role not in ["AXCheckBox"]:
            return False
        
        return True 

from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXMenuItem(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        return [self.element,]

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)
        

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder
        for item in subItems:
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance

            item.CaptureControlScreenshot()
            inserted = CTraversed.InsertElement(item)
            if inserted == True:
                item.navigationKey = "Tab"
                sql = item.formatToSql()
                res.append(sql)
                order = order + 1
            

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        for item in subItems:
            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
            
        return (False,None)
    
    @staticmethod
    def IsAXMenumItem(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        config = CRSSikipMgr.ReadConfig()                
        if element.role_description in config["specialNames"]["MenuItem"] and element.role in ["AXUnknown",]:
            return True

        if element.role in ["AXMenuItem",]:
            return True
              
        return False 

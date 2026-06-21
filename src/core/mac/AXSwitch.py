from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXSwitch(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = self.element.children
        
        for c in children:
            if c.role in ["AXButton",]:
                value = c.value
                self.element.otherInfo = value
                self.element.otherInfoType = "AXSwitchValue"
                break

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
            enable = item.enabled
            if enable == False:
                return (False,None)
            
            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
                
        return (False,None)
    
    def GetAllSqlsOfChildren(self, newLevel, order) -> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        tabOrder = order
        for item in subItems:
            item.level = newLevel
            item.productName = self.element.productName
            item.tabOrder = tabOrder
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.navigationKey = "Tab"

            sql = item.formatToSql()
            res.append(sql)
            tabOrder = tabOrder + 1
            
        return (tabOrder,res)
    
    
    @staticmethod
    def IsAXSwitch(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        config = CRSSikipMgr.ReadConfig() 
        if element.role_description in config["specialNames"]["AXSwitchDescription"] and element.role in ["AXUnknown","AXSwitch"]:
            return True
        
        return False 

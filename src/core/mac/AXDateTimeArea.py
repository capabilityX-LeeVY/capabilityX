from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXDateTimeArea(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        return [self.element,]

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)
    
    @property
    def dateTimeComponents(self) -> int:
        try:
            return self.element.__getattr__('AXDateTimeComponents')
        except:
            return 0
        
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
        for time in range(0,3):
            CRSKeyboard.SpaceKeyPressed()

        CRSKeyboard.TabKeyPressed()    
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        for item in subItems:
            enable = item.enabled
            if enable == False:
                return (False,None)

            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
        
        for time in range(0,3):
            CRSKeyboard.SpaceKeyPressed()
        
        CRSKeyboard.TabKeyPressed()                            
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
    

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        return (True,self.element)
    
    @staticmethod
    def IsAXDateTimeArea(element:NativeUIElement) -> bool:
        if element is None:
            return False
                
        # if element.role_description in ["date time area",] and element.role in ["AXDateTimeArea",]:
        #     return True

        if element.role in ["AXDateTimeArea",]:
            return True      

        
        return False 

from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXDialpad(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.childrenInNavigationOrder
        res = []
        if children is None or len(children) == 0:
            return res
        
        return children

    def children(self)-> list['NativeUIElement']:
        if self.role not in ["AXGroup"]:
            return []
        
        return self._traverChild(self.element)
    
    def _Reverse_Direction(self,subItems:list['NativeUIElement']):
        for index,_ in enumerate(subItems):
            if index < len(subItems) -1:
                CRSKeyboard.LeftArrowKeyPressed(delay=0.1)

    def _Direction(self,subItems:list['NativeUIElement']):
        for index,_ in enumerate(subItems):
            if index < len(subItems) -1:
                CRSKeyboard.RightArrowKeyPressed(delay=0.1)  

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        if len(subItems) != 12:
            return (res,tabOrder)
        
        self._Reverse_Direction(subItems=subItems)

        order = tabOrder
        for index,item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.processID = self.element.processID
            item.navigationKey = "Right"
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            if item.enabled == False:
                continue

            item.RecordTraversalInfo()
            sql = item.formatToSql()
            res.append(sql)
            order = order + 1
            CTraversed.InsertElement(item)

            if index != len(subItems) -1:
                CRSKeyboard.LeftArrowKeyPressed()

        self._Reverse_Direction(subItems=subItems)
        return (res,order)

    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        if len(subItems) == 0:
            return (False,None)
        
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
            
            if index != len(subItems) -1:
                CRSKeyboard.RightArrowKeyPressed()
        
        self._Reverse_Direction(subItems=subItems)
        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:        
        subItems = self.children()
        if len(subItems) != 12:
            return (False,self.element)
        else:
            if controlName == None and controlHash == None and controlNameReg == None:
                return (True,subItems[0])
            
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
    def IsAXDialpad(element:NativeUIElement) -> bool:
        if element is None:
            return False

        if element.role not in ["AXGroup"]:
            return False
        
        if element.description is None:
            return False
        
        from core.mac.RSSkipMgr import CRSSikipMgr
        config = CRSSikipMgr.ReadConfig()
    
        if config["specialNames"]["Dialpad"] not in element.description:
            return False
        
        children = element.children
        if children is None or len(children) != 12:
            return False
        
        return True

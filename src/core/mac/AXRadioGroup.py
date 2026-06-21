from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXRadioGroup(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = self.element.children
        return children

    def children(self)-> list['NativeUIElement']:
        # if self.element.role_description not in ["radio group"]:
        #     return []
        
        if self.element.role not in ("AXRadioGroup"):
            return []
        
        return self._traverChild(self.element)
        
    def _Direction(self,subItems:list['NativeUIElement']):
        if len(subItems) <2:
            return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)
        
        first = subItems[0]
        second = subItems[1]
        if first is None or second is None:
            return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)
        
        if first.frame.x == second.frame.x:
            return ("DownArrow",CRSKeyboard.DownArrowKeyPressed)
        
        if first.frame.y == second.frame.y:
            return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)
        
        return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)

    def _ReverseDirection(self,subItems:list['NativeUIElement']):
        if len(subItems) <2:
            return ("LeftArrow",CRSKeyboard.LeftArrowKeyPressed)
        
        first = subItems[0]
        second = subItems[1]
        if first is None or second is None:
            return ("LeftArrow",CRSKeyboard.LeftArrowKeyPressed)
        
        if first.frame.x == second.frame.x:
            return ("UpArrow",CRSKeyboard.UpArrowKeyPressed)
        
        if first.frame.y == second.frame.y:
            return ("LeftArrow",CRSKeyboard.LeftArrowKeyPressed)
        
        return ("LeftArrow",CRSKeyboard.LeftArrowKeyPressed)
    

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder + 1
        
        (reversed_name,reversed_dir) = self._ReverseDirection(subItems)
        for index,item in enumerate(subItems):
            if item.roleLevelOne() == True:
              if index != len(subItems) -1:
                    reversed_dir()

        (name,dir) = self._Direction(subItems)
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.processID = self.element.processID
            item.fromControl = self.element.fromControl
            item.navigationKey = name
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate   
            item.screenshotInstance = self.element.screenshotInstance
            item.CaptureControlScreenshot()
            inserted = CTraversed.InsertElement(item)
            if inserted == True:
                item.RecordTraversalInfo()
                sql = item.formatToSql()
                res.append(sql)
                order = order + 1

            if item.roleLevelOne() == True:
                if index != len(subItems) -1:
                    dir()

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:            
        subItems:list['NativeUIElement'] = self.children()
    
        (reversed_name,reversed_dir) = self._ReverseDirection(subItems)
        for index,item in enumerate(subItems):
            if item.roleLevelOne() == True:
              if index != len(subItems) -1:
                  reversed_dir()

        (name,dir) = self._Direction(subItems)      
        for index,item in enumerate(subItems):
            enable = item.enabled
            if enable == False:
                continue

            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,item)
            
            if item.roleLevelOne() == True:
                if index != len(subItems) -1:
                    dir()

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
    def IsAXRadioGroup(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ("AXRadioGroup"):
            return False
        
        # if element.role_description not in ["radio group"]:
        #     return False
        
        return True 

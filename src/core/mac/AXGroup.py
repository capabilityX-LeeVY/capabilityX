from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXGroup(NativeUIElement):
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
        if self.role not in ["AXGroup"]:
            return []
        
        return self._traverChild(self.element)
    
    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        if len(subItems) == 0:
            return (res,tabOrder)
        
        self.CaptureControlScreenshot()
        order = tabOrder
        if self.IsGroupButton() == True:
            inserted = CTraversed.InsertElement(self.element)
            if inserted == True:
                self.element.tabOrder = order
                sql = self.element.formatToSql()
                res.append(sql)
                order = order  + 1
            
            return (res,order)
            
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
            

            #if item.isContainer() == False and index != len(subItems) -1:
            if index != len(subItems) -1:
                CRSKeyboard.TabKeyPressed()

        return (res,order)

    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        if self.IsGroupButton() == True:
            if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,self.element)
            return (False,None)
        
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

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        if self.IsEmptyGroup() == True:
            return (False,self.element)
        
        if self.IsGroupButton() == True:
            if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,self.element)
            return (False,None)
        
        subItems = self.children()
        if len(subItems) == 0:
            return (False,self.element)
        else:
            if controlName == None and controlHash == None and controlNameReg == None:
                for index,item in enumerate(subItems): 
                    if item.roleFocusedable() == True and item.isContainer() == False:
                        return item.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                
                return subItems[0].LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

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
            res = item.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                return res
            
        return (False,self.element)
    
    def IsEmptyGroup(self):
        children = self.element.children
        if children is None or len(children) == 0:
            return True
        
        return False

    @staticmethod
    def IsAXGroup(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXGroup"]:
            return False
        
        return True 

    def IsGroupButton(self) -> bool:
        if self.role != "AXGroup":
            return False
        
        children = self.children()
        if len(children) != 1:
            return False
        
        config = CRSSikipMgr.ReadConfig()
        if self.role_description in config["specialNames"]["AXButtonDescription"]:
            return True
                
        return False
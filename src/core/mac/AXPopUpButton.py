from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXPopUpButton(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children
        result = []
        for child in children:
            if child.role == "AXMenu":
                res = self._traverChild(child)
                if len(res) >0:
                    result.extend(res)
            
            if child.role == "AXMenuItem": 
                result.append(child)

        return result

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)

    def GoToTop(self,subItems):
        for index,item in enumerate(subItems):
            if index < len(subItems) -1:
                CRSKeyboard.UpArrowKeyPressed(delay=0.5)
    
    def GoToButtom(self,subItems):
        for index,item in enumerate(subItems):
            if index < len(subItems) -1:
                CRSKeyboard.DownArrowKeyPressed(delay=0.5)
    

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder

        if len(subItems) == 0:
            # add self
            self.element.CaptureControlScreenshot()
            inserted = CTraversed.InsertElement(self.element)
            if inserted == True:
                self.element.tabOrder = order
                sql = self.element.formatToSql()
                res.append(sql)
                order = order  + 1
            
            return (res,order)
        
        self.GoToTop(subItems=subItems)
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

            item.level = self.element.level 
            item.productName = self.element.productName
            item.processID = self.element.processID
            item.tabOrder = order
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
                sql = item.formatToSql()
                res.append(sql)
                order = order + 1
    
            if index != len(subItems) -1:
                CRSKeyboard.DownArrowKeyPressed()

        return (res,order)
    
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()

        if len(subItems) == 0:
            if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,self.element)
        else:
            self.GoToTop(subItems = subItems)
            for index,item in enumerate(subItems):
                if item.enabled == False:
                    continue
                
                if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                    return (True,item)
                
                if index < len(subItems) -1:
                    CRSKeyboard.DownArrowKeyPressed(delay=0.5)
                    
            CRSKeyboard.ESCPressed()

        return (False,None)
    

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if len(subItems) == 0:
            if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                return (True,self.element)
            else:
                return (False,self.element)
        else:
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
    def IsAXPopUpButton(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        # if element.role_description in ["pop up button",] and element.role in ["AXPopUpButton",]:
        #     return True

        if element.role in ["AXPopUpButton",]:
            return True
         
        return False 
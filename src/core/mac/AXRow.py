from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from core.mac.AXGroup import AXGroup
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXRowCell(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children
        res = []
        if children is None or len(children) == 0:
            return res
        
        for item in children:
            enabled = item.enabled
            if enabled == False:
                continue

            if item.roleNotFocusedable() == False:
                continue
            
            res.append(item)
                
        return res
    
    def children(self)-> list['NativeUIElement']:        
        return self._traverChild(self.element)
    

    def Traveral(self,tabOrder)-> list:
        res = []
        order = tabOrder

        subItems:list['NativeUIElement'] = self.children()
        for index,item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.processID = self.element.processID
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate   = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance
            item.navigationKey = "Tab"

            (skipFlag,result,newOrder) = item.Traveral(order)
            if skipFlag == True:
                continue

            res.extend(result)
            order = newOrder
            
            if index != len(subItems) - 1:
                CRSKeyboard.TabKeyPressed()

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()                
        for _,item in enumerate(subItems):
            if item.isContainer() == True:
                res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    return res
            else:
                if item.enabled == False:
                    continue
                
                if item.roleNotFocusedable() == True:
                    continue

                res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    CRSKeyboard.TabKeyPressed()
                    return res
                                
                CRSKeyboard.TabKeyPressed()
                    
        return (False,None)
    
    @staticmethod
    def IsAXRowCell(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXCell"]:
            return False
        
        # if element.role_description not in ["cell"]:
        #     return False
        
        return True 


class AXRow(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children
        res = []
        if children is None or len(children) == 0:
            return res
        
        return children
    
    def children(self)-> list['NativeUIElement']:        
        return self._traverChild(self.element)
    

    def Traveral(self,tabOrder)-> list:
        res = []
        order = tabOrder

        subItems:list['NativeUIElement'] = self.children()
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
            
            if AXRowCell.IsAXRowCell(item) == True:
                cell = AXRowCell(item)
                (result,newOrder) = cell.Traveral(tabOrder=order)
                res.extend(result)
                order = newOrder
            else:
                (skipFlag,result,newOrder) = item.Traveral(order)
                if skipFlag == True:
                    continue

                res.extend(result)
                order = newOrder
            
            if index != len(subItems) - 1:
                CRSKeyboard.RightArrowKeyPressed()

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()

        for _,item in enumerate(subItems):
            if AXRowCell.IsAXRowCell(item) == True:
                cell = AXRowCell(item)
                res = cell.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    return res
            else:
                if item.enabled == False:
                    continue
                
                if item.roleNotFocusedable() == True:
                    continue

                res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    CRSKeyboard.TabKeyPressed()
                    return res
                                
                CRSKeyboard.TabKeyPressed()
                    
        return (False,None)
    
    @staticmethod
    def IsAXRow(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXRow"]:
            return False
        
        # if element.role_description not in ["table row"]:
        #     return False
        
        return True 
from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from core.mac.AXGroup import AXGroup
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXCell(NativeUIElement):
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
        if self.role not in ["AXCell"]:
            return []
                
        return self._traverChild(self.element)
    

    def Traveral(self,tabOrder)-> list:
        res = []
        order = tabOrder
        # add self
        inserted = CTraversed.InsertElement(self.element)
        if inserted == True:
            self.element.tabOrder = order
            sql = self.element.formatToSql()
            res.append(sql)
            order = order  + 1

        subItems:list['NativeUIElement'] = self.children()
        for index,item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.processID = self.element.processID
            item.navigationKey = "RightArrow"
            item.isDeep = self.element.isDeep
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance
            item.tableName = self.element.tableName

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

        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            CRSKeyboard.RightArrowKeyPressed()
            return (True,self.element)
                
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
                    CRSKeyboard.RightArrowKeyPressed()
                    return res
                                
                CRSKeyboard.RightArrowKeyPressed()
                    
        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                return (True, subItems[0])
            else:
                return (False,self.element)
        
        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            return (True, self.element)
        
        for index,item in enumerate(subItems):
            if item.isContainer() == True:
                res = item.LocateItem(controlName=controlName, controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    return res
            else:
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
                    item.pathInfo = self.element.pathInfo
                    item.pathInfo_Names = self.element.pathInfo_Names
                    item.needValidate = self.element.needValidate
                
                    return (True,item)
                
        return (False,self.element)
    
    
    @staticmethod
    def IsAXCell(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXCell"]:
            return False
        
        # if element.role_description not in ["cell","list item","","单元格"]:
        #     return False
        
        return True 

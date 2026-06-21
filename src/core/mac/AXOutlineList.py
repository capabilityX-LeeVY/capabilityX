from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXOutlineList(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.selectedCellHash = None
        self.screenshotInstance = element.screenshotInstance

    def _traversalCell(self,row):
        resCell = []
        if row is None:
            return resCell
        
        cells = row.children
        return cells
        
    def _traversalOutLineRow(self):
        resultRows = []
        if self.element is not None:
            rows = self.element.children
            if rows is not None:
                for row in rows:
                    if row.role not in ("AXRow"):
                        continue

                    row.processID = self.element.processID
                    row.level = self.element.level
                    row.productName = self.element.productName
                    row.fromControl = self.element.fromControl
                    row.isDeep = self.element.isDeep
                    row.tableName = self.element.tableName
                    row.pathInfo = self.element.pathInfo
                    row.pathInfo_Names = self.element.pathInfo_Names
                    row.needValidate = self.element.needValidate

                    res = self._traversalCell(row)
                    if res is not None:
                        resultRows.extend(res)
        
        return resultRows
    
    def children(self)-> list['NativeUIElement']:
        return self._traversalOutLineRow()

    def Traveral(self,tabOrder)-> list:
        res = []
        if self.element is None:
            return (res,tabOrder)
    
        CRSKeyboard.DownArrowKeyPressed()
        subItems = self.children()        
        order = tabOrder
        for index,item in enumerate(subItems):
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
            
            item.navigationKey = "DownArrow"
            (skipFlag,result,newOrder) = item.Traveral(order)
            if skipFlag == True:
                continue

            res.extend(result)
            order = newOrder
            
            if index != len(subItems) - 1:
                CRSKeyboard.DownArrowKeyPressed()

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()

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
                    CRSKeyboard.DownArrowKeyPressed()
                    return res
                                
                CRSKeyboard.DownArrowKeyPressed()

        return (False,None)

    @staticmethod
    def IsAXOutlineList(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXOutline",]:
            return False

        config = CRSSikipMgr.ReadConfig()
        if element.role_description not in config["specialNames"]["ListDescription"]:
            return False
        
        return True 


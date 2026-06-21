from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.AXSwitch import AXSwitch
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr
from core.mac.TraversedElementMgr import CTraversed

class AXTable(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traversalCell(self,column):
        resCell = []
        if column is None:
            return resCell
        
        cells = column.children
        config = CRSSikipMgr.ReadConfig()
        if cells is not None:
            for cell in cells:
                if cell.enabled == False:
                    continue

                cellRoleDescription = cell.role_description
                if cellRoleDescription in config["specialNames"]["SectionHeader"]:
                    continue
                
                avali = cell.avaliableInfo
                if  avali in config["specialNames"]["SeparatorRow"]:
                    continue

                resCell.append(cell)

        return resCell
    
    def _traversalColumns(self,row):
        resColumns = []
        if row is None:
            return resColumns
        
        columns = row.children
        if columns is not None:
            for column in columns:
                if column.enabled == False:
                    continue
                column.processID = row.processID
                column.level = row.level
                column.productName = row.productName
                column.fromControl = row.fromControl
                column.tabOrder = row.tabOrder
                column.isDeep = row.isDeep
                column.tableName = row.tableName
                column.needValidate = row.needValidate
                column.parentInfo = row.parentInfo
                child = column.children
                if child is not None and len(child) == 1:
                    res = self._traversalCell(column=column)
                    if res is not None:
                        resColumns.extend(res)
                elif child is not None and len(child) >= 2:
                    resColumns.append(column)

        return resColumns

    def _traversalRow(self):
        resultRows = []
        if self.element is not None and self.element.role == "AXTable":
            rows = self.element.children
            if rows is not None:
                # skip large tables
                if len(rows) > 50:
                    return resultRows 
                
                for row in rows:
                    if row.enabled == False:
                        continue
                    row.processID = self.element.processID
                    row.level = self.element.level
                    row.productName = self.element.productName
                    row.fromControl = self.element.fromControl
                    row.tabOrder = self.element.tabOrder
                    row.isDeep = self.element.isDeep
                    row.tableName = self.element.tableName
                    row.needValidate = self.element.needValidate
                    row.parentInfo = self.element
                    res = self._traversalColumns(row)
                    if res is not None:
                        resultRows.extend(res)
        
        return resultRows

    def children(self)-> list['NativeUIElement']:
        return self._traversalRow()
        

    @property
    def selectedRows(self) -> list['NativeUIElement']:
        try:
            selectRows = self.element.__getattr__('AXSelectedRows')
            if selectRows is None:
                return []
            return selectRows
        except:
            return []  
        
    def _isTableItemIsContain(self,item):
        exceptRole = ("AXGroup","AXList","AXTabGroup",
                      "AXTable","AXScrollBar","AXScrollArea",)
        
        if item is None:
            return False
        
        if item.role in exceptRole:
            return True
        
        if item.role in ("AXUnknown") and item.children is not None and len(item.children)>0:
            return True
        
        return False
    

    def Traveral(self,tabOrder)-> list:
        from core.mac.AXListItem import AXListItem
        subItems = self.children()
        res = []
        selectRows = self.selectedRows
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
            item.parentInfo = self.element
            item.screenshotInstance = self.element.screenshotInstance
            item.parentInfo = self.element  

            if self._isTableItemIsContain(item) == True:
                (skipFlag,result,newOrder) = item.Traveral(order)
                if skipFlag is True:
                    continue
                else:
                    res.extend(result)
                    order = newOrder
                
                if len(selectRows) >0:
                    if index != len(subItems) -1:
                        CRSKeyboard.DownArrowKeyPressed()
                else:
                    CRSKeyboard.DownArrowKeyPressed()
            else:
                if item.enabled == False:
                    continue
                
                if item.roleNotFocusedable() == True:
                    continue

                if len(selectRows) >0:
                    if index != len(subItems) -1:
                        CRSKeyboard.DownArrowKeyPressed()
                else:
                    CRSKeyboard.DownArrowKeyPressed()
                
                inserted = CTraversed.InsertElement(item)
                item.navigationKey = "DownArrow"
                if inserted == True:
                    sql = item.formatToSql()
                    res.append(sql)
                    order = order + 1

                # (skipFlag,result,newOrder) = item.Traveral(order)
                # if skipFlag is True:
                #     continue
                # else:
                #     res.extend(result)
                #     order = newOrder
                    
        CRSKeyboard.ESCPressed()
        return (res,order)
    
    # def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
    #     subItems = self.children()
    #     selectRows = self.selectedRows

    #     for index,item in enumerate(subItems):
    #         if self._isTableItemIsContain(item) == True:
    #             res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
    #             if res[0] == True:
    #                 return res
    #         else:
    #             if item.enabled == False:
    #                 continue
                
    #             if item.roleNotFocusedable() == True:
    #                 continue

    #             res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
    #             if res[0] == True:
    #                 return res
    #         if len(selectRows) >0:
    #             if index != len(subItems) -1:
    #                 CRSKeyboard.DownArrowKeyPressed()
    #         else:
    #             CRSKeyboard.DownArrowKeyPressed()

    #     CRSKeyboard.ESCPressed()
    #     return (False,None)

    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        selectRows = self.selectedRows

        for index,item in enumerate(subItems):
            item.parentInfo = self.element
            if item.enabled == False:
                continue
            
            if item.roleNotFocusedable() == True:
                continue

            item.parentInfo = self.element
            if str(controlName).find(" Checked,") != -1:
                if controlHash is not None:
                    if item._isSameWith(controlName=controlName,controlHash=None,controlNameReg=controlNameReg) == True:
                        return (True,item)
            else:   
                if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                    return (True,item)
            
            if len(selectRows) >0:
                if index != len(subItems) -1:
                    CRSKeyboard.DownArrowKeyPressed()
            else:
                CRSKeyboard.DownArrowKeyPressed()       

        #CRSKeyboard.ESCPressed()
        return (False,None)
    
    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                subItems[0].parentInfo = self.element
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
                item.parentInfo = self.element
                return (True,item)
            
        return (False,self.element)
    
    @staticmethod
    def IsAXTable(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXTable",]:
            return False
        
        return True 

    def GetAllSqlsOfChildren(self,newLevel,order) -> list:
        sqls = []
        subItems = self.children()
        newOrder = order
        for item in subItems:
            if item is None:
                continue

            if item.enabled == False:
                continue

            item.level = newLevel 
            item.productName = self.element.productName
            item.processID = self.element.processID
            item.tabOrder = newOrder
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.parentInfo = self.element
            (newOrder,result) = item.GetAllSqlsOfChildren(newLevel,order)
            sqls.extend(result)

        return (newOrder,sqls)
from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from typing import Optional
from core.mac.TraversedElementMgr import CTraversed
from core.mac.RSSkipMgr import CRSSikipMgr

KEYBOARD_DELAY = 0.3

class AXOutlineCell(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.cellName = None
        self.rowInfo = ""
        self.screenshotInstance = element.screenshotInstance
        self.hasExpendedButton = False

    def children(self)-> list['NativeUIElement']:
        if self.element is None:
            return []
        
        result = []
        controls = self.element.children

        if controls is not None:
            for control in controls:
                if control.role in ("AXStaticText"):
                    if control.value is not None and len(str(control.value)) != 0:
                        self.element.settedInfo = control.value
                        self.cellName = control.value
                    else:
                        self.element.settedInfo = control.avaliableInfo
                        self.cellName = control.avaliableInfo
                elif control.role in ("AXButton"):
                    #control.settedInfo = f'''{control.avaliableInfo}_{self.cellName}''' 
                    self.hasExpendedButton = True                  

                if control.roleNotFocusedable() == True:
                    continue

                enable = control.enabled
                if enable == False:
                    continue
                
                if self.element.settedInfo is not None:
                    control.parentHashString = self.element.settedInfo
                
                # control.distinctFlagForHash = self.rowInfo
                # control.parentInfo = self.element.parentInfo
                # result.append(control)

        result.insert(0,self.element)
        return result
    
    def Traveral(self,tabOrder)-> list:
        result = []
        if self.element is None:
            return (result,tabOrder)
        
        subItems = self.children()
        newOrder = tabOrder
        skipFlag = False
        for index,item in enumerate(subItems):
            item.level = self.element.level 
            item.productName = self.element.productName
            item.processID = self.element.processID
            item.tabOrder = newOrder
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.parentInfo = self.element.parentInfo
            item.screenshotInstance = self.element.screenshotInstance
            item.CaptureControlScreenshot()
            if item.enabled == False:
                continue  
            try:
                inserted = CTraversed.InsertElement(item)
                if inserted == True:
                    item.tabOrder = tabOrder
                    item.navigationKey = "DownArrow"
                    sql = item.formatToSql()
                    result.append(sql)
                    newOrder = tabOrder + 1
            except Exception as e:
                item.erroMessage = str(e)
                item.tabOrder = tabOrder
                item.navigationKey = "DownArrow"
                sql = item.formatToSql()
                raise Exception (sql)

            #if index < len(subItems) - 1:
            if self.hasExpendedButton == True:
                CRSKeyboard.TabKeyPressed(delay=KEYBOARD_DELAY)

        return (skipFlag,result,newOrder)


    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            if self.hasExpendedButton == True:
                CRSKeyboard.TabKeyPressed(delay=KEYBOARD_DELAY) 
            return (True,self.element)
        
        # for index,item in enumerate(subItems):
        #     item.parentInfo = self.element.parentInfo
        #     res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        #     if self.hasExpendedButton == True:
        #         CRSKeyboard.TabKeyPressed(delay=KEYBOARD_DELAY) 
        #     if res[0] == True:
        #         # if index != len(subItems) - 1:
        #         #     CRSKeyboard.TabKeyPressed(delay=KEYBOARD_DELAY) 
        #         return res
            
            # if index != len(subItems) - 1:
            #     CRSKeyboard.TabKeyPressed(delay=KEYBOARD_DELAY)   
        
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
                item.parentInfo = self.element.parentInfo

                return (True,item)
            
        return (False,self.element)
    
    def GetAllSqlsOfChildren(self, newLevel, tabOrder) -> list:
        result = []
        if self.element is None:
            return (tabOrder,result)
        
        subItems = self.children()
        newOrder = tabOrder
        for index,item in enumerate(subItems):
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
            item.parentInfo = self.element.parentInfo

            if item.enabled == False:
                continue  
    
            item.tabOrder = tabOrder
            item.navigationKey = "DownArrow"
            sql = item.formatToSql()
            result.append(sql)
            newOrder = tabOrder + 1

        return (newOrder,result)
    
class AXOutline(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.selectedCellHash = None

    def _traversalCell(self,row):
        resCell = []
        if row is None:
            return resCell
        
        children = row.children
        if children is not None:
            for cell in children:
                if cell.role in ("AXCell"):
                    cell.processID = row.processID
                    cell.level = row.level
                    cell.productName = row.productName
                    cell.fromControl = row.fromControl
                    res = self._traversalCell(cell)
                    resCell.extend(res)
                else:
                    enable = cell.enabled
                    if enable == False:
                        continue

                    if cell.role in ("AXStaticText"):
                        row.settedInfo = cell.avaliableInfo

                    if len(resCell) == 0:
                        row.settedInfo = cell.avaliableInfo
                        resCell.append(row)
        
        #resCell.append(row)
        return resCell
    
    def _traversalRow(self):
        resultRows = []
        if self.element is not None and self.element.role == "AXOutline":
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
    
    def _updateCellInfo(self,cell):
        if cell.role not in ("AXCell"):
            return cell
        
        controls = cell.children
        if controls is not None:
            for control in controls:
                enable = control.enabled
                if enable == False:
                    continue

                if control.role in ("AXStaticText"):
                    if control.value is not None and len(str(control.value)) != 0:
                        cell.settedInfo = control.value
                    else:
                        cell.settedInfo = control.avaliableInfo

        return cell


    def _selectCellHash(self):
        self.selectedCellHash = ""
        if self.element is None:
            return self.selectedCellHash
        
        cells = self.element.AXSelectedCells
        if cells is not None and len(cells) > 0:
            firstCell = cells[0]
            firstCellChild = firstCell.children
            if firstCellChild is not None:
                if firstCellChild[0].role in ("AXCell"):
                    self._updateCellInfo(firstCellChild[0])
                    self.selectedCellHash =  firstCellChild[0].hashstr
                else:
                    self._updateCellInfo(firstCell)
                    self.selectedCellHash = firstCell.hashstr

            return self.selectedCellHash
        
        return self.selectedCellHash
    

    def _GoToTop(self,subItems):
        if len(subItems) == 0:
            return 
        
        if self.selectedCellHash is not None and self.selectedCellHash != "":
            first = subItems[0]
            self._updateCellInfo(first)
            if first.hashstr == self.selectedCellHash:
                LOGGER_INFO("select Item is first Item , don't need Go To Top!")
                return 

        for index,item in enumerate(reversed(subItems)):
            if index < len(subItems) -1:
                CRSKeyboard.UpArrowKeyPressed(delay=KEYBOARD_DELAY)

    def _GoToButtom(self,subItems):
        for index,item in enumerate(subItems):
            if index < len(subItems) -1:
                CRSKeyboard.DownArrowKeyPressed(delay=KEYBOARD_DELAY)

    
    def _GoToSelectItem(self,subItems):
        if self.selectedCellHash is None or self.selectedCellHash == "":
            return 
        
        found = False
        for index,item in enumerate(reversed(subItems)):
            self._updateCellInfo(item)
            if item.hashstr == self.selectedCellHash:
                found = True
                break
            
            if index < len(subItems) - 1:
                CRSKeyboard.UpArrowKeyPressed(delay=KEYBOARD_DELAY)
        
        if found is False:
            for index,item in enumerate(subItems):
                self._updateCellInfo(item)
                item.print()
                LOGGER_ERROR(f'''{item.hashstr}, {self.selectedCellHash}''')
                if item.hashstr == self.selectedCellHash:
                    found = True
                    break
                
                if index < len(subItems) -1:
                    CRSKeyboard.DownArrowKeyPressed(delay=KEYBOARD_DELAY)


    def children(self)-> list['NativeUIElement']:
        return self._traversalRow()

    def Traveral(self,tabOrder)-> list:
        res = []
        if self.element is None:
            return (res,tabOrder)
        
        self._selectCellHash()
        subItems = self.children() 
        self._GoToTop(subItems=subItems)

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
    
            if item.enabled == False:
                continue
            
            outlineCell = AXOutlineCell(item)
            outlineCell.rowInfo = index
            outlineCell.parentInfo = self.element
            (skipFlag,result,newOrder) = outlineCell.Traveral(order)
            if skipFlag is True:
                continue
            else:
                res.extend(result)
                order = newOrder

            if index < len(subItems) - 1:
                CRSKeyboard.DownArrowKeyPressed(delay=KEYBOARD_DELAY)   
                
        self._GoToSelectItem(subItems=subItems)
                
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        self._selectCellHash()

        subItems = self.children() 
        if len(subItems) == 0:
            return (False,None)
        
        self._GoToTop(subItems=subItems)
        
        for index,item in enumerate(subItems):
            item.parentInfo = self.element
            outlineCell = AXOutlineCell(item)
            outlineCell.rowInfo = index
            res = outlineCell.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                return res
            
            if index < len(subItems) - 1:
                CRSKeyboard.DownArrowKeyPressed()

        self._GoToSelectItem(subItems=subItems)
        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                item = subItems[0]
                outlineCell = AXOutlineCell(item)
                outlineCell.rowInfo = 0
                res = outlineCell.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                return res
            else:
                return (False,self.element)
            
        for index,item in enumerate(subItems):
            if item.enabled == False:
                continue

            outlineCell = AXOutlineCell(item)
            outlineCell.rowInfo = index
            outlineCell.parentInfo = self.element
            res = outlineCell.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                return res
            
        return (False,self.element)
    
    def GetAllSqlsOfChildren(self, newLevel, tabOrder) -> list:
        res = []

        subItems = self.children() 
        order = tabOrder
        for index,item in enumerate(subItems):
            item.level = newLevel 
            item.productName = self.element.productName
            item.processID = self.element.processID
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            
            if item.enabled == False:
                continue
            
            outlineCell = AXOutlineCell(item)
            outlineCell.rowInfo = index
            (newOrder,result) = outlineCell.GetAllSqlsOfChildren(newLevel=newLevel, tabOrder=order)
            res.extend(result)
            order = newOrder
            
        return (order,res)
    

    @staticmethod
    def IsAXOutline(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXOutline",]:
            return False


        config = CRSSikipMgr.ReadConfig()
        if element.role_description not in ["outline",config["specialNames"]["AXOutlineDescription"],]:
            return False
        
        return True 


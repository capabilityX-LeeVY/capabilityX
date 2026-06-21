from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXTabGroup(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        # children = ele.children
        children = ele.childrenInNavigationOrder
        res = []
        if children is None or len(children) == 0:
            # fallback to regular children
            children = ele.children
            if children is None or len(children) == 0:
                LOGGER_INFO(f"AXTabGroup._traverChild: both childrenInNavigationOrder and children are empty")
                return res
            LOGGER_INFO(f"AXTabGroup._traverChild: childrenInNavigationOrder empty, using children instead ({len(children)} items)")
        
        for c in children:
            LOGGER_INFO(f"AXTabGroup._traverChild: child role=[{c.role}] name=[{c.avaliableInfo}]")
            if c.role in ("AXRadioButton",):
                res.append(c)

        if len(res) == 0:
            LOGGER_INFO(f"AXTabGroup._traverChild: no AXRadioButton found among {len(children)} children")
        
        return res

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)
    
    def _Reverse_Direction(self,subItems:list['NativeUIElement']):
        if len(subItems) <2:
            CRSKeyboard.LeftArrowKeyPressed()
            return "LeftArrow"
        
        first = subItems[0]
        second = subItems[1]
        if first is None or second is None:
            CRSKeyboard.LeftArrowKeyPressed()
            return "LeftArrow"
        
        if first.frame.x == second.frame.x:
            CRSKeyboard.UpArrowKeyPressed()
            return "UpArrow"
        
        if first.frame.y == second.frame.y:
            CRSKeyboard.LeftArrowKeyPressed()
            return "LeftArrow" 
        
        CRSKeyboard.LeftArrowKeyPressed()
        return "LeftArrow"
    
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

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        if len(subItems) == 0:
            return (res,tabOrder)
        
        for index,item in enumerate(subItems):
            self._Reverse_Direction(subItems)

        order = tabOrder
        count = len(subItems)
        dirName,dirFunc = self._Direction(subItems)
        for index,item in enumerate(subItems):
            item.level = self.element.level
            item.productName = self.element.productName
            item.processID = self.element.processID
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.screenshotInstance
            item.valuOfDescription = f'''{index+1} of {count}.'''
            item.tabOrder = order
            item.CaptureControlScreenshot()
            if item.isContainer() == True:
                (skipFlag,result,newOrder) = item.Traveral(order)
                if skipFlag is True:
                    continue
                else:
                    res.extend(result)
                    order = newOrder
            else:
                if item.enabled != True:
                    continue
                
                inserted = CTraversed.InsertElement(item)
                item.navigationKey = dirName
                if inserted == True:
                    sql = item.formatToSql()
                    res.append(sql)
                    order = order + 1
                
                if index != len(subItems) - 1:
                    dirFunc()
                
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        if len(subItems) == 0:
            LOGGER_INFO(f"AXTabGroup.FindeControlBy: no children found")
            return (False,None)
    
        LOGGER_INFO(f"AXTabGroup.FindeControlBy: {len(subItems)} children, looking for name=[{controlName}] reg=[{controlNameReg}]")
        
        # When only 1 child, skip arrow key navigation to avoid moving focus away
        if len(subItems) == 1:
            item = subItems[0]
            LOGGER_INFO(f"AXTabGroup.FindeControlBy: single child avaliableInfo=[{item.avaliableInfo}] role=[{item.role}]")
            if item.enabled and item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg):
                LOGGER_INFO(f"AXTabGroup.FindeControlBy: MATCHED single child [{item.avaliableInfo}]")
                return (True,item)
            return (False,None)
        
        for _,item in enumerate(subItems):
            self._Reverse_Direction(subItems)
        
        dirName,dirFunc = self._Direction(subItems)
        for index,item in enumerate(subItems):
            enable = item.enabled
            if enable == False:
                continue

            LOGGER_INFO(f"AXTabGroup.FindeControlBy: checking child[{index}] avaliableInfo=[{item.avaliableInfo}] role=[{item.role}]")
            if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                LOGGER_INFO(f"AXTabGroup.FindeControlBy: MATCHED child[{index}] [{item.avaliableInfo}]")
                return (True,item)
            
            if index != len(subItems) - 1:
                dirFunc()
        
        LOGGER_INFO(f"AXTabGroup.FindeControlBy: no match found in {len(subItems)} children")
        return (False,None)
    
    
    def IsEmptyGroup(self):
        children = self.element.children
        if children is None or len(children) == 0:
            return True
        
        return False

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
    def IsAXTabGroup(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ("AXTabGroup","AXGroup"):
            return False
        
        return True 

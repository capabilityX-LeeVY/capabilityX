from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXTab(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        res = []
        father = self.element.parent
        if father is not None:
            children = father.children
            res.extend(children)
        return res

    def children(self)-> list['NativeUIElement']:        
        return self._traverChild(self.element)
        
    def _Direction(self,subItems:list['NativeUIElement']):
        if len(subItems) <2:
            CRSKeyboard.RightArrowKeyPressed()
            return "RightArrow"
        
        first = subItems[0]
        second = subItems[1]
        if first is None or second is None:
            CRSKeyboard.RightArrowKeyPressed()
            return "RightArrow"
        
        if first.frame.x == second.frame.x:
            CRSKeyboard.DownArrowKeyPressed()
            return "DownArrow"
        
        if first.frame.y == second.frame.y:
            CRSKeyboard.RightArrowKeyPressed()
            return "RightArrow" 
        
        CRSKeyboard.RightArrowKeyPressed()
        return "RightArrow"

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

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()

        for index,item in enumerate(subItems):
            self._Reverse_Direction(subItems)

        res = []
        order = tabOrder + 1
        for item in subItems:
            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.processID = self.element.processID
            item.fromControl = self.element.fromControl
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate   
            item.screenshotInstance = self.element.screenshotInstance
            item.CaptureControlScreenshot()
            
            #print(item.avaliableInfo)
            if item.role in ["AXRadioButton",]:
                dir = self._Direction(subItems)
                item.navigationKey = dir
                inserted = CTraversed.InsertElement(item)
                if inserted == True:
                    item.RecordTraversalInfo()
                    sql = item.formatToSql()
                    res.append(sql)
                    order = order + 1
            else:
                continue
                # (skipFlag,result,newOrder) = item.Traveral(order)
                # if skipFlag is True:
                #     continue
                # else:
                #     res.extend(result)
                #     order = newOrder

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:            
        subItems:list['NativeUIElement'] = self.children()

        for index,item in enumerate(subItems):
            self._Reverse_Direction(subItems)
        
        inTab = False

        for item in subItems:
            if item.role in ["AXRadioButton",]:
                if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                    inTab = True
            
        for item in subItems:
            enable = item.enabled
            if enable == False:
                continue
            
            if inTab:
                if item.role in ["AXRadioButton",]:
                    if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                        return (True,item)
                    
                    self._Direction(subItems)

            else:
                if item.role in ["AXRadioButton",]:
                    continue
                
                return item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)

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
            
            if item.role in ["AXRadioButton",]:
                if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
                    return (True,item)
            else:
                return item.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            
        return (False,self.element)
    

    @staticmethod
    def IsAXTab(element:NativeUIElement) -> bool:
        if element is None:
            return False

        if element.role != "AXTab":
            return False
        
        config = CRSSikipMgr.ReadConfig()
        if element.role_description not in config["specialNames"]["TabDescription"]:
            return False
        
        return True 

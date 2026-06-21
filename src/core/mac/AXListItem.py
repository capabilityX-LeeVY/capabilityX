from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXListItem(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.needBack = False
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = ele.children
        result = []
        result.extend(children)
        return result

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)

    def Traveral(self,tabOrder)-> list:
        subItems:list['NativeUIElement'] = self.children()
        res = []
        order = tabOrder
        # add self
        if self.element.enabled == False:
            return (res,order)
        
        self.CaptureControlScreenshot()
        inserted = CTraversed.InsertElement(self.element)
        if inserted == True:
            self.element.tabOrder = order
            sql = self.element.formatToSql()
            res.append(sql)
            order = order  + 1

        # for index,item in enumerate(subItems):
        #     item.level = self.element.level 
        #     item.productName = self.element.productName
        #     item.processID = self.element.processID
        #     item.tabOrder = order
        #     item.fromControl = self.element.fromControl
        #     item.isDeep = self.element.isDeep
        #     item.tableName = self.element.tableName
        #     item.pathInfo = self.element.pathInfo
        #     item.pathInfo_Names = self.element.pathInfo_Names
        #     item.needValidate = self.element.needValidate
            
        #     if item.isContainer() == True:
        #         (skipFlag,result,newOrder) = item.Traveral(order)
        #         if skipFlag is True:
        #             continue
        #         else:
        #             res.extend(result)
        #             order = newOrder
        #     else:
        #         if item.enabled == False:
        #             continue
                
        #         if item.roleNotFocusedable() == True:
        #             continue

        #         item.navigationKey = "Tab"

        #         (skipFlag,result,newOrder) = item.Traveral(order)
        #         if skipFlag is True:
        #             continue
        #         else:
        #             res.extend(result)
        #             order = newOrder
                
        #         CRSKeyboard.TabKeyPressed()

        return (res,order)
    
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()

        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            return (True,self.element)
                
        # for _,item in enumerate(subItems):
        #     if item.isContainer() == True:
        #         res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        #         if res[0] == True:
        #             return res
        #     else:
        #         if item.enabled == False:
        #             continue
                
        #         if item.roleNotFocusedable() == True:
        #             continue

        #         res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        #         if res[0] == True:
        #             CRSKeyboard.TabKeyPressed()
        #             return res
                                
        #         CRSKeyboard.TabKeyPressed()
                    
        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        # subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            return (False,self.element)

        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            return (True,self.element)
        
        # for index,item in enumerate(subItems):
        #     if item.enabled == False:
        #         continue

        #     if item._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
        #         item.level = self.element.level 
        #         item.productName = self.element.productName
        #         item.processID = self.element.processID
        #         item.tabOrder = self.element.tabOrder
        #         item.fromControl = self.element.fromControl
        #         item.isDeep = self.element.isDeep
        #         item.tableName = self.element.tableName
        #         item.pathInfo = self.element.pathInfo
        #         item.pathInfo_Names = self.element.pathInfo_Names
        #         item.needValidate = self.element.needValidate
                
        #         return (True,item)
            
        return (False,self.element)
    
    @staticmethod
    def IsAXListItem(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        config = CRSSikipMgr.ReadConfig()
        if element.role_description in config["specialNames"]["AXListItemDescription"] and element.role in ["AXUnknown",]:
            return True
        
        if element.role_description in config["specialNames"]["AXListItemDescription"] and element.role in ["AXList",]:
            return True
        
        return False 
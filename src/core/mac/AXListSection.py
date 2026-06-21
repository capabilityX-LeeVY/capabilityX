from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from core.mac.AXGroup import AXGroup
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr
import re

class AXListSection(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        result  = []
        children = ele.children
        if children is not None:
            for c in children:
                if AXGroup.IsAXGroup(c) == True:  # remove empty group video layout
                    group = AXGroup(c)
                    if group.IsEmptyGroup() == True:
                        continue
                result.append(c)
        return result

    def children(self)-> list['NativeUIElement']:
        if self.role not in ["AXList"]:
            return []
        
        return self._traverChild(self.element)

    def _NoneDirection(self):
        pass

    def _Direction2(self,item:NativeUIElement,lastItem:NativeUIElement):
        directionFun = self._NoneDirection
        if item is None or lastItem is None:
            return ("None",directionFun)
        
        if item.frame is None or lastItem.frame is None:
            return ("None",directionFun)
        
        if item.frame.x == lastItem.frame.x:
            return ("DownArrow",CRSKeyboard.DownArrowKeyPressed)
        
        if item.frame.y == lastItem.frame.y:
            return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)
        
        return ("RightArrow",CRSKeyboard.RightArrowKeyPressed)

    def _getRowAndColumn(self,subItems:list['NativeUIElement']):
        count = len(subItems)
        firstItem = subItems[0]
        if firstItem is None or firstItem.frame is None:
            return (1,count)
        firstX = firstItem.frame.x
        firstY = firstItem.frame.y

        column = 0
        row = 0
        for item in subItems:
            if item.frame is None:
                continue
            if item.frame.y == firstY:
                column +=1
            if item.frame.x == firstX:
                row +=1

        return (row,column)


    def _GoToFirst(self,subItems:list['NativeUIElement']):
        row,column = self._getRowAndColumn(subItems)
        if row >1:
            while row >1:
                CRSKeyboard.UpArrowKeyPressed()
                row -=1
        
        if column >1:
            while column >1:
                CRSKeyboard.LeftArrowKeyPressed()
                column -=1

    def _TraveralItem(self,item:NativeUIElement,order):
        skipFlag = True
        result = []
        newOrder = order
        if item is None:
            return (skipFlag,result,newOrder)
        
        if item.role in ("AXGroup",):
            child = item.children
            if child is None or len(child) == 0:
                return (skipFlag,result,newOrder) 

            if len(child) == 1:
                child[0].level = item.level
                child[0].productName = item.productName
                child[0].tabOrder = order
                child[0].fromControl = item.fromControl
                child[0].processID = item.processID
                child[0].isDeep = item.isDeep
                child[0].tableName = item.tableName
                child[0].pathInfo = item.pathInfo
                child[0].pathInfo_Names = item.pathInfo_Names
                child[0].needValidate = item.needValidate
                child[0].screenshotInstance = item.screenshotInstance
                return child[0].Traveral(newOrder)
            else:
                return item.Traveral(newOrder)
        else:
            return item.Traveral(newOrder)
    
    def Traveral(self,tabOrder)-> list:
        res = []
        config = CRSSikipMgr.ReadConfig()
        subItems:list['NativeUIElement'] = self.children()
        order = tabOrder
        if self.element.description is not None and re.match(config["specialNames"]["ShareDialogSelectScreen"],self.description.strip()):
            CRSKeyboard.TabKeyPressed()
            return (res,order)
        
        if self.element.description is not None and re.match(config["specialNames"]["ShareDialogSelectApp"],self.description.strip()):
            CRSKeyboard.TabKeyPressed()
            CRSKeyboard.TabKeyPressed()
            CRSKeyboard.TabKeyPressed()
            return (res,order)
        
        self._GoToFirst(subItems)
        #CRSKeyboard.DownArrowKeyPressed()
        row,column = self._getRowAndColumn(subItems)

        for index,item in enumerate(subItems):
            if index >=1 and index % column ==0:
                # move to next row
                for i in range(column):
                    CRSKeyboard.LeftArrowKeyPressed()

                CRSKeyboard.DownArrowKeyPressed()

            item.level = self.element.level
            item.productName = self.element.productName
            item.tabOrder = order
            item.fromControl = self.element.fromControl
            item.processID = self.element.processID
            item.isDeep = self.element.isDeep
            item.tableName = self.element.tableName
            item.pathInfo = self.element.pathInfo
            item.pathInfo_Names = self.element.pathInfo_Names
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.element.screenshotInstance
            
            (skipFlag,result,newOrder) = self._TraveralItem(item=item,order=order)
            if skipFlag == True:
                continue
            
            if index != len(subItems) -1:
                CRSKeyboard.RightArrowKeyPressed()

            res.extend(result)
            order = newOrder

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        config = CRSSikipMgr.ReadConfig()
        if self.element.description is not None and re.match(config["specialNames"]["ShareDialogSelectScreen"],self.description.strip()):
            CRSKeyboard.TabKeyPressed()
            return (False,None)
        
        if self.element.description is not None and re.match(config["specialNames"]["ShareDialogSelectApp"],self.description.strip()):
            CRSKeyboard.TabKeyPressed()
            CRSKeyboard.TabKeyPressed()
            CRSKeyboard.TabKeyPressed()
            return (False,None)
        
        subItems:list['NativeUIElement'] = self.children()
        self._GoToFirst(subItems)
        row,column = self._getRowAndColumn(subItems)

        for index,item in enumerate(subItems):
            if index >=1 and index % column ==0:
                # move to next row
                for i in range(column):
                    CRSKeyboard.LeftArrowKeyPressed()
                    
                CRSKeyboard.DownArrowKeyPressed()

            if AXGroup.IsAXGroup(item) == True:
                group = AXGroup(item)
                if index == len(subItems) -1:
                   group.needBack = False
                   
                if group.IsEmptyGroup() == True:
                    continue

                res = group.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    return res
            else:
                res = item.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    return res
                else:
                    continue
                
            if index != len(subItems) -1:
                CRSKeyboard.RightArrowKeyPressed()

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
                    return subItems[0].LocateItem(controlName,controlHash,controlNameReg)
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
                
                res = item.LocateItem(controlName,controlHash,controlNameReg)
                if res[0] == True:
                    return res
            
        return (False,self.element)

    @staticmethod
    def IsAXListSection(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        config = CRSSikipMgr.ReadConfig()        
        if element.role in ["AXList"] and element.role_description  in config["specialNames"]["AXListDescription_section"]:
            return True
        
        return False 

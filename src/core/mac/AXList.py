from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from core.mac.AXGroup import AXGroup
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional
from core.mac.RSSkipMgr import CRSSikipMgr

class AXList(NativeUIElement):
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
    
        # result  = []
        # children = ele.children

        # if children is not None:
        #     for c in children:
        #         # if c.isContainer() == True:
        #         #     res = self._traverChild(c)
        #         #     result.extend(res)
        #         # elif c.roleLevelOne() == True:
        #         #     if c.enabled != True:
        #         #         continue
        #         #     result.append(c)
        #         # else:
        #         #     message = f'''role {c.role} not supported!'''
        #         #     raise Exception (message)

        #         if c.role in ["AXList"] or c.role_description in ["collection"]:
        #             res = self._traverChild(c)
        #             result.extend(res)
        #         else:
        #             if c.role in ["AXGroup"]:
        #                 group = AXGroup(c)
        #                 if group.IsEmptyGroup() == True:
        #                     continue
        #                 else:
        #                     c.RecordTraversalInfo()
        #                     result.append(c)
        #             else:
        #                 result.append(c)
        # return result

    def children(self)-> list['NativeUIElement']:        
        return self._traverChild(self.element)

    def PrintItem(self,item):
        next = item.nextContentSibling
        if next is not None:
            print("=========Next:=================")
            next.print()

        previous = item.previousContentSibling
        if previous is not None:
            print("=========previous:=================")
            previous.print()

        above = item.contentSiblingAbove
        if above is not None:
            print("=========above:=================")
            above.print()

        below = item.contentSiblingBelow
        if below is not None:
            print("=========below:=================")
            below.print()

        first = item.firstContentSibling
        if first is not None:
            print("=========first:=================")
            first.print()

        last = item.lastContentSibling
        if last is not None:
            print("=========last:=================")
            last.print()

    def _Direction(self,item:NativeUIElement):
        next = item.nextContentSibling
        itemFrame = item.frame
        nextFrame = next.frame
        if itemFrame.y == nextFrame.y:
            CRSKeyboard.RightArrowKeyPressed()
            return "RightArrow"
        
        if itemFrame.x == nextFrame.x:
            CRSKeyboard.DownArrowKeyPressed()
            return "DownArrow"
        
        CRSKeyboard.TabKeyPressed()
        return "Tab"

    def Traveral(self,tabOrder)-> list:
        res = []
        subItems:list['NativeUIElement'] = self.children()
        order = tabOrder
        columnCount = 0
        lastFrame = None
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
            item.needValidate = self.element.needValidate
            item.screenshotInstance = self.screenshotInstance

            (skipFlag,result,newOrder) = item.Traveral(order)
            if skipFlag == True:
                continue

            res.extend(result)
            order = newOrder

            # if lastFrame == None:
            #     lastFrame = item.frame
            # else:
            #     frame = item.frame
            #     if frame.x != lastFrame.x and frame.y != lastFrame.y:
            #         for i in range(columnCount):
            #             CRSKeyboard.LeftArrowKeyPressed()
                    
            #         CRSKeyboard.DownArrowKeyPressed()
            #         columnCount = 0
            #         item.navigationKey = "DownArrow"
            #     else:
            #         columnCount  = columnCount + 1
            #         if frame.x == lastFrame.x:
            #             CRSKeyboard.DownArrowKeyPressed()
            #             item.navigationKey = "DownArrow"

            #         elif frame.y == lastFrame.y:
            #             CRSKeyboard.RightArrowKeyPressed()
            #             item.navigationKey = "RightArrow"

            #     lastFrame = frame
            
            if index != len(subItems) - 1:
                next = item.nextContentSibling
                if next is not None:
                    self._Direction(item)


                    
        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems:list['NativeUIElement'] = self.children()
        lastFrame = None
        columnCount = 0
        for index,item in enumerate(subItems):
            if lastFrame == None:
                lastFrame = item.frame
            else:
                frame = item.frame
                if frame.x != lastFrame.x and frame.y != lastFrame.y:
                    for i in range(columnCount):
                        CRSKeyboard.LeftArrowKeyPressed()
                    
                    CRSKeyboard.DownArrowKeyPressed()
                    columnCount = 0
                else:
                    columnCount  = columnCount + 1
                    CRSKeyboard.RightArrowKeyPressed()
                lastFrame = frame

            if AXGroup.IsAXGroup(item) == True:
                group = AXGroup(item)
                # group.needBack = True
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

        return (False,None)

    def LocateItem(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:
        subItems = self.children()
        if controlName == None and controlHash == None and controlNameReg == None:
            if len(subItems)>0:
                return subItems[0].LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
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
            
            res = item.LocateItem(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                return res
            
        return (False,self.element)
    
    @staticmethod
    def IsAXList(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ["AXList"]:
            return False
        
        config = CRSSikipMgr.ReadConfig()
        if element.role_description not in config["specialNames"]["AXListDescription_collection"]:
            return False
        
        return True 

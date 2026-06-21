import core.mac as acchelp
from core.mac.AXClasses import NativeUIElement,CElementKeyInfoItem,CRSCircleCheck
from core.mac.AXTable import AXTable
from core.mac.AXList import AXList
from core.mac.RSKeyboard import CRSKeyboard
from core.mac.TraversedElementMgr import CTraversed
from common.utils.playSound import play_sound_with_subprocess
from common.utils.featureToggle import FeatureToggle
from core.mac.controlRecorder import ControlRecorder
from core.mac.RSSkipMgr import CRSSikipMgr
from rs_sdk.utils.model_handler import ModelHandler

from typing import Optional
import time
import re

from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR

class CRSApplication(object):
    pass

class CRSApplication(object):
    def __init__(self,dbConnection = None) -> None:
        self.nativeUIElement:Optional['NativeUIElement'] = None
        self.windows = list['NativeUIElement']
        self.lastTabOrder = 1
        self.currentWindowName = ""
        self.currentWindowIdentifier = ""
        self.navigationMethod = "Tab" # 'Tab', 'DownAndTab', 'Down_Right_Tab'
        self.productName = "Meeting"
        self.dbConnection = dbConnection
        self.processID = None
        self.isDeep = False
        self.needValidate = True
        self.controlRecorder = ControlRecorder()
        self.tableName = None
        self.ai_processor = ModelHandler()
    
    @staticmethod
    def ApplicationByBundleID(bundleID:str)-> Optional['NativeUIElement']:
        return acchelp.get_app_ref_by_bundle_id(bundle_id=bundleID)
    
    @staticmethod
    def TerminateAppByBundleID(bundleID:str):
        return acchelp.terminate_app_by_bundle_id(bundle_id=bundleID)


    @staticmethod
    def frontmostApp()-> CRSApplication:
        ele = NativeUIElement.get_frontmost_app()
        app =CRSApplication()
        app.nativeUIElement = ele
        return app
        
    @staticmethod
    def focusedElementOfTopWindow()-> Optional['NativeUIElement']:
        element = NativeUIElement.get_frontmost_app()
        if element is not None:
            return element.focusedElement

        return None

    def RaiseWindowByName(self,bundleID,windowNameReg) -> Optional['NativeUIElement']:
        self.nativeUIElement = CRSApplication.ApplicationByBundleID(bundleID)
        self.nativeUIElement.activate()
        windows = self.nativeUIElement.windows()
        for win in windows:
            #print(win.avaliableInfo) 
            if re.match(windowNameReg,win.avaliableInfo) != None:
                win.perform_ax_action("AXRaise")
                self.currentWindowName = win.avaliableInfo
                self.currentWindowIdentifier = win.identifier
                return win
        
        return None
    
    def RaiseFirstWindow(self,bundleID) -> Optional['NativeUIElement']:
        self.nativeUIElement = CRSApplication.ApplicationByBundleID(bundleID)
        self.nativeUIElement.activate()
        windows_result = self.nativeUIElement.windows()
        # Convert filter object to list if needed for Python 3 compatibility
        windows = list(windows_result) if not isinstance(windows_result, list) else windows_result
        if len(windows) >0:
            win = windows[0]
            win.perform_ax_action("AXRaise")

    def GetAppRefByBundleID(self,bundleID: str) -> Optional['NativeUIElement']:
        self.nativeUIElement = CRSApplication.ApplicationByBundleID(bundleID)
        windows_result = self.nativeUIElement.windows()
        # Convert filter object to list if needed for Python 3 compatibility
        windows = list(windows_result) if not isinstance(windows_result, list) else windows_result
        if len(windows) >0:
            return windows[0]
        return None
    
    def GetFocusedWindowElement(self):
        return self.nativeUIElement.focusedWindow
    
    def GetFocusedUIElementToSql(self,tabOrder) -> str:
        focuseUI:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
        if focuseUI is None:
            return ""
        
        return focuseUI.formatToSql(tabOrder)
    
    def GetFocusedUIElement(self) -> Optional['NativeUIElement']:
        focuseUI:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
        return focuseUI

    def subWindowCount(self):
        windows_result = self.nativeUIElement.windows()
        # Convert filter object to list if needed for Python 3 compatibility
        windows = list(windows_result) if not isinstance(windows_result, list) else windows_result
        return len(windows)
    
    def focuseWindowChildrenCount(self):
        focuseWin =  self.nativeUIElement.focusedWindow
        if focuseWin is not None:
            children = focuseWin.children
            if children is not None:
                return len(children)
            else:
                return 0
        return 0
    
    def _printChild(self,father,level = 1):
        if father is None:
            return
        
        if level == 1:
            message = f'''Father: {father.avaliableInfo}  {father.role}  {father.role_description}\n'''
        else:
            message = ""
        children = father.children
        if children is not None:
            for index,c in enumerate(children):
                newMsg = "  "*level +  f'''+ {index} {c.avaliableInfo}  {c.role}  {c.role_description}\n'''
                message = message + newMsg
                childMsg = self._printChild(c,level=level+1)
                message = message + childMsg
        
        if level == 1:
            print(message)

        return message

    def _childCount(self,element:NativeUIElement):
        if element is None:
            return 0
        
        child = element.children
        if child is None:
            return 0
        
        return len(child)

    def _hasPopupWindow1(self,focusedElement:NativeUIElement):
        count1 = self.subWindowCount()
        CRSKeyboard.SpaceKeyPressed()
        count2 = self.subWindowCount()
        if count2 != count1:
            CRSKeyboard.ESCPressed()
            return True
        
        return False
    
    def _hasPopupWindow2(self,focusedElement:NativeUIElement):
        if focusedElement is None:
            return False
        
        count1 = self._childCount(focusedElement.parent)
        CRSKeyboard.SpaceKeyPressed()
        count2 = self._childCount(focusedElement.parent)
        if count1 == count2:
            return False
        
        CRSKeyboard.ESCPressed()
        return True
    
    def _traversalSublayer(self,focusedElement:NativeUIElement):
        count1 = self.subWindowCount()
        CRSKeyboard.SpaceKeyPressed()
        count2 = self.subWindowCount()
        if count2 != count1:
            CRSKeyboard.ESCPressed()
            return True
        
        return False
    
    def _hasSubLayer(self,focusedElement:NativeUIElement,newFocusedElement:NativeUIElement):
        resultsSql = []
        if focusedElement is None or newFocusedElement is None:
            return (False,None,None)
        
        if focusedElement.avaliableInfo == newFocusedElement.avaliableInfo:
            return (False,None,None)
        
        if focusedElement.avaliableInfo != newFocusedElement.avaliableInfo:
            f1 = focusedElement.frame
            f2 = focusedElement.frame
            if f1 is not None and f2 is not None:
                if f1.x == f2.x and f1.y == f2.y:
                    newFocusedElement.level = focusedElement.level
                    newFocusedElement.productName = focusedElement.productName
                    newFocusedElement.tabOrder = focusedElement.tabOrder + 1
                    sql = newFocusedElement.formatToSql()
                    resultsSql.append(sql)
                    return (True,resultsSql,newFocusedElement)
                else:
                    return (True,resultsSql,newFocusedElement)

            return (False,None,None)
        

        # if self._hasPopupWindow1(focusedElement) == True:
        #     return True
        
        # if self._hasPopupWindow2(focusedElement) == True:
        #     return True
        
        return False
    

    def _findTopWindow(self,focusedElement:NativeUIElement):
        config = CRSSikipMgr.ReadConfig()
        roleDescriptions = config["specialNames"]["WindowsDescriptions"]
        SheetDescriptions = config["specialNames"]["SheetDescriptions"]
        popoverDescriptions = config["specialNames"]["PopoverDescriptions"]
        exceptRole = {
            "AXWindow":roleDescriptions,
            "AXSheet":SheetDescriptions,
            "AXPopover":popoverDescriptions,
        }
        found = False
        for role in exceptRole:
            roleDes = exceptRole[role]
            if focusedElement.role == role and (focusedElement.role_description in roleDes):
                found = True
                break

        if found == False:
            father = focusedElement.parent
            if father == None:
                return None
            else:
                return self._findTopWindow(father)
        else:
            return focusedElement

    def _traversalSubLayWindow2(self,focusedElement:NativeUIElement,fromControl:NativeUIElement = None):
        result = []
        if focusedElement is None or fromControl is None:
            return (False,result)
        
        CTraversed.ResetEachItemCount()
        tabOrder = fromControl.tabOrder + 1
        processID = fromControl.processID
        level = focusedElement.level
        productName = fromControl.productName


        focusedElement.fromControl = fromControl.hashstrBeforeClick
        focusedElement.processID = processID
        focusedElement.level = level
        focusedElement.productName = productName
        skipFlag,res,tabOrder = focusedElement.Traveral(tabOrder)
        if skipFlag == False:
            result.extend(res)

        CRSKeyboard.TabKeyPressed()
        firstHash = focusedElement.hashstr

        while(True):
            newFocusedElement = self.nativeUIElement.focusedElement
            newFocusedElement.processID = processID
            newFocusedElement.fromControl = fromControl.hashstrBeforeClick
            newFocusedElement.level = level
            newFocusedElement.productName = productName

            LOGGER_INFO(newFocusedElement.avaliableInfo,'RED')
            newHash = newFocusedElement.hashstr
            if newHash == firstHash:
                break
            
            #skipFlag,res,tabOrder = newFocusedElement.Traveral(tabOrder)
            try:
                skipFlag,res,tabOrder = newFocusedElement.Traveral(tabOrder)
            except Exception as e:
                self.dbConnection.Execute(str(e))
                break

            if skipFlag == True and newFocusedElement.isContainer() == False: 
                CRSKeyboard.TabKeyPressed()   
                continue

            CRSKeyboard.TabKeyPressed()
            result.extend(res)
        
        return (True,result)


    def _traversalSubLayWindow(self,focusedElement:NativeUIElement,fromControl:NativeUIElement = None):
        result = []
        if focusedElement is None or fromControl is None:
            return (False,result)
        
        #focusedElement.print()
        window = self._findTopWindow(focusedElement)

        if window == None or window.avaliableInfo == self.currentWindowName:
            res = self._traversalSubLayWindow2(focusedElement=focusedElement,fromControl=fromControl)
            fromControlNameHash = fromControl.hashstr
            ele = self.FindControlBy(controlHash=fromControlNameHash)
            if ele is not None and ele[0] == True:
                CRSKeyboard.SpaceKeyPressed()
            
            exceptNameReg = [
                "^Back.*",
                "^back.*",
            ]
            findFlag = False
            for index in range(5):
                if findFlag == True:
                    break
                for nameReg in exceptNameReg:
                    if findFlag == True:
                        break
                    ele = self.FindControlBy(controlNameReg=nameReg)
                    if ele is not None and ele[0] == True:
                        CRSKeyboard.SpaceKeyPressed()
                        findFlag = True
                        break

            return res
        
        #window.print()
        allChildren  =  window.childrenInNavigationOrder
        if allChildren is None:
            return (False,result)
        
        tabOrder = fromControl.tabOrder + 1
        processID = fromControl.processID
        level = focusedElement.level
        productName = fromControl.productName

        for index,child in enumerate(allChildren):
            child.processID = processID
            child.fromControl = fromControl.hashstrBeforeClick
            child.level = level
            child.productName = productName
            #child.print()
            skipFlag,res, tabOrder = child.Traveral(tabOrder)

            if skipFlag == True:    
                continue
            
            CRSKeyboard.TabKeyPressed()
            result.extend(res)

        if window.role_description in ("standard window",) and window.avaliableInfo != self.currentWindowName:
            CRSKeyboard.CommandW()
            newFocused:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
            currentWin = newFocused.window
            if currentWin.role_description in ("standard window",) and currentWin.avaliableInfo != self.currentWindowName:
                exceptNameReg = [
                ".*Discard.*",
                ".*Cancel.*",
                ".*OK.*",
                ]
                findFlag = False
                for index in range(5):
                    if findFlag == True:
                        break
                    for nameReg in exceptNameReg:
                        if findFlag == True:
                            break
                        ele = self.FindControlBy(controlNameReg=nameReg)
                        if ele is not None and ele[0] == True:
                            CRSKeyboard.SpaceKeyPressed()
                            findFlag = True
                            break
                        CRSKeyboard.TabKeyPressed()
        else:
            CRSKeyboard.ESCPressed()
        return (False,result)

    def traversalSublayer(self,focusedElement:NativeUIElement):
        result = []
        if focusedElement is None:
            return (False,result)
        
        CTraversed.ResetEachItemCount()
        lastTabOrder = focusedElement.tabOrder + 1
        level = focusedElement.level + 1
        productName = focusedElement.productName
        processID = focusedElement.processID
        hashStr = focusedElement.hashstr

        info1 = focusedElement.avaliableInfo
        f1 = focusedElement.frame
    
        CRSKeyboard.SpaceKeyPressed(2) # 这里按了之后focusedElement 可能会改变
        newFocused:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
        father = newFocused.parent
        # father1 = newFocused.topLevelUIElement
        # father2 = newFocused.window
        #father.print()
        # father1.print()
        # father2.print()
        #newFocused.print()

        newFocused.level = level
        newFocused.productName = productName
        newFocused.tabOrder = lastTabOrder
        newFocused.processID = processID
        

        info2 = newFocused.avaliableInfo
        f2 = newFocused.frame

        if info1!=info2 and (f1.x == f2.x and f1.y == f2.y):  #type 1
            newFocused.fromControl = hashStr
            newFocused.navigationKey = "SpaceKey"
            try:
                res = CTraversed.InsertElement(newFocused)
                if res == True:
                    sql = newFocused.formatToSql()
                    result.append(sql)
            except Exception as e:
                newFocused.erroMessage = str(e)
                sql = newFocused.formatToSql()
                self.dbConnection.Execute(sql)
                
            CRSKeyboard.SpaceKeyPressed(2)

            return (True,result)
    
        #type 2
        focusedElement.hashstrBeforeClick = hashStr
        _,res = self._traversalSubLayWindow(newFocused,focusedElement)
        result.extend(res)

        return (True,result)
    
    def isToTheEnd(self,firstElement:NativeUIElement,lastElement:NativeUIElement):
        currentElement:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
        if currentElement is None:
            LOGGER_WARNING(f'''isToTheEnd: focusedUI is None''')
            return (True,None)
        
        if currentElement.isEqual(firstElement) == True:
            LOGGER_WARNING(f'''isToTheEnd: focusedUIElement == firstElement''')
            return (True,currentElement)

        if currentElement.isEqual(lastElement) == True:
            LOGGER_WARNING(f'''isToTheEnd: focusedUIElement == lastElement''')
            return (True,currentElement)
        
        return (False,currentElement)
    

    def FindCloseAndDoClose(self):
        controlNames = ["Close","close",]
        for controlName in controlNames:
            res = self.FindControlAndPressed(controlName=controlName)
            if res == True:
                break

    def FindControlAndPressed(self,controlName = None,controlHash = None,controlNameReg = None):
        control = self.FindControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        if control is not None:
            CRSKeyboard.SpaceKeyPressed()
            return True
        
        return False

    def FindControlBy(self,controlName = None,controlHash = None,controlNameReg = None):
        firstElement = self.nativeUIElement.focusedElement
        keyInfo_first:CElementKeyInfoItem = CElementKeyInfoItem()
        keyInfo_first.KeyInfoFromElement(firstElement)

        lastElement = firstElement
        keyInfo_last:CElementKeyInfoItem = CElementKeyInfoItem()

        if firstElement is None:
            return (False,None)
        
        # If focus is on AXWindow, press Tab to move focus to an actual control
        if firstElement.role == "AXWindow":
            LOGGER_INFO(f'''Focused element is AXWindow, pressing Tab to move focus to a child control.''',"YELLOW")
            CRSKeyboard.TabKeyPressed()
            firstElement = self.nativeUIElement.focusedElement
            if firstElement is None:
                return (False,None)
            keyInfo_first = CElementKeyInfoItem()
            keyInfo_first.KeyInfoFromElement(firstElement)
            lastElement = firstElement

        if controlName is not None:
            LOGGER_INFO(f'''Try to find [{controlName}], first element name is:[{firstElement.avaliableInfo}], current element hash:[{firstElement.hashstr}]''',"YELLOW")
        elif controlHash is not None:
            LOGGER_INFO(f'''Try to find [{controlHash}], first element name is:[{firstElement.avaliableInfo}], current element hash:[{firstElement.hashstr}]''',"YELLOW")
        elif controlNameReg is not None:
            LOGGER_INFO(f'''Try to find [{controlNameReg}], first element name is:[{firstElement.avaliableInfo}], current element hash:[{firstElement.hashstr}]''',"YELLOW")

        res = firstElement.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        if  res[0] == True:
            return res
        
        CRSKeyboard.TabKeyPressed() 
        secondElement = None
        keyInfo_second:CElementKeyInfoItem = CElementKeyInfoItem()

        circleCheck = CRSCircleCheck()
        while(True):
            nextElement:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
            if nextElement is None:
                LOGGER_ERROR(f'''FindControlBy: next Element is None ''',"RED")
                break
            #nextElement.print()
            if controlName is not None:
                LOGGER_INFO(f'''Try to find [{controlName}], current element name is:[{nextElement.avaliableInfo}], current element hash:[{nextElement.hashstr}]''',"YELLOW")
            elif controlHash is not None:
                LOGGER_INFO(f'''Try to find [{controlHash}], current element name is:[{nextElement.avaliableInfo}], current element hash:[{nextElement.hashstr}]''',"YELLOW")
            elif controlNameReg is not None:
                LOGGER_INFO(f'''Try to find [{controlNameReg}], current element name is:[{nextElement.avaliableInfo}], current element hash:[{nextElement.hashstr}]''',"YELLOW")

            if circleCheck.isCircle(nextElement.hashstr) == True:
                LOGGER_ERROR(f'''FindControlBy: next Element is Circle ''',"RED")
                break
            
            if nextElement.isEqualWithKeyInfo(keyInfo_first) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    play_sound_with_subprocess("Ping.aiff")
                    return (res)
            
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with First element ''',"RED")
                break

            if nextElement.isEqualWithKeyInfo(keyInfo_second) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    play_sound_with_subprocess("Ping.aiff")
                    return res
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with Second element ''',"RED")
                break

            if nextElement.isEqualWithKeyInfo(keyInfo_last) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
                if res[0] == True:
                    play_sound_with_subprocess("Ping.aiff")
                    return res 
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with Last element ''',"RED")
                break

            if secondElement is None:
                secondElement = nextElement
                keyInfo_second.KeyInfoFromElement(secondElement)
                
            res = nextElement.FindeControlBy(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg)
            if res[0] == True:
                play_sound_with_subprocess("Ping.aiff")
                return res
            
            lastElement = nextElement
            keyInfo_last.KeyInfoFromElement(lastElement)
            CRSKeyboard.TabKeyPressed()

        play_sound_with_subprocess("Glass.aiff")
        return (False,None)
        
    def _NextElement_TabOnly(self,firstElement:NativeUIElement,lastElement:NativeUIElement):
        sqls = []

        if firstElement is None or lastElement is None:
            return (None,sqls,None)
        
        CRSKeyboard.TabKeyPressed()
        flag3,tabKeyElement = self.isToTheEnd(firstElement,lastElement)
        lastOrder = lastElement.tabOrder + 1
        lastLevel = lastElement.level
        
        if flag3 == False and tabKeyElement is not None:
            tabKeyElement.navigationKey = "Tab"
            tabKeyElement.productName = self.productName
            tabKeyElement.processID = self.processID
            tabKeyElement.level = lastLevel
            tabKeyElement.isDeep = self.isDeep
            tabKeyElement.tableName = self.tableName
            tabKeyElement.needValidate = self.needValidate
            skipFlag,sqls,lastOrder = tabKeyElement.Traveral(lastOrder)
            # try:
            #     skipFlag,sqls,lastOrder = tabKeyElement.Traveral(lastOrder)
            # except Exception as e:
            #     self.dbConnection.Execute(str(e))

            tabKeyElement.tabOrder = lastOrder
            LOGGER_INFO(f'''New Element found by: Tab Key Pressed ''')
            return (tabKeyElement,sqls,lastOrder)
        
        return (None,sqls,lastOrder)
    

    def _NextElement_DownAndTab(self,firstElement:NativeUIElement,lastElement:NativeUIElement):
        sqls = []

        if firstElement is None or lastElement is None:
            return (None,sqls,None)
        
        lastOrder = lastElement.tabOrder + 1
        lastLevel = lastElement.level

        CRSKeyboard.DownArrowKeyPressed()
        flag1, downArrowKeyElement = self.isToTheEnd(firstElement,lastElement)
        if flag1 == False and downArrowKeyElement is not None:
            downArrowKeyElement.navigationKey = "DownArrow"
            downArrowKeyElement.productName = self.productName
            downArrowKeyElement.processID = self.processID
            downArrowKeyElement.level = lastLevel
            skipFlag,sqls,newTabOrder = downArrowKeyElement.Traveral(lastOrder)

            downArrowKeyElement.tabOrder = lastOrder
            LOGGER_INFO(f'''New Element found by: DownArrow Key Pressed ''')
            return (downArrowKeyElement,sqls,newTabOrder)

        CRSKeyboard.TabKeyPressed()
        flag3,tabKeyElement = self.isToTheEnd(firstElement,lastElement)
        if flag3 == False and tabKeyElement is not None:
            tabKeyElement.navigationKey = "Tab"
            tabKeyElement.productName = self.productName
            tabKeyElement.processID = self.processID
            tabKeyElement.level = lastLevel
            skipFlag,sqls,newTabOrder = tabKeyElement.Traveral(lastOrder)

            tabKeyElement.tabOrder = lastOrder 
            LOGGER_INFO(f'''New Element found by: Tab Key Pressed ''')
            return (tabKeyElement,sqls,newTabOrder)
        
        return (None,sqls,lastOrder)
     
    def _NextElement_Down_Right_Tab(self,firstElement:NativeUIElement,lastElement:NativeUIElement):
        sqls = []

        if firstElement is None or lastElement is None:
            return (None,None)
        
        lastOrder = lastElement.tabOrder  + 1
        lastLevel = lastElement.level

        CRSKeyboard.DownArrowKeyPressed()
        flag1, downArrowKeyElement = self.isToTheEnd(firstElement,lastElement)
        if flag1 == False and downArrowKeyElement is not None:
            downArrowKeyElement.navigationKey = "DownArrow"
            downArrowKeyElement.productName = self.productName
            downArrowKeyElement.processID = self.processID
            downArrowKeyElement.level = lastLevel

            skipFlag,sqls,newTabOrder = downArrowKeyElement.Traveral(lastOrder)

            downArrowKeyElement.tabOrder = lastOrder
            LOGGER_INFO(f'''New Element found by: DownArrow Key Pressed ''')
            return (downArrowKeyElement,sqls,newTabOrder)

        CRSKeyboard.RightArrowKeyPressed()
        flag2, RightKeyElement = self.isToTheEnd(firstElement,lastElement)
        if flag2 == False and RightKeyElement is not None:
            RightKeyElement.navigationKey = "RightArrow"
            RightKeyElement.productName = self.productName
            RightKeyElement.processID = self.processID
            RightKeyElement.tabOrder = lastOrder
            RightKeyElement.level = lastLevel

            skipFlag,sqls,newTabOrder = RightKeyElement.Traveral(lastOrder)
            LOGGER_INFO(f'''New Element found by: RightArrow Key Pressed ''')
            return (RightKeyElement,sqls,newTabOrder)

        CRSKeyboard.TabKeyPressed()
        flag3,tabKeyElement = self.isToTheEnd(firstElement,lastElement)
        
        if flag3 == False and tabKeyElement is not None:
            tabKeyElement.navigationKey = "Tab"
            tabKeyElement.productName = self.productName
            tabKeyElement.processID = self.processID
            tabKeyElement.level = lastLevel
            skipFlag,sqls,newTabOrder = tabKeyElement.Traveral(lastOrder)

            tabKeyElement.tabOrder = lastOrder
            LOGGER_INFO(f'''New Element found by: Tab Key Pressed ''')
            return (tabKeyElement,sqls,newTabOrder)
        
        return (None,sqls,lastOrder)
    

    def _NextElement(self,firstElement:NativeUIElement,lastElement:NativeUIElement):
        if self.navigationMethod == "Tab":
            return self._NextElement_TabOnly(firstElement,lastElement)
        
        # if self.navigationMethod == "DownAndTab":
        #     return self._NextElement_DownAndTab(firstElement,lastElement)
        
        # if self.navigationMethod == "Down_Right_Tab":
        #     return self._NextElement_Down_Right_Tab(firstElement,lastElement)
        
        return (None,None,None)
                
    def TraversalNeighbors(self,firstElement:NativeUIElement):
        sqls = []
        tabOrder = firstElement.tabOrder
        if firstElement is None:
            return (sqls,tabOrder)
        
        LOGGER_INFO(f'''TraversalNeighbors: first Element :{firstElement.avaliableInfo}''')
        firstElement.navigationKey = "startPoint"
        firstElement.productName = self.productName
        firstElement.processID = self.processID
        firstElement.isDeep = self.isDeep
        firstElement.tableName = self.tableName
        firstElement.needValidate = self.needValidate
        (skipFlag,result,tabOrder) = firstElement.Traveral(tabOrder)
        if skipFlag == False:
            sqls.extend(result)

        lastElement = firstElement
        
        circleCheck = CRSCircleCheck()
        while(True):
            currentElement,newSqls,newOrder = self._NextElement(firstElement,lastElement)
            if currentElement is None:
                LOGGER_ERROR(f'''-----> TraversalNeighbors: Current Element is None ''',"RED")
                break

            if circleCheck.isCircle(currentElement.hashstr) == True:
                LOGGER_ERROR(f'''-----> TraversalNeighbors: Current Element is Circle ''',"RED")
                break
            
            if currentElement is not None:
                name = currentElement.avaliableInfo
                LOGGER_INFO(f'''-----> TraversalNeighbors: 
                            first Element is: [{firstElement.avaliableInfo}]
                            LastElement is : [{lastElement.avaliableInfo}]
                            Current Element is:[{name}],tabOrder: [{currentElement.tabOrder}] [{currentElement.role} {currentElement.role_description}] ''',"YELLOW")
                
                if name is None:
                    LOGGER_ERROR(f'''TraversalNeighbors: focusedUI name is None''',"RED")
                    break
                
                if newSqls is not None: 
                    if isinstance(newSqls,(tuple,list)):
                        sqls.extend(newSqls)
                        tabOrder = newOrder
                        
                    else:
                        sqls.append(newSqls)
                        tabOrder = newOrder + 1
                else:
                    LOGGER_ERROR(f'''TraversalNeighbors: focusedUI sql is None,{name}''',"RED")

                self.controlRecorder.cropControlImage(currentElement, lastElement)

                lastElement = currentElement
                lastElement.tabOrder = tabOrder - 1
            else:
                break

            # if currentElement.role in ["AXDateTimeArea",]:
            #     dateTimeComponents = 0
            #     try:
            #         dateTimeComponents = currentElement.__getattr__('AXDateTimeComponents')
            #     except:
            #         pass

            #     if dateTimeComponents == 224: # date pick
            #         for time in range(0,3):
            #             CRSKeyboard.TabKeyPressed()
            #     elif dateTimeComponents == 12:
            #         for time in range(0,2):
            #             CRSKeyboard.TabKeyPressed()

        return (sqls,tabOrder)

    
    def FindButtonAndPress(self,controlName = None,controlHash = None,controlNameReg = None,delay = 0):
        control = self.FindControlBy(controlName = controlName,controlHash=controlHash,controlNameReg=controlNameReg)
        if control is not None:
            CRSKeyboard.SpaceKeyPressed()
            #control.press()
            time.sleep(delay)
            LOGGER_INFO(f'''FindButtonAndPress: find control with name:{controlName}, controlHash:{controlHash} and press Done.''')
        else:
            LOGGER_ERROR(f'''FindButtonAndPress: can't find control with name:{controlName}, controlHash:{controlHash}''',"RED")

        return control
    
                    
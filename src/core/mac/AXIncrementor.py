from core.mac.AXClasses import NativeUIElement
from core.mac.RSKeyboard import CRSKeyboard
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.TraversedElementMgr import CTraversed
from typing import Optional

class AXIncrementor(NativeUIElement):
    def __init__(self, element:NativeUIElement):
        self.element = element
        super().__init__(self.element.ref)
        self.increment:NativeUIElement = None
        self.decrement:NativeUIElement = None
        self.screenshotInstance = element.screenshotInstance

    def _traverChild(self,ele:NativeUIElement)-> list['NativeUIElement']:
        children = self.element.children
        for item in children:
            subRole = item.subRole
            if subRole in ("AXDecrementArrow"):
                self.decrement = item
            
            if subRole in ("AXIncrementArrow"):
                self.increment = item

        return [self.element,]

    def children(self)-> list['NativeUIElement']:
        return self._traverChild(self.element)
        

    def Traveral(self,tabOrder)-> list:
        self.children()
        res = []
        order = tabOrder

        enable = self.element.enabled
        if enable == False:
            return (res,order)
        
        self.CaptureControlScreenshot()
        self.element.navigationKey = "Tab"
        self.element.tabOrder = order
        inserted = CTraversed.InsertElement(self.element)
        if inserted == True:
            sql = self.element.formatToSql()
            res.append(sql)
            order = order + 1

        return (res,order)
    
    def FindeControlBy(self,controlName = None,controlHash = None,controlNameReg = None) -> tuple[bool,Optional['NativeUIElement']]:            
        self.children()
        enable = self.element.enabled
        if enable == False:
            return (False,None)
        
        if self.element._isSameWith(controlName=controlName,controlHash=controlHash,controlNameReg=controlNameReg) == True:
            return (True,self.element)
                
        return (False,None)
    

    def Press(self):
        if self.increment is not None:
            self.increment.press()

        if self.decrement is not None:
            self.decrement.press()


    @staticmethod
    def IsAXIncrementor(element:NativeUIElement) -> bool:
        if element is None:
            return False
        
        if element.role not in ("AXIncrementor"):
            return False
        
        # if element.role_description not in ["stepper"]:
        #     return False
        
        return True 

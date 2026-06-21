from core.mac.RSApplication import CRSApplication
from core.mac.TraversedElementMgr import CTraversed
from core.mac.AXClasses import NativeUIElement,CElementKeyInfoItem,CRSCircleCheck
from common.utils.logger import LOGGER_INFO,LOGGER_WARNING,LOGGER_ERROR
from core.mac.RSKeyboard import CRSKeyboard
from typing import Optional
import time

class CRSFocusedDemo(CRSApplication):
    def __init__(self,dbConnection) -> None:
        super().__init__(dbConnection)

    def Test(self):
        ui = self.nativeUIElement.focusedElement
        if ui is not None:
            #ui.FindeControlBy("Screen or application")
            # ui.print()
            ui.Traveral(1)        


    def Find(self,controlName:str):
        firstElement = self.nativeUIElement.focusedElement
        keyInfo_first:CElementKeyInfoItem = CElementKeyInfoItem()
        keyInfo_first.KeyInfoFromElement(firstElement)

        lastElement = firstElement
        keyInfo_last:CElementKeyInfoItem = CElementKeyInfoItem()

        if firstElement is None:
            return (False,None)
        
        if controlName is not None:
            LOGGER_INFO(f'''Try to find [{controlName}], first element name is:[{firstElement.avaliableInfo}], current element hash:[{firstElement.hashstr}]''',"YELLOW")

        res = firstElement.FindeControlBy(controlName=controlName,controlHash=None,controlNameReg=None)
        if  res[0] == True:
            return res
        
        CRSKeyboard.TabKeyPressed() 
        secondElement = None
        keyInfo_second:CElementKeyInfoItem = CElementKeyInfoItem()

        circleCheck = CRSCircleCheck()
        while(True):
            time.sleep(5)
            nextElement:Optional['NativeUIElement'] = self.nativeUIElement.focusedElement
            nextElement.print()
            if nextElement is None:
                LOGGER_ERROR(f'''FindControlBy: next Element is None ''',"RED")
                break
            #nextElement.print()
            if controlName is not None:
                LOGGER_INFO(f'''Try to find [{controlName}], current element name is:[{nextElement.avaliableInfo}], current element hash:[{nextElement.hashstr}]''',"YELLOW")

            if circleCheck.isCircle(nextElement.hashstr) == True:
                LOGGER_ERROR(f'''FindControlBy: next Element is Circle ''',"RED")
                break
            
            if nextElement.isEqualWithKeyInfo(keyInfo_first) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=None,controlNameReg=None)
                if res[0] == True:
                    #play_sound_with_subprocess("Ping.aiff")
                    return (res)
            
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with First element ''',"RED")
                break

            if nextElement.isEqualWithKeyInfo(keyInfo_second) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=None,controlNameReg=None)
                if res[0] == True:
                    #play_sound_with_subprocess("Ping.aiff")
                    return res
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with Second element ''',"RED")
                break

            if nextElement.isEqualWithKeyInfo(keyInfo_last) == True:
                res = nextElement.FindeControlBy(controlName=controlName,controlHash=None,controlNameReg=None)
                if res[0] == True:
                    #play_sound_with_subprocess("Ping.aiff")
                    return res 
                LOGGER_ERROR(f'''FindControlBy: next Element isEqual with Last element ''',"RED")
                break

            if secondElement is None:
                secondElement = nextElement
                keyInfo_second.KeyInfoFromElement(secondElement)
                
            res = nextElement.FindeControlBy(controlName=controlName,controlHash=None,controlNameReg=None)
            if res[0] == True:
                #play_sound_with_subprocess("Ping.aiff")
                return res
            
            lastElement = nextElement
            keyInfo_last.KeyInfoFromElement(lastElement)
            CRSKeyboard.TabKeyPressed()

        #play_sound_with_subprocess("Glass.aiff")
        return (False,None)

    

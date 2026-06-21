
from core.mac.AXClasses import NativeUIElement
from typing import Optional
from common.utils.logger import LOGGER_INFO


class CRSFocusedElement(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def focusedElementOfTopWindow()-> Optional['NativeUIElement']:
        element = NativeUIElement.get_frontmost_app()
        if element is not None and element.focusedElement is not None:
            msg = f'''Current Focused Element is: {(element.focusedElement).print(level=1,printFlag=False)}'''
            LOGGER_INFO(msg,"GREEN")
            return element.focusedElement

        LOGGER_INFO("Current Focused Element is:  None!","RED")
        return None
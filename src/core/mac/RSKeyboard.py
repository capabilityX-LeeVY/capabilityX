import time
from common.utils.logger import LOGGER_INFO
from pynput.keyboard import Key, Controller

KeyboardDelay = 0.8
class CRSKeyboard(object):
    pass

    @staticmethod
    def TabKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.tab)
        keyboard.release(Key.tab)

        time.sleep(delay)

    @staticmethod
    def DownArrowKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.down)
        keyboard.release(Key.down)

        time.sleep(delay)

    @staticmethod
    def UpArrowKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.up)
        keyboard.release(Key.up)

        time.sleep(delay)

    @staticmethod
    def RightArrowKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.right)
        keyboard.release(Key.right)

        time.sleep(delay)

    @staticmethod
    def LeftArrowKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.left)
        keyboard.release(Key.left)

        time.sleep(delay)

    @staticmethod
    def SpaceKeyPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.space)
        keyboard.release(Key.space)

        time.sleep(delay)

    @staticmethod
    def ESCPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.esc)
        keyboard.release(Key.esc)

        time.sleep(delay)

    @staticmethod
    def EnterPressed(delay = KeyboardDelay):
        keyboard = Controller()
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)

        time.sleep(delay)

    @staticmethod
    def ShiftTabPressed(delay = KeyboardDelay):
        keyboard = Controller()
        with keyboard.pressed(Key.shift):
            keyboard.press(Key.tab)
            keyboard.release(Key.tab)

        time.sleep(delay)

    @staticmethod
    def CommandW(delay = KeyboardDelay):
        keyboard = Controller()
        with keyboard.pressed(Key.cmd):
            keyboard.press('w')
            keyboard.release('w')

        time.sleep(delay)

    @staticmethod
    def CommandV(delay = KeyboardDelay):
        keyboard = Controller()
        with keyboard.pressed(Key.cmd):
            keyboard.press('v')
            keyboard.release('v')

        time.sleep(delay)

    @staticmethod
    def CommandQ(delay = KeyboardDelay):
        keyboard = Controller()
        with keyboard.pressed(Key.cmd):
            keyboard.press('q')
            keyboard.release('q')

        time.sleep(delay)   

    @staticmethod
    def SendKeys(keys,delay = KeyboardDelay):
        from core.mac._input import Keyboard
        import core.mac as acchelp
        """
        keys: List[str], e.g. ["Command", "w"] or ["Ctrl", "Shift", "a"]
        """
        key_map = {
            "command": acchelp.Key.cmd,
            "cmd": acchelp.Key.cmd,
            "ctrl": acchelp.Key.ctrl,
            "control": acchelp.Key.ctrl,
            "alt": acchelp.Key.alt,
            "shift": acchelp.Key.shift,
        }
        modifiers = [key_map[k.lower()] for k in keys if k.lower() in key_map]
        
        otherkey_map = {
            "up": acchelp.Key.up,
            "down": acchelp.Key.down,
            "left": acchelp.Key.left,
            "right": acchelp.Key.right,
            "backspace": acchelp.Key.backspace,
            "delete": acchelp.Key.delete,
            "return": acchelp.Key.enter,
            "tab": acchelp.Key.tab,
            "esc": acchelp.Key.esc,
            "space": acchelp.Key.space,
            "enter": acchelp.Key.enter
        }
        normal_keys = []
        for k in keys:
            kl = k.lower()
            if kl == "enter":
                print("Empty key found in SendKeys, skip it.")
            if kl in otherkey_map:
                normal_keys.append(otherkey_map[kl])
            elif kl not in key_map:
                normal_keys.append(kl)
                
    
        if len(modifiers) == 0:
            Keyboard().send_key(normal_keys[0])
            time.sleep(delay)
        else:
            if len(keys) == 1:
                Keyboard().send_key(normal_keys[0])
                time.sleep(delay)
            else:
                Keyboard().send_key_with_modifiers(normal_keys[0], modifiers)
                time.sleep(delay)
        
        LOGGER_INFO(f"Sent keys: {' + '.join(keys)} Done.")
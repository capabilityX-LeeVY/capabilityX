import ctypes
from ctypes import wintypes

GW_HWNDNEXT = 2

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class WINDOWINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("rcWindow", wintypes.RECT),
                ("rcClient", wintypes.RECT),
                ("dwStyle", wintypes.DWORD),
                ("dwExStyle", wintypes.DWORD),
                ("dwWindowStatus", wintypes.DWORD),
                ("cxWindowBorders", wintypes.DWORD),
                ("cyWindowBorders", wintypes.DWORD),
                ("atomWindowType", wintypes.ATOM),
                ("wCreatorVersion", wintypes.WORD)]

def getWindowPid(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def getWindowTitle(hwnd):
    length = user32.GetWindowTextLengthW(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buffer, length)
    return buffer.value

def getWindowsByPid(pid):
    hwnd_list = []

    def enumWindowsProc(hwnd, lParam):
        if getWindowPid(hwnd) == lParam:
            title = getWindowTitle(hwnd)
            # print(f"HWND: {hwnd}, Title: {title}")
            hwnd_list.append(hwnd)
        return True

    EnumWindowsProcType = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProcType(enumWindowsProc), pid)
    return hwnd_list
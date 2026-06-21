import os
import yaml
from common.utils.logger import LOGGER_INFO,LOGGER_ERROR

windows_keys = ['Ctrl', 'Alt', 'Shift', 'Win', 'Tab', 'Esc',
                'Enter', 'Space', 'Up', 'Down', 'Left', 'Right',
                'Backspace', 'Delete', 'Home', 'End', 'PageUp', 'PageDown',
                'Insert', 'PrintScreen', 'ScrollLock', 'Pause', 'NumLock',
                'CapsLock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 
                'F8', 'F9', 'F10', 'F11', 'F12',
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                # Add more ...
                ]
mac_keys = ['Command', 'Option', 'Shift', 'Ctrl', 'Fn', 'CapsLock', 'Return',
            'Tab', 'Esc', 'Enter', 'Space', 'Up', 'Down', 'Left', 'Right',
            'Backspace', 'Delete', 'Home', 'End', 'PageUp', 'PageDown','Insert', 
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
            'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
            # Add more ...
            ]

class CShortcuts(object):
    def __init__(self):
        self.shutcuts_windows = None
        self.shutcuts_mac = None
        self.name = None
    
    def from_dict(self, name,shortcuts_dict):
        windows = shortcuts_dict.get('windows', None)
        mac = shortcuts_dict.get('mac', None)
        self.name = name
        if windows is not None:
            self.shutcuts_windows = windows.split('+')

        if mac is not None:
            self.shutcuts_mac = mac.split('+')

        self._Validate()

    def _Validate(self):
        if self.shutcuts_windows is None and self.shutcuts_mac is None:
            message = "At least one of windows or mac shortcuts must be provided."
            LOGGER_ERROR(message)
            raise ValueError(message)

        if self.shutcuts_windows is not None:
            for key in self.shutcuts_windows:
                if key not in windows_keys and len(key) != 1:
                    message = f'''Invalid key in windows shortcuts: {key}'''
                    LOGGER_ERROR(message)
                    raise ValueError(message)

        if self.shutcuts_mac is not None:
            for key in self.shutcuts_mac:
                if key not in mac_keys and len(key) != 1:
                    message = f'''Invalid key in mac shortcuts: {key}'''
                    LOGGER_ERROR(message)
                    raise ValueError(message)

class ShortcutsHandler(object):
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(__file__), "shortcuts.yaml")
        else:
            self.config_path = os.path.abspath(config_path)
        self.shortcuts = []
        self.load_shortcuts()
        LOGGER_INFO(f"Loaded {len(self.shortcuts)} shortcuts.")

    def load_shortcuts(self):
        LOGGER_INFO(f"Loading shortcuts from file: {self.config_path}")
        if os.path.exists(self.config_path) == False:
            message = f"YAML file not found: {self.config_path}"
            LOGGER_ERROR(message)
            raise FileNotFoundError(message)

        with open(self.config_path, 'r', encoding='utf-8') as file:
            shortcuts = yaml.safe_load(file)
            shortcuts_dict = shortcuts.get('shortcuts', [])
            for key in shortcuts_dict:
                shortcut = CShortcuts()
                shortcut.from_dict(key,shortcuts_dict[key])
                self.shortcuts.append(shortcut)

    def get_shortcut(self, shortcut_name, platform='windows'):
        for shortcut in self.shortcuts:
            if shortcut.name != shortcut_name:
                continue
            if platform == 'windows' and shortcut.shutcuts_windows is not None:
                return shortcut.shutcuts_windows
            elif platform == 'mac' and shortcut.shutcuts_mac is not None:
                return shortcut.shutcuts_mac
        return None
     

# Global instance
shutcutsHandler = ShortcutsHandler()
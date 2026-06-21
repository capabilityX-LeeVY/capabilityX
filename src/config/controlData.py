from dataclasses import dataclass

@dataclass
class ControlInfo:
    Name: str = ''
    LocalizedControlType: str = ''
    IsEnabled: int = 1
    IsKeyboardFocusable: int = 1
    HasKeyboardFocus: bool = True
    FullDescription: str = ''



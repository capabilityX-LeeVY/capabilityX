import platform

if platform.system() == "Windows":
    from core.windows.controls.control_explorer import ControlExplorer
elif platform.system() == "Linux":
    from core.linux.control_explorer import ControlExplorer
else:
    raise NotImplementedError(f"{platform.system()} platform is not supported yet.")

class ExplorerBase:

    def __init__(self):
        self.platform = platform.system()

    def explorer_base(self):
        """Create and return a control instance based on the current platform."""
        return ControlExplorer().control_explorer()

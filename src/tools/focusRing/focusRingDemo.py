import time
import platform
if platform.system().lower() == 'windows':
    import pythoncom    

from tools.webexApp import appHandler               
from tools.focusRing.modules import controlsImageGenerator, focusRingReportGenerator
if platform.system().lower() == 'windows':
    from acc.handler import accTraverse
elif platform.system().lower() == 'darwin':
    from core.mac import traverse as macTraverse

def demo():
    appHandler.initWebex()
    time.sleep(5)
    if platform.system().lower() == 'windows':
        accTraverse.traverseControls()
    elif platform.system().lower() == 'darwin':
        macTraverse.traverseControls()

    controlsImageGenerator.createImageFromControls()
    focusRingReportGenerator.getFocusRingReport()

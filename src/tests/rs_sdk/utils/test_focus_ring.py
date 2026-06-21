import os
import sys
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from pathlib import Path
from core.processor.focus_processor import FocusRingProcessor
from common.utils.logger import LOGGER_INFO

def test_onfocus_status():
    image_path = Path(fr"src\tests\rs_sdk\utils\sample\settings_vbg.png")  # or Windows C:/...
    fr = FocusRingProcessor()
    pd = fr.validate_image_focused_status(image_path)
    LOGGER_INFO(f"Analysis Result: {pd}")

test_onfocus_status()
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
    image_path = Path("/Users/weiqli/testData/img/fr")
    result_path = Path("/Users/weiqli/testData/img/fr")
    fr_detector = FocusRingProcessor(image_path, result_path)
    fr_detector.validate_onFocus_controls()
    fr_detector.validate_onFocusLost_controls()

test_onfocus_status()
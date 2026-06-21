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
from common.startup import token_initializer
from models.model_shared import VisualComplianceAnalyzer
from common.utils.logger import LOGGER_INFO

def test_onfocus_status():
    image_path = Path("/Users/weiqli/test data/img/fr/currentControls")
    result_path = Path("/Users/weiqli/test data/cc")
    prompt_file = "/Users/weiqli/workF/WebexRegressSheild/src/prompts/highContrastTemplate.md"
    token_initializer.update_token()
    analyzer = VisualComplianceAnalyzer(prompt_file, image_path, result_path)
    analyzer.generate_visual_compliance_report()

test_onfocus_status()
import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

import agent_handler
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

def test_handle_generate_control_dataset():
    agent_handler.handle_generate_control_dataset()

test_handle_generate_control_dataset()
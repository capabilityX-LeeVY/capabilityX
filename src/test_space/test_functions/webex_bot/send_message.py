import os
import sys

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from tools.MessageBot import BotMessage

def send_message_to_webex(message):
    BotMessage.sendMessageToTeams(message)

# message = "send, message test!"
# send_message_to_webex(message)
"""
Meeting-related functions for Webex meetings
"""
import os
import sys
from tools.webexApp import appHandler
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH
from core.managers.app_manager import AppManager

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)


def run_init_app_functions():
    """
    Run the specified test suites for app core
    """
    appHandler.initWebex()
    return {
        "status": "success",
        "message": "app restarted successfully",
        "action": "restart app"
    }

def uninstall_app():
    """
    Uninstall Webex application
    """
    appHandler.uninstallWebex()
    
    return {
        "status": "success",
        "message": "uninstall app successfully",
        "action": "uninstall app"
    }

def install_app():
    """
    Install Webex application
    """
    appHandler.installWebex(GT=True)
    return {
        "status": "success",
        "message": "install app successfully",
        "action": "install app"
    }

# def focus_app(platform=None):
#     """
#     Focus on Webex application window
#     """
#     if platform is None:
#         import platform
#         platform = platform.system().lower()
#     app_manager = AppManager(platform)
#     app_manager.focus_webex_app_if_needed()
#     return {
#         "status": "success",
#         "message": "focus app successfully",
#         "action": "focus app"
#     }
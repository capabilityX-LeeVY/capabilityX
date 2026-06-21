import time
from typing import Optional
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

class GTAPI(object):
    def __init__(self):
        pass

    def call_by_name(self, name: str, *args, **kwargs):
        func = getattr(self, name, None)
        if not callable(func):
            raise AttributeError(f"Unknown function: {name}")
        return func(*args, **kwargs)
    

    def run_agent_api(self, **kwargs):
        from core.strategies.api_action_strategy import ApiActionStrategy
        from config.paths import SETTINGS_PATH
        from common.handler.settingsHandler import DynamicConfig

        test_case_name = kwargs.get("test_case_name","")
        agent_node = kwargs.get("agent_node","")
        platform = kwargs.get("agent_platform","")
        params = kwargs.get("parameters",{})
        if params is None:
            raise ValueError("Parameters for run_agent_api cannot be None")
        
        if not agent_node:
            raise ValueError("Agent node must be specified for run_agent_api")
        
        if not test_case_name:
            raise ValueError("Test case name must be specified for run_agent_api")
        
        try:
            api_action = {
                "type": "api",
                "value": "run_agent_api",
                "agent_node": agent_node,
                "parameters": {
                    "test_case_name": test_case_name,
                    "platform": platform,
                    "mode": "case",
                    **params
                }
            }
            
            api_strategy = ApiActionStrategy()
            result = api_strategy.execute(api_action, None, {})
            
            LOGGER_INFO(f"Agent execution result: {result}", "GREEN" if "ERROR" not in str(result) else "RED")
            
            success = "ERROR" not in str(result) and result is not None
            return success
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to execute on agent: {str(e)}", "RED")
            return False
    

    

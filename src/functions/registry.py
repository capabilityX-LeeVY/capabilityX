"""
Function registry for managing all available functions
"""
from typing import Dict, Callable, Any
from functions.handlers import user_functions, meetings_functions, video_functions, common_functions, ucm_calling_functions, app_core_functions, bwc_calling_functions


class FunctionRegistry:
    """Registry for managing all available functions"""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._register_all_functions()
    
    def _register_all_functions(self):
        """Register all functions from different modules"""
        # User functions
        self.register('greet_user', user_functions.greet_user)
        self.register('who_are_you', user_functions.who_are_you)
        self.register('what_is_model', user_functions.what_is_model)
        self.register('what_can_you_do', user_functions.what_can_you_do)
        
        # Meeting functions
        self.register('run_meetings_functions', meetings_functions.run_meetings_functions)
        self.register('start_pmr_meeting', lambda: meetings_functions.run_test_case_function('jmt/basic/start_pmr_meeting'))
        self.register('end_meeting', lambda: meetings_functions.run_test_case_function('jmt/basic/end_meeting'))
        self.register('invite_people', lambda: meetings_functions.run_test_case_function('jmt/basic/invite_people'))
        self.register('start_screen_sharing', lambda: meetings_functions.run_test_case_function('meetings/share/start_screen_sharing'))
        self.register('stop_screen_sharing', lambda: meetings_functions.run_test_case_function('meetings/share/stop_screen_sharing'))
        
        # Video functions
        self.register('start_video', video_functions.start_video)
        self.register('stop_video', video_functions.stop_video)
                
        # Common functions
        self.register('get_current_time', common_functions.get_current_time)
        self.register('get_date', common_functions.get_date)
        self.register('wait_seconds', common_functions.wait_seconds)

        # Calling functions
        self.register('run_calling_functions', ucm_calling_functions.run_calling_functions)
        self.register('run_bwc_calling_functions', bwc_calling_functions.run_bwc_calling_functions)

        # App core functions
        self.register('run_init_app_functions', app_core_functions.run_init_app_functions)
        self.register('uninstall_app', app_core_functions.uninstall_app)
        self.register('install_app', app_core_functions.install_app)
           
    def register(self, name: str, func: Callable):
        """Register a function with a given name"""
        self._functions[name] = func
    
    def get_function(self, name: str) -> Callable:
        """Get a function by name"""
        if name not in self._functions:
            raise ValueError(f"Function '{name}' not found in registry")
        return self._functions[name]
    
    def list_functions(self) -> Dict[str, str]:
        """List all available functions with their docstrings"""
        return {
            name: func.__doc__ or "No description available"
            for name, func in self._functions.items()
        }
    
    def execute_function(self, name: str, *args, **kwargs) -> Any:
        """Execute a function by name with given arguments"""
        func = self.get_function(name)
        return func(*args, **kwargs)


# Global registry instance
function_registry = FunctionRegistry()

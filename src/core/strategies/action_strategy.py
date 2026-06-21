"""
Abstract Action Strategy Base Class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ActionStrategy(ABC):
    """Abstract base class for action execution strategies"""
    
    @abstractmethod
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> Any:
        """Execute action and return send_value"""
        pass
    
    @abstractmethod
    def get_action_type(self) -> str:
        """Get action type name"""
        pass

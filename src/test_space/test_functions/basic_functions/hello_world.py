"""
hello_world.py

Basic test function that prints hello world message
"""

from common.utils.logger import LOGGER_INFO


def print_hello_world(message="Hello World from test function!"):
    """
    Simple test function that prints a hello world message
    
    Args:
        message (str): Custom message to print
    
    Returns:
        bool: True if successful
    """
    try:
        LOGGER_INFO(f"[PRINT] {message}", "GREEN")
        return True
        
    except Exception as e:
        LOGGER_INFO(f"[ERROR] print_hello_world: {str(e)}", "RED")
        return False

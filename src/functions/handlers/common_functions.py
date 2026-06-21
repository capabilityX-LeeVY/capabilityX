# 
import datetime
import time
from common.utils.logger import LOGGER_INFO

def get_current_time():
    """Return the current time"""
    return {"current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

def get_date():
    """Return the current date"""
    return {"current_date": datetime.datetime.now().strftime("%Y-%m-%d")}

def wait_seconds(seconds: int):
    """Wait for a specified number of seconds with logging"""
    LOGGER_INFO(f"=== Starting {seconds} second wait ===")
    start_time = datetime.datetime.now()
    LOGGER_INFO(f"Start time: {start_time}")
    
    time.sleep(seconds)
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    LOGGER_INFO(f"End time: {end_time}")
    LOGGER_INFO(f"Actual duration: {duration:.2f} seconds")
    LOGGER_INFO(f"=== {seconds} second wait completed ===")
    
    return {"status": "completed", "duration": duration}
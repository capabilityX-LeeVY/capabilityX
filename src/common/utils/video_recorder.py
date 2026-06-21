"""
Simple video recorder for test execution
"""

import cv2
import mss
import numpy as np
import threading
import time
import os
from datetime import datetime
from pathlib import Path

from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG
from config.paths import RECORDING_PATH


class VideoRecorder:
    """
    Simple video recorder for test execution
    """
    
    def __init__(self, output_dir=None):
        """Initialize the video recorder"""
        if output_dir is None:
            self.output_dir = RECORDING_PATH
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.recording_thread = None
        self.video_writer = None
        
    def start_recording(self, filename=None):
        """Start recording"""
        if self.is_recording:
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_recording_{timestamp}.mp4"
        
        if not filename.endswith('.mp4'):
            filename += '.mp4'
            
        filepath = self.output_dir / filename
        
        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            args=(str(filepath),),
            daemon=True
        )
        self.recording_thread.start()
        
        LOGGER_DEBUG(f"Started recording: {filepath}")
        return str(filepath)
    
    def stop_recording(self):
        """Stop recording"""
        if not self.is_recording:
            return False
            
        self.is_recording = False
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
            
        LOGGER_INFO("Recording stopped")
        return True
    
    def _recording_loop(self, filepath):
        """Recording loop that runs in a separate thread"""
        sct = None
        try:
            # Create mss object in this thread
            sct = mss.mss()
            monitor = sct.monitors[1]  # Primary monitor
            
            # Setup video writer
            fourcc = cv2.VideoWriter.fourcc(*'mp4v')
            fps = 10
            width = monitor["width"]
            height = monitor["height"]
            
            self.video_writer = cv2.VideoWriter(
                filepath, fourcc, fps, (width, height)
            )
            
            frame_time = 1.0 / fps
            
            while self.is_recording:
                start_time = time.time()
                
                # Capture screen
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Write frame
                self.video_writer.write(frame)
                
                # Control frame rate
                elapsed = time.time() - start_time
                sleep_time = frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            LOGGER_ERROR(f"Recording error: {str(e)}")
        finally:
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            if sct:
                sct.close()


# Global recorder instance
_recorder = None

def start_test_recording(output_dir=None):
    """Start test recording"""
    global _recorder
    
    # Use RECORDING_PATH by default if no output_dir is specified
    _recorder = VideoRecorder(output_dir)
    return _recorder.start_recording()

def stop_test_recording():
    """Stop test recording"""
    global _recorder
    if _recorder:
        return _recorder.stop_recording()
    return False

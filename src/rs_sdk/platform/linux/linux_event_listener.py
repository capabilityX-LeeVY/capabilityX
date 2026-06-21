"""
Linux Event Listener - Platform-specific implementation for Linux/AT-SPI

This module provides focus change event listening functionality for Linux
using AT-SPI (Assistive Technology Service Provider Interface).

Implementation uses pyatspi for AT-SPI event monitoring, proven to work
with manual keyboard navigation (generates focus events reliably).
"""

import threading
import time
import pyatspi
from gi.repository import GLib
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


class FocusListener:
    """
    Linux-specific focus change event listener using AT-SPI.
    
    This class monitors focus changes in Linux applications using the AT-SPI
    accessibility framework. Based on proven pattern from debug_focus_monitor.py.
    
    Key Features:
    - Registers AT-SPI focus event listener
    - Runs GLib.MainLoop() in separate thread
    - Captures focus changes when user navigates with keyboard
    - Thread-safe focus tracking
    
    Note: Works with MANUAL keyboard navigation (proven).
          Programmatic keys (xdotool, rawinput) may not trigger events.
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(FocusListener, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Linux focus listener."""
        if getattr(self, "_initialized", False):
            return
        self.current_focus = None
        self.previous_focus = None
        self.running = False
        self.listener_thread = None
        self.main_loop = None
        self._lock = threading.Lock()
        self._initialized = True
        LOGGER_INFO("[FocusListener] Initialized with AT-SPI support", "GREEN")

    def _on_focus(self, event):
        """
        Callback when focus changes (runs in GLib event loop thread)
        
        Args:
            event: AT-SPI focus event
        """
        try:
            source = event.source
            name = source.name or "(no name)"
            role = source.getRoleName() or "(no role)"
            description = getattr(source, 'description', '') or ''
            accessible_id = getattr(source, 'accessibleId', '') or ''
            with self._lock:
                # Update focus tracking
                self.previous_focus = self.current_focus
                self.current_focus = {
                    'name': name,
                    'role': role,
                    'description': description,
                    'accessible_id': accessible_id
                }
            
            if accessible_id:
                LOGGER_INFO(
                    f"[FocusListener] Focus changed: {role} '{name}' (id: {accessible_id})",
                    "CYAN"
                )
            else:
                LOGGER_INFO(f"[FocusListener] Focus changed: {role} '{name}'", "CYAN")
            
        except Exception as e:
            LOGGER_ERROR(f"[FocusListener] Error in focus callback: {e}")

    def _event_loop_thread(self):
        """
        Event loop thread - runs GLib.MainLoop() to process AT-SPI events
        """
        try:
            LOGGER_INFO("[FocusListener] Starting GLib.MainLoop() in background thread...", "CYAN")
            
            # Register focus event listener
            pyatspi.Registry.registerEventListener(self._on_focus, "focus")
            LOGGER_INFO("[FocusListener] ✅ AT-SPI focus listener registered", "GREEN")
            
            # Create and run main loop
            self.main_loop = GLib.MainLoop()
            self.main_loop.run()
            
            LOGGER_INFO("[FocusListener] GLib.MainLoop() stopped", "YELLOW")
            
        except Exception as e:
            LOGGER_ERROR(f"[FocusListener] Error in event loop thread: {e}")
        finally:
            # Cleanup
            try:
                if self.main_loop:
                    pyatspi.Registry.deregisterEventListener(self._on_focus, "focus")
                    LOGGER_INFO("[FocusListener] AT-SPI listener deregistered", "YELLOW")
            except:
                pass

    def start(self):
        """
        Start the focus change listener in background thread.
        
        Starts GLib.MainLoop() to process AT-SPI events.
        Events are captured when user navigates with keyboard.
        """
        if self.running:
            LOGGER_WARNING("[FocusListener] Already running")
            return
        
        with self._lock:
            self.running = True
            self.current_focus = None
            self.previous_focus = None
        
        # Start event loop in separate thread (non-blocking)
        self.listener_thread = threading.Thread(
            target=self._event_loop_thread,
            daemon=True,
            name="FocusListener-EventLoop"
        )
        self.listener_thread.start()
        
        # Give thread time to start
        time.sleep(0.2)
        
        LOGGER_INFO("[FocusListener] ✅ Started - monitoring focus events", "GREEN")
        LOGGER_INFO("[FocusListener] ⚠️  Note: Works with manual keyboard navigation", "YELLOW")
    
    def get_current_focus(self):
        """
        Get the current focused element information.
        
        Returns:
            dict or None: Dictionary with 'name', 'role', 'description', 'timestamp'
                         or None if no focus event has been captured yet
        """
        with self._lock:
            # Return a COPY of the dict to avoid reference issues
            # This ensures each call gets fresh data instead of stale cached reference
            return self.current_focus.copy() if self.current_focus else None
    
    def stop(self):
        """
        Stop the focus change listener and release resources.
        """
        if not self.running:
            LOGGER_WARNING("[FocusListener] Not running")
            return
        
        LOGGER_INFO("[FocusListener] Stopping...", "YELLOW")
        
        with self._lock:
            self.running = False
        
        # Stop GLib.MainLoop()
        if self.main_loop and self.main_loop.is_running():
            self.main_loop.quit()
        
        # Wait for thread to finish (with timeout)
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2.0)
            if self.listener_thread.is_alive():
                LOGGER_WARNING("[FocusListener] Thread did not stop cleanly", "YELLOW")
        
        LOGGER_INFO("[FocusListener] ✅ Stopped", "GREEN")

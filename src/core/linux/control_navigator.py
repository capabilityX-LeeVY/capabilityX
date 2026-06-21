"""
Linux Control Navigator

Provides direct UI control access using dogtail (AT-SPI) for Linux.
Mirrors Windows ControlNavigator functionality for cross-platform compatibility.

Key Features:
- Direct control access (grabFocus, click, doAction)
- Keyboard simulation fallback (Tab navigation)
- Control tree traversal and metadata collection
- Dogtail (AT-SPI) integration for accessibility tree access
"""

import time
import subprocess
from typing import Tuple, List, Dict, Any, Optional
from dogtail.tree import root
from dogtail.config import config as dogtail_config

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from rs_sdk.platform.linux.linux_event_listener import FocusListener

# Constants
class NavigationConfig:
    """Configuration constants for navigation behavior"""
    DEFAULT_SEARCH_CUTOFF = 30
    DEFAULT_SEARCH_BACKOFF = 0.1
    DEFAULT_ACTION_DELAY = 0.5
    DEFAULT_MAX_TABS = 50
    DEFAULT_MAX_EVENT_ATTEMPTS = 30
    FOCUS_WAIT_TIME = 0.2
    TAB_WAIT_TIME = 0.15
    EVENT_INIT_WAIT = 0.3
    REFOCUS_WAIT = 0.15

class ContainerTypes:
    """Container types that require special navigation"""
    GRID_LIKE = ['table', 'tree table', 'list', 'tree', 'grid', 'scroll pane']
    GENERIC = ['panel', 'filler', 'scroll pane']


class ControlNavigator:
    """
    Linux Control Navigator - keyboard-based UI navigation using dogtail (AT-SPI)
    
    Mirrors Windows ControlNavigator API for cross-platform compatibility.
    """
    
    # Class-level singleton for FocusListener - shared across ALL instances
    # This ensures only ONE listener thread is running, preventing multiple
    # listeners from conflicting with each other
    _shared_focus_listener = None
    _listener_lock = None
    
    def __init__(self):
        """Initialize the control navigator"""
        self._configure_dogtail()
        self._initialize_state()
        LOGGER_INFO("[navigator][init] Initialized with dogtail/AT-SPI support", "GREEN")
    
    def _configure_dogtail(self):
        """Configure dogtail for accessibility tree access"""
        dogtail_config.search_cut_off_limit = NavigationConfig.DEFAULT_SEARCH_CUTOFF
        dogtail_config.search_back_off_delay = NavigationConfig.DEFAULT_SEARCH_BACKOFF
        dogtail_config.action_delay = NavigationConfig.DEFAULT_ACTION_DELAY
        dogtail_config.debug_searching = False
    
    def _initialize_state(self):
        """Initialize navigation state variables"""
        # Navigation state
        self.current_control = None
        self.order = 0
        
        # Track previous controls for navigation
        self.pre_control_name_up = None
        self.pre_control_name_down = None
        self.pre_control_name_left = None
        self.pre_control_name_right = None
        self.pre_control_tab = None
        
        # Control type flags
        self.flag_tree = ""
        self.flag_tab = ""
        self.flag_list = ""
        self.flag_combox = ""
        
        # Event-based navigation support - use class-level singleton listener
        # This ensures only ONE listener exists across ALL ControlNavigator instances
        if ControlNavigator._listener_lock is None:
            import threading
            ControlNavigator._listener_lock = threading.Lock()
        
        with ControlNavigator._listener_lock:
            if ControlNavigator._shared_focus_listener is None:
                LOGGER_INFO("[navigator][init] Creating singleton FocusListener (first instance)", "GREEN")
                ControlNavigator._shared_focus_listener = FocusListener()
                ControlNavigator._shared_focus_listener.start()
                time.sleep(NavigationConfig.EVENT_INIT_WAIT)
                LOGGER_INFO("[navigator][init] Singleton focus listener started and active", "GREEN")
            else:
                LOGGER_INFO("[navigator][init] Reusing existing singleton FocusListener", "CYAN")
        
        # Point instance variable to the shared singleton
        self.focus_listener = ControlNavigator._shared_focus_listener

    def control_navigator(self, level=1, from_control=None, process_id=None,
                         is_validated=False, is_recorded=False, is_located=False,
                         locate_control_meta=None, close_flag=False, locate_id_flag=True,
                         locate_optimized_by_window_flag=False, test_case_flag=False):
        """
        Main navigation method - traverses controls using keyboard navigation
        
        Args:
            level: Navigation depth level
            from_control: Starting control (unused in Linux, we use focused control)
            process_id: Process ID to filter (unused in Linux)
            is_validated: Whether to validate controls
            is_recorded: Whether to record control metadata
            is_located: Whether to locate specific control
            locate_control_meta: Metadata of control to locate
            close_flag: Whether to close control after locating
            locate_id_flag: Whether to locate by ID
            locate_optimized_by_window_flag: Optimization flag
            test_case_flag: Test case execution flag
            
        Returns:
            tuple: (traverse_record_controls, traverse_all_controls, result, control_metadata)
        """
        traverse_record_controls = []
        traverse_all_controls = []
        control_metadata = []
        result = False
        
        try:
            LOGGER_DEBUG(f"[navigator][traverse] Starting - locate_control: {locate_control_meta}", "CYAN")
            
            # Get Webex application from accessibility tree
            webex_app = self._find_webex_application()
            if not webex_app:
                return traverse_record_controls, traverse_all_controls, result, control_metadata
            
            # Get currently focused control
            self.current_control = self._get_focused_control(webex_app)
            
            # Validate and extract locate parameters
            if not (is_located and locate_control_meta):
                LOGGER_ERROR("[navigator][traverse] Called without locate target - this shouldn't happen", "RED")
                return traverse_record_controls, traverse_all_controls, result, control_metadata
            
            # Extract target information
            target_name = locate_control_meta.get('name', '')
            target_id = locate_control_meta.get('id', '')
            control_type = locate_control_meta.get('control_type', '')
            
            LOGGER_INFO(f"[navigator][locate] Target: {target_name} (type: {control_type})", "CYAN")
            
            # Attempt to locate and navigate to control
            result, found_control = self._navigate_to_control(webex_app, target_name, target_id, control_type)
            
            # Process results
            if result and found_control:
                self._process_successful_navigation(
                    found_control, target_name, is_recorded, test_case_flag,
                    traverse_all_controls, traverse_record_controls, control_metadata
                )
                LOGGER_INFO(f"[navigator][locate] ✅ Successfully located: {target_name}", "GREEN")
            else:
                LOGGER_WARNING(f"[navigator][locate] ❌ Failed to locate: {target_name}", "YELLOW")
            
        except Exception as e:
            LOGGER_ERROR(f"[navigator][traverse] Error: {str(e)}", "RED")
            import traceback
            traceback.print_exc()
        
        return traverse_record_controls, traverse_all_controls, result, control_metadata
    
    def _find_webex_application(self, max_retries=5, retry_delay=1.0):
        """Find the Webex application in the accessibility tree with retry logic
        
        Args:
            max_retries: Maximum number of retry attempts (default: 5)
            retry_delay: Delay in seconds between retries (default: 1.0)
        
        Returns:
            Application object or None if not found
        """
        for attempt in range(max_retries):
            apps = root.applications()
            
            for app in apps:
                app_name = app.name
                # Look for Webex app (exact match, case-insensitive)
                if app_name.lower() == 'webex':
                    # Verify it's the correct Webex app using description field
                    description = getattr(app, 'description', '')
                    if 'ciscocollabhost' in description.lower():
                        LOGGER_DEBUG(f"[navigator][traverse] ✅ Found Webex app: '{app_name}' (CiscoCollabHost)", "GREEN")
                        return app
                    else:
                        LOGGER_DEBUG(f"[navigator][traverse] Found '{app_name}' but description doesn't match: '{description}'", "YELLOW")
            
            # If not found on this attempt, log and retry
            if attempt < max_retries - 1:
                LOGGER_WARNING(f"[navigator][traverse] Webex app not in accessibility tree (attempt {attempt + 1}/{max_retries}), retrying...", "YELLOW")
                LOGGER_DEBUG(f"[navigator][traverse] Available apps: {[app.name for app in apps]}", "YELLOW")
                time.sleep(retry_delay)
            else:
                # Final attempt failed
                LOGGER_ERROR("[navigator][traverse] Webex application not found after all retries", "RED")
                LOGGER_DEBUG(f"[navigator][traverse] Available apps: {[app.name for app in apps]}", "RED")
        
        return None
    
    def _get_focused_control(self, webex_app):
        """Get the currently focused control in the application
        
        Prioritizes focus listener (event-driven, real-time) over tree query
        (which can return stale data). 
        
        Args:
            webex_app: The Webex application object
            
        Returns:
            Focused control or application root if not found
        """
        # Strategy 1: Use focus listener data (more reliable, real-time)
        focus_info = self.focus_listener.get_current_focus() if self.focus_listener else None
        if focus_info:
            focus_name = focus_info.get('name', '')
            focus_role = focus_info.get('role', '')
            LOGGER_DEBUG(f"[navigator][traverse] Using focus from event listener: {focus_role} '{focus_name}'", "GREEN")
            
            # Try to find this element in the tree (for returning actual control object)
            try:
                focused = webex_app.findChild(
                    lambda x: hasattr(x, 'name') and x.name == focus_name,
                    retry=False,
                )
                if focused:
                    LOGGER_DEBUG(f"[navigator][traverse] Found matching control in tree", "GREEN")
                    return focused
                else:
                    LOGGER_DEBUG(f"[navigator][traverse] Could not find exact name match in tree, but trusting listener data", "YELLOW")
                    LOGGER_DEBUG(f"[navigator][traverse] Applying focus workaround: Tab + Shift+Tab to reset focus", "YELLOW")
                    # Workaround: Focus might be wrong, do Tab and back-tab to reset
                    self._send_key("Tab")
                    time.sleep(NavigationConfig.REFOCUS_WAIT)
                    self._send_key("shift+Tab")
                    time.sleep(NavigationConfig.REFOCUS_WAIT)
                    
                    # CRITICAL: Wait aggressively for AT-SPI events to be fully processed
                    # Focus events are logged immediately but self.current_focus dict 
                    # is updated asynchronously in GLib.MainLoop background thread
                    # Poll multiple times to ensure we catch the update
                    LOGGER_DEBUG(f"[navigator][traverse] Waiting for focus to stabilize after Tab/Shift+Tab...", "YELLOW")
                    max_polls = 10
                    poll_interval = 0.1
                    last_focus_name = None
                    stable_count = 0
                    
                    # CRITICAL: Sleep BEFORE first poll to allow event processing
                    time.sleep(poll_interval)
                    
                    for poll in range(max_polls):
                        time.sleep(poll_interval)
                        current_info = self.focus_listener.get_current_focus() if self.focus_listener else None
                        if current_info:
                            current_name = current_info.get('name', '')
                            LOGGER_DEBUG(f"[navigator][traverse] Poll {poll+1}/{max_polls}: '{current_name}'", "CYAN")
                            
                            # Check if focus has stabilized (same name for 2 consecutive polls)
                            if current_name == last_focus_name and current_name != focus_name:
                                stable_count += 1
                                if stable_count >= 2:
                                    LOGGER_DEBUG(f"[navigator][traverse] Focus stabilized after {poll+1} polls", "GREEN")
                                    break
                            else:
                                stable_count = 0
                            
                            last_focus_name = current_name
                    
                    # Get updated focus from listener after workaround
                    updated_focus_info = self.focus_listener.get_current_focus() if self.focus_listener else None
                    if updated_focus_info:
                        updated_focus_name = updated_focus_info.get('name', '')
                        LOGGER_DEBUG(f"[navigator][traverse] Updated focus from listener after workaround: '{updated_focus_name}'", "CYAN")
                        
                        # Try to find control matching updated focus
                        try:
                            focused_after_workaround = webex_app.findChild(
                                lambda x: hasattr(x, 'name') and x.name == updated_focus_name,
                                retry=False,
                            )
                            if focused_after_workaround:
                                LOGGER_DEBUG(f"[navigator][traverse] Found matching control after workaround: {getattr(focused_after_workaround, 'name', 'N/A')}", "GREEN")
                                return focused_after_workaround
                        except Exception as e:
                            LOGGER_DEBUG(f"[navigator][traverse] Could not find control matching updated focus: {e}", "YELLOW")
                    
                    # Fallback to app root if still can't find focused control
                    LOGGER_DEBUG(f"[navigator][traverse] Falling back to app root", "YELLOW")
                    return webex_app
            except Exception as e:
                LOGGER_DEBUG(f"[navigator][traverse] Error searching tree: {e}", "YELLOW")
                return webex_app
        
        # Strategy 2: Only use tree query if listener has NO data
        LOGGER_DEBUG(f"[navigator][traverse] Focus listener has no data, querying tree...", "YELLOW")
        try:
            focused = webex_app.findChild(lambda x: hasattr(x, 'focused') and x.focused)
            if focused:
                focus_name = getattr(focused, 'name', '')
                LOGGER_DEBUG(f"[navigator][traverse] Found focused control from tree query: {focus_name}", "YELLOW")
                
                # Update focus listener with tree data to bootstrap it
                if self.focus_listener:
                    self.focus_listener.current_focus = {
                        'name': focus_name,
                        'role': getattr(focused, 'roleName', ''),
                        'description': getattr(focused, 'description', '')
                    }
                    LOGGER_DEBUG(f"[navigator][traverse] Bootstrapped focus listener with tree data", "YELLOW")
                
                return focused
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][traverse] Could not determine focused control: {e}", "YELLOW")
        
        LOGGER_DEBUG("[navigator][traverse] Using app root as current control", "YELLOW")
        return webex_app
    
    def _process_successful_navigation(self, found_control, target_name, is_recorded, 
                                      test_case_flag, traverse_all_controls, 
                                      traverse_record_controls, control_metadata):
        """Process a successful control navigation
        
        Args:
            found_control: The control that was found
            target_name: Name of the target control
            is_recorded: Whether to record metadata
            test_case_flag: Test case execution flag
            traverse_all_controls: List to append traversed controls
            traverse_record_controls: List to append recorded controls
            control_metadata: List to append control metadata
        """
        control_name = getattr(found_control, 'name', target_name)
        traverse_all_controls.append(control_name)
        
        if is_recorded or test_case_flag:
            metadata = self._build_control_metadata(found_control)
            control_metadata.append(metadata)
            traverse_record_controls.append(control_name)
    
    def _navigate_to_control(self, app, target_name, target_id, control_type=''):
        """
        Navigate to a specific control using keyboard-first approach
        
        Two-Strategy Approach:
        
        **Strategy 1: Tab Navigation** (preferred - more robust for dynamic content)
          - Tab through controls until target is focused
          - Works reliably for web-based forms and dynamic elements
        
        **Strategy 2: Direct Access** (fallback when Tab fails)
          - Find element by ID (most reliable) or name (fallback)
          - Use grabFocus() to focus
          - Use click() or doAction() to activate
        
        Args:
            app: Application root
            target_name: Target control name
            target_id: Target control ID
            control_type: Control type (unused, kept for API compatibility)
            
        Returns:
            tuple: (success, control)
        """
        LOGGER_INFO(f"[navigator][locate] Target: ID='{target_id}', name='{target_name}'", "CYAN")
        
        # Strategy 1: Tab Navigation (preferred)
        success, control = self._try_tab_navigation(app, target_name, target_id, control_type)
        if success:
            return success, control
        
        # Strategy 2: Direct Access (fallback)
        LOGGER_WARNING(f"[navigator][locate] Tab navigation failed, trying direct access", "YELLOW")
        return self._try_direct_access(app, target_name, target_id, control_type)
    
    def _try_tab_navigation(self, app, target_name, target_id, control_type):
        """Try Tab navigation strategy
        
        Args:
            app: Application root
            target_name: Target control name
            target_id: Target control ID
            control_type: Control type
            
        Returns:
            tuple: (success, control)
        """
        LOGGER_INFO(f"[navigator][locate] Trying Tab navigation first", "CYAN")
        success, control = self._tab_to_control(
            app, target_name, target_id, control_type, 
            max_tabs=NavigationConfig.DEFAULT_MAX_TABS
        )
        if success:
            LOGGER_INFO(f"[navigator][locate] ✅ Tab navigation successful", "GREEN")
        return success, control
    
    def _try_direct_access(self, app, target_name, target_id, control_type):
        """Try direct access strategy
        
        Args:
            app: Application root
            target_name: Target control name
            target_id: Target control ID
            control_type: Control type
            
        Returns:
            tuple: (success, control)
        """
        # Find element (try ID first, then name)
        target_control = self._find_control(app, target_id, target_name)
        
        if target_control:
            return self._activate_control(target_control, control_type)
        
        LOGGER_WARNING(f"[navigator][locate] ❌ Both strategies failed", "YELLOW")
        return False, None
    
    def _find_control(self, app, target_id, target_name):
        """Find control by ID or name
        
        Args:
            app: Application root
            target_id: Target control ID
            target_name: Target control name
            
        Returns:
            Control object or None
        """
        # Try by ID first
        if target_id:
            control = self._find_control_by_id(app, target_id)
            if control:
                return control
        
        # Fallback to name search
        if target_name:
            return self._find_control_by_name(app, target_name)
        
        return None
    
    def _find_control_by_id(self, app, target_id):
        """Find control by exact accessible ID
        
        Args:
            app: Application root
            target_id: Target control ID
            
        Returns:
            Control object or None
        """
        try:
            def id_matcher(x):
                if not hasattr(x, 'accessibleId'):
                    return False
                return x.accessibleId == target_id
            
            control = app.findChild(id_matcher, retry=False)
            if control:
                LOGGER_INFO(f"[navigator][locate] ✅ Found by ID: '{target_id}' (actual: '{control.accessibleId}')", "GREEN")
                return control
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][locate] ID search failed: {e}", "YELLOW")
        
        return None
    
    def _find_control_by_name(self, app, target_name):
        """Find control by name
        
        Args:
            app: Application root
            target_name: Target control name
            
        Returns:
            Control object or None
        """
        try:
            control = app.findChild(
                lambda x: hasattr(x, 'name') and x.name == target_name,
                retry=False,
            )
            if control:
                LOGGER_INFO(f"[navigator][locate] ✓ Found by name: '{target_name}'", "GREEN")
                return control
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][locate] Name search failed: {e}", "YELLOW")
        
        return None
    
    def _activate_control(self, control, control_type):
        """Activate a control using focus and click/action
        
        Args:
            control: Control to activate
            control_type: Control type ('input' or other)
            
        Returns:
            tuple: (success, control)
        """
        try:
            # Focus the control
            if not (hasattr(control, 'focused') and control.focused):
                LOGGER_INFO(f"[navigator][locate] Setting focus directly (grabFocus)", "CYAN")
                control.grabFocus()
                time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
            else:
                LOGGER_INFO(f"[navigator][locate] Control already focused", "GREEN")
            
            self._trigger_control_action(control)
            
            LOGGER_INFO(f"[navigator][locate] ✅ Direct access successful", "GREEN")
            return True, control
            
        except Exception as e:
            LOGGER_ERROR(f"[navigator][locate] Activation failed: {e}", "RED")
            return False, None
    
    def _trigger_control_action(self, control):
        """Trigger control action using click or doAction
        
        Args:
            control: Control to trigger
        """
        # Try click() first
        try:
            LOGGER_INFO(f"[navigator][locate] Clicking control directly", "CYAN")
            control.click()
            time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
            return
        except Exception:
            pass
        
        # Fallback to doAction('activate')
        try:
            LOGGER_INFO(f"[navigator][locate] Using doAction('activate')", "CYAN")
            control.doAction('activate')
            time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
            return
        except Exception:
            pass
        
        # Final fallback to doAction('press')
        try:
            LOGGER_INFO(f"[navigator][locate] Using doAction('press')", "CYAN")
            control.doAction('press')
            time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
        except Exception as e:
            LOGGER_WARNING(f"[navigator][locate] All activation methods failed: {e}", "YELLOW")
    
    def _tab_to_control(self, app, target_name, target_id='', control_type='', max_tabs=50):
        """
        Tab navigation fallback (Strategy 2)
        
        Approach:
        1. Try to find element by ID or name
        2. If found: Use direct methods (grabFocus/click)
        3. If not found or direct methods fail: Tab until element is focused
        
        Args:
            app: Application root
            target_name: Target control name
            target_id: Target control ID (checked first)
            control_type: Control type ('input' or '')
            max_tabs: Maximum Tab presses
            
        Returns:
            tuple: (success, control)
        """
        LOGGER_INFO(f"[navigator][tab] Searching for ID='{target_id}' or name='{target_name}'", "CYAN")
        
        # Find target element
        target_elem = self._find_control(app, target_id, target_name)
        
        # If found directly, use keyboard activation
        if target_elem:
            return self._activate_via_keyboard(target_elem, control_type, max_tabs, app)
        
        # Fallback: Event-based navigation if target not found in tree
        LOGGER_WARNING(f"[navigator][tab] Target not found in tree, trying event-based navigation...", "YELLOW")
        return self._try_event_based_navigation(target_name)
    
    def _activate_via_keyboard(self, target_elem, control_type, max_tabs, webex_app):
        """Activate control via keyboard (grabFocus + Return key)
        
        Args:
            target_elem: Target element to activate
            control_type: Control type ('input' or '')
            max_tabs: Maximum Tab attempts if focus fails
            webex_app: Application root (for navigation key determination)
            
        Returns:
            tuple: (success, control)
        """
        try:
            LOGGER_INFO(f"[navigator][tab] Element found, using keyboard activation", "CYAN")
            self._log_element_properties(target_elem)
            
            # Handle already-focused controls
            was_focused = self._handle_already_focused_control(target_elem)
            
            # Try to focus the control
            target_elem.grabFocus()
            time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
            
            # Verify focus
            is_focused = getattr(target_elem, 'focused', False)
            LOGGER_INFO(f"[navigator][tab]   Focused (after grabFocus): {is_focused}", "GREEN" if is_focused else "RED")
            
            # Fallback: Tab navigation if grabFocus failed
            if not is_focused:
                is_focused = self._focus_via_tab_navigation(target_elem, max_tabs, webex_app)
            
            if is_focused:
                control_role = getattr(target_elem, 'roleName', '')
                activation_key = self.get_activation_key(control_type_name='', control_role=control_role)
                LOGGER_INFO(f"[navigator][tab] Pressing {activation_key} key (role: {control_role})", "CYAN")
                self._send_key(activation_key)
                time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
            else:
                LOGGER_WARNING(f"[navigator][tab] Skipping activation - control not focused", "YELLOW")
            
            LOGGER_INFO(f"[navigator][tab] ✅ Successfully focused and activated via keyboard", "GREEN")
            return True, target_elem
            
        except Exception as e:
            LOGGER_WARNING(f"[navigator][tab] Keyboard activation failed: {e}, continuing with Tab", "YELLOW")
            return False, None
    
    def _log_element_properties(self, element):
        """Log element properties for debugging
        
        Args:
            element: Element to log
        """
        LOGGER_INFO(f"[navigator][tab] === Element Properties ===", "CYAN")
        LOGGER_INFO(f"[navigator][tab]   Name: {getattr(element, 'name', 'N/A')}", "CYAN")
        LOGGER_INFO(f"[navigator][tab]   Role: {getattr(element, 'roleName', 'N/A')}", "CYAN")
        LOGGER_INFO(f"[navigator][tab]   ID: {getattr(element, 'accessibleId', 'N/A')}", "CYAN")
        LOGGER_INFO(f"[navigator][tab]   Focused (before): {getattr(element, 'focused', 'N/A')}", "YELLOW")
        LOGGER_INFO(f"[navigator][tab]   States: {getattr(element, 'states', 'N/A')}", "CYAN")
        LOGGER_INFO(f"[navigator][tab]   Description: {getattr(element, 'description', 'N/A')}", "CYAN")
    
    def _handle_already_focused_control(self, element):
        """Handle controls that are already focused
        
        Workaround: Sometimes activation doesn't work even on focused items.
        If already focused, do backtab + tab to regain focus.
        
        Args:
            element: Element to check
            
        Returns:
            bool: Whether element was already focused
        """
        was_focused = getattr(element, 'focused', False)
        if was_focused:
            LOGGER_INFO(f"[navigator][tab] Control already focused, doing backtab+tab to regain...", "YELLOW")
            self._send_key("shift+Tab")  # Backtab
            time.sleep(NavigationConfig.REFOCUS_WAIT)
            self._send_key("Tab")  # Tab forward again
            time.sleep(NavigationConfig.REFOCUS_WAIT)
        return was_focused
    
    def _focus_via_tab_navigation(self, target_elem, max_tabs, webex_app):
        """Focus element using Tab key navigation
        
        Args:
            target_elem: Target element to focus
            max_tabs: Maximum Tab attempts
            webex_app: Application root (for navigation key determination)
            
        Returns:
            bool: Whether element was successfully focused
        """
        LOGGER_WARNING(f"[navigator][tab] grabFocus() failed, trying Tab navigation...", "YELLOW")
        
        # Check if we should use Right arrow instead of Tab
        # (when current focus and target are in the same container)
        nav_key = self._determine_navigation_key(target_elem, webex_app)
        
        for tab_count in range(max_tabs):
            self._send_key(nav_key)
            time.sleep(NavigationConfig.TAB_WAIT_TIME)
            
            try:
                if getattr(target_elem, 'focused', False):
                    key_name = "Right arrows" if nav_key == "Right" else "Tabs"
                    LOGGER_INFO(f"[navigator][tab] ✅ Focused after {tab_count+1} {key_name}", "GREEN")
                    return True
            except Exception as e:
                LOGGER_DEBUG(f"[navigator][tab] {nav_key} {tab_count}: {e}")
                continue
        
        if nav_key == "Right":
            LOGGER_WARNING(
                f"[navigator][tab] Failed to focus after {max_tabs} Right arrows, trying {max_tabs} Left arrows",
                "YELLOW"
            )
            for left_count in range(max_tabs):
                self._send_key("Left")
                time.sleep(NavigationConfig.TAB_WAIT_TIME)
                try:
                    if getattr(target_elem, 'focused', False):
                        LOGGER_INFO(f"[navigator][tab] ✅ Focused after {left_count+1} Left arrows", "GREEN")
                        return True
                except Exception as e:
                    LOGGER_DEBUG(f"[navigator][tab] Left {left_count}: {e}")
                    continue

        key_name = "Right arrows" if nav_key == "Right" else "Tabs"
        LOGGER_WARNING(f"[navigator][tab] Failed to focus after {max_tabs} {key_name}", "YELLOW")
        return False
    
    def _try_event_based_navigation(self, target_name):
        """Try event-based navigation for controls not in accessibility tree
        
        Args:
            target_name: Target control name
            
        Returns:
            tuple: (success, None) - None because we don't have element object
        """
        success = self._navigate_with_events(
            target_name=target_name,
            target_role='menu item',  # Common for menu items
            max_attempts=NavigationConfig.DEFAULT_MAX_EVENT_ATTEMPTS,
            use_right=False  # Use Down arrow for vertical menus
        )
        
        if success:
            LOGGER_INFO(f"[navigator][tab] ✅ Event-based navigation succeeded", "GREEN")
            return True, None
        else:
            LOGGER_WARNING(f"[navigator][tab] All strategies failed for '{target_name}'", "YELLOW")
            return False, None
        
        # Detect parent container type to choose navigation strategy
        parent_container_type = self._detect_parent_container(target_elem)
        use_arrow_nav = parent_container_type in ContainerTypes.GRID_LIKE
        
        if use_arrow_nav:
            LOGGER_INFO(f"[navigator][tab] Parent is '{parent_container_type}', using arrow navigation", "CYAN")
            return self._navigate_with_arrows(target_elem, control_type, max_tabs, "Right")
        else:
            # Try Tab navigation, fallback to Right arrow if Tab fails
            success, elem = self._navigate_with_tabs(target_elem, control_type, max_tabs)
            if success:
                return success, elem
            
            # Right arrow fallback
            LOGGER_WARNING(f"[navigator][tab] Tab navigation failed, trying Right arrow fallback...", "YELLOW")
            return self._navigate_with_arrows(target_elem, control_type, max_tabs, "Right")
    
    def _navigate_with_tabs(self, target_elem, control_type, max_tabs):
        """Navigate using Tab key
        
        Args:
            target_elem: Target element to focus
            control_type: Control type
            max_tabs: Maximum Tab attempts
            
        Returns:
            tuple: (success, control)
        """
        for i in range(max_tabs):
            self._send_key("Tab")
            time.sleep(NavigationConfig.TAB_WAIT_TIME)
            
            try:
                if getattr(target_elem, 'focused', False):
                    control_name = getattr(target_elem, 'name', '')
                    control_role = getattr(target_elem, 'roleName', '')
                    LOGGER_INFO(f"[navigator][tab] ✅ Focused after {i+1} tabs: {control_name}", "GREEN")
                    
                    activation_key = self.get_activation_key(control_type_name='', control_role=control_role)
                    LOGGER_INFO(f"[navigator][tab] Pressing {activation_key} key (role: {control_role})", "CYAN")
                    self._send_key(activation_key)
                    time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
                    
                    return True, target_elem
                else:
                    LOGGER_DEBUG(f"Tab {i}: Target not focused yet")
            except Exception as e:
                LOGGER_DEBUG(f"[navigator][tab] Error at Tab {i}: {e}")
                continue
        
        return False, None
    
    def _navigate_with_arrows(self, target_elem, control_type, max_attempts, arrow_key):
        """Navigate using arrow keys
        
        Args:
            target_elem: Target element to focus
            control_type: Control type
            max_attempts: Maximum arrow key attempts
            arrow_key: Arrow key to use ("Right", "Down", etc.)
            
        Returns:
            tuple: (success, control)
        """
        for i in range(max_attempts):
            self._send_key(arrow_key)
            time.sleep(NavigationConfig.TAB_WAIT_TIME)
            
            try:
                if getattr(target_elem, 'focused', False):
                    control_name = getattr(target_elem, 'name', '')
                    control_role = getattr(target_elem, 'roleName', '')
                    fallback_msg = " (fallback)" if arrow_key == "Right" else ""
                    LOGGER_INFO(f"[navigator][tab] ✅ Focused after {i+1} {arrow_key} arrows{fallback_msg}: {control_name}", "GREEN")
                    
                    activation_key = self.get_activation_key(control_type_name='', control_role=control_role)
                    LOGGER_INFO(f"[navigator][tab] Pressing {activation_key} key (role: {control_role})", "CYAN")
                    self._send_key(activation_key)
                    time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
                    
                    return True, target_elem
            except Exception as e:
                LOGGER_DEBUG(f"[navigator][tab] {arrow_key} arrow {i}: {e}")
                continue
        
        LOGGER_WARNING(f"[navigator][tab] Failed after {max_attempts} {arrow_key} arrows", "YELLOW")
        return False, None
    
    def _detect_parent_container(self, element):
        """Detect parent container type to determine navigation strategy
        
        Args:
            element: Target element to check
            
        Returns:
            str: Parent container type or empty string
        """
        try:
            if not element or not hasattr(element, 'parent'):
                return ''
            
            # Check parent role
            parent_role = self._get_element_role(element.parent)
            if not parent_role:
                return ''
            
            LOGGER_DEBUG(f"[navigator][parent] Parent role: {parent_role}", "CYAN")
            
            # Check for grid-like containers
            for grid_type in ContainerTypes.GRID_LIKE:
                if grid_type in parent_role:
                    return grid_type
            
            # Check grandparent if parent is generic container
            if parent_role in ContainerTypes.GENERIC:
                grandparent_role = self._get_grandparent_role(element)
                if grandparent_role:
                    LOGGER_DEBUG(f"[navigator][parent] Grandparent role: {grandparent_role}", "CYAN")
                    for grid_type in ContainerTypes.GRID_LIKE:
                        if grid_type in grandparent_role:
                            return grid_type
            
            return ''
            
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][parent] Error detecting parent: {e}", "YELLOW")
            return ''
    
    def _determine_navigation_key(self, target_elem, webex_app):
        """Determine which navigation key to use (Tab or Right arrow)
        
        Use Right arrow when:
        - Current focused item and target item are in the same panel/container
        
        Args:
            target_elem: Target element to navigate to
            webex_app: Application root (to find current focus)
            
        Returns:
            str: Navigation key to use ("Tab" or "Right")
        """
        try:
            # Get target's parent container
            target_parent = self._find_container_parent(target_elem)
            if not target_parent:
                LOGGER_DEBUG(f"[navigator][nav-key] No container parent for target, using Tab")
                return "Tab"
            
            LOGGER_INFO(f"[navigator][nav-key] === Target Parent Container ===" , "YELLOW")
            LOGGER_INFO(f"[navigator][nav-key]   Name: {target_parent.name}", "YELLOW")
            LOGGER_INFO(f"[navigator][nav-key]   Role: {target_parent.roleName}", "YELLOW")
            
            # Get currently focused element from tree
            current_focus_control = None
            focus_info = self.focus_listener.get_current_focus() if self.focus_listener else None
            
            if focus_info:
                focus_name = focus_info.get('name', '')
                LOGGER_INFO(f"[navigator][nav-key] === Current Focus (from listener) ===" , "YELLOW")
                LOGGER_INFO(f"[navigator][nav-key]   Name: {focus_name}", "YELLOW")
                LOGGER_INFO(f"[navigator][nav-key]   Role: {focus_info.get('role', 'N/A')}", "YELLOW")
                
                # Find the actual control in the tree that matches the listener info
                try:
                    # Try to find by name in the app tree
                    if focus_name:
                        current_focus_control = webex_app.child(name=focus_name, recursive=True)
                except Exception as e:
                    LOGGER_DEBUG(f"[navigator][nav-key] Could not find current focus in tree: {e}")
            
            if not current_focus_control:
                LOGGER_DEBUG(f"[navigator][nav-key] No current focus control found, using Tab")
                return "Tab"
            
            # Get current focus's parent container
            current_parent = self._find_container_parent(current_focus_control)
            if not current_parent:
                LOGGER_DEBUG(f"[navigator][nav-key] No container parent for current focus, using Tab")
                return "Tab"
            
            LOGGER_INFO(f"[navigator][nav-key] === Current Focus Parent Container ===" , "YELLOW")
            LOGGER_INFO(f"[navigator][nav-key]   Name: {current_parent.name}", "YELLOW")
            LOGGER_INFO(f"[navigator][nav-key]   Role: {current_parent.roleName}", "YELLOW")
            
            # Compare parents - if they're the same container, use Right arrow
            if current_parent == target_parent:
                LOGGER_INFO(f"[navigator][nav-key] ✅ Same parent container - using Right arrow", "CYAN")
                return "Right"
            else:
                LOGGER_INFO(f"[navigator][nav-key] ⚠️  Different parent containers - using Tab", "CYAN")
                return "Tab"
            
        except Exception as e:
            LOGGER_WARNING(f"[navigator][nav-key] Error determining navigation key: {e}")
            return "Tab"
    
    def _find_container_parent(self, control):
        """Find the parent container (panel, grid, etc.) of a control
        
        Args:
            control: The control to find parent for
            
        Returns:
            Parent container or None
        """
        CONTAINER_ROLES = ['panel', 'filler', 'scroll pane', 'table', 'tree table', 
                          'list', 'tree', 'grid', 'page tab list']
        
        try:
            # Check if control is valid
            if not control:
                return None
            
            # Verify control is still accessible (not destroyed)
            try:
                _ = control.name  # Quick property access to verify control is alive
            except Exception:
                LOGGER_DEBUG(f"[navigator][find-container] Control is destroyed/stale")
                return None
            
            current = control.parent if hasattr(control, 'parent') else None
            max_depth = 20  # Prevent infinite loops
            depth = 0
            
            while current and depth < max_depth:
                # Check if parent is still valid before accessing properties
                try:
                    _ = current.name  # Verify parent is still accessible
                    role = current.roleName.lower() if hasattr(current, 'roleName') else ''
                    if role in CONTAINER_ROLES:
                        return current
                    current = current.parent if hasattr(current, 'parent') else None
                    depth += 1
                except Exception:
                    # Parent is destroyed/stale, stop traversal
                    LOGGER_DEBUG(f"[navigator][find-container] Parent at depth {depth} is destroyed/stale")
                    return None
            
            return None
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][find-container] Error finding container parent: {e}")
            return None
    
    def _get_element_role(self, element):
        """Get element role name safely
        
        Args:
            element: Element to get role from
            
        Returns:
            str: Role name in lowercase or empty string
        """
        if not element or not hasattr(element, 'roleName'):
            return ''
        return element.roleName.lower()
    
    def _get_grandparent_role(self, element):
        """Get grandparent element role safely
        
        Args:
            element: Element to get grandparent role from
            
        Returns:
            str: Grandparent role name in lowercase or empty string
        """
        try:
            parent = element.parent
            if parent and hasattr(parent, 'parent'):
                grandparent = parent.parent
                return self._get_element_role(grandparent)
        except Exception:
            pass
        return ''
    
    def _send_key(self, key):
        """
        Send keyboard key using xdotool
        
        Args:
            key: Key to send (Tab, Return, Escape, Up, Down, Left, Right, etc.)
        """
        try:
            subprocess.run(['xdotool', 'key', key], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            LOGGER_DEBUG(f"[navigator][key] Error sending '{key}': {e}", "YELLOW")
        except FileNotFoundError:
            LOGGER_WARNING("[navigator][key] xdotool not found - install with: sudo apt-get install xdotool", "YELLOW")
    
    def _navigate_with_events(self, target_name, target_role=None, max_attempts=None, use_right=False):
        """Event-based navigation fallback (Strategy 3)
        
        When direct search by ID/name fails, use arrow keys with AT-SPI event monitoring.
        This is especially useful for Qt popup menus that are invisible to tree traversal.
        
        Approach:
        1. Start FocusListener to monitor AT-SPI focus events
        2. Press Down (or Right) arrows repeatedly
        3. Check focus events after each key press
        4. Stop when target item receives focus
        5. Press Return to activate (typically menu items)
        
        Args:
            target_name: Target control name (case-insensitive partial match)
            target_role: Target control role (optional, e.g., 'menu item')
            max_attempts: Maximum arrow key presses (default: DEFAULT_MAX_EVENT_ATTEMPTS)
            use_right: Use Right arrow instead of Down (for horizontal menus)
            
        Returns:
            bool: True if target found and activated, False otherwise
        """
        if max_attempts is None:
            max_attempts = NavigationConfig.DEFAULT_MAX_EVENT_ATTEMPTS
        
        arrow_key = "Right" if use_right else "Down"
        LOGGER_INFO(f"[navigator][events] Starting event-based navigation for '{target_name}'...", "CYAN")
        LOGGER_INFO(f"[navigator][events] Will press {arrow_key} up to {max_attempts} times", "CYAN")
        
        if not self.focus_listener:
            LOGGER_ERROR("[navigator][events] Focus listener not initialized - this shouldn't happen", "RED")
            return False
        
        try:
            time.sleep(NavigationConfig.EVENT_INIT_WAIT)
            
            # Navigate with arrow keys and monitor focus
            for i in range(max_attempts):
                self._send_key(arrow_key)
                time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
                
                if self._check_event_target_match(target_name, target_role, i):
                    self._activate_event_target()
                    return True
            
            LOGGER_WARNING(f"[navigator][events] Target '{target_name}' not found after {max_attempts} arrows", "YELLOW")
            return False
            
        finally:
            self._cleanup_focus_listener()
    
    def _check_event_target_match(self, target_name, target_role, attempt_num):
        """Check if current focused element matches target
        
        Args:
            target_name: Target control name
            target_role: Target control role (optional)
            attempt_num: Current attempt number
            
        Returns:
            bool: True if target matches
        """
        focus_info = self.focus_listener.get_current_focus() if self.focus_listener else None
        if not focus_info:
            return False
        name = focus_info.get('name', '').lower()
        role = focus_info.get('role', '').lower()
        
        LOGGER_DEBUG(f"[navigator][events] [{attempt_num+1}] {focus_info.get('role')}: '{focus_info.get('name')}'", "CYAN")
        
        # Check if target found (case-insensitive partial match)
        name_match = target_name.lower() in name
        role_match = True
        if target_role:
            role_match = target_role.lower() in role
        
        if name_match and role_match:
            LOGGER_INFO(f"[navigator][events] ✅ Found target after {attempt_num+1} arrows: '{focus_info.get('name')}'!", "GREEN")
            return True
        
        return False
    
    def _activate_event_target(self):
        """Activate the currently focused target via Return key
        
        Event-based navigation is typically used for menu items,
        so we use Return key which is standard for menu activation.
        """
        time.sleep(0.1)
        self._send_key("Return")
        time.sleep(NavigationConfig.FOCUS_WAIT_TIME)
        LOGGER_INFO(f"[navigator][events] ✅ Activated target with Return key", "GREEN")
    
    def _cleanup_focus_listener(self):
        """Cleanup focus listener safely"""
        # FocusListener is a shared singleton; do not stop it here.
        return
    
    def _build_control_metadata(self, control):
        """Build control metadata dictionary
        
        Args:
            control: Control object from dogtail
            
        Returns:
            dict: Control metadata
        """
        try:
            return {
                'name': self._get_control_attribute(control, 'name', ''),
                'role': self._get_control_attribute(control, 'roleName', ''),
                'description': self._get_control_attribute(control, 'description', ''),
                'states': str(self._get_control_attribute(control, 'states', '')),
                'position': self._get_control_position(control),
                'size': self._get_control_size(control),
                'platform': 'linux',
                'framework': 'dogtail/AT-SPI'
            }
        except Exception as e:
            LOGGER_DEBUG(f"[navigator][metadata] Error building: {str(e)}", "YELLOW")
            return self._get_default_metadata()
    
    def _get_control_attribute(self, control, attr_name, default=''):
        """Safely get control attribute
        
        Args:
            control: Control object
            attr_name: Attribute name
            default: Default value if attribute not found
            
        Returns:
            Attribute value or default
        """
        return getattr(control, attr_name, default)
    
    def _get_control_position(self, control):
        """Get control position safely
        
        Args:
            control: Control object
            
        Returns:
            tuple: (x, y) position or (0, 0)
        """
        if hasattr(control, 'position'):
            pos = control.position
            return (pos[0], pos[1])
        return (0, 0)
    
    def _get_control_size(self, control):
        """Get control size safely
        
        Args:
            control: Control object
            
        Returns:
            tuple: (width, height) or (0, 0)
        """
        if hasattr(control, 'size'):
            size = control.size
            return (size[0], size[1])
        return (0, 0)
    
    def _get_default_metadata(self):
        """Get default metadata for error cases
        
        Returns:
            dict: Minimal metadata
        """
        return {
            'name': '',
            'role': '',
            'platform': 'linux'
        }
    
    def get_keyboard_action(self, flag_control_type, current_control_name, current_control_id,
                           flag_parent_type, flag_accesskey=None, pre_control_class_name=None,
                           pre_control_parent_type=None):
        """
        Determine keyboard action based on control type
        
        Args:
            flag_control_type: Type of current control (control_type_name from dataset)
            current_control_name: Current control name
            current_control_id: Current control ID
            flag_parent_type: Parent control type
            flag_accesskey: Access key flag
            pre_control_class_name: Previous control class name
            pre_control_parent_type: Previous control parent type
            
        Returns:
            str: Keyboard action to perform ("space" or "Return")
        """
        # Default to Tab for most controls
        return "Tab"
    
    def get_activation_key(self, control_type_name='', control_role=''):
        """
        Determine which key to use for activation based on control type
        
        Args:
            control_type_name: Control type name from dataset (e.g., 'button', 'menu item')
            control_role: Control role from AT-SPI (e.g., 'menu item', 'push button')
            
        Returns:
            str: Key to press ("space" for most controls, "Return" for menu items)
        """
        # Check both control_type_name and control_role for menu items
        if control_type_name and 'menu item' in control_type_name.lower():
            return "Return"
        if control_role and 'menu item' in control_role.lower():
            return "Return"
        
        # Default to Space for all other controls (buttons, checkboxes, etc.)
        return "space"
    
    def set_control_validated_status(self, control_name, control_type, control_path_hash,
                                     control_id, control_class_name):
        """
        Set validation status for a control (Linux simplified)
        
        Args:
            control_name: Control name
            control_type: Control type
            control_path_hash: Control path hash
            control_id: Control ID
            control_class_name: Control class name
            
        Returns:
            int: Validation status (always 0 for Linux)
        """
        return 0

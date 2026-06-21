"""
Linux Control Explorer using dogtail

This module provides UI automation capabilities for Linux using the dogtail library,
which interfaces with AT-SPI (Assistive Technology Service Provider Interface).
"""

from dogtail.tree import root
from dogtail.config import config
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG
import time


class ControlExplorer:
    """
    Linux UI automation using dogtail and AT-SPI
    """
    
    def __init__(self):
        """Initialize the control explorer with dogtail configuration"""
        config.search_cut_off_limit = 30
        config.search_back_off_delay = 0.1
        config.action_delay = 0.5
        config.run_interval = 0.1
        config.default_delay = 0.5
        config.debug_searching = False
        
        LOGGER_INFO("Linux ControlExplorer initialized with dogtail")
    
    def control_explorer(self):
        """
        Explore controls in the current application
        
        This method explores the accessibility tree and returns control information
        similar to the Windows implementation.
        
        Returns:
            dict: Control information or None if exploration fails
        """
        try:
            LOGGER_INFO("Starting Linux control exploration using AT-SPI")
            
            # Get all accessible applications
            apps = root.applications()
            
            LOGGER_INFO(f"Found {len(apps)} accessible applications")
            
            # Look for Webex application
            # The application name is "Webex" and the executable is CiscoCollabHost
            webex_app = None
            for app in apps:
                app_name = app.name
                LOGGER_DEBUG(f"Found application: {app.name}")
                
                # Check for exact match "Webex" or partial matches
                if (app_name == 'Webex' or 
                    app_name.lower() == 'webex' or
                    'webex' in app_name.lower() or 
                    'ciscocollabhost' in app_name.lower() or
                    'cisco collab' in app_name.lower()):
                    webex_app = app
                    LOGGER_INFO(f"✅ Found Webex application: {app.name}")
                    break
            
            if not webex_app:
                LOGGER_ERROR("❌ Webex application not found in accessibility tree")
                LOGGER_INFO(f"Available applications: {[app.name for app in apps]}")
                return None
            
            # Explore the application's control tree
            controls = self._explore_tree(webex_app)
            
            LOGGER_INFO(f"Explored {len(controls)} controls in Webex application")
            
            return {
                'application': webex_app.name,
                'controls': controls,
                'platform': 'linux',
                'framework': 'dogtail/AT-SPI'
            }
            
        except Exception as e:
            LOGGER_ERROR(f"Control exploration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _explore_tree(self, node, depth=0, max_depth=10):
        """
        Recursively explore the accessibility tree
        
        Args:
            node: Current node in the tree
            depth: Current depth level
            max_depth: Maximum depth to explore
            
        Returns:
            list: List of control information dictionaries
        """
        controls = []
        
        if depth > max_depth:
            return controls
        
        try:
            # Get node information
            control_info = {
                'name': node.name if hasattr(node, 'name') else '',
                'role': node.roleName if hasattr(node, 'roleName') else '',
                'description': node.description if hasattr(node, 'description') else '',
                'states': str(node.states) if hasattr(node, 'states') else '',
                'depth': depth
            }
            
            # Add to list if it's a meaningful control
            if control_info['name'] or control_info['role']:
                controls.append(control_info)
                LOGGER_DEBUG(f"{'  ' * depth}[{control_info['role']}] {control_info['name']}")
            
            # Recursively explore children
            if hasattr(node, 'children'):
                for child in node.children:
                    controls.extend(self._explore_tree(child, depth + 1, max_depth))
                    
        except Exception as e:
            LOGGER_DEBUG(f"Error exploring node at depth {depth}: {str(e)}")
        
        return controls
    
    def find_control(self, name=None, role=None, description=None):
        """
        Find a control by its properties
        
        Args:
            name: Control name to search for
            role: Control role (button, text, etc.)
            description: Control description
            
        Returns:
            Control object or None if not found
        """
        try:
            # Search from root
            apps = root.applications()
            
            # Find Webex application
            for app in apps:
                app_name = app.name
                # Check for Webex application (exact match "Webex" or partial matches)
                if (app_name == 'Webex' or 
                    app_name.lower() == 'webex' or
                    'webex' in app_name.lower() or 
                    'ciscocollabhost' in app_name.lower() or
                    'cisco collab' in app_name.lower()):
                    
                    LOGGER_DEBUG(f"🔍 Searching in application: {app.name}")
                    
                    # Build search criteria
                    criteria = {}
                    if name:
                        criteria['name'] = name
                    if role:
                        criteria['roleName'] = role
                    if description:
                        criteria['description'] = description
                    
                    # Search in the application
                    try:
                        control = app.child(**criteria)
                        if control:
                            LOGGER_INFO(f"✅ Found control: {name or role}")
                            return control
                    except Exception as search_error:
                        LOGGER_DEBUG(f"Control not found in {app.name}: {str(search_error)}")
                        continue
            
            LOGGER_ERROR(f"❌ Control not found: name={name}, role={role}")
            LOGGER_DEBUG(f"Available applications: {[app.name for app in apps]}")
            return None
            
        except Exception as e:
            LOGGER_ERROR(f"Error finding control: {str(e)}")
            return None
    
    def click_control(self, control):
        """
        Click on a control
        
        Args:
            control: Control object to click
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if control:
                control.click()
                LOGGER_INFO(f"Clicked control: {control.name}")
                time.sleep(0.5)  # Wait for action to complete
                return True
            return False
        except Exception as e:
            LOGGER_ERROR(f"Error clicking control: {str(e)}")
            return False
    
    def type_text(self, control, text):
        """
        Type text into a control
        
        Args:
            control: Control object to type into
            text: Text to type
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if control:
                control.typeText(text)
                LOGGER_INFO(f"Typed text into control: {control.name}")
                return True
            return False
        except Exception as e:
            LOGGER_ERROR(f"Error typing text: {str(e)}")
            return False

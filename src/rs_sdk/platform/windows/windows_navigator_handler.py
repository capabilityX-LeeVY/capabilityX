import time
import uiautomation as auto
import comtypes.client

from comtypes.client import GetModule
GetModule('oleacc.dll')
GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient
from rs_sdk.factory.control_factory import ControlFactory
from rs_sdk.framework.abstract_navigator import BaseControlNavigate

class WindowsNavigateHandler(BaseControlNavigate):
    """Class to traverse application menu controls using SendKeys."""

    def __init__(self):
        """Initialize the class and set up initial state."""
        self.automation = comtypes.client.CreateObject(UIAutomationClient.CUIAutomation)
        self.control_factory = ControlFactory()
        self.current_focus = self.control_factory.create_control()
        self.traverse_controls = []
        self.skipcontrols = []

    def traverse_control(self):
        init_control = self.control_factory.create_control()
        init_control_name = init_control.ControlName
        self.traverse_controls.append(init_control_name)
        print(f"Focused Control: {init_control_name}, Type: {init_control.get_control_type_name()}, Type id: {init_control.ControlType}")

        while True:
            self.current_focus = self.control_factory.create_control()
            if self.current_focus.ControlType == 50000:            
                self.traverse_button()
            elif self.current_focus.ControlType == 50011:
                self.traverse_menu()
            elif self.current_focus.ControlType == 50019:
                self.traverse_button()

            self.current_focus = self.control_factory.create_control()
            control_changed_name = self.current_focus.ControlName
            if control_changed_name == init_control_name:
                break

            self.traverse_controls.append(control_changed_name)
            print(f"Focused Control: {control_changed_name}, Type: {self.current_focus.get_control_type_name()}, Type id: {self.current_focus.ControlType}")
        
        return self.traverse_controls
    
    def traverse_button(self):
        """Navigate to the button by name and click it."""
        auto.SendKeys("{Tab}")
        time.sleep(0.5)

    def traverse_tab(self):
        """Navigate to the tab by name and traverse its controls using arrow keys."""
        auto.SendKeys("{Right}")
        time.sleep(0.5)
        self.current_focus = self.control_factory.create_control()
        self.traverse_controls.append(self.current_focus.ControlName)
        while True:
            auto.SendKeys("{Down}")
            time.sleep(0.5)
            self.current_focus = self.control_factory.create_control()
            if self.current_focus.ControlType == 50000:
                break
            self.traverse_controls.append(self.current_focus.ControlName)

    def traverse_menu(self):
        """Navigate to the menu by name and traverse its submenu using arrow keys."""
        init_control = self.control_factory.create_control()
        init_control_name = init_control.ControlName
        visited_controls = []
        
        while True:
            pre_control = self.control_factory.create_control()
            pre_control_name = pre_control.ControlName
            auto.SendKeys("{Down}")
            self.current_focus = self.control_factory.create_control()
            post_control = self.control_factory.create_control()
            post_control_name = post_control.ControlName

            if pre_control_name != post_control_name:
                visited_controls.append(post_control_name)
                self.traverse_controls.append(post_control_name)
                self.traverse_submenu()

            self.current_focus = self.control_factory.create_control()
            visited_controls.append(self.current_focus.ControlName)

            print(f"Focused Control: {self.current_focus.ControlName}, visited_controls: [{visited_controls}]")
            if visited_controls.count(self.current_focus.ControlName) > 1:
                auto.SendKeys("{ESC}")
                break
            
            auto.SendKeys("{Right}")
            time.sleep(0.5)
            self.current_focus = self.control_factory.create_control()
            
            print(f"Focused Control: {self.current_focus.ControlName}, visited_controls: [{visited_controls}]")
            if visited_controls.count(self.current_focus.ControlName) > 1:
                auto.SendKeys("{ESC}")
                break

            if self.current_focus.ControlName == init_control_name:
                auto.SendKeys("{Tab}")
                break
            self.traverse_controls.append(self.current_focus.ControlName)
            
    def traverse_submenu(self):
        """Navigate to the submenu by name and traverse its controls using arrow keys."""
        visited_controls = [] 
        init_control = self.control_factory.create_control()
        init_control_name = init_control.ControlName

        while True:
            self.current_focus = self.control_factory.create_control()
            
            control_expand_collapse_state = self.current_focus.get_control_expand_collapse()

            if control_expand_collapse_state == 0:
                self.expand_control()
                self.traverse_submenu()

            auto.SendKeys("{Down}")
            time.sleep(0.5)
            self.current_focus = self.control_factory.create_control()
            visited_controls.append(self.current_focus.ControlName)

            self.traverse_controls.append(self.current_focus.ControlName)
            print(f"Focused Control: {self.current_focus.ControlName}, visited_controls: [{visited_controls}]")
            
            if self.current_focus.ControlName == init_control_name:
                auto.SendKeys("{ESC}")
                break
        
    def expand_control(self):
        """Expand the control."""
        auto.SendKeys("{Right}")


from abc import ABC, abstractmethod

class BaseControl(ABC):
    def __init__(self, element):
        self.element = element
    
    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def get_control_name(self):
        pass

    @abstractmethod
    def get_control_id(self):
        pass

    @abstractmethod
    def get_control_id_hash(self):
        pass

    @abstractmethod
    def get_control_type(self):
        pass

    @abstractmethod
    def get_control_type_name(self):
        pass

    @abstractmethod
    def get_control_help_text(self):
        pass

    @abstractmethod
    def get_fulldescription(self):
        pass

    @abstractmethod
    def get_control_ancestor_element(self):
        pass

    @abstractmethod
    def get_control_all_ancestor_elements(self):
        pass

    @abstractmethod
    def get_control_ancestor_levels_elements(self):
        pass

    @abstractmethod
    def get_control_previous_sibling(self):
        pass

    @abstractmethod
    def get_control_next_sibling(self):
        pass

    @abstractmethod
    def get_control_parent(self):
        pass

    @abstractmethod
    def get_control_process_id(self):
        pass

    @abstractmethod
    def get_control_runtime_id(self):
        pass

    @abstractmethod
    def get_control_accesskey(self):
        pass

    @abstractmethod
    def get_control_Level(self):
        pass

    @abstractmethod
    def get_control_from_name(self):
        pass

    @abstractmethod
    def get_control_toggle_state(self, control_name):
        pass

    # ── Property interface (mirrors WindowsControl) ─────────────────────────
    # Defined here so all subclasses (LinuxControl, MacControl, etc.) expose
    # a consistent attribute surface without needing platform-specific code.

    @property
    def ControlName(self):
        return self.get_control_name()

    @property
    def ControlID(self):
        return self.get_control_id()

    @property
    def ControlIDHash(self):
        return self.get_control_id_hash()

    @property
    def ControlType(self):
        return self.get_control_type()

    @property
    def ControlTypeName(self):
        return self.get_control_type_name()

    @property
    def ControlHelpText(self):
        return self.get_control_help_text()

    @property
    def ControlFullDescription(self):
        return self.get_fulldescription()

    @property
    def ControlToggleState(self):
        return self.get_control_toggle_state(None)

    @property
    def ControlAncestorElement(self):
        return self.get_control_ancestor_element()

    @property
    def ControlAllAncestorElements(self):
        return self.get_control_all_ancestor_elements()

    @property
    def ControlAncestorLevelsElements(self):
        return self.get_control_ancestor_levels_elements()

    @property
    def ControlPreviousSibling(self):
        return self.get_control_previous_sibling()

    @property
    def ControlNextSibling(self):
        return self.get_control_next_sibling()

    @property
    def ControlParent(self):
        return self.get_control_parent()

    @property
    def ControlProcessID(self):
        return self.get_control_process_id()

    @property
    def ControlRuntimeID(self):
        return self.get_control_runtime_id()

    @property
    def ControlAccessKey(self):
        return self.get_control_accesskey()

    # Properties without a corresponding abstract method — platform impls
    # override these; the base returns a safe default.

    @property
    def ControlBoundingRectangle(self):
        return None

    @property
    def ControlLegacyProperties(self):
        return None

    @property
    def ControlCollapseState(self):
        return None

    @property
    def ControlFirstAncestorWindow(self):
        return None

    @property
    def ControlExpandCollapse(self):
        return None

    @property
    def ControlClassName(self):
        return ""

    @property
    def ControlValue(self):
        return ""
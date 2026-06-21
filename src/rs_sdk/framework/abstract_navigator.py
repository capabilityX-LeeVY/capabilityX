from abc import ABC, abstractmethod

class BaseControlNavigate(ABC):
    def __init__(self, element):
        self.element = element

    @abstractmethod
    def traverse_button(self):
        pass

    @abstractmethod
    def traverse_tab(self):
        pass

    @abstractmethod
    def traverse_menu(self):
        pass

    @abstractmethod
    def traverse_submenu(self):
        pass


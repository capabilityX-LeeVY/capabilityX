# **DeepNaviSDK**  

`DeepNaviSDK` is a Python-based SDK designed to provide an extensible navigation framework for controlling and interacting with various platforms (Windows, Mac, Web, Mobile). It is built using the Factory Design Pattern for flexibility and scalability. The SDK allows developers to easily extend support for different platforms by implementing platform-specific navigation and control logic.

---

## **Features**
- **Control Factory**: Create various types of UI controls dynamically.  
- **Navigation Framework**: Abstract navigation methods for traversing Windows UI elements like menus, buttons, and tabs.  
- **Cross-Platform Structure**: Modular design with a factory pattern to support multiple platforms (currently focused on Windows).  
- **Extendable and Reusable**: Easily extend the base navigation and control classes for specific applications.  

---

## **Project Structure**
```plaintext
src/
  └── deepNaviSDK/
      ├── core/
      │    ├── abstract_control.py          # Abstract control class
      │    └── abstract_navigator.py        # Abstract navigator class
      ├── platform/
      │    └── windows/
      │         ├── windows_control.py      # Windows control implementation
      │         ├── windows_navigator.py    # Windows navigation implementation
      │         └── windows_navigator_handler.py  # Windows navigation handler
      ├── factory/
      │    ├── control_factory.py           # Factory for creating control instances
      │    └── navigator_factory.py         # Factory for creating navigator instances
      └── __init__.py                       # Package initialization file
  └── setup.py                               # Package setup file
```

---

## **Project Structure Overview**

### **1. Core**
The `core` module defines the fundamental abstraction layers for the SDK. It provides the base classes that can be extended to implement specific control and navigation functionalities for different platforms.

- **abstract_control.py**  
  Contains the abstract `Control` class, which defines the interface for control objects across platforms (e.g., Windows, Mac, Web, Mobile). This class ensures that every platform-specific control class implements the required methods like retrieving control names, types, and actions.

- **abstract_navigator.py**  
  Contains the abstract `Navigator` class, which serves as a base for navigation logic. This class defines the core navigation methods that must be implemented in each platform's specific navigator (e.g., navigating menus, handling buttons, and traversing UI elements).

---

### **2. Platform**
The `platform` module contains platform-specific implementations of controls and navigators. Each platform (e.g., Windows, Mac, Web, Mobile) has its own subdirectory for organizing platform-dependent logic.

- **windows_control.py**  
  Implements the control class for Windows. This class inherits from the abstract control class and provides Windows-specific logic for interacting with UI elements (e.g., buttons, menus, tabs).

- **windows_navigator.py**  
  Implements the navigator class for Windows. This class inherits from the abstract navigator class and defines how to traverse UI elements and perform navigation operations on the Windows platform.

- **windows_navigator_handler.py**  
  Acts as a handler that coordinates navigation tasks, calling appropriate functions from the `windows_navigator` class to execute control traversal logic.

> **Note:** Additional platforms like Mac, Web, and Mobile can be added similarly by creating their own control and navigator classes.

---

### **3. Factory**
The `factory` module provides factory classes that create instances of controls and navigators based on the specified platform. This design ensures loose coupling and makes the SDK easily extensible for new platforms.

- **control_factory.py**  
  Responsible for creating control instances. It abstracts the platform-specific logic and returns the appropriate control object based on the target platform.

- **navigator_factory.py**  
  Responsible for creating navigator instances. It provides an interface for generating platform-specific navigators to handle navigation tasks.


---

## **Installation**
1. Clone the repository:  
   ```
   git clone https://github.com/yourusername/deepNaviSDK.git
   ```  
2. Navigate to the project directory:  
   ```
   cd deepNaviSDK
   ```  
3. Install the package using `setup.py`:  
   ```
   python setup.py install
   ```

---

## **Usage Example**
```python
from deepNaviSDK.platform.windows.windows_navigator import WindowsNavigator
from deepNaviSDK.factory.control_factory import ControlFactory

navigator = WindowsNavigator()
factory = ControlFactory()

# Example: Traverse a menu and interact with a control
navigator.windowsnavigate()
```

---

## **Dependencies**
- `uiautomation >= 1.0`  
- `comtypes >= 1.1.10`  
- Python 3.6 or later  

---

## **Contributing**  
We welcome contributions! Please fork the repository and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## **License**  
This project is licensed under the MIT License. See the `LICENSE` file for details.  


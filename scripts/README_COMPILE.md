# WRS Cython Compilation Guide

This document describes how to use the Webex RegressShield (WRS) Cython compilation script to compile performance-critical Python modules.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Compilation Process](#compilation-process)
- [Compilation Output](#compilation-output)
- [Using Compiled Modules](#using-compiled-modules)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

## 🔍 Overview

The WRS Cython compilation script (`compile_wrs.py`) is an automated tool for compiling Python source code into high-performance Cython extension modules. The script creates an isolated build environment to ensure the compilation process doesn't affect the source code development environment.

### Key Features

- ✅ **Isolated Build Environment** - Compilation in separate directory without affecting source code
- ✅ **Automated Workflow** - One-click process from source copying to compilation verification
- ✅ **Progress Bar Display** - Real-time display of file copying and compilation progress
- ✅ **Type Hint Generation** - Automatically generates `.pyi` files for type information
- ✅ **Import Wrappers** - Creates backward-compatible import interfaces
- ✅ **Build Verification** - Automatically verifies compilation results
- ✅ **Smart Cleanup** - Automatically cleans build artifacts and temporary files

## 📦 Prerequisites

### System Requirements
- **Python 3.7+** - Python 3.10 recommended
- **Windows Operating System** - Current version optimized for Windows
- **Visual Studio Build Tools** - Required for C++ compilation

### Python Dependencies

```bash
# Core dependencies
pip install Cython>=0.29.0
pip install setuptools

# Project dependencies
pip install -r requirements.txt
```

### Directory Structure Requirements

Ensure the project has the following structure:
```
WebexRegressSheild/
├── scripts/
│   ├── compile_wrs.py          # Compilation script
│   └── compile_wrs.ps1         # PowerShell wrapper script
├── src/                        # Source code directory
│   ├── rs_sdk/utils/
│   ├── core/windows/
│   └── ...
├── setup.py                    # Cython build configuration
└── requirements.txt
```

## 🚀 Quick Start

**Add submodule** (for new repository setup):

```bash
git submodule add -b main git@sqbu-github.cisco.com:binbiwan/wrs-core.git src/core/windows/controls/source
```

### Method 1: Using PowerShell Script (Recommended)

```powershell
# Run from project root directory
.\scripts\compile_wrs.ps1
```

### Method 2: Direct Python Script Execution

```bash
# Run from project root directory
python scripts/compile_wrs.py
```

### Method 3: Run from Scripts Directory

```bash
cd scripts
python compile_wrs.py
```

## 🔧 Compilation Process

The compilation script executes the following 10 steps:

### Step 1: Prerequisites Check ✓
- Verify `setup.py` file exists
- Check if source files to be compiled exist
- Confirm Cython is installed

```python
# Auto-detected files to compile
compile_files = [
    "src/rs_sdk/utils/control.py",
    "src/rs_sdk/utils/event_listener.py", 
    "src/rs_sdk/platform/windows/windows_control.py",
    "src/core/windows/control_explorer.py",
    "src/core/windows/control_locator.py", 
    "src/core/windows/control_validator.py",
    "src/core/windows/control_validator_handler.py",
    "src/core/windows/control_navigator.py",
    "src/core/windows/control_navigator_handler.py"
]
```

### Step 2: Prepare Build Environment 🧹
- Clean existing build environment: `../WebexRegressSheild_build_env/`
- Create directory structure
- Handle file locking issues

### Step 3: Copy Source Code 📁
- Copy entire `src/` directory to build environment
- Copy `setup.py`, `requirements.txt` and other necessary files
- Display real-time progress bar:

```
📁 Copying: [████████████░░░░░░] 65.2% (1250/1920 files), ETA: 2.3s
```

### Step 4: Generate Type Hint Files 📝
- Generate `.pyi` files for each file to be compiled
- Automatically parse class and method signatures
- Provide intelligent type annotations

Example generated `.pyi` file:
```python
from typing import Dict, List, Tuple, Any, Optional, Union

class ControlNavigator:
    def __init__(self) -> None: ...
    
    def control_navigator(
        self,
        level: int = 1,
        from_control: Optional[str] = None,
        # ... more parameters
    ) -> TraversalResult: ...
```

### Step 5: Execute Cython Compilation 🔨
- Run `setup.py build_ext --inplace`
- Monitor compilation progress:

```
🔨 Compiling: [🔧🔧🔧🔧⚪⚪] 66.7% (6/9 files), ETA: 15.2s Processing control_navigator.py
```

### Step 6: Organize Compilation Artifacts 📦
- Find generated `.pyd` files
- Rename to standard format: `module_name.pyd`
- Move to correct directory structure

### Step 7: Create Import Wrappers 🔗
- Create Python wrapper files for each compiled module
- Maintain backward-compatible import interface
- Re-export compiled classes and functions

### Step 8: Clean Build Artifacts 🧹
- Delete temporary `.c` files
- Delete Cython annotation `.html` files
- Clean up `build/` directory

### Step 9: Clean Source Directory Artifacts 🔒
- Ensure source directory doesn't contain compilation artifacts
- Remove any `.pyd` files that might have been copied

### Step 10: Verify Build Results ✅
- Test importing compiled modules
- Verify accessibility of classes and methods
- Report verification results

## 📤 Compilation Output

After successful compilation, the following structure will be created:

```
../WebexRegressSheild_build_env/
├── src/
│   ├── rs_sdk/utils/
│   │   ├── control.pyd              # Compiled module
│   │   ├── control.pyi              # Type hint file
│   │   ├── control.py               # Import wrapper
│   │   ├── event_listener.pyd
│   │   ├── event_listener.pyi
│   │   └── event_listener.py
│   ├── core/windows/
│   │   ├── control_navigator.pyd
│   │   ├── control_navigator.pyi
│   │   ├── control_navigator.py
│   │   ├── control_navigator_handler.pyd
│   │   ├── control_navigator_handler.pyi
│   │   ├── control_navigator_handler.py
│   │   └── ... (other compiled modules)
│   └── ... (other source files, not compiled)
├── requirements.txt
├── requirements_mac.txt
└── setup.py
```

### File Type Description

| File Type | Description | Example |
|-----------|-------------|---------|
| `.pyd` | Compiled binary module | `control_navigator.pyd` |
| `.pyi` | Type hint file | `control_navigator.pyi` |
| `.py` | Import wrapper | `control_navigator.py` |

## 🎯 Using Compiled Modules

### Method 1: Set PYTHONPATH (Recommended)

```bash
# Windows PowerShell
$env:PYTHONPATH = "../WebexRegressSheild_build_env/src"
python your_script.py

# Windows CMD
set PYTHONPATH=..\WebexRegressSheild_build_env\src
python your_script.py

# Linux/macOS
export PYTHONPATH="../WebexRegressSheild_build_env/src"
python your_script.py
```

### Method 2: Run in Build Environment

```bash
cd ../WebexRegressSheild_build_env
python src/run_explorer.py
```

### Method 3: Dynamic Setting in Code

```python
import sys
from pathlib import Path

# Add build environment to Python path
build_env = Path(__file__).parent.parent / "WebexRegressSheild_build_env" / "src"
sys.path.insert(0, str(build_env))

# Now you can import compiled modules
from core.windows.control_navigator import ControlNavigator
```

### Verify Compiled Version

```python
import core.windows.control_navigator as cn
print(f"Module file: {cn.__file__}")
# Output should point to .pyd file path
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Compilation Failed: Visual Studio Not Found

**Error Message:**
```
error: Microsoft Visual C++ 14.0 is required
```

**Solution:**
```bash
# Download and install Visual Studio Build Tools
# Or install Visual Studio Community
# Make sure to select "C++ build tools" component
```

#### 2. Directory Access Denied

**Error Message:**
```
[WinError 32] The process cannot access the file because it is being used by another process
```

**Solution:**
- Close all Python processes using the build environment
- Restart PowerShell/Command Prompt
- If the problem persists, restart the system

#### 3. Missing .pyd Files

**Error Message:**
```
Warning: No .pyd file found for module_name
```

**Solution:**
- Check if Visual Studio Build Tools are properly installed
- Confirm Python and Cython version compatibility
- Review error messages in compilation output

#### 4. Import Failure

**Error Message:**
```
ImportError: DLL load failed while importing module
```

**Solution:**
- Confirm PYTHONPATH is set correctly
- Check Python version match (compilation environment vs runtime environment)
- Install missing dependency libraries

### Debug Mode

Enable verbose logging output:

```python
# Temporarily add to compile_wrs.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ⚙️ Technical Details

### Cython Compilation Configuration

Compilation uses the following configuration (defined in `setup.py`):

```python
setup(
    ext_modules=cythonize(
        compile_files,
        compiler_directives={
            "language_level": "3",    # Python 3 syntax
        },
        annotate=True                 # Generate performance analysis HTML
    ),
)
```

### Performance Optimization

Compiled modules typically achieve:
- **2-10x** execution speed improvement
- **Reduced memory usage**
- **Better startup time**

### Limitations and Considerations

1. **Platform Dependency** - `.pyd` files can only be used on the same platform
2. **Python Version Binding** - Compiled modules are bound to specific Python versions
3. **Debugging Difficulty** - Compiled code is difficult to debug
4. **Dynamic Feature Limitations** - Some Python dynamic features may not be available

### Build Environment Isolation

Benefits of completely isolated build environment:

- ✅ **Source Code Protection** - Original source code directory remains unchanged
- ✅ **Development Friendly** - Can develop and use compiled versions simultaneously
- ✅ **Version Management** - Easy to manage different versions of compilation artifacts
- ✅ **Simple Deployment** - Build environment can be directly used for production deployment

## 📚 Related Files

- `scripts/compile_wrs.py` - Main compilation script
- `scripts/compile_wrs.ps1` - PowerShell wrapper script  
- `setup.py` - Cython build configuration
- `requirements.txt` - Python dependency list

## 📞 Support

If you encounter issues, please:

1. Check the [Troubleshooting](#troubleshooting) section of this document
2. Review error messages in compilation output
3. Confirm all [Prerequisites](#prerequisites) are met
4. Contact the development team for support

---

**Last Updated:** July 7, 2025  
**Version:** 1.0  
**Maintainer:** WRS Development Team

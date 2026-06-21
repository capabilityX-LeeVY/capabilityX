#!/usr/bin/env python3
"""
Webex RegressShield (WRS) Compilation Script

This script compiles control_navigator.py using Cython in an isolated build environment.
The build environment can be used directly for running the compiled code.

Author: Auto-generated compilation script
Date: July 5, 2025
"""

import os
import sys
import shutil
import subprocess
import glob
import ast
import re
import time
from pathlib import Path
import yaml

class WRSCompiler_Mac:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent  # Go up one level from scripts/
        self.project_name = self.project_root.name  # Get project directory name
        
        # Source directories
        self.src_root = self.project_root / "src"
        
        # Files to compile (read from setup_mac.py)
        self.compile_files = self._get_compile_files_from_setup()
        
        # Build environment directories (same level as project)
        self.build_root = self.project_root.parent / f"{self.project_name}_build_env"
        self.build_src = self.build_root / "src"
        
        # Target deployment directory (webex-regress-shield at same level as project)
        self.target_deployment_dir = self.project_root.parent / "webex-regress-shield"
        
        # Files
        self.setup_file = self.project_root / "setup_mac.py"
        self.build_setup_file = self.build_root / "setup_mac.py"

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_prerequisites(self):
        """Check if all required files exist"""
        self.log("Checking prerequisites...")
        
        if not self.setup_file.exists():
            raise FileNotFoundError(f"setup_mac.py not found at {self.setup_file}")
        
        # Filter out files that shouldn't be compiled
        files_to_compile = []
        skipped_files = []
        
        for filename in self.compile_files:
            if self._should_skip_compilation(filename):
                skipped_files.append(filename)
                continue
                
            file_path = self.src_root / filename
            if not file_path.exists():
                raise FileNotFoundError(f"{filename} not found at {file_path}")
            
            files_to_compile.append(filename)
            self.log(f"Will compile: {filename}")
        
        # Update compile_files list to exclude skipped files
        self.compile_files = files_to_compile
        
        if skipped_files:
            self.log(f"Skipped {len(skipped_files)} files due to dependencies:", "INFO")
            for skipped in skipped_files:
                self.log(f"  - {skipped} (COM/system dependencies)", "INFO")
        
        try:
            import Cython
            self.log("Cython is available")
        except ImportError:
            raise ImportError("Cython is not installed. Please install it with: pip install Cython")
        
        self.log("Prerequisites check passed")
    
    def clean_build_environment(self):
        """Clean and prepare build environment"""
        self.log("Preparing isolated build environment...")
        
        # Try to remove existing build environment, but continue if it fails
        if self.build_root.exists():
            try:
                shutil.rmtree(self.build_root)
                self.log(f"Removed existing build environment: {self.build_root}")
            except (OSError, PermissionError) as e:
                self.log(f"Warning: Could not fully remove existing build environment: {e}", "WARNING")
                self.log("Attempting to clean individual files instead...")
                
                # Try to clean specific subdirectories instead
                try:
                    if self.build_src.exists():
                        shutil.rmtree(self.build_src, ignore_errors=True)
                    
                    # Remove specific build artifacts
                    for pattern in ["*.so", "build","*.c"]:
                        for item in self.build_root.glob(pattern):
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except:
                                pass
                except Exception as cleanup_error:
                    self.log(f"Warning: Partial cleanup failed: {cleanup_error}", "WARNING")
        
        # Create build directory structure
        self.build_root.mkdir(parents=True, exist_ok=True)
        self.build_src.mkdir(parents=True, exist_ok=True)

        # 自动创建所有包结构目录
        for filename in self.compile_files:
            pkg_dir = self.build_src / Path(filename).parent
            pkg_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"Build environment ready: {self.build_root}")
    
    def copy_source_to_build_env(self):
        """Copy source code to isolated build environment with progress bar"""
        self.log("Copying source code to build environment...")
        
        # Remove existing build_src if exists
        if self.build_src.exists():
            shutil.rmtree(self.build_src)
        
        # Count total files for progress tracking
        total_files = sum(1 for _ in self.src_root.rglob('*') if _.is_file())
        self.log(f"Found {total_files} files to copy...")
        
        # Copy with progress tracking
        self._copy_tree_with_progress(self.src_root, self.build_src, total_files)
        self.log(f"✅ Completed copying {self.src_root} to {self.build_src}")
        
        # Copy setup_mac.py to build environment and create filtered version
        shutil.copy2(self.setup_file, self.build_root / "setup_original.py")
        self.log(f"Copied original setup_mac.py as backup")
        
        # Create filtered setup_mac.py for compilation
        self.create_filtered_setup_py()
        
        # Copy other necessary files
        additional_files = [
            "requirements.txt", 
            "requirements_mac.txt", 
            "README.md",
            ".gitignore",
            ".env",
            ".python-version",
            "uv.lock",
            "pyproject.toml"
            ]
        for file_name in additional_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                dst_file = self.build_root / file_name
                shutil.copy2(src_file, dst_file)
                self.log(f"Copied {src_file} to {dst_file}")
    
    def _copy_tree_with_progress(self, src, dst, total_files):
        """Copy directory tree with progress bar"""
        import time
        
        # Create destination directory
        dst.mkdir(parents=True, exist_ok=True)
        
        copied_files = 0
        start_time = time.time()
        last_progress_time = start_time
        
        def copy_file_with_progress(src_file, dst_file):
            nonlocal copied_files, last_progress_time
            
            # Ensure destination directory exists
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(src_file, dst_file)
            copied_files += 1
            
            # Update progress every 0.5 seconds or every 100 files
            current_time = time.time()
            if (current_time - last_progress_time >= 0.5) or (copied_files % 100 == 0) or (copied_files == total_files):
                progress = (copied_files / total_files) * 100
                elapsed = current_time - start_time
                if copied_files > 0:
                    estimated_total = (elapsed / copied_files) * total_files
                    eta = estimated_total - elapsed
                    eta_str = f", ETA: {eta:.1f}s" if eta > 0 else ""
                else:
                    eta_str = ""
                
                # Create progress bar
                bar_length = 30
                filled_length = int(bar_length * copied_files // total_files)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                print(f"\rCopying: [{bar}] {progress:.1f}% ({copied_files}/{total_files} files){eta_str}", end='', flush=True)
                last_progress_time = current_time
        
        # Copy all files recursively
        for src_file in self.src_root.rglob('*'):
            if src_file.is_file():
                # Calculate relative path
                rel_path = src_file.relative_to(self.src_root)
                dst_file = dst / rel_path
                
                copy_file_with_progress(src_file, dst_file)
        
        # Complete the progress bar
        print()  # New line after progress bar
    
    def generate_pyi_files_in_build_env(self):
        """Generate .pyi files for all target files in build environment"""
        self.log("Generating .pyi files in build environment...")
        
        pyi_files = []
        for filename in self.compile_files:
            build_py_file = self.build_src / filename
            build_pyi_file = self.build_src / filename.replace('.py', '.pyi')
            
            # Read the source file in build environment
            with open(build_py_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Generate .pyi content
            pyi_content = self._generate_pyi_content(original_content, filename)
            
            # Write .pyi file in build environment
            with open(build_pyi_file, 'w', encoding='utf-8') as f:
                f.write(pyi_content)
            
            self.log(f"Generated {build_pyi_file}")
            pyi_files.append(build_pyi_file)
        
        return pyi_files
    
    def _generate_pyi_content(self, original_content, filename):
        """Generate .pyi content from original Python file"""
        import ast
        
        # Get base name without extension for class detection
        base_name = filename.replace('.py', '')
        
        try:
            # Parse the original file to extract class and method signatures
            tree = ast.parse(original_content)
            
            pyi_lines = []
            pyi_lines.append('"""')
            pyi_lines.append(f'Type stub file for {filename}')
            pyi_lines.append('')
            pyi_lines.append(f'This file provides type hints and interface definitions for classes in {filename}.')
            pyi_lines.append('Generated in WRS build environment.')
            pyi_lines.append('"""')
            pyi_lines.append('')
            
            # Add imports
            pyi_lines.append('from typing import Dict, List, Tuple, Any, Optional, Union')
            if 'control_navigator.py' in filename:
                pyi_lines.append('import uiautomation as auto')
            pyi_lines.append('')
            
            # Add type aliases (for control_navigator)
            if 'control_navigator.py' in filename:
                pyi_lines.append('# Type aliases')
                pyi_lines.append('ControlMetadataDict = Dict[str, Any]')
                pyi_lines.append('TraversalResult = Tuple[List[str], List[str], bool, List[ControlMetadataDict]]')
                pyi_lines.append('ValidationStatus = int')
                pyi_lines.append('ControlType = int')
                pyi_lines.append('ControlLevel = int')
                pyi_lines.append('')
            
            # Extract class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pyi_lines.append(f'class {node.name}:')
                    pyi_lines.append('    """')
                    
                    # Add specific docstrings based on class
                    if node.name == 'ControlNavigator':
                        pyi_lines.append('    Main class for navigating and traversing UI controls in automated testing.')
                    elif node.name == 'ControlNavigatorHandler':
                        pyi_lines.append('    Handler class for control navigation operations and traversal logic.')
                    else:
                        pyi_lines.append(f'    {node.name} class for WRS automation.')
                    
                    pyi_lines.append('    """')
                    pyi_lines.append('')
                    
                    # Extract class variables and attributes
                    class_attributes = self._extract_class_attributes(node)
                    for attr in class_attributes:
                        pyi_lines.append(f'    {attr}')
                        pyi_lines.append('')
                    
                    # Add __init__ method
                    init_method = self._find_init_method(node)
                    if init_method:
                        init_signature = self._extract_method_signature(init_method)
                        pyi_lines.append(f'    {init_signature}')
                    else:
                        pyi_lines.append('    def __init__(self) -> None: ...')
                    pyi_lines.append('')
                    
                    # Extract all methods (excluding __init__ since we handled it above)
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name != '__init__':
                            method_signature = self._extract_method_signature(item)
                            pyi_lines.append(f'    {method_signature}')
                            pyi_lines.append('')
            
            return '\n'.join(pyi_lines)
            
        except Exception as e:
            self.log(f"Error generating .pyi content for {filename}: {e}", "WARNING")
            # Fallback to basic .pyi content
            return self._generate_basic_pyi_content(filename)
    
    def _extract_method_signature(self, func_node):
        """Extract method signature from AST function node"""
        args = []
        
        # Handle function arguments
        for i, arg in enumerate(func_node.args.args):
            arg_name = arg.arg
            
            # Try to infer type from defaults or use Any
            arg_type = 'Any'
            
            # Handle type annotations if present
            if hasattr(arg, 'annotation') and arg.annotation:
                arg_type = self._extract_type_annotation(arg.annotation)
            
            # Build argument string
            arg_str = f'{arg_name}: {arg_type}'
            args.append(arg_str)
        
        # Handle defaults
        defaults = func_node.args.defaults
        if defaults:
            # Apply defaults to last N arguments
            num_defaults = len(defaults)
            for i in range(num_defaults):
                arg_index = len(args) - num_defaults + i
                if arg_index >= 0 and arg_index < len(args):
                    args[arg_index] = f'{args[arg_index]} = ...'
        
        args_str = ', '.join(args)
        
        # Handle return type annotation
        return_type = 'Any'
        if func_node.returns:
            return_type = self._extract_type_annotation(func_node.returns)
        else:
            # Special handling for known methods
            if func_node.name == 'control_navigator':
                return_type = 'TraversalResult'
            elif func_node.name == 'set_control_validated_status':
                return_type = 'ValidationStatus'
            elif func_node.name == 'handle_control_traversal':
                return_type = 'Union[str, ControlMetadataDict]'
            elif func_node.name == '__init__':
                return_type = 'None'
        
        return f'def {func_node.name}({args_str}) -> {return_type}: ...'
    
    def _generate_basic_pyi_content(self, filename):
        """Generate basic .pyi content as fallback"""
        if 'control_navigator.py' in filename:
            return '''"""
Type stub file for control_navigator.py

This file provides type hints and interface definitions for the ControlNavigator class.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union

# Type aliases
ControlMetadataDict = Dict[str, Any]
TraversalResult = Tuple[List[str], List[str], bool, List[ControlMetadataDict]]
ValidationStatus = int
ControlType = int

class ControlNavigator:
    """Main class for navigating and traversing UI controls in automated testing."""
    
    def __init__(self) -> None: ...
    
    def control_navigator(
        self,
        level: int = 1,
        from_control: Optional[str] = None,
        process_id: int = 0,
        is_validated: int = 0,
        is_recorded: bool = True,
        is_located: bool = False,
        locate_control_meta: Optional[Dict[str, Any]] = None,
        close_flag: bool = False,
        locate_id_flag: bool = False
    ) -> TraversalResult: ...
    
    def handle_control_traversal(
        self,
        flag_control_type: int,
        current_control_name: str,
        current_control_id: str,
        flag_parent_type: int,
        init_control_name: str,
        init_control_id_hash: str,
        is_located: bool,
        from_control: str,
        visited_controls: List[str],
        tree_visited: List[str],
        tab_visited: List[str],
        radio_visited: List[str],
        text_visited: List[str],
        combox_visited: List[str],
        button_list_visited: List[str],
        custom_visited: List[str],
        list_visited: List[str]
    ) -> Union[str, ControlMetadataDict]: ...
    
    def set_control_validated_status(
        self,
        control_name: str,
        control_type: int,
        control_path_hash: str,
        control_id: str,
        control_class_name: Optional[str]
    ) -> int: ...
'''
        elif 'control_navigator_handler.py' in filename:
            return '''"""
Type stub file for control_navigator_handler.py

This file provides type hints and interface definitions for the ControlNavigatorHandler class.
Generated in WRS build environment.
"""

from typing import Any, Optional, List

class ControlNavigatorHandler:
    """Handler class for control navigation operations and traversal logic."""
    
    def __init__(self) -> None: ...
    
    def control_navigator_hander(self) -> None: ...
    
    def traverse_control(self, direction: str) -> None: ...
    
    def traverse_button(self) -> None: ...
    
    def traverse_menu(self) -> None: ...
    
    def traverse_tree(
        self,
        direction: str,
        pre_control_name: str,
        init_control_name: str,
        flag_tree: str,
        tree_visited: List[str]
    ) -> bool: ...
    
    def traverse_tab(
        self,
        direction: str,
        pre_control_name: str,
        init_control_name: str,
        from_control: str,
        flag_tab: str,
        tab_visited: List[str],
        is_located: bool
    ) -> bool: ...
    
    def traverse_combo_box(
        self,
        direction: str,
        combox_visited: List[str],
        flag_custom: Optional[str] = None
    ) -> bool: ...
    
    def traverse_list(
        self,
        direction: str,
        list_visited: List[str]
    ) -> bool: ...
    
    def traverse_radio(self, radio_visited: List[str]) -> None: ...
    
    def traverse_text(self, text_visited: List[str]) -> List[str]: ...
    
    def traverse_group(self) -> None: ...
    
    def traverse_widgets(self) -> None: ...
    
    def traverse_windows(self) -> None: ...
    
    def traverse_empty_control(self) -> None: ...
    
    def traverse_button_accesskey(
        self,
        direction: str,
        custom_visited: List[str],
        is_located: bool = False
    ) -> bool: ...
    
    def traverse_custom(
        self,
        direction: str,
        custom_visited: List[str]
    ) -> bool: ...
'''
        else:
            return f'''"""
Type stub file for {filename}

Generated in WRS build environment.
"""

from typing import Any

# Basic stub for {filename}
'''
    
    def _get_compile_files_from_setup(self):
        """Read compile files list from setup_mac.py"""
        try:
            setup_content = (self.project_root / "setup_mac.py").read_text()
            
            # Extract compile_files list from setup_mac.py
            # This is a simple parser - could be made more robust
            import ast
            tree = ast.parse(setup_content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'compile_files':
                            if isinstance(node.value, ast.List):
                                files = []
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        # Remove 'src/' prefix and keep only relative path from src
                                        file_path = elt.value
                                        if file_path.startswith('src/'):
                                            file_path = file_path[4:]  # Remove 'src/'
                                        files.append(file_path)
                                self.log(f"Found {len(files)} files to compile from setup_mac.py")
                                return files
            
            # Fallback to default if parsing fails
            self.log("Could not parse setup_mac.py, using default files", "WARNING")
            return ["core/windows/control_navigator.py", "core/windows/control_navigator_handler.py"]
            
        except Exception as e:
            self.log(f"Error reading setup_mac.py: {e}", "WARNING")
            return ["core/windows/control_navigator.py", "core/windows/control_navigator_handler.py"]
    
    def _should_skip_compilation(self, filename):
        """Determine if a file should be skipped during compilation"""
        # Skip files with COM dependencies
        if self._requires_com_dependencies(filename):
            self.log(f"Skipping compilation for {filename} due to COM dependencies", "INFO")
            return True
        return False
    
    def _requires_com_dependencies(self, filename):
        """Check if a file requires COM dependencies that shouldn't be compiled"""
        com_indicators = [
            'GetModule(',
            'comtypes.gen',
            'UIAutomationClient',
            'CreateObject(',
            'pythoncom',
            'from comtypes'
        ]
        
        try:
            file_path = self.src_root / filename
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                return any(indicator in content for indicator in com_indicators)
        except Exception as e:
            self.log(f"Error checking COM dependencies for {filename}: {e}", "WARNING")
        
        return False
    
    def create_filtered_setup_py(self):
        """Create a setup_mac.py in build environment with filtered compile files"""
        self.log("Creating filtered setup_mac.py for build environment...")
        
        # Create setup_mac.py content with only compilable files
        setup_content = f'''from setuptools import setup
from Cython.Build import cythonize

# Files to compile (filtered to exclude COM dependencies)
compile_files = {repr([f"src/{f}" for f in self.compile_files])}

setup(
    ext_modules=cythonize(
        compile_files,
        compiler_directives={{"language_level": "3"}},
        annotate=True
    ),
)
'''
        
        # Write filtered setup_mac.py
        with open(self.build_setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        
        self.log(f"Created filtered setup_mac.py with {len(self.compile_files)} files to compile")
    
    def handle_skipped_files(self):
        """Handle files that were skipped from compilation"""
        self.log("Handling skipped files...")
        
        # Get original compile list from setup_mac.py
        original_files = self._get_compile_files_from_setup()
        skipped_files = [f for f in original_files if f not in self.compile_files]
        
        if skipped_files:
            self.log(f"Ensuring {len(skipped_files)} skipped files remain as Python source:")
            for filename in skipped_files:
                # These files are already copied as .py files, just log them
                build_py_file = self.build_src / filename
                if build_py_file.exists():
                    self.log(f"  ✓ {filename} - kept as Python source (COM dependencies)")
                else:
                    self.log(f"  ⚠ {filename} - file not found in build environment", "WARNING")
        else:
            self.log("No files were skipped from compilation")
    
    def clean_source_artifacts(self):
        """Clean up any .so files that may have been copied to source directory"""
        self.log("Cleaning source directory artifacts...")
        
        # Remove .so files from source directory
        for filename in self.compile_files:
            file_path_obj = Path(filename)
            base_name = file_path_obj.stem
            
            # Look for .so files in the source directory
            source_dir = self.src_root / file_path_obj.parent
            pyd_patterns = [
                source_dir / f"{base_name}.so",
                source_dir / f"{base_name}.cp*.so"
            ]
            
            for pattern in pyd_patterns:
                if isinstance(pattern, Path) and pattern.exists():
                    os.remove(pattern)
                    self.log(f"Removed source artifact: {pattern}")
                else:
                    # Handle glob pattern for .cp*.so files
                    glob_pattern = str(pattern)
                    if '*' in glob_pattern:
                        matching_files = glob.glob(glob_pattern)
                        for file_path in matching_files:
                            os.remove(file_path)
                            self.log(f"Removed source artifact: {file_path}")
    
    def verify_build(self):
        """Verify that the build was successful"""
        self.log("Verifying build...")
        
        try:
            # Try to import the modules from build environment
            import sys
            original_path = sys.path.copy()
            sys.path.insert(0, str(self.build_src))
            
            verification_results = []
            
            try:
                # Test each compiled module
                for filename in self.compile_files:
                    module_path = filename.replace('.py', '').replace('/', '.')
                    try:
                        # Import the module
                        exec(f"import {module_path}")
                        
                        # Try to find and import classes (but don't instantiate them)
                        original_file = self.src_root / filename
                        if original_file.exists():
                            content = original_file.read_text()
                            import re
                            class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                            
                            for class_name in class_matches:
                                try:
                                    # Only import and check if class exists, don't instantiate
                                    exec(f"from {module_path} import {class_name}")
                                    exec(f"assert hasattr({class_name}, '__init__'), 'Class has __init__ method'")
                                    verification_results.append(f"✓ {class_name} class imported from {filename}")
                                except Exception as e:
                                    verification_results.append(f"⚠ {class_name} import failed from {filename}: {e}")
                        else:
                            verification_results.append(f"✓ {module_path} module imported successfully")
                            
                    except Exception as e:
                        verification_results.append(f"✗ {filename} import failed: {e}")
                
            finally:
                # Restore original sys.path
                sys.path = original_path
            
            # Log results
            for result in verification_results:
                if result.startswith("✓"):
                    self.log(result)
                else:
                    self.log(result, "WARNING")
            
            self.log("Build verification completed")
            return True
            
        except Exception as e:
            self.log(f"Build verification failed: {e}", "ERROR")
            return False
    
    def _extract_class_attributes(self, class_node):
        """Extract class attributes and variables from AST class node"""
        attributes = []
        
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                # Handle class variables like: PREVALIDATEDCONTROLS = []
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        # Try to infer type from the value
                        attr_type = self._infer_type_from_value(item.value)
                        attributes.append(f"{attr_name}: {attr_type}")
            
            elif isinstance(item, ast.AnnAssign):
                # Handle annotated assignments like: handler: SomeType = None
                if isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    if item.annotation:
                        # Extract type annotation
                        attr_type = self._extract_type_annotation(item.annotation)
                    else:
                        attr_type = "Any"
                    attributes.append(f"{attr_name}: {attr_type}")
        
        # Also check for attributes assigned in __init__ method
        init_method = self._find_init_method(class_node)
        if init_method:
            init_attributes = self._extract_init_attributes(init_method)
            attributes.extend(init_attributes)
        
        return attributes
    
    def _find_init_method(self, class_node):
        """Find the __init__ method in a class node"""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                return item
        return None
    
    def _extract_init_attributes(self, init_node):
        """Extract instance attributes from __init__ method"""
        attributes = []
        
        for item in ast.walk(init_node):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if (isinstance(target, ast.Attribute) and 
                        isinstance(target.value, ast.Name) and 
                        target.value.id == 'self'):
                        
                        attr_name = target.attr
                        # Skip if already found (avoid duplicates)
                        if not any(attr.startswith(f"{attr_name}:") for attr in attributes):
                            attr_type = self._infer_type_from_value(item.value)
                            attributes.append(f"{attr_name}: {attr_type}")
        
        return attributes
    
    def _infer_type_from_value(self, value_node):
        """Infer type from AST value node"""
        if isinstance(value_node, ast.Constant):
            if isinstance(value_node.value, str):
                return "str"
            elif isinstance(value_node.value, int):
                return "int"
            elif isinstance(value_node.value, float):
                return "float"
            elif isinstance(value_node.value, bool):
                return "bool"
            elif value_node.value is None:
                return "Optional[Any]"
        elif isinstance(value_node, ast.List):
            return "List[Any]"
        elif isinstance(value_node, ast.Dict):
            return "Dict[str, Any]"
        elif isinstance(value_node, ast.Set):
            return "Set[Any]"
        elif isinstance(value_node, ast.Tuple):
            return "Tuple[Any, ...]"
        elif isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                func_name = value_node.func.id
                if func_name in ['list', 'List']:
                    return "List[Any]"
                elif func_name in ['dict', 'Dict']:
                    return "Dict[str, Any]"
                elif func_name in ['set', 'Set']:
                    return "Set[Any]"
                elif func_name in ['tuple', 'Tuple']:
                    return "Tuple[Any, ...]"
        
        return "Any"
    
    def _extract_type_annotation(self, annotation_node):
        """Extract type annotation from AST annotation node"""
        if isinstance(annotation_node, ast.Name):
            return annotation_node.id
        elif isinstance(annotation_node, ast.Attribute):
            # Handle things like typing.Optional
            return self._get_full_attribute_name(annotation_node)
        elif isinstance(annotation_node, ast.Subscript):
            # Handle things like List[str], Optional[int]
            if isinstance(annotation_node.value, ast.Name):
                base_type = annotation_node.value.id
                # Try to extract the slice (generic parameter)
                return f"{base_type}[Any]"  # Simplified for now
            elif isinstance(annotation_node.value, ast.Attribute):
                base_type = self._get_full_attribute_name(annotation_node.value)
                return f"{base_type}[Any]"
        
        return "Any"
    
    def _get_full_attribute_name(self, attr_node):
        """Get full attribute name like 'typing.Optional'"""
        if isinstance(attr_node, ast.Name):
            return attr_node.id
        elif isinstance(attr_node, ast.Attribute):
            base = self._get_full_attribute_name(attr_node.value)
            return f"{base}.{attr_node.attr}"
        return "Any"

    def run_setup_in_build_env(self):
        """Run setup_mac.py to compile in build environment with progress bar"""
        self.log("Running setup_mac.py in build environment...")
        
        try:
            # Change to build directory
            original_cwd = os.getcwd()
            os.chdir(self.build_root)
            
            # Run setup_mac.py build_ext --inplace with real-time output
            process = subprocess.Popen([
                sys.executable, "setup_mac.py", 
                "build_ext",
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
               text=True, bufsize=1, universal_newlines=True)
            
            # Monitor compilation progress
            self._monitor_setup_progress(process)
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                self.log("Setup.py executed successfully in build environment")
            else:
                raise subprocess.CalledProcessError(return_code, "setup_mac.py")
                
        except subprocess.CalledProcessError as e:
            self.log(f"Setup.py failed: {e}", "ERROR")
            raise
        finally:
            os.chdir(original_cwd)
    
    def _monitor_setup_progress(self, process):
        """Monitor setup_mac.py compilation progress with simple file completion progress bar"""
        import time
        import re
        
        total_files = len(self.compile_files)
        compiled_files = 0
        start_time = time.time()
        
        # Patterns to detect file compilation completion
        compiling_patterns = [
            re.compile(r'Compiling (.+\.py)'),
            re.compile(r'building (.+) extension'),
            re.compile(r'creating (.+\.so)'),
            re.compile(r'gcc.*\.c')
        ]
        
        def update_progress(current, total, message=""):
            progress = (current / total) * 100 if total > 0 else 0
            elapsed = time.time() - start_time
            
            if current > 0:
                estimated_total = (elapsed / current) * total
                eta = estimated_total - elapsed
                eta_str = f", ETA: {eta:.1f}s" if eta > 0 else ""
            else:
                eta_str = ""
            
            # Create progress bar
            bar_length = 30
            filled_length = int(bar_length * current // total) if total > 0 else 0
            bar = 'X' * filled_length + '.' * (bar_length - filled_length)
            
            print(f"\rCompiling: [{bar}] {progress:.1f}% ({current}/{total} files){eta_str} {message}", 
                  end='', flush=True)
        
        # Initial progress display
        update_progress(0, total_files, "Starting compilation...")
        
        # Read output line by line
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line:
                break
                
            line = line.strip()
            output_lines.append(line)
            
            # Check for compilation progress
            for pattern in compiling_patterns:
                if pattern.search(line):
                    compiled_files = min(compiled_files + 1, total_files)
                    # Extract filename if possible
                    filename = ""
                    if "Compiling" in line:
                        try:
                            filename = line.split("Compiling")[1].split()[0].split("/")[-1]
                        except:
                            pass
                    elif "building" in line and "extension" in line:
                        try:
                            filename = line.split("'")[1].split("'")[0]
                        except:
                            pass
                    
                    update_progress(compiled_files, total_files, f"Processing {filename}")
                    break
        
        # Complete the progress bar
        update_progress(total_files, total_files, "Compilation completed!")
        print()  # New line after progress bar
        
        # Log any errors or warnings
        if any('error' in line.lower() or 'warning' in line.lower() for line in output_lines):
            full_output = '\n'.join(output_lines)
            self.log(f"Compilation output: {full_output}")
        else:
            self.log("✅ All files compiled successfully")
    
    def codeSign(self,organized_files):
        """Code sign the compiled .so files in build environment"""
        
        self.log("Code signing compiled .so files...")
        # Code sign each .so file
        for pyd_file in organized_files:
            try:
                subprocess.run([
                    "codesign", "--force", "--sign", "-", pyd_file
                ], check=True)
                self.log(f"Code signed: {pyd_file}")
            except subprocess.CalledProcessError as e:
                self.log(f"Code signing failed for {pyd_file}: {e}", "ERROR")

    def find_and_organize_pyd_files(self):
        """Find generated .so files and organize them in build environment"""
        self.log("Organizing .so files in build environment...")
        
        # Look for .so files in build environment
        search_patterns = [
            str(self.build_root / "*.so"),
            str(self.build_root / "build" / "**" / "*.so"),
            str(self.build_src / "**" / "*.so"),
            str(self.build_root / "*.so"),
            str(self.build_root / "build" / "**" / "*.so"),
            str(self.build_src / "**" / "*.so"),
        ]
        
        pyd_files = []
        for pattern in search_patterns:
            pyd_files.extend(glob.glob(pattern, recursive=True))
        
        organized_files = []
        
        # Process each target file
        for filename in self.compile_files:
            file_path_obj = Path(filename)
            base_name = file_path_obj.stem
            
            # More precise matching: look for exact module name match
            related_pyd_files = []
            for pyd_file in pyd_files:
                pyd_basename = os.path.basename(pyd_file)
                # Match files that start with the exact module name
                if pyd_basename.startswith(base_name + ".cp") or pyd_basename == f"{base_name}.so" or pyd_basename == f"{base_name}.so":
                    related_pyd_files.append(pyd_file)
            
            if not related_pyd_files:
                self.log(f"Warning: No .so file found for {filename} (looking for {base_name}.*)", "WARNING")
                # List available files for debugging
                self.log(f"Available .so files: {[os.path.basename(f) for f in pyd_files]}", "DEBUG")
                continue
            
            # Use the first found .so file for this module
            source_pyd = related_pyd_files[0]
            source_filename = os.path.basename(source_pyd)
            
            # Ensure target directory exists in build environment
            target_dir = self.build_src / file_path_obj.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Always rename to clean module name in the correct directory
            target_pyd = target_dir / f"{base_name}.so"
            
            # Remove existing target file if exists
            if target_pyd.exists():
                os.remove(target_pyd)
                self.log(f"Removed existing {target_pyd}")
            
            # Move and rename .so file
            try:
                shutil.move(source_pyd, target_pyd)
                self.log(f"Moved and renamed {source_filename} to {target_pyd}")

                organized_files.append(target_pyd)
            except FileNotFoundError as e:
                self.log(f"Error moving {source_pyd}: {e}", "ERROR")
                self.log(f"Available files in source location: {list(Path(source_pyd).parent.glob('*.so'))}", "DEBUG")

        
        return organized_files
    
    def create_import_wrappers_in_build_env(self):
        """Create import wrappers for all compiled files in build environment"""
        self.log("Creating import wrappers in build environment...")
        
        for filename in self.compile_files:
            build_py_file = self.build_src / filename
            base_name = Path(filename).stem
            
            # Generate appropriate wrapper content based on the file
            file_path_obj = Path(filename)
            module_name = file_path_obj.stem
            
            if 'control_navigator.py' == file_path_obj.name:
                wrapper_content = f'''"""
Control Navigator Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version of ControlNavigator.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
from .{module_name} import ControlNavigator

# Re-export for backward compatibility
__all__ = ['ControlNavigator']
'''
            elif 'control_navigator_handler.py' == file_path_obj.name:
                wrapper_content = f'''"""
Control Navigator Handler Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version of ControlNavigatorHandler.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
from .{module_name} import ControlNavigatorHandler

# Re-export for backward compatibility
__all__ = ['ControlNavigatorHandler']
'''
            else:
                # Generic wrapper for other files - try to detect main class
                try:
                    # Read the original source to find class names
                    original_py_file = self.src_root / filename
                    if original_py_file.exists():
                        content = original_py_file.read_text()
                        import re
                        class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                        if class_matches:
                            main_classes = class_matches
                            imports = [f"from .{module_name} import {cls}" for cls in main_classes]
                            exports = main_classes
                        else:
                            imports = [f"from .{module_name} import *"]
                            exports = []
                    else:
                        imports = [f"from .{module_name} import *"]
                        exports = []
                except:
                    imports = [f"from .{module_name} import *"]
                    exports = []
                
                wrapper_content = f'''"""
{file_path_obj.name} Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
{chr(10).join(imports)}

# Re-export for backward compatibility
{f"__all__ = {exports}" if exports else ""}
'''
            
            # Write import wrapper
            with open(build_py_file, 'w', encoding='utf-8') as f:
                f.write(wrapper_content)
            
            self.log(f"Created import wrapper in build environment: {build_py_file}")
    
    def clean_build_artifacts(self):
        """Clean up immediate build artifacts (but keep necessary files for deployment)"""
        self.log("Cleaning immediate build artifacts...")
        
        # Only remove the most immediate build artifacts, keep other files for deployment
        
        # Remove build directory in build environment
        build_dir = self.build_root / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            self.log(f"Removed build directory: {build_dir}")
        
        # Remove original .cp*.so files (keep only the renamed .so files)
        for pattern in [str(self.build_root / "**" / "*.cp*.so")]:
            cp_pyd_files = glob.glob(pattern, recursive=True)
            for cp_pyd_file in cp_pyd_files:
                os.remove(cp_pyd_file)
                self.log(f"Removed original .so file: {cp_pyd_file}")
        
        self.log("✅ Immediate build artifacts cleaned")
    
    def clean_build_env_for_deployment(self):
        """Clean build environment by removing unnecessary files before deployment"""
        self.log("Cleaning build environment for deployment...")
        
        try:
            # Files and directories to remove from build environment
            cleanup_patterns = [
                # Temporary build files
                "**/*.c",           # C source files generated by Cython
                "**/*.html",        # Cython annotation files
                "build/",           # Build directory
                "**/*.cp*.so",     # Original .cp*.so files (keep only renamed .so files)
                
                # Setup files
                "setup_original.py", # Backup of original setup_mac.py
                "setup_mac.py",         # Setup.py used for compilation
                
                # Cache and temporary files
                "**/__pycache__/",  # Python cache directories
                "**/*.pyc",         # Compiled Python files
                "**/*.pyo",         # Optimized Python files
                "**/.*DS_Store",    # macOS system files
                "**/Thumbs.db",     # Windows system files
            ]
            
            # Additional directories and files from PowerShell script
            additional_cleanup_items = []
            configPath = Path(__file__).parent / "compile_config.yaml"
            with open(configPath, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                additional_cleanup_items = config.get("additional_cleanup_items", [])
                            
            removed_files = 0
            removed_dirs = 0
            
            # Process original cleanup patterns
            for pattern in cleanup_patterns:
                if pattern.endswith('/'):
                    # Directory pattern
                    search_pattern = str(self.build_root / pattern.rstrip('/'))
                    matching_dirs = [p for p in Path(search_pattern).parent.rglob(Path(search_pattern).name) if p.is_dir()]
                    
                    for dir_path in matching_dirs:
                        if dir_path.exists():
                            try:
                                shutil.rmtree(dir_path)
                                removed_dirs += 1
                                self.log(f"Removed directory: {dir_path.relative_to(self.build_root)}")
                            except Exception as e:
                                self.log(f"Warning: Could not remove directory {dir_path}: {e}", "WARNING")
                else:
                    # File pattern
                    search_pattern = str(self.build_root / pattern)
                    matching_files = glob.glob(search_pattern, recursive=True)
                    
                    for file_path in matching_files:
                        try:
                            os.remove(file_path)
                            removed_files += 1
                            rel_path = Path(file_path).relative_to(self.build_root)
                            self.log(f"Removed file: {rel_path}")
                        except Exception as e:
                            self.log(f"Warning: Could not remove file {file_path}: {e}", "WARNING")
            
            # Process additional cleanup items from PowerShell script
            for item in additional_cleanup_items:
                item_path = self.build_root / item
                if item_path.exists():
                    try:
                        if item_path.is_dir():
                            shutil.rmtree(item_path)
                            removed_dirs += 1
                            self.log(f"Removed directory: {item}")
                        else:
                            item_path.unlink()
                            removed_files += 1
                            self.log(f"Removed file: {item}")
                    except Exception as e:
                        self.log(f"Warning: Could not remove {item}: {e}", "WARNING")
            
            self.log(f"✅ Cleanup completed: {removed_files} files and {removed_dirs} directories removed")
            
            # for filename in self.compile_files:
            #     file_path_obj = Path(filename)
            #     # Look for .so files in the source directory
            #     originalFile = self.build_root / "src" / file_path_obj
            #     if originalFile.exists():
            #         os.remove(originalFile)
            #         self.log(f"Removed source artifact: {originalFile}")
    
            # Log what remains in build environment
            remaining_files = sum(1 for _ in self.build_root.rglob('*') if _.is_file())
            self.log(f"Build environment ready for deployment with {remaining_files} files")
            
        except Exception as e:
            self.log(f"Error cleaning build environment: {e}", "ERROR")
            raise

    def deploy_to_target_directory(self):
        """Deploy build environment contents to webex-regress-shield directory"""
        self.log("Deploying build environment to webex-regress-shield directory...")
        
        try:
            # Create target directory if it doesn't exist
            self.target_deployment_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"Target directory: {self.target_deployment_dir}")
            
            # Count total files for progress tracking
            total_files = sum(1 for _ in self.build_root.rglob('*') if _.is_file())
            self.log(f"Found {total_files} files to deploy...")
            
            # Deploy with progress tracking
            self._deploy_with_progress(self.build_root, self.target_deployment_dir, total_files)
            
            self.log("✅ Successfully deployed build environment to webex-regress-shield")
            self.log(f"💡 Deployed directory: {self.target_deployment_dir}")
            
        except Exception as e:
            self.log(f"Error deploying to target directory: {e}", "ERROR")
            raise
    
    def _deploy_with_progress(self, src_dir, target_dir, total_files):
        """Deploy build environment with progress tracking"""
        import time
        
        deployed_files = 0
        start_time = time.time()
        last_progress_time = start_time
        replaced_files = 0
        new_files = 0
        
        def deploy_file_with_progress(src_file, target_file):
            nonlocal deployed_files, last_progress_time, replaced_files, new_files
            
            # Ensure target directory exists
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            file_existed = target_file.exists()
            
            # Copy file (this will replace if exists)
            shutil.copy2(src_file, target_file)
            deployed_files += 1
            
            if file_existed:
                replaced_files += 1
            else:
                new_files += 1
            
            # Update progress every 0.5 seconds or every 50 files
            current_time = time.time()
            if (current_time - last_progress_time >= 0.5) or (deployed_files % 50 == 0) or (deployed_files == total_files):
                progress = (deployed_files / total_files) * 100
                elapsed = current_time - start_time
                if deployed_files > 0:
                    estimated_total = (elapsed / deployed_files) * total_files
                    eta = estimated_total - elapsed
                    eta_str = f", ETA: {eta:.1f}s" if eta > 0 else ""
                else:
                    eta_str = ""
                
                # Create progress bar
                bar_length = 30
                filled_length = int(bar_length * deployed_files // total_files)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                print(f"\rDeploying: [{bar}] {progress:.1f}% ({deployed_files}/{total_files} files){eta_str}", end='', flush=True)
                last_progress_time = current_time
        
        # Deploy all files recursively
        for src_file in src_dir.rglob('*'):
            if src_file.is_file():
                # Calculate relative path from build root
                rel_path = src_file.relative_to(src_dir)
                target_file = target_dir / rel_path
                
                deploy_file_with_progress(src_file, target_file)
        
        # Complete the progress bar
        print()  # New line after progress bar
        
        # Log deployment summary
        self.log(f"Deployment summary:")
        self.log(f"  - {new_files} new files created")
        self.log(f"  - {replaced_files} existing files replaced")
        self.log(f"  - {deployed_files} total files deployed")

    def compile(self):
        """Main compilation process"""
        try:
            self.log("Starting WRS Control Navigator compilation")
            self.log("=" * 80)
            
            # Step 1: Check prerequisites
            print("############### Step 1: Checking prerequisites ###############")
            self.check_prerequisites()
            
            # Step 2: Clean and prepare build environment
            print("############### Step 2: Preparing build environment ###############")
            self.clean_build_environment()
            
            # Step 3: Copy source code to build environment
            print("############### Step 3: Copying source code to build environment ###############")
            self.copy_source_to_build_env()
            
            # Step 4: Generate .pyi files in build environment
            print("############### Step 4: Generating .pyi files in build environment ###############")
            self.generate_pyi_files_in_build_env()
            
            # Step 5: Create filtered setup_mac.py in build environment
            print("############### Step 5: Creating filtered setup_mac.py in build environment ###############")
            self.create_filtered_setup_py()
            
            # Step 6: Run setup_mac.py in build environment
            print("############### Step 6: Running setup_mac.py in build environment ###############")
            self.run_setup_in_build_env()
            
            # Step 7: Organize .so files in build environment
            print("############### Step 7: Organizing .so files in build environment ###############")
            pyd_files = self.find_and_organize_pyd_files()
            self.codeSign(pyd_files)
            
            # Step 8: Handle skipped files (keep as Python source)
            print("############### Step 8: Handling skipped files ###############")
            self.handle_skipped_files()
            
            # Step 9: Create import wrappers
            print("############### Step 9: Creating import wrappers in build environment ###############")
            self.create_import_wrappers_in_build_env()
            
            # Step 10: Clean build artifacts
            print("############### Step 10: Cleaning build artifacts ###############")
            self.clean_build_artifacts()
            
            # Step 11: Clean source directory artifacts
            print("############### Step 11: Cleaning source directory artifacts ###############")
            self.clean_source_artifacts()
            
            # Step 12: Verify build
            print("############### Step 12: Verifying build ###############")
            if self.verify_build():
                self.log("WRS Control Navigator compilation completed successfully!", "SUCCESS")
            else:
                self.log("Compilation completed but verification failed", "WARNING")
            
            # Step 13: Clean build environment for deployment
            print("############### Step 13: Cleaning build environment for deployment ###############")
            self.clean_build_env_for_deployment()
            
            # Step 14: Deploy to webex-regress-shield directory
            print("############### Step 14: Deploying to webex-regress-shield directory ###############")
            self.deploy_to_target_directory()
            
            # Summary
            self.log("=" * 80)
            self.log("WRS COMPILATION SUMMARY")
            self.log("=" * 80)
            self.log(f"Project directory: {self.project_root}")
            self.log(f"Source directory (untouched): {self.src_root}")
            self.log(f"Build environment: {self.build_root}")
            self.log(f"Deployed to: {self.target_deployment_dir}")
            self.log(f"Build environment structure:")
            
            # List compiled files
            for filename in self.compile_files:
                file_path_obj = Path(filename)
                base_name = file_path_obj.stem
                self.log(f"  - {base_name}.pyi (type hints)")
                self.log(f"  - {base_name}.so (compiled module)")
                self.log(f"  - {filename} (import wrapper)")
            
            self.log("=" * 80)
            self.log(f"💡 Build environment: {self.build_root}")
            self.log(f"💡 Deployed directory: {self.target_deployment_dir}")
            self.log("💡 To use compiled version: Use the deployed directory")
            self.log("💡 To return to development: Use the original src directory")
            
        except Exception as e:
            self.log(f"Compilation failed: {e}", "ERROR")
            sys.exit(1)


def main():
    """Main entry point"""
    compiler = WRSCompiler_Mac()
    compiler.compile()


if __name__ == "__main__":
    main()

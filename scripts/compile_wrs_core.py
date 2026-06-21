#!/usr/bin/env python3
"""
WRS Core Controls Simple Compilation Script

This script compiles control files from src/core/windows/controls/source 
and generates compiled files directly to src/core/windows/controls.

Usage:
    python scripts/compile_wrs_core.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def log(message):
    """Simple logging"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def monitor_setup_progress(process, total_files):
    """Monitor setup.py compilation progress with simple file completion progress bar"""
    import time
    import re
    
    compiled_files = 0
    start_time = time.time()
    
    # Patterns to detect file compilation completion
    compiling_patterns = [
        re.compile(r'Compiling (.+\.py)'),
        re.compile(r'building (.+) extension'),
        re.compile(r'creating (.+\.pyd)'),
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
        log(f"Compilation output: {full_output}")
    else:
        log("✅ All files compiled successfully")


def restore_source_files(source_dir, target_dir):
    """Restore original source files by removing compiled files and copying source"""
    log("Restoring original source files...")
    
    # Check if source directory exists
    if not source_dir.exists():
        log(f"ERROR: Source directory not found: {source_dir}")
        log("Please ensure the submodule is initialized:")
        log("  git submodule update --init --recursive")
        sys.exit(1)
    
    # Get all Python files in source directory
    py_files = list(source_dir.glob("*.py"))
    if not py_files:
        log("ERROR: No Python files found in source directory")
        sys.exit(1)
    
    log(f"Found {len(py_files)} source files to restore")
    
    # Remove compiled files from target directory
    removed_count = 0
    for py_file in py_files:
        base_name = py_file.stem
        
        # Remove .py wrapper, .pyd, and .pyi files
        for ext in ['.py', '.pyd', '.pyi']:
            target_file = target_dir / f"{base_name}{ext}"
            if target_file.exists():
                target_file.unlink()
                log(f"  Removed: {target_file.name}")
                removed_count += 1
    
    log(f"✓ Removed {removed_count} compiled files")
    
    # Copy source files to target directory
    log("Copying source files...")
    copied_count = 0
    for py_file in py_files:
        target_file = target_dir / py_file.name
        shutil.copy2(py_file, target_file)
        log(f"  ✓ Copied: {py_file.name}")
        copied_count += 1
    
    log(f"✓ Copied {copied_count} source files to {target_dir}")


def main():
    """Main compilation process"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    log("=" * 80)
    log("WRS Core Controls Compilation")
    log("=" * 80)
    
    # Paths
    source_dir = project_root / "src" / "core" / "windows" / "controls" / "source"
    target_dir = project_root / "src" / "core" / "windows" / "controls"
    
    # User confirmation prompt
    print("\nPlease select mode:")
    print("1. Compile mode - Generate compiled .pyd files with wrappers")
    print("2. Source mode  - Use original .py source files")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    # Handle source mode
    if choice == '2':
        log("Source mode selected - Switching to source files...")
        restore_source_files(source_dir, target_dir)
        log("=" * 80)
        log("Successfully switched to source mode!")
        log(f"Source files are now active in: {target_dir}")
        log("=" * 80)
        return
    
    # Continue with compilation mode
    log("Compile mode selected - Starting compilation...")
    
    # Check source directory
    if not source_dir.exists():
        log(f"ERROR: Source directory not found: {source_dir}")
        log("Please ensure the submodule is initialized:")
        log("  git submodule update --init --recursive")
        sys.exit(1)
    
    # Get Python files to compile
    py_files = list(source_dir.glob("*.py"))
    if not py_files:
        log("ERROR: No Python files found in source directory")
        sys.exit(1)
    
    log(f"Found {len(py_files)} Python files to compile")
    
    # Create temporary setup.py
    log("Creating setup.py...")
    compile_files = [f"src/core/windows/controls/source/{f.name}" for f in py_files]
    
    setup_content = f'''from setuptools import setup
from Cython.Build import cythonize

compile_files = {repr(compile_files)}

setup(
    ext_modules=cythonize(
        compile_files,
        compiler_directives={{"language_level": "3"}},
        annotate=True
    ),
)
'''
    
    setup_file = project_root / "setup_temp.py"
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(setup_content)
    
    # Compile with progress monitoring
    log("Compiling with Cython...")
    process = subprocess.Popen(
        [sys.executable, "setup_temp.py", "build_ext"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Monitor compilation progress
    monitor_setup_progress(process, len(py_files))
    
    # Wait for process to complete
    return_code = process.wait()
    
    if return_code != 0:
        log("ERROR: Compilation failed!")
        setup_file.unlink(missing_ok=True)
        sys.exit(1)
    
    log("✓ Compilation successful")
    
    # Setup temp directory
    build_dir = project_root / "build"
    temp_dir = source_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    log(f"Created temp directory: {temp_dir.relative_to(project_root)}")
    
    # Find and copy .pyd files
    log("Copying and renaming compiled files...")
    copied_pyd = 0
    
    # Find all .pyd files in build directory
    pyd_files = list(build_dir.rglob("*.pyd"))
    
    if not pyd_files:
        log("WARNING: No .pyd files found in build directory")
    else:
        # Copy and rename .pyd files
        for pyd_file in pyd_files:
            # Extract base name (e.g., control_explorer from control_explorer.cp311-win_amd64.pyd)
            base_name = pyd_file.name.split('.')[0]
            
            # First copy to temp directory with full name
            temp_target = temp_dir / pyd_file.name
            shutil.copy2(pyd_file, temp_target)
            
            # Then copy to target directory with simplified name
            target = target_dir / f"{base_name}.pyd"
            shutil.copy2(pyd_file, target)
            log(f"  ✓ {base_name}.pyd (from {pyd_file.name})")
            copied_pyd += 1
    
    # Generate .py wrappers (not copy from source)
    log("Generating import wrappers...")
    copied_wrappers = 0
    
    for py_file in py_files:
        base_name = py_file.stem
        
        # Read source file to find class names
        try:
            content = py_file.read_text(encoding='utf-8')
            import re
            class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            
            if class_matches:
                main_class = class_matches[0]  # Use first class as main
                wrapper_content = f'''"""
{py_file.name} Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
from .{base_name} import {main_class}

# Re-export for backward compatibility
__all__ = ['{main_class}']
'''
            else:
                # Fallback if no class found
                wrapper_content = f'''"""
{py_file.name} Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version.
Generated automatically by WRS compilation script.
"""

# Import the compiled Cython module
from .{base_name} import *

__all__ = []
'''
        except:
            # Fallback wrapper
            wrapper_content = f'''"""
{py_file.name} Import Wrapper (WRS Compiled Version)
"""
from .{base_name} import *
'''
        
        # Write wrapper to target
        wrapper_file = target_dir / f"{base_name}.py"
        wrapper_file.write_text(wrapper_content, encoding='utf-8')
        log(f"  ✓ {base_name}.py")
        copied_wrappers += 1
    
    # Generate .pyi stubs using AST parsing like compile_wrs.py
    log("Generating .pyi stub files...")
    import re
    import ast
    
    for py_file in py_files:
        try:
            content = py_file.read_text(encoding='utf-8')
            
            # Parse the AST
            tree = ast.parse(content)
            
            pyi_lines = []
            pyi_lines.append('"""')
            pyi_lines.append(f'Type stub file for {py_file.name}')
            pyi_lines.append('')
            pyi_lines.append(f'This file provides type hints and interface definitions for classes in {py_file.name}.')
            pyi_lines.append('Generated in WRS build environment.')
            pyi_lines.append('"""')
            pyi_lines.append('')
            
            # Add imports
            pyi_lines.append('from typing import Dict, List, Tuple, Any, Optional, Union')
            
            # Extract imports from source (simplified)
            import_lines = []
            for line in content.split('\n')[:50]:  # Check first 50 lines
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if 'uiautomation' in stripped or 'auto' in stripped:
                        pyi_lines.append('import uiautomation as auto')
                        break
            
            pyi_lines.append('')
            
            # Add type aliases if needed
            if 'control_navigator' in py_file.name:
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
                    elif node.name == 'ControlExplorer':
                        pyi_lines.append('    Class for exploring and discovering UI controls in the application.')
                    elif node.name == 'ControlLocator':
                        pyi_lines.append('    Class for locating specific UI controls based on metadata.')
                    elif node.name == 'ControlValidator':
                        pyi_lines.append('    Class for validating UI controls and their properties.')
                    elif node.name == 'ControlValidatorHandler':
                        pyi_lines.append('    Handler class for control validation operations.')
                    else:
                        pyi_lines.append(f'    {node.name} class for WRS automation.')
                    
                    pyi_lines.append('    """')
                    pyi_lines.append('')
                    
                    # Extract class attributes
                    class_attributes = extract_class_attributes(node)
                    for attr in class_attributes:
                        pyi_lines.append(f'    {attr}')
                        pyi_lines.append('')
                    
                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_signature = extract_method_signature(item)
                            pyi_lines.append(f'    {method_signature}')
                            pyi_lines.append('')
            
            # Write .pyi file
            pyi_file = target_dir / py_file.with_suffix('.pyi').name
            pyi_file.write_text('\n'.join(pyi_lines), encoding='utf-8')
            
            # Count classes for logging
            class_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            log(f"  ✓ {pyi_file.name} ({class_count} classes)")
            
        except Exception as e:
            log(f"  Warning: Failed to parse {py_file.name}: {e}")
            # Fallback to basic stub
            pyi_file = target_dir / py_file.with_suffix('.pyi').name
            stub_content = f'''"""
Type stub file for {py_file.name}

Generated in WRS build environment.
"""

from typing import Any

# Basic stub for {py_file.name}
'''
            pyi_file.write_text(stub_content, encoding='utf-8')
            log(f"  ✓ {pyi_file.name} (basic)")
    
    # Cleanup
    log("")
    log("Cleaning up temporary files...")
    
    # Remove temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        log(f"  ✓ Removed {temp_dir.relative_to(project_root)}")
    
    # Remove build directory
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
        log(f"  ✓ Removed {build_dir.relative_to(project_root)}")
    
    # Remove .c and .html files from source
    c_files = list(source_dir.glob("*.c"))
    html_files = list(source_dir.glob("*.html"))
    for c_file in c_files:
        c_file.unlink()
    for html_file in html_files:
        html_file.unlink()
    if c_files or html_files:
        log(f"  ✓ Removed {len(c_files)} .c and {len(html_files)} .html files")
    
    # Remove setup_temp.py
    setup_file.unlink(missing_ok=True)
    log(f"  ✓ Removed setup_temp.py")
    
    # Summary
    log("")
    log("=" * 80)
    log("COMPILATION SUMMARY")
    log("=" * 80)
    log(f"✓ Compiled {len(py_files)} modules")
    log(f"✓ Generated {copied_pyd} .pyd files (renamed from .cp311-win_amd64.pyd)")
    log(f"✓ Generated {copied_wrappers} .py wrappers")
    log(f"✓ Generated {len(py_files)} .pyi stubs")
    log(f"✓ Output: {target_dir.relative_to(project_root)}")
    log("")
    log("Files generated:")
    log("  - .py  (import wrappers)")
    log("  - .pyd (compiled modules with simplified names)")
    log("  - .pyi (type stubs)")
    log("")
    log("Build process:")
    log("  1. Compiled to source/temp/")
    log("  2. Copied to src/core/windows/controls/")
    log("  3. Cleaned up temporary files")
    log("=" * 80)
    log("Compilation completed successfully!")


def extract_class_attributes(class_node):
    """Extract class attributes and variables from AST class node"""
    import ast
    attributes = []
    
    for item in class_node.body:
        if isinstance(item, ast.Assign):
            # Handle class variables like: PREVALIDATEDCONTROLS = []
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attr_name = target.id
                    # Try to infer type from the value
                    attr_type = infer_type_from_value(item.value)
                    attributes.append(f"{attr_name}: {attr_type}")
        
        elif isinstance(item, ast.AnnAssign):
            # Handle annotated assignments like: handler: SomeType = None
            if isinstance(item.target, ast.Name):
                attr_name = item.target.id
                if item.annotation:
                    # Extract type annotation
                    attr_type = extract_type_annotation(item.annotation)
                else:
                    attr_type = "Any"
                attributes.append(f"{attr_name}: {attr_type}")
    
    # Also check for attributes assigned in __init__ method
    init_method = find_init_method(class_node)
    if init_method:
        init_attributes = extract_init_attributes(init_method)
        attributes.extend(init_attributes)
    
    return attributes


def find_init_method(class_node):
    """Find the __init__ method in a class node"""
    import ast
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
            return item
    return None


def extract_init_attributes(init_node):
    """Extract instance attributes from __init__ method"""
    import ast
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
                        attr_type = infer_type_from_value(item.value)
                        attributes.append(f"{attr_name}: {attr_type}")
    
    return attributes


def infer_type_from_value(value_node):
    """Infer type from AST value node"""
    import ast
    
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


def extract_method_signature(func_node):
    """Extract method signature from AST function node"""
    args = []
    
    # Handle function arguments
    for i, arg in enumerate(func_node.args.args):
        arg_name = arg.arg
        
        # Try to infer type from annotations or use Any
        arg_type = 'Any'
        
        # Handle type annotations if present
        if hasattr(arg, 'annotation') and arg.annotation:
            arg_type = extract_type_annotation(arg.annotation)
        
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
        return_type = extract_type_annotation(func_node.returns)
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


def extract_type_annotation(node):
    """Extract type annotation from AST node"""
    import ast
    
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Subscript):
        # Handle List[X], Dict[X, Y], etc.
        base_type = extract_type_annotation(node.value)
        if isinstance(node.slice, ast.Tuple):
            slice_types = ', '.join(extract_type_annotation(e) for e in node.slice.elts)
        else:
            slice_types = extract_type_annotation(node.slice)
        return f'{base_type}[{slice_types}]'
    elif isinstance(node, ast.Attribute):
        return f'{extract_type_annotation(node.value)}.{node.attr}'
    else:
        return 'Any'


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCompilation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

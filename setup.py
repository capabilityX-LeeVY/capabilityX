from setuptools import setup
from Cython.Build import cythonize

# Files to compile
compile_files = [
    "src/core/windows/controls/source/control_explorer.py",
    "src/core/windows/controls/source/control_locator.py",
    "src/core/windows/controls/source/control_validator.py",
    "src/core/windows/controls/source/control_validator_handler.py", 
    "src/core/windows/controls/source/control_navigator.py",
    "src/core/windows/controls/source/control_navigator_handler.py"
]

setup(
    ext_modules=cythonize(
        compile_files,
        compiler_directives={"language_level": "3"},
        annotate=True
    ),
)
#!/usr/bin/env python3
"""
This is a simple script to verify that the cylestio_monitor package is correctly installed
and accessible in the CI environment.

Run this script directly to test package installation:
    python tests/ci_check_installation.py
"""

import sys
import pkgutil
import importlib
import inspect
import os

def print_separator():
    print("-" * 80)

def check_path():
    """Check Python path to make sure our package can be found."""
    print("PYTHON PATH:")
    for path in sys.path:
        print(f"  - {path}")
    print_separator()

def check_package():
    """Try to import the cylestio_monitor package and print info."""
    try:
        import cylestio_monitor
        print(f"Package found: {cylestio_monitor.__file__}")
        
        # Show package location
        package_path = os.path.dirname(cylestio_monitor.__file__)
        print(f"Package path: {package_path}")
        
        # Check if package is installed in development mode
        if 'site-packages' in package_path:
            print("WARNING: Package is installed in site-packages, not in development mode")
        elif 'src' in package_path:
            print("Package is installed in development mode (using src/)")
        
        # Print version
        try:
            print(f"Version: {cylestio_monitor.__version__}")
        except AttributeError:
            print("Version not found")
        
        print_separator()
        return True
    except ImportError as e:
        print(f"ERROR: Could not import cylestio_monitor package: {e}")
        print_separator()
        return False

def check_submodules():
    """Check if the submodules are available."""
    try:
        import cylestio_monitor
        
        # Get all submodules
        print("SUBMODULES:")
        for _, name, ispkg in pkgutil.iter_modules(cylestio_monitor.__path__, 'cylestio_monitor.'):
            try:
                module = importlib.import_module(name)
                print(f"  ✓ {name}: {module.__file__}")
            except ImportError as e:
                print(f"  ✗ {name}: IMPORT ERROR - {e}")
                
        print_separator()
        
        # Check specific modules that have been causing problems
        modules_to_check = [
            "cylestio_monitor.events_processor",
            "cylestio_monitor.events.processing.security",
            "cylestio_monitor.config.config_manager"
        ]
        
        print("SPECIFIC MODULES:")
        for module_name in modules_to_check:
            try:
                module = importlib.import_module(module_name)
                print(f"  ✓ {module_name}: {module.__file__}")
                
                # Print available attributes
                attrs = [attr for attr in dir(module) if not attr.startswith('_')]
                print(f"    Attributes: {', '.join(attrs[:10])}...")
                
                # Print functions
                functions = [attr for attr in attrs if inspect.isfunction(getattr(module, attr))]
                if functions:
                    print(f"    Functions: {', '.join(functions[:5])}...")
                
            except ImportError as e:
                print(f"  ✗ {module_name}: IMPORT ERROR - {e}")
                
        print_separator()
        
    except ImportError as e:
        print(f"ERROR: Could not check submodules: {e}")
        print_separator()

def main():
    """Run all checks."""
    print_separator()
    print("PYTHON ENVIRONMENT CHECK")
    print(f"Python version: {sys.version}")
    print(f"Executable: {sys.executable}")
    print_separator()
    
    check_path()
    package_found = check_package()
    
    if package_found:
        check_submodules()
    
    print("CHECK COMPLETE")
    print_separator()

if __name__ == "__main__":
    main() 
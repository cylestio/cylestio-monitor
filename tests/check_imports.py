#!/usr/bin/env python3
"""
Diagnostic script to check module imports and help debug CI issues.
"""

import sys
import os
import importlib
import pkgutil
from pathlib import Path


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 40)
    print(f" {title} ")
    print("=" * 40)


def check_module_path(module_name):
    """Try to import a module and print its file location."""
    try:
        module = importlib.import_module(module_name)
        path = getattr(module, "__file__", "No __file__ attribute")
        print(f"✅ Successfully imported {module_name}")
        print(f"   Path: {path}")
        return module
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return None


def list_submodules(package_name):
    """List all submodules of a package."""
    try:
        package = importlib.import_module(package_name)
        print(f"Submodules of {package_name}:")
        
        if hasattr(package, "__path__"):
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
                print(f"  {'📁' if is_pkg else '📄'} {name}")
        else:
            print("  (Not a package with __path__)")
    except ImportError as e:
        print(f"Cannot list submodules of {package_name}: {e}")


def check_file_exists(filepath):
    """Check if a file exists in the filesystem."""
    path = Path(filepath)
    if path.exists():
        print(f"✅ File exists: {path}")
        print(f"   Size: {path.stat().st_size} bytes")
        return True
    else:
        print(f"❌ File does not exist: {path}")
        return False


def main():
    """Run import checks and diagnostics."""
    print_section("Python Environment")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    print_section("Package Structure")
    # Check main package
    main_module = check_module_path("cylestio_monitor")
    if main_module:
        # List top-level submodules
        list_submodules("cylestio_monitor")
    
    print_section("Events Module Structure")
    # Check events module and submodules
    check_module_path("cylestio_monitor.events")
    list_submodules("cylestio_monitor.events")
    
    print_section("Processing Module Structure")
    # Try to import the processing module
    check_module_path("cylestio_monitor.events.processing")
    list_submodules("cylestio_monitor.events.processing")
    
    print_section("Security Module")
    # Check specific security module
    security_module = check_module_path("cylestio_monitor.events.processing.security")
    
    # Check if the old module still exists
    print_section("Legacy Module Check")
    old_module = check_module_path("cylestio_monitor.events_processor")
    
    # Try file system checks
    print_section("File System Checks")
    new_security_path = "src/cylestio_monitor/events/processing/security.py"
    old_processor_path = "src/cylestio_monitor/events_processor.py"
    
    check_file_exists(new_security_path)
    check_file_exists(old_processor_path)
    
    # Print Python path
    print_section("Python Path")
    for path in sys.path:
        print(f"  {path}")


if __name__ == "__main__":
    main() 
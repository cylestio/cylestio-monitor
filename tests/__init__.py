"""Tests for the Cylestio Monitor SDK."""

# This code runs when the tests package is imported, before any test runs
import sys
import types
import os
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tests")

# Setup mock db modules
def setup_mock_db():
    """Set up mock DB modules to prevent import errors."""
    if 'cylestio_monitor.db' not in sys.modules:
        logger.info("Creating mock DB modules")
        db_module = types.ModuleType('cylestio_monitor.db')
        sys.modules['cylestio_monitor.db'] = db_module
        
        db_manager_module = types.ModuleType('cylestio_monitor.db.db_manager')
        
        class DBManager:
            def __init__(self):
                pass
            def _get_connection(self):
                pass
        
        db_manager_module.DBManager = DBManager
        sys.modules['cylestio_monitor.db.db_manager'] = db_manager_module
        
        db_utils_module = types.ModuleType('cylestio_monitor.db.utils')
        db_utils_module.log_to_db = lambda *args, **kwargs: None
        sys.modules['cylestio_monitor.db.utils'] = db_utils_module

# Setup mock langchain modules
def setup_mock_langchain():
    """Set up mock langchain modules to prevent import errors."""
    for module_name in ['langchain', 'langchain_core']:
        if module_name not in sys.modules:
            logger.info(f"Creating mock {module_name} module")
            # Create base module
            base_module = types.ModuleType(module_name)
            sys.modules[module_name] = base_module
            
            # Create callbacks submodule
            callbacks_name = f"{module_name}.callbacks"
            callbacks_module = types.ModuleType(callbacks_name)
            sys.modules[callbacks_name] = callbacks_module
            setattr(base_module, 'callbacks', callbacks_module)
            
            # Create base submodule
            base_name = f"{module_name}.callbacks.base"
            base_submodule = types.ModuleType(base_name)
            
            # Add BaseCallbackHandler class
            class MockBaseCallbackHandler:
                pass
            
            base_submodule.BaseCallbackHandler = MockBaseCallbackHandler
            sys.modules[base_name] = base_submodule
            setattr(callbacks_module, 'base', base_submodule)

# Run setup
setup_mock_db()
setup_mock_langchain()

logger.info("Mock modules initialized in tests/__init__.py")

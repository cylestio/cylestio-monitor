"""
Sitecustomize module for Python

This module is automatically imported by Python when it starts.
We use it to set up our mock modules before any other imports happen.
"""

import sys
import types
import logging
import os

# Skip in development environments
if os.environ.get('CYLESTIO_DEV_ENV') == 'local':
    # Don't apply mocks in local dev environment
    print("Skipping mock setup in local development environment")
    sys.exit(0)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sitecustomize")

logger.info("Initializing mock modules for CI environment")

# Create and register mock DB modules
def setup_mock_db():
    """Set up mock DB modules."""
    if 'cylestio_monitor.db' not in sys.modules:
        db_module = types.ModuleType('cylestio_monitor.db')
        sys.modules['cylestio_monitor.db'] = db_module
        
        db_manager_module = types.ModuleType('cylestio_monitor.db.db_manager')
        
        class DBManager:
            def __init__(self):
                pass
            def _get_connection(self):
                return None
        
        db_manager_module.DBManager = DBManager
        sys.modules['cylestio_monitor.db.db_manager'] = db_manager_module
        
        db_utils_module = types.ModuleType('cylestio_monitor.db.utils')
        
        def log_to_db(*args, **kwargs):
            return None
        
        db_utils_module.log_to_db = log_to_db
        sys.modules['cylestio_monitor.db.utils'] = db_utils_module

# Create and register mock langchain modules
def setup_mock_langchain():
    """Set up mock langchain modules."""
    for module_name in ['langchain', 'langchain_core']:
        if module_name not in sys.modules:
            # Create the base module
            base_module = types.ModuleType(module_name)
            sys.modules[module_name] = base_module
            
            # Create callbacks module
            callbacks_module = types.ModuleType(f"{module_name}.callbacks")
            sys.modules[f"{module_name}.callbacks"] = callbacks_module
            setattr(base_module, 'callbacks', callbacks_module)
            
            # Create base submodule
            base_submodule = types.ModuleType(f"{module_name}.callbacks.base")
            
            # Add BaseCallbackHandler class
            class MockBaseCallbackHandler:
                pass
            
            base_submodule.BaseCallbackHandler = MockBaseCallbackHandler
            sys.modules[f"{module_name}.callbacks.base"] = base_submodule
            setattr(callbacks_module, 'base', base_submodule)

# Run setup
setup_mock_db()
setup_mock_langchain()

logger.info("Mock modules initialized by sitecustomize.py") 
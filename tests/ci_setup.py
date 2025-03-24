#!/usr/bin/env python
"""
CI setup script to prepare test environment.
This script sets up necessary mocks for dependencies that might be missing.
Run this before running pytest in CI environments.
"""

import sys
import types
import importlib.util
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ci_setup")

logger.info("CI setup script running...")

# Create mock DB modules
def setup_mock_db():
    """Set up mock DB modules."""
    if 'cylestio_monitor.db' not in sys.modules:
        logger.info("Creating mock DB modules")
        # Create db module
        db_module = types.ModuleType('cylestio_monitor.db')
        sys.modules['cylestio_monitor.db'] = db_module
        
        # Create db_manager module with DBManager class
        db_manager_module = types.ModuleType('cylestio_monitor.db.db_manager')
        
        class DBManager:
            def __init__(self):
                logger.info("Mock DBManager initialized")
            def _get_connection(self):
                return None
        
        db_manager_module.DBManager = DBManager
        sys.modules['cylestio_monitor.db.db_manager'] = db_manager_module
        
        # Create db_utils module with log_to_db function
        db_utils_module = types.ModuleType('cylestio_monitor.db.utils')
        
        def log_to_db(*args, **kwargs):
            logger.info(f"Mock log_to_db called with: {args}, {kwargs}")
            return None
        
        db_utils_module.log_to_db = log_to_db
        sys.modules['cylestio_monitor.db.utils'] = db_utils_module
        
        logger.info("Mock DB modules created")

# Create mock langchain modules
def setup_mock_langchain():
    """Set up mock langchain modules."""
    for module_name in ['langchain', 'langchain_core']:
        if module_name not in sys.modules:
            logger.info(f"Creating mock {module_name} module")
            
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
                def __init__(self):
                    logger.info("Mock BaseCallbackHandler initialized")
            
            base_submodule.BaseCallbackHandler = MockBaseCallbackHandler
            sys.modules[f"{module_name}.callbacks.base"] = base_submodule
            setattr(callbacks_module, 'base', base_submodule)
            
            logger.info(f"Mock {module_name} module created")

# Run setup
setup_mock_db()
setup_mock_langchain()

# Verify mock modules are registered
logger.info("Verifying mock modules...")
mock_modules = [
    'cylestio_monitor.db',
    'cylestio_monitor.db.db_manager',
    'cylestio_monitor.db.utils',
    'langchain',
    'langchain.callbacks',
    'langchain.callbacks.base',
    'langchain_core',
    'langchain_core.callbacks',
    'langchain_core.callbacks.base'
]

for module_name in mock_modules:
    if module_name in sys.modules:
        logger.info(f"✓ {module_name} is available")
    else:
        logger.error(f"✗ {module_name} is missing")

logger.info("CI setup complete") 
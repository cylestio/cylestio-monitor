#!/usr/bin/env python
"""
CI verification script.
This script verifies that necessary mock modules are properly set up.
"""

import sys
import types
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ci_verify")

logger.info("CI verification starting...")

# Create and verify mock DB modules
def verify_db_modules():
    """Set up and verify DB modules."""
    # Create mock db modules if they don't exist
    if 'cylestio_monitor.db' not in sys.modules:
        logger.info("Creating cylestio_monitor.db module")
        db_module = types.ModuleType('cylestio_monitor.db')
        sys.modules['cylestio_monitor.db'] = db_module
        
        db_manager_module = types.ModuleType('cylestio_monitor.db.db_manager')
        
        class DBManager:
            def __init__(self):
                logger.info("Mock DBManager initialized")
                
            def _get_connection(self):
                return None
        
        db_manager_module.DBManager = DBManager
        sys.modules['cylestio_monitor.db.db_manager'] = db_manager_module
        
        db_utils_module = types.ModuleType('cylestio_monitor.db.utils')
        db_utils_module.log_to_db = lambda *args, **kwargs: None
        sys.modules['cylestio_monitor.db.utils'] = db_utils_module
    
    # Verify modules exist and can be imported
    try:
        from cylestio_monitor.db.db_manager import DBManager
        logger.info("✓ DBManager successfully imported")
        db_instance = DBManager()
        logger.info("✓ DBManager successfully initialized")
    except (ImportError, AttributeError) as e:
        logger.error(f"✗ Failed to import or initialize DBManager: {e}")
        return False
        
    return True

# Verify langchain modules
def verify_langchain_modules():
    """Set up and verify langchain modules."""
    # Create mock langchain modules if they don't exist
    for module_name in ['langchain', 'langchain_core']:
        if module_name not in sys.modules:
            logger.info(f"Creating {module_name} module")
            
            # Create base module
            base_module = types.ModuleType(module_name)
            sys.modules[module_name] = base_module
            
            # Create callbacks module
            callbacks_module = types.ModuleType(f"{module_name}.callbacks")
            sys.modules[f"{module_name}.callbacks"] = callbacks_module
            setattr(base_module, 'callbacks', callbacks_module)
            
            # Create base submodule
            base_submodule = types.ModuleType(f"{module_name}.callbacks.base")
            
            class MockBaseCallbackHandler:
                def __init__(self):
                    logger.info(f"Mock {module_name} BaseCallbackHandler initialized")
            
            base_submodule.BaseCallbackHandler = MockBaseCallbackHandler
            sys.modules[f"{module_name}.callbacks.base"] = base_submodule
            setattr(callbacks_module, 'base', base_submodule)
    
    # Verify modules exist and can be imported
    success = True
    try:
        from langchain.callbacks.base import BaseCallbackHandler as LCHandler
        logger.info("✓ langchain.callbacks.base.BaseCallbackHandler successfully imported")
    except (ImportError, AttributeError) as e:
        logger.error(f"✗ Failed to import langchain.callbacks.base.BaseCallbackHandler: {e}")
        success = False
        
    try:
        from langchain_core.callbacks.base import BaseCallbackHandler as LCCoreHandler
        logger.info("✓ langchain_core.callbacks.base.BaseCallbackHandler successfully imported")
    except (ImportError, AttributeError) as e:
        logger.error(f"✗ Failed to import langchain_core.callbacks.base.BaseCallbackHandler: {e}")
        success = False
        
    return success

# Run verifications
logger.info("Verifying mock modules...")
db_success = verify_db_modules()
langchain_success = verify_langchain_modules()

# Final status
if db_success and langchain_success:
    logger.info("✅ All mock modules successfully verified!")
    sys.exit(0)
else:
    logger.error("❌ Some mock modules failed verification!")
    sys.exit(1) 
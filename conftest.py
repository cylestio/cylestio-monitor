"""Root conftest.py for pytest."""

import sys
import types
import logging
import pytest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conftest")

# Setup mock modules at collection time
def pytest_configure(config):
    """Set up mock modules for collection time."""
    logger.info("Setting up mock modules from root conftest.py")
    
    # Setup DB modules
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
        db_utils_module.log_to_db = lambda *args, **kwargs: None
        sys.modules['cylestio_monitor.db.utils'] = db_utils_module
    
    # Setup langchain modules
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

# Mark problematic tests to skip if needed
def pytest_collection_modifyitems(items):
    """Skip problematic tests if modules are not available."""
    for item in items:
        if any(name in item.nodeid for name in ['test_events_processor.py', 'test_patchers_anthropic.py']):
            if 'cylestio_monitor.db' not in sys.modules or 'langchain' not in sys.modules:
                item.add_marker(pytest.mark.skip(reason="Required modules not available")) 
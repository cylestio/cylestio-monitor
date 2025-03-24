#!/usr/bin/env python3
"""
Patch the disable_monitoring function to emit monitor_finish event
"""

import os
import sys
import inspect

# Path to src directory
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from cylestio_monitor.monitor import disable_monitoring
from cylestio_monitor.event_logger import process_and_log_event
from cylestio_monitor.config import ConfigManager
from datetime import datetime

# Print the original function for reference
print("Original disable_monitoring function:")
print(inspect.getsource(disable_monitoring))
print("\n")

# Apply our fix
def patched_disable_monitoring():
    """
    Patched version of disable_monitoring that emits a monitor_finish event.
    """
    from cylestio_monitor.monitor import logger
    
    logger.info("Disabling Cylestio monitoring")
    
    # Get agent_id from configuration
    config_manager = ConfigManager()
    agent_id = config_manager.get("monitoring.agent_id")
    
    # Log the monitoring finish event before unpatching everything
    if agent_id:
        process_and_log_event(
            agent_id=agent_id,
            event_type="monitor_finish",
            data={
                "timestamp": datetime.now().isoformat(),
            },
            channel="SYSTEM"
        )
    
    # Continue with the original disable_monitoring code...
    # We'll just log a message here for testing
    logger.info("This is a placeholder for the rest of disable_monitoring logic")
    logger.info("Cylestio monitoring disabled")

print("Our patched function:")
print(inspect.getsource(patched_disable_monitoring))

# Print instructions
print("\n")
print("To fix the issue:")
print("1. Edit src/cylestio_monitor/monitor.py")
print("2. Modify the disable_monitoring function to add the 'monitor_finish' event")
print("3. The function should look similar to our patched version above")
print("4. This will ensure all agents emit the monitor_finish event") 
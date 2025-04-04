#!/usr/bin/env python
"""
Debug Test Script

This script demonstrates that debug output is properly suppressed when debug_mode is False.
Run this script with no arguments to see no debug output, or with --debug to see debug output.
"""

import logging
import sys
import time
from pathlib import Path
from cylestio_monitor import start_monitoring, stop_monitoring

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug_test")

def main():
    debug_mode = "--debug" in sys.argv
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("Starting debug test script")
    logger.info(f"Debug mode is {'enabled' if debug_mode else 'disabled'}")
    
    # Configure monitoring
    start_monitoring(
        agent_id="debug-test-agent",
        config={
            "events_output_file": "logs/events.json",
            "debug_mode": debug_mode,
            "debug_level": "DEBUG",  # Use highest verbosity for testing
        }
    )
    
    # Perform some actions that would generate debug logging
    logger.info("Performing test actions...")
    time.sleep(1)  # Allow time for any logs to be processed
    
    # Stop monitoring
    stop_monitoring()
    
    logger.info("Test completed")
    logger.info("If debug_mode is False, you should see NO Cylestio SDK debug output above")
    logger.info("If debug_mode is True, you should see Cylestio SDK debug output above")

if __name__ == "__main__":
    main() 
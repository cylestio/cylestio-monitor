#!/usr/bin/env python
"""
Debug Logging Configuration Example

This example demonstrates how to configure the debug logging options
in the Cylestio Monitor SDK using a simple, direct approach.
"""

import logging
import time
from pathlib import Path

from cylestio_monitor import start_monitoring, stop_monitoring

# Set up basic logging for this example
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug_example")


def run_with_no_debug():
    """Run the monitor with debug disabled (default)"""
    logger.info("Starting monitor with debug disabled (default)")
    
    start_monitoring(
        agent_id="example-agent-no-debug",
        config={
            # No debug configuration - debug mode is False by default
            "events_output_file": "logs/event_logs.json"
        }
    )
    
    # Simulate some activity
    logger.info("Agent running without debug output...")
    time.sleep(1)
    
    # Stop monitoring
    stop_monitoring()
    logger.info("Monitor stopped\n")


def run_with_console_debug():
    """Run the monitor with debug to console"""
    logger.info("Starting monitor with debug enabled to console")
    
    start_monitoring(
        agent_id="example-agent-console-debug",
        config={
            "events_output_file": "logs/event_logs.json",
            "debug_mode": True,  # Enable debug output to console
            "debug_level": "DEBUG",  # Optional, sets the verbosity level
        }
    )
    
    # Simulate some activity
    logger.info("Agent running with debug to console...")
    time.sleep(1)
    
    # Stop monitoring
    stop_monitoring()
    logger.info("Monitor stopped\n")


def run_with_file_debug():
    """Run the monitor with debug to file"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    debug_log_path = log_dir / "debug_example.log"
    
    logger.info(f"Starting monitor with debug enabled to file: {debug_log_path}")
    
    start_monitoring(
        agent_id="example-agent-file-debug",
        config={
            "events_output_file": "logs/event_logs.json",
            "debug_mode": True,  # Enable debug output
            "debug_log_file": str(debug_log_path),  # Send to file instead of console
            "debug_level": "DEBUG",  # Optional
        }
    )
    
    # Simulate some activity
    logger.info("Agent running with debug to file...")
    time.sleep(1)
    
    # Stop monitoring
    stop_monitoring()
    logger.info(f"Monitor stopped. Debug logs written to: {debug_log_path}\n")


if __name__ == "__main__":
    logger.info("=== Cylestio Monitor Debug Logging Example ===")
    
    # Example 1: No debug (default behavior)
    run_with_no_debug()
    
    # Example 2: Debug to console
    run_with_console_debug()
    
    # Example 3: Debug to file
    run_with_file_debug()
    
    logger.info("All examples completed!") 
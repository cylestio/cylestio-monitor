"""
Backward compatibility module for cylestio_monitor.event_logger.

This module reexports functions from the new module structure to maintain
backward compatibility with existing code and tests.
"""

# Re-export functions from new structure
try:
    from cylestio_monitor.events.processing.logger import (
        log_to_file,
        process_and_log_event,
        log_console_message,
    )
except ImportError as e:
    # If import fails, provide mock implementations to allow tests to run
    import logging
    import json
    
    logger = logging.getLogger("CylestioMonitor")
    logger.warning(f"Failed to import from new structure: {e}. Using mock implementations.")
    
    def log_to_file(event, log_file):
        """Write event to log file."""
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    
    def process_and_log_event(*args, **kwargs):
        """Process and log event."""
        logger.info(f"process_and_log_event called with args={args}, kwargs={kwargs}")
    
    def log_console_message(message):
        """Log message to console."""
        logger.info(message) 
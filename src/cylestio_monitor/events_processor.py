"""
Backward compatibility module for cylestio_monitor.events_processor.

This module reexports functions from the new module structure to maintain
backward compatibility with existing code and tests.
"""

# Re-export functions from new structure
from cylestio_monitor.events.processing.security import (
    contains_dangerous,
    contains_suspicious,
    normalize_text,
    check_security_concerns,
    mask_sensitive_data,
)
from cylestio_monitor.events.processing.logger import (
    log_event,
    log_to_file,
    process_and_log_event,
    log_console_message,
)

# Define config_manager for patch compatibility
from cylestio_monitor.config import config_manager 
# src/cylestio_monitor/event_logger.py
"""
Event logging module for Cylestio Monitor.

This module handles all actual logging to database and file,
maintaining a single source of truth for all output operations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.db import utils as db_utils

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()

# Console logger for user-facing messages
monitor_logger = logging.getLogger("CylestioMonitor")


def log_to_db(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log an event to the SQLite database.
    
    Args:
        agent_id: The ID of the agent
        event_type: The type of event being logged
        data: Event data dictionary
        channel: Event channel
        level: Log level
        timestamp: Timestamp for the event (defaults to now)
    """
    try:
        # Log to the database using db_utils
        db_utils.log_to_db(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level,
            timestamp=timestamp or datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to log event to database: {e}")
        # Don't re-raise; we want to continue with file logging even if DB fails


def log_to_file(
    record: Dict[str, Any],
    log_file: Optional[str] = None
) -> None:
    """
    Log an event to a JSON file.
    
    Args:
        record: The complete record to log (already formatted)
        log_file: Path to the log file (if None, uses configured log_file)
    """
    # Get log file path from config if not provided
    log_file = log_file or config_manager.get("monitoring.log_file")
    
    if not log_file:
        return
    
    try:
        # Ensure directory exists
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Convert to JSON string and write to file
        msg = json.dumps(record)
        with open(log_file, "a") as f:
            f.write(msg + "\n")
    except Exception as e:
        logger.error(f"Failed to log event to file {log_file}: {e}")
        # Log to console as fallback
        monitor_logger.error(f"Failed to log to file: {e}")


def log_console_message(
    message: str,
    level: str = "info",
    channel: str = "SYSTEM"
) -> None:
    """
    Log a simple message to the console.
    
    Args:
        message: The message to log
        level: Log level
        channel: Channel for extra context
    """
    if level.lower() == "debug":
        monitor_logger.debug(message, extra={"channel": channel})
    elif level.lower() == "warning":
        monitor_logger.warning(message, extra={"channel": channel})
    elif level.lower() == "error":
        monitor_logger.error(message, extra={"channel": channel})
    else:
        monitor_logger.info(message, extra={"channel": channel})


def process_and_log_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    record: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process and log an event to both database and file.
    
    This is the main entry point for all logging operations.
    
    Args:
        agent_id: The ID of the agent
        event_type: The type of event being logged
        data: Event data dictionary
        channel: Event channel
        level: Log level
        record: Optional pre-formatted record (if not provided, just logs data directly)
    """
    # Log a simple console message for user feedback
    log_console_message(f"Event: {event_type}", level, channel)
    
    # Log to database
    if agent_id:
        log_to_db(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level
        )
    
    # Log to file if a record is provided
    if record:
        log_to_file(record) 
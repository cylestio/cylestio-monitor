"""Cylestio Monitor - A monitoring tool for LLM API calls."""

from .events_processor import log_event
from .monitor import cleanup_old_events, disable_monitoring, enable_monitoring, get_database_path, log_to_file_and_db

# Import the db module to make it available
from . import db
from . import event_logger

__version__ = "0.1.2"

__all__ = [
    "enable_monitoring",
    "disable_monitoring",
    "log_event",
    "get_database_path",
    "cleanup_old_events",
    "log_to_file_and_db",
    "db",
    "event_logger",
]

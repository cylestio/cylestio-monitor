"""Cylestio Monitor - A monitoring tool for LLM API calls."""

from .events_processor import log_event
from .monitor import disable_monitoring, enable_monitoring, get_api_endpoint, log_to_file_and_api

# Import the API client module to make it available
from . import api_client
from . import event_logger

__version__ = "0.1.3"

__all__ = [
    "enable_monitoring",
    "disable_monitoring",
    "log_event",
    "get_api_endpoint",
    "log_to_file_and_api",
    "api_client",
    "event_logger",
]

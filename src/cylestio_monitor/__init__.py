"""Cylestio Monitor - A monitoring tool for LLM API calls."""

from .events_processor import log_event
from .monitor import disable_monitoring, enable_monitoring

__version__ = "0.1.0"

__all__ = [
    "enable_monitoring",
    "disable_monitoring",
    "log_event",
]

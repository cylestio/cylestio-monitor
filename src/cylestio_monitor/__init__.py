"""Cylestio Monitor - A monitoring tool for LLM API calls."""

from .monitor import enable_monitoring, disable_monitoring
from .events_processor import log_event

__version__ = "0.1.0"

__all__ = [
    "enable_monitoring",
    "disable_monitoring",
    "log_event",
]
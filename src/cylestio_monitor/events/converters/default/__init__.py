"""
Default event converter.

This module provides a default converter for events that don't have a specific converter.
It handles the basic conversion of events to the standardized schema.
"""

from cylestio_monitor.events.converters.default.converter import DefaultEventConverter

__all__ = ['DefaultEventConverter'] 
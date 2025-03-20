"""
Events package for standardizing and processing telemetry events.

This package contains the standardized event schema and converters for
transforming framework-specific events into a unified format.
"""

# Import for convenience
from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.events.converters import BaseEventConverter, EventConverterFactory

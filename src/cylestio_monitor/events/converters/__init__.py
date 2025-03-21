"""
Event converters for transforming framework-specific events into standardized schema.

This package contains converters for various frameworks (LangChain, LangGraph, etc.)
that transform their specific event formats into a unified standardized schema.
"""

# Import for convenience
from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.converters.factory import EventConverterFactory 
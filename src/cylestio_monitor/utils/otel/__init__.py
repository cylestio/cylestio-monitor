"""
OpenTelemetry utilities for generating trace and span IDs.

This module provides utility functions for generating OpenTelemetry-compliant
trace and span IDs for use in telemetry events.
"""

from cylestio_monitor.utils.otel.generators import (
    generate_trace_id,
    generate_span_id,
    generate_trace_context
)

from cylestio_monitor.utils.otel.context import (
    get_or_create_agent_trace_context,
    create_child_span
)

__all__ = [
    'generate_trace_id',
    'generate_span_id',
    'generate_trace_context',
    'get_or_create_agent_trace_context',
    'create_child_span',
] 
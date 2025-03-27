"""
OpenTelemetry ID generators.

This module provides functions for generating OpenTelemetry-compliant trace and span IDs.
"""

import random
import uuid
from typing import Dict, Optional


def generate_trace_id() -> str:
    """
    Generate an OpenTelemetry-compliant trace ID.

    A trace ID is a 16-byte array (32 hex characters) that is used to uniquely identify
    a trace across different systems.

    Returns:
        A 32-character hex string representing a valid trace ID.
    """
    # Generate a random 16-byte array (as hexadecimal string)
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """
    Generate an OpenTelemetry-compliant span ID.

    A span ID is an 8-byte array (16 hex characters) that is used to uniquely identify
    a span within a trace.

    Returns:
        A 16-character hex string representing a valid span ID.
    """
    # Generate a random 8-byte array (as hexadecimal string)
    return ''.join(f'{random.randint(0, 255):02x}' for _ in range(8))


def generate_trace_context(parent_span_id: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a complete trace context with trace_id, span_id, and optional parent_span_id.

    Args:
        parent_span_id: Optional parent span ID. If provided, the created span will be a child of this span.

    Returns:
        A dictionary containing trace_id, span_id, and optional parent_span_id.
    """
    return {
        "trace_id": generate_trace_id(),
        "span_id": generate_span_id(),
        "parent_span_id": parent_span_id
    } 
"""
Security detection module for Cylestio Monitor.

This package provides security scanning capabilities for all event types in the system,
ensuring comprehensive coverage and thread-safe operation.
"""

from .scanner import SecurityScanner
from .security_schema import (
    SECURITY_ATTRIBUTES,
    ALERT_ATTRIBUTES,
    PROCESS_SECURITY_CATEGORIES,
    SECURITY_RISK_TYPES,
    SECURITY_ALERT_SCHEMA
)

__all__ = [
    "SecurityScanner",
    "SECURITY_ATTRIBUTES",
    "ALERT_ATTRIBUTES",
    "PROCESS_SECURITY_CATEGORIES",
    "SECURITY_RISK_TYPES",
    "SECURITY_ALERT_SCHEMA"
]

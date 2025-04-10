"""
Security detection module for Cylestio Monitor.

This package provides security scanning capabilities for all event types in the system,
ensuring comprehensive coverage and thread-safe operation.
"""

from .scanner import SecurityScanner

__all__ = ["SecurityScanner"] 
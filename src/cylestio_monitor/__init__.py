"""Cylestio Monitor - Simple monitoring for AI agents.

This module provides a simple, framework-agnostic way to monitor AI agents.
It automatically detects available frameworks and sets up appropriate monitoring.
"""

from .monitor import Monitor, init_monitoring

# Create a global monitor instance
monitor = Monitor()

# Clean up the public API
__all__ = ['monitor', 'init_monitoring']

# Optional: package metadata
__version__ = "0.1.0"
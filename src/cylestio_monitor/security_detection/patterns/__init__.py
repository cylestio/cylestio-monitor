"""
Pattern matching module for security detection.

This module provides pattern matching capabilities for security concerns,
with patterns compiled once at load time for performance.
"""

from .matcher import PatternRegistry

__all__ = ["PatternRegistry"] 
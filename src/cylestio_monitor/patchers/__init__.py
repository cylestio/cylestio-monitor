"""Patchers for Cylestio Monitor.

This module provides patchers for different frameworks and libraries.
Each patcher is responsible for monitoring a specific framework or library.
"""

from .base import BasePatcher
from .anthropic import AnthropicPatcher
from .mcp import MCPPatcher

__all__ = [
    'BasePatcher',
    'AnthropicPatcher',
    'MCPPatcher'
]

"""Patchers module for Cylestio Monitor.

This module contains patchers for various frameworks and libraries.
"""

import logging

from . import base
from . import mcp
from . import anthropic
from . import langchain_patcher

# Expose the auto-patching function
from .anthropic import patch_anthropic_module, unpatch_anthropic_module

# Set up module-level logger
logger = logging.getLogger(__name__)

# Try to import LangGraph patcher if available
try:
    from . import langgraph_patcher
    logger.debug("LangGraph patcher imported successfully")
except ImportError:
    logger.debug("LangGraph not available, skipping patcher import")

__all__ = ["patch_anthropic_module", "unpatch_anthropic_module"]

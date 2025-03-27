"""Patchers module for Cylestio Monitor.

This module contains patchers for various frameworks and libraries.
"""

import logging

from . import base
from . import mcp_patcher
from . import anthropic
from . import langchain_patcher

# Expose patcher classes
from .base import BasePatcher
from .anthropic import AnthropicPatcher
from .mcp_patcher import MCPPatcher
from .langchain_patcher import LangChainPatcher

# Expose the patching functions for all supported frameworks
from .mcp_patcher import patch_mcp, unpatch_mcp
from .anthropic import patch_anthropic_module, unpatch_anthropic_module
from .langchain_patcher import patch_langchain, unpatch_langchain

# Set up module-level logger
logger = logging.getLogger(__name__)

# Try to import LangGraph patcher if available
try:
    from . import langgraph_patcher
    from .langgraph_patcher import patch_langgraph, unpatch_langgraph, LangGraphPatcher
    logger.debug("LangGraph patcher imported successfully")
except ImportError:
    logger.debug("LangGraph not available, skipping patcher import")
    # Define empty functions to avoid errors if called
    def patch_langgraph():
        logger.warning("LangGraph is not available, patch_langgraph has no effect")
    
    def unpatch_langgraph():
        logger.warning("LangGraph is not available, unpatch_langgraph has no effect")
    
    # Define a placeholder class
    class LangGraphPatcher(BasePatcher):
        def patch(self):
            logger.warning("LangGraph is not available, patch method has no effect")
        
        def unpatch(self):
            logger.warning("LangGraph is not available, unpatch method has no effect")

# Define what's available via imports
__all__ = [
    # Patcher classes
    "BasePatcher",
    "AnthropicPatcher",
    "MCPPatcher",
    "LangChainPatcher",
    "LangGraphPatcher",
    
    # Patching functions
    "patch_mcp", 
    "unpatch_mcp",
    "patch_anthropic_module", 
    "unpatch_anthropic_module",
    "patch_langchain", 
    "unpatch_langchain",
    "patch_langgraph", 
    "unpatch_langgraph"
]

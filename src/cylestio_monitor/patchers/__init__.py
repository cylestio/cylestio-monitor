"""Patchers module for Cylestio Monitor.

This module contains patchers for various frameworks and libraries.
"""

import logging

from .anthropic import (AnthropicPatcher, patch_anthropic_module,
                        unpatch_anthropic_module)
# Expose patcher classes
from .base import BasePatcher
from .decorated_tools_patcher import (DecoratedToolsPatcher,
                                      patch_decorated_tools,
                                      unpatch_decorated_tools)
from .langchain_callbacks import (ToolMonitorCallbackHandler,
                                  get_callback_handler)
from .langchain_patcher import (LangChainPatcher, patch_langchain,
                                unpatch_langchain)
# Expose the patching functions for all supported frameworks
from .mcp_patcher import patch_mcp, unpatch_mcp
from .openai_patcher import (OpenAIPatcher, patch_openai_module,
                             unpatch_openai_module)
from .tool_decorator_patcher import (ToolDecoratorPatcher,
                                     patch_tool_decorator,
                                     unpatch_tool_decorator)
from .process_patcher import (patch_process_monitoring,
                             unpatch_process_monitoring)
from .network_patcher import (patch_network_monitoring,
                             unpatch_network_monitoring)
from .http_patcher import (patch_http_monitoring,
                          unpatch_http_monitoring)
from .tool_patcher import initialize as initialize_tool_patcher

# Set up module-level logger
logger = logging.getLogger(__name__)

# Try to import LangGraph patcher if available
try:
    from . import langgraph_patcher
    from .langgraph_patcher import (LangGraphPatcher, patch_langgraph,
                                    unpatch_langgraph)

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
    "LangChainPatcher",
    "LangGraphPatcher",
    "OpenAIPatcher",
    "ToolDecoratorPatcher",
    "DecoratedToolsPatcher",
    "ToolMonitorCallbackHandler",
    # Functions
    "get_callback_handler",
    "initialize_tool_patcher",
    # Patching functions
    "patch_mcp",
    "unpatch_mcp",
    "patch_anthropic_module",
    "unpatch_anthropic_module",
    "patch_langchain",
    "unpatch_langchain",
    "patch_langgraph",
    "unpatch_langgraph",
    "patch_openai_module",
    "unpatch_openai_module",
    "patch_tool_decorator",
    "unpatch_tool_decorator",
    "patch_decorated_tools",
    "unpatch_decorated_tools",
    "patch_process_monitoring",
    "unpatch_process_monitoring",
    "patch_network_monitoring",
    "unpatch_network_monitoring",
    "patch_http_monitoring",
    "unpatch_http_monitoring"
]

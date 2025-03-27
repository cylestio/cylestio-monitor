"""MCP patcher for monitoring MCP client calls."""

import functools
import logging
import time
from typing import Any, Dict, Optional

from ..utils.trace_context import TraceContext
from ..utils.event_logging import log_event
from .base import BasePatcher


class MCPPatcher(BasePatcher):
    """Patcher for monitoring MCP client calls."""

    def __init__(self, client=None, config: Optional[Dict[str, Any]] = None):
        """Initialize MCP patcher.

        Args:
            client: Optional MCP client instance to patch
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.client = client
        self.original_funcs = {}
        self.logger = logging.getLogger("CylestioMonitor.MCP")

    def patch(self) -> None:
        """Apply patches to MCP client."""
        if not self.client:
            self.logger.warning("No MCP client provided, skipping patch")
            return

        self.logger.info("Applying MCP monitoring patches")

        # Patch list_tools
        original_list_tools = self.client.list_tools
        self.original_funcs["list_tools"] = original_list_tools

        @functools.wraps(original_list_tools)
        async def wrapped_list_tools(*args, **kwargs):
            # Log request
            log_event(
                name="mcp.request", 
                attributes={"method": "list_tools", "args": str(args), "kwargs": kwargs}
            )

            try:
                # Call original function
                result = await original_list_tools(*args, **kwargs)

                # Log response
                log_event(
                    name="mcp.response",
                    attributes={
                        "method": "list_tools",
                        "response": {"tools": [t.model_dump() for t in result.tools]},
                    }
                )

                return result

            except Exception as e:
                # Log error
                log_event(
                    name="mcp.error", 
                    attributes={"method": "list_tools", "error": str(e)}, 
                    level="ERROR"
                )
                raise

        self.client.list_tools = wrapped_list_tools

        # Patch call_tool
        if hasattr(self.client, "call_tool"):
            original_call_tool = self.client.call_tool
            self.original_funcs["call_tool"] = original_call_tool

            @functools.wraps(original_call_tool)
            async def wrapped_call_tool(tool_name, tool_args, *args, **kwargs):
                """Wrapped call_tool with monitoring."""
                # Log the call start
                start_time = time.time()
                log_event(
                    name="mcp.call.start",
                    attributes={
                        "method": "call_tool",
                        "tool": tool_name,
                        "args": str(tool_args),
                        "kwargs": str(kwargs),
                    }
                )

                # Call the original method
                try:
                    result = await original_call_tool(tool_name, tool_args, *args, **kwargs)

                    # Log the call finish
                    duration = time.time() - start_time
                    log_event(
                        name="mcp.call.finish",
                        attributes={
                            "method": "call_tool",
                            "tool": tool_name,
                            "duration": duration,
                            "result": str(result),
                        }
                    )

                    return result
                except Exception as e:
                    # Log the error
                    log_event(
                        name="mcp.call.error",
                        attributes={"method": "call_tool", "tool": tool_name, "error": str(e)},
                        level="ERROR"
                    )
                    raise

            self.client.call_tool = wrapped_call_tool

        # Patch get_completion
        if hasattr(self.client, "get_completion"):
            original_get_completion = self.client.get_completion
            self.original_funcs["get_completion"] = original_get_completion

            @functools.wraps(original_get_completion)
            async def wrapped_get_completion(context, *args, **kwargs):
                """Wrapped get_completion with monitoring."""
                # Log the call start
                start_time = time.time()
                log_event(
                    name="mcp.call.start",
                    attributes={
                        "method": "get_completion",
                        "context": str(context),
                        "args": str(args),
                        "kwargs": str(kwargs),
                    }
                )

                # Call the original method
                try:
                    result = await original_get_completion(context, *args, **kwargs)

                    # Log the call finish
                    duration = time.time() - start_time
                    log_event(
                        name="mcp.call.finish",
                        attributes={
                            "method": "get_completion", 
                            "duration": duration, 
                            "result": str(result)
                        }
                    )

                    return result
                except Exception as e:
                    # Log the error
                    log_event(
                        name="mcp.call.error", 
                        attributes={"method": "get_completion", "error": str(e)},
                        level="ERROR"
                    )
                    raise

            self.client.get_completion = wrapped_get_completion

        self.is_patched = True
        self.logger.info("Applied MCP monitoring patches")

    def unpatch(self) -> None:
        """Remove monitoring patches from MCP client."""
        if not self.is_patched:
            return

        # Restore original functions
        for name, func in self.original_funcs.items():
            setattr(self.client, name, func)
        self.original_funcs.clear()

        self.is_patched = False
        self.logger.info("Removed MCP monitoring patches")


def patch_mcp():
    """Patch MCP for monitoring.
    
    This function applies global patching to the MCP module to intercept all
    ClientSession instances created after this function is called.
    """
    logger = logging.getLogger("CylestioMonitor.MCP")
    
    try:
        # Import MCP and related classes
        from mcp import ClientSession
        
        # Store original methods for restoration
        original_init = ClientSession.__init__
        
        # Define patched initialization method
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            # Call original init first
            original_init(self, *args, **kwargs)
            
            # Then patch this instance
            logger.debug(f"Auto-patching new MCP ClientSession instance")
            patcher = MCPPatcher(client=self)
            patcher.patch()
        
        # Apply the patch
        ClientSession.__init__ = patched_init
        
        logger.info("Applied global MCP module patches")
        
    except ImportError:
        logger.warning("MCP module not found. MCP monitoring not enabled.")
    except Exception as e:
        logger.error(f"Error patching MCP: {e}")


def unpatch_mcp():
    """Remove MCP monitoring patches.
    
    This function removes the global patching applied to the MCP module.
    """
    logger = logging.getLogger("CylestioMonitor.MCP")
    
    try:
        # Import MCP and restore original methods
        from mcp import ClientSession
        
        # Check if we have access to the original method
        if hasattr(ClientSession.__init__, "__wrapped__"):
            ClientSession.__init__ = ClientSession.__init__.__wrapped__
            logger.info("Removed global MCP module patches")
        else:
            logger.warning("Could not restore original MCP ClientSession.__init__")
        
    except ImportError:
        logger.debug("MCP module not found during unpatch")
    except Exception as e:
        logger.error(f"Error unpatching MCP: {e}")

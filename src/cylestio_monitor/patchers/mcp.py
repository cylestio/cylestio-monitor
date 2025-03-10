"""MCP patcher for monitoring MCP client calls."""

import functools
import logging
import time
from typing import Any, Dict, Optional

from ..events_processor import log_event
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
                "mcp_request", {"method": "list_tools", "args": str(args), "kwargs": kwargs}, "MCP"
            )

            try:
                # Call original function
                result = await original_list_tools(*args, **kwargs)

                # Log response
                log_event(
                    "mcp_response",
                    {
                        "method": "list_tools",
                        "response": {"tools": [t.model_dump() for t in result.tools]},
                    },
                    "MCP",
                )

                return result

            except Exception as e:
                # Log error
                log_event(
                    "mcp_error", {"method": "list_tools", "error": str(e)}, "MCP", level="error"
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
                    "call_start",
                    {
                        "method": "call_tool",
                        "tool": tool_name,
                        "args": str(tool_args),
                        "kwargs": str(kwargs),
                    },
                    "MCP",
                )

                # Call the original method
                try:
                    result = await original_call_tool(tool_name, tool_args, *args, **kwargs)

                    # Log the call finish
                    duration = time.time() - start_time
                    log_event(
                        "call_finish",
                        {
                            "method": "call_tool",
                            "tool": tool_name,
                            "duration": duration,
                            "result": str(result),
                        },
                        "MCP",
                    )

                    return result
                except Exception as e:
                    # Log the error
                    log_event(
                        "call_error",
                        {"method": "call_tool", "tool": tool_name, "error": str(e)},
                        "MCP",
                        "error",
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
                    "call_start",
                    {
                        "method": "get_completion",
                        "context": str(context),
                        "args": str(args),
                        "kwargs": str(kwargs),
                    },
                    "MCP",
                )

                # Call the original method
                try:
                    result = await original_get_completion(context, *args, **kwargs)

                    # Log the call finish
                    duration = time.time() - start_time
                    log_event(
                        "call_finish",
                        {"method": "get_completion", "duration": duration, "result": str(result)},
                        "MCP",
                    )

                    return result
                except Exception as e:
                    # Log the error
                    log_event(
                        "call_error", {"method": "get_completion", "error": str(e)}, "MCP", "error"
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

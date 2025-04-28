#!/usr/bin/env python3
"""
Patch Fix for MCP Tool Monitoring

This script applies a fix for MCP tool monitoring that handles the parameter name change
in MCP 1.6.0 from 'params' to 'arguments'.
"""

import inspect
import logging
from typing import Any, Dict, Optional
from mcp import ClientSession
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.trace_context import TraceContext

logger = logging.getLogger("PatchFix")

# Store the original method
original_call_tool = ClientSession.call_tool

def apply_fix():
    """Apply the fix for MCP tool monitoring."""
    # Check the signature of call_tool to determine parameter names
    signature = inspect.signature(original_call_tool)
    param_names = list(signature.parameters.keys())
    
    # Determine if we're using 'params' (older MCP) or 'arguments' (newer MCP 1.6.0+)
    uses_arguments = 'arguments' in param_names
    param_name = 'arguments' if uses_arguments else 'params'
    
    print(f"Detected MCP ClientSession.call_tool using parameter name: {param_name}")

    # Define the patched async method wrapper with the correct signature
    async def instrumented_call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None):
        """Instrumented version of ClientSession.call_tool."""
        # Start a new span for this tool call
        span_info = TraceContext.start_span(f"tool.{name}")
        
        # Extract relevant attributes
        tool_attributes = {
            "tool.name": name,
            "tool.id": str(id(self)),
            "framework.name": "mcp",
            "framework.type": "tool",
        }

        # Capture parameters (safely)
        if arguments:
            if isinstance(arguments, dict):
                tool_attributes["tool.params"] = list(arguments.keys())
            else:
                tool_attributes["tool.params.type"] = type(arguments).__name__

        # Log tool execution start event
        log_event(name="tool.execution", attributes=tool_attributes)

        try:
            # Call the original method with the same parameters
            result = await original_call_tool(self, name, arguments)

            # Prepare result attributes
            result_attributes = tool_attributes.copy()
            result_attributes.update(
                {
                    "tool.status": "success",
                }
            )

            # Process the result
            if result is not None:
                result_attributes["tool.result.type"] = type(result).__name__

                # For dict results, include keys but not values
                if hasattr(result, "content") and isinstance(
                    result.content, dict
                ):
                    result_attributes["tool.result.keys"] = list(
                        result.content.keys()
                    )

            # Log tool result event
            log_event(name="tool.result", attributes=result_attributes)

            return result
        except Exception as e:
            # Log tool error event
            log_error(name="tool.error", error=e, attributes=tool_attributes)
            raise
        finally:
            # End the span
            TraceContext.end_span()

    # Apply the patch to the ClientSession class
    ClientSession.call_tool = instrumented_call_tool
    print("Successfully applied MCP patch fix")

if __name__ == "__main__":
    apply_fix() 
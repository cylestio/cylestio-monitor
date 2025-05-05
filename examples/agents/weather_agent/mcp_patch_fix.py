#!/usr/bin/env python3
"""
Custom MCP Patching for Weather Agent Example

This script provides a custom patch to fix the compatibility issue with 
cylestio_monitor.patchers.mcp_patcher that's failing with:
'log_event() got an unexpected keyword argument 'agent_id''
"""

import logging
import inspect
from typing import Any, Dict, Optional
from mcp import ClientSession
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.trace_context import TraceContext

logger = logging.getLogger("MCP-CustomPatch")

# Store the original method
original_call_tool = ClientSession.call_tool

def apply_custom_mcp_patch():
    """Apply a custom MCP patch that works around the agent_id issue."""
    # Check the signature of call_tool to determine parameter names
    signature = inspect.signature(original_call_tool)
    param_names = list(signature.parameters.keys())
    
    # Determine if we're using 'params' (older MCP) or 'arguments' (newer MCP 1.6.0+)
    uses_arguments = 'arguments' in param_names
    param_name = 'arguments' if uses_arguments else 'params'
    
    print(f"Detected MCP ClientSession.call_tool using parameter name: {param_name}")

    # Define the patched async method wrapper that matches the original method signature
    if uses_arguments:
        async def instrumented_call_tool(self, name, arguments=None):
            """Instrumented version of ClientSession.call_tool for MCP 1.6.0+."""
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

            # Log tool execution start event - don't pass agent_id
            try:
                log_event(name="tool.execution", attributes=tool_attributes)
            except Exception as e:
                print(f"Warning: Failed to log tool execution: {e}")

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

                # Log tool result event - don't pass agent_id
                try:
                    log_event(name="tool.result", attributes=result_attributes)
                except Exception as e:
                    print(f"Warning: Failed to log tool result: {e}")

                return result
            except Exception as e:
                # Log tool error event - don't pass agent_id
                try:
                    log_error(name="tool.error", error=e, attributes=tool_attributes)
                except Exception as log_e:
                    print(f"Warning: Failed to log tool error: {log_e}")
                raise
            finally:
                # End the span
                TraceContext.end_span()
    else:
        async def instrumented_call_tool(self, name, params=None):
            """Instrumented version of ClientSession.call_tool for older MCP."""
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
            if params:
                if isinstance(params, dict):
                    tool_attributes["tool.params"] = list(params.keys())
                else:
                    tool_attributes["tool.params.type"] = type(params).__name__

            # Log tool execution start event - don't pass agent_id
            try:
                log_event(name="tool.execution", attributes=tool_attributes)
            except Exception as e:
                print(f"Warning: Failed to log tool execution: {e}")

            try:
                # Call the original method with the same parameters
                result = await original_call_tool(self, name, params)

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

                # Log tool result event - don't pass agent_id
                try:
                    log_event(name="tool.result", attributes=result_attributes)
                except Exception as e:
                    print(f"Warning: Failed to log tool result: {e}")

                return result
            except Exception as e:
                # Log tool error event - don't pass agent_id
                try:
                    log_error(name="tool.error", error=e, attributes=tool_attributes)
                except Exception as log_e:
                    print(f"Warning: Failed to log tool error: {log_e}")
                raise
            finally:
                # End the span
                TraceContext.end_span()

    # Apply the patch to the ClientSession class
    ClientSession.call_tool = instrumented_call_tool
    print("Successfully applied custom MCP patch")

if __name__ == "__main__":
    apply_custom_mcp_patch() 
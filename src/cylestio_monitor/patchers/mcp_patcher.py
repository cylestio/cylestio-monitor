"""
MCP Protocol Patcher for Telemetry Integration.

This module provides patchers for the MCP (Machine Conversation Protocol) to 
instrument it for telemetry data collection.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union, Type

from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.patchers.base import BasePatcher

logger = logging.getLogger("CylestioMonitor")


class MCPPatcher(BasePatcher):
    """Patcher for MCP Protocol."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCP patcher."""
        super().__init__(config)
        self._patched = False
        self._original_methods = {}  # Keep track of original methods
        
    def patch(self) -> None:
        """Apply the MCP patches.
        
        Raises:
            ImportError: If MCP is not available
            RuntimeError: If patching fails
        """
        if self._patched:
            logger.warning("MCP is already patched")
            return
        
        try:
            # Log patch event
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "mcp",
                    "patch.type": "monkey_patch",
                    "patch.components": ["client", "tool_calls"]
                }
            )
            
            # Apply patches
            self._patch_client()
            self._patch_tool_calls()
            
            self._patched = True
            logger.info("Successfully patched MCP")
        except ImportError as e:
            logger.warning(f"Failed to patch MCP: {e}")
            raise
        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={
                    "framework.name": "mcp"
                }
            )
            logger.exception(f"Error patching MCP: {e}")
            raise RuntimeError(f"Failed to patch MCP: {e}")
    
    def unpatch(self) -> None:
        """Remove the MCP patches.
        
        Raises:
            RuntimeError: If unpatching fails
        """
        if not self._patched:
            logger.warning("MCP is not patched")
            return
        
        try:
            # Restore the original methods from the dictionary
            for method_name, original_method in self._original_methods.items():
                if method_name == "call_tool":
                    try:
                        # Import here to avoid dependency issues
                        import mcp
                        from mcp import ClientSession
                        
                        # Restore the original method
                        ClientSession.call_tool = original_method
                        logger.debug("Restored ClientSession.call_tool")
                    except ImportError:
                        logger.debug("Could not restore ClientSession.call_tool - module not found")
                        
            # Log unpatch event
            log_event(
                name="framework.unpatch",
                attributes={
                    "framework.name": "mcp"
                }
            )
            
            self._patched = False
            logger.info("Successfully unpatched MCP")
        except Exception as e:
            logger.exception(f"Error unpatching MCP: {e}")
            raise RuntimeError(f"Failed to unpatch MCP: {e}")
    
    def _patch_client(self) -> None:
        """Patch MCP client."""
        try:
            # Note that this function is a fallback and may not be used
            # The actual ClientSession patching happens in _patch_tool_calls
            logger.debug("Attempting to patch MCP client elements")
            logger.debug("This is a fallback mechanism and may not be needed for MCP monitoring")
            
            # No need to raise exceptions if we can't find the class
            # We'll focus on the ClientSession patching instead
        except Exception as e:
            logger.debug(f"Client patching skipped: {e}")
    
    def _patch_tool_calls(self) -> None:
        """Patch MCP tool calls."""
        try:
            # Import here to avoid dependency if not used
            import mcp
            # ClientSession is a top-level class in MCP module
            from mcp import ClientSession
            
            # Check if we can access ClientSession.call_tool
            if not hasattr(ClientSession, "call_tool"):
                logger.warning("Could not find ClientSession.call_tool method")
                return
                
            # Store the original method
            original_call_tool = ClientSession.call_tool
            self._original_methods["call_tool"] = original_call_tool
            
            # Define the patched async method wrapper
            async def instrumented_call_tool(self, name, params=None, *args, **kwargs):
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
                if params:
                    if isinstance(params, dict):
                        tool_attributes["tool.params"] = list(params.keys())
                    else:
                        tool_attributes["tool.params.type"] = type(params).__name__
                
                # Log tool execution start event
                log_event(
                    name="tool.execution",
                    attributes=tool_attributes
                )
                
                try:
                    # Call the original method
                    result = await original_call_tool(self, name, params, *args, **kwargs)
                    
                    # Prepare result attributes
                    result_attributes = tool_attributes.copy()
                    result_attributes.update({
                        "tool.status": "success",
                    })
                    
                    # Process the result
                    if result is not None:
                        result_attributes["tool.result.type"] = type(result).__name__
                        
                        # For dict results, include keys but not values
                        if hasattr(result, "content") and isinstance(result.content, dict):
                            result_attributes["tool.result.keys"] = list(result.content.keys())
                    
                    # Log tool result event
                    log_event(
                        name="tool.result",
                        attributes=result_attributes
                    )
                    
                    return result
                except Exception as e:
                    # Log tool error event
                    log_error(
                        name="tool.error",
                        error=e,
                        attributes=tool_attributes
                    )
                    raise
                finally:
                    # End the span
                    TraceContext.end_span()
            
            # Apply the patch to the ClientSession class
            logger.debug(f"Patching ClientSession.call_tool (async method)")
            ClientSession.call_tool = instrumented_call_tool
            logger.info("Successfully patched MCP ClientSession.call_tool")
            
        except ImportError as e:
            logger.debug(f"MCP ClientSession not available: {e}")
            raise ImportError(f"MCP ClientSession not available: {e}")
        except Exception as e:
            logger.warning(f"Error patching MCP tool calls: {e}")
            raise

# Global instance for module-level patching
_mcp_patcher = None

def patch_mcp():
    """Apply MCP patches globally."""
    global _mcp_patcher
    
    if _mcp_patcher is None:
        logger.info("Initializing global MCP patcher")
        _mcp_patcher = MCPPatcher()
    
    try:
        _mcp_patcher.patch()
        logger.info("MCP patched successfully")
        return True
    except ImportError:
        logger.warning("MCP not available, skipping patch")
        return False
    except Exception as e:
        logger.error(f"Error patching MCP: {e}")
        return False

def unpatch_mcp():
    """Remove MCP patches globally."""
    global _mcp_patcher
    
    if _mcp_patcher is not None and _mcp_patcher._patched:
        try:
            _mcp_patcher.unpatch()
            logger.info("MCP unpatched successfully")
            return True
        except Exception as e:
            logger.error(f"Error unpatching MCP: {e}")
            return False
    return False

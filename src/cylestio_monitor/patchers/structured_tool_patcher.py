"""StructuredTool Patcher for Cylestio Monitor.

This module provides patching functionality for LangChain's StructuredTool class (created by @tool decorator),
allowing comprehensive monitoring of tool executions in LangChain agents.
"""

import logging
import functools
import time
from typing import Any, Dict, List, Optional, Union, Callable

from cylestio_monitor.patchers.base import BasePatcher
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.serialization import safe_event_serialize

logger = logging.getLogger("CylestioMonitor")

# Use a global flag to track patching state
_STRUCTURED_TOOL_PATCHED = False
_ORIGINAL_CALLS = {}


class StructuredToolPatcher(BasePatcher):
    """Patcher for LangChain StructuredTool class."""

    def __init__(self):
        """Initialize the StructuredTool patcher."""
        super().__init__("langchain_structured_tool")

    def apply(self) -> bool:
        """Apply the patches for StructuredTool class.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _STRUCTURED_TOOL_PATCHED, _ORIGINAL_CALLS
        
        if _STRUCTURED_TOOL_PATCHED:
            logger.warning("LangChain StructuredTool already patched")
            return False

        try:
            # Log patch attempt
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "langchain_structured_tool",
                    "patch.type": "method_wrapper",
                    "patch.components": ["StructuredTool.__call__"]
                }
            )

            # Try to patch StructuredTool
            patched = self._patch_structured_tool()
            
            if patched:
                _STRUCTURED_TOOL_PATCHED = True
                logger.info("Successfully patched LangChain StructuredTool")
                return True
            else:
                logger.warning("Failed to patch LangChain StructuredTool")
                return False

        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={
                    "framework.name": "langchain_structured_tool"
                }
            )
            logger.exception(f"Error patching LangChain StructuredTool: {e}")
            return False
            
    def patch(self) -> bool:
        """Apply patches (implementation of abstract method).
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.apply()
        
    def detect(self) -> bool:
        """Detect if LangChain's StructuredTool is available.
        
        Returns:
            bool: True if StructuredTool is available, False otherwise
        """
        try:
            try:
                from langchain.tools import StructuredTool
                return True
            except ImportError:
                try:
                    from langchain_core.tools import StructuredTool
                    return True
                except ImportError:
                    return False
        except Exception:
            return False

    def _patch_structured_tool(self) -> bool:
        """Patch the StructuredTool class.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _ORIGINAL_CALLS
        patched_classes = []
        
        try:
            # Try to import StructuredTool from different possible locations
            structured_tool_classes = []
            
            try:
                from langchain.tools import StructuredTool
                structured_tool_classes.append(("langchain.tools.StructuredTool", StructuredTool))
            except ImportError:
                pass
                
            try:
                from langchain_core.tools import StructuredTool as CoreStructuredTool
                structured_tool_classes.append(("langchain_core.tools.StructuredTool", CoreStructuredTool))
            except ImportError:
                pass
                
            if not structured_tool_classes:
                logger.warning("Unable to import StructuredTool from any known location")
                return False
                
            # Patch each implementation of StructuredTool
            for class_name, cls in structured_tool_classes:
                # Store original __call__ method
                _ORIGINAL_CALLS[class_name] = cls.__call__
                
                @functools.wraps(cls.__call__)
                def patched_call(self, *args, **kwargs):
                    # Get the original method for this class
                    original_call = _ORIGINAL_CALLS.get(class_name)
                    if not original_call:
                        # Fallback if original not found
                        return self.__call__(*args, **kwargs)
                        
                    # Generate a span ID for this tool execution
                    tool_name = getattr(self, "name", "unknown_tool")
                    span_id = TraceContext.start_span(f"tool.{tool_name}")
                    start_time = time.time()
                    
                    # Get current trace context
                    context = TraceContext.get_current_context()
                    trace_id = context.get("trace_id")
                    parent_span_id = context.get("span_id")
                    
                    # Parse inputs - combine args and kwargs for logging
                    tool_inputs = kwargs
                    if args and len(args) > 0:
                        # If positional args are used, add them to inputs
                        for i, arg in enumerate(args):
                            tool_inputs[f"arg_{i}"] = arg
                    
                    # Extract tool metadata
                    tool_description = getattr(self, "description", None)
                    
                    # Log tool execution start
                    log_event(
                        name="tool.execution.start",
                        attributes={
                            "tool.name": tool_name,
                            "tool.inputs": safe_event_serialize(tool_inputs),
                            "tool.description": tool_description,
                            "framework.name": "langchain",
                            "framework.type": "structured_tool"
                        },
                        level="INFO",
                        span_id=span_id,
                        trace_id=trace_id,
                        parent_span_id=parent_span_id
                    )
                    
                    try:
                        # Execute the original method
                        result = original_call(self, *args, **kwargs)
                        
                        # Calculate duration
                        duration = time.time() - start_time
                        
                        # Log tool execution end
                        log_event(
                            name="tool.execution.end",
                            attributes={
                                "tool.name": tool_name,
                                "tool.outputs": safe_event_serialize(result),
                                "tool.duration": duration,
                                "tool.success": True,
                                "framework.name": "langchain",
                                "framework.type": "structured_tool"
                            },
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            parent_span_id=parent_span_id
                        )
                        
                        return result
                        
                    except Exception as e:
                        # Calculate duration
                        duration = time.time() - start_time
                        
                        # Log tool execution error
                        log_event(
                            name="tool.execution.error",
                            attributes={
                                "tool.name": tool_name,
                                "tool.error": str(e),
                                "tool.error_type": e.__class__.__name__,
                                "tool.duration": duration,
                                "tool.success": False,
                                "framework.name": "langchain",
                                "framework.type": "structured_tool"
                            },
                            level="ERROR",
                            span_id=span_id,
                            trace_id=trace_id,
                            parent_span_id=parent_span_id
                        )
                        
                        # Re-raise the exception
                        raise
                    finally:
                        # End the span
                        TraceContext.end_span()
                
                # Apply the patch
                cls.__call__ = patched_call
                patched_classes.append(class_name)
            
            if patched_classes:
                logger.debug(f"Successfully patched StructuredTool classes: {', '.join(patched_classes)}")
                return True
            else:
                return False
            
        except ImportError:
            logger.debug("StructuredTool not available, skipping patch")
            return False
        except Exception as e:
            logger.warning(f"Error patching StructuredTool: {e}")
            return False

    def unpatch(self) -> bool:
        """Remove the patches.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _STRUCTURED_TOOL_PATCHED, _ORIGINAL_CALLS
        
        if not _STRUCTURED_TOOL_PATCHED:
            logger.warning("LangChain StructuredTool is not patched")
            return False
            
        try:
            # Restore original methods
            for class_name, original_call in _ORIGINAL_CALLS.items():
                # Find the class to unpatch
                if "langchain.tools" in class_name:
                    try:
                        from langchain.tools import StructuredTool
                        StructuredTool.__call__ = original_call
                    except ImportError:
                        pass
                elif "langchain_core.tools" in class_name:
                    try:
                        from langchain_core.tools import StructuredTool
                        StructuredTool.__call__ = original_call
                    except ImportError:
                        pass
                    
            # Reset state
            _STRUCTURED_TOOL_PATCHED = False
            _ORIGINAL_CALLS = {}
            
            logger.info("Successfully unpatched LangChain StructuredTool")
            return True
            
        except Exception as e:
            logger.warning(f"Error unpatching LangChain StructuredTool: {e}")
            return False


def patch_structured_tool():
    """Patch the LangChain StructuredTool class."""
    patcher = StructuredToolPatcher()
    return patcher.apply()


def unpatch_structured_tool():
    """Unpatch the LangChain StructuredTool class."""
    patcher = StructuredToolPatcher()
    return patcher.unpatch() 
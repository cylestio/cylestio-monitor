"""Base Tool Patcher for Cylestio Monitor.

This module provides patching functionality for LangChain's BaseTool class,
allowing comprehensive monitoring of tool executions in the customer support bot.
"""

import logging
import functools
import time
from typing import Any, Callable, Dict, Optional, Union

from cylestio_monitor.patchers.base import BasePatcher
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.serialization import safe_event_serialize

logger = logging.getLogger("CylestioMonitor")

# Use a global flag to track patching state
_BASE_TOOL_PATCHED = False
_ORIGINAL_INVOKE = None
_ORIGINAL_AINVOKE = None


class BaseToolPatcher(BasePatcher):
    """Patcher for LangChain BaseTool class."""

    def __init__(self):
        """Initialize the BaseTool patcher."""
        super().__init__("langchain_base_tool")

    def apply(self) -> bool:
        """Apply the patches for BaseTool class.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _BASE_TOOL_PATCHED, _ORIGINAL_INVOKE, _ORIGINAL_AINVOKE
        
        if _BASE_TOOL_PATCHED:
            logger.warning("LangChain BaseTool already patched")
            return False

        try:
            # Log patch attempt
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "langchain_base_tool",
                    "patch.type": "method_wrapper",
                    "patch.components": ["BaseTool.invoke", "BaseTool.ainvoke"]
                }
            )

            # Try to patch BaseTool
            patched = self._patch_base_tool()
            
            if patched:
                _BASE_TOOL_PATCHED = True
                logger.info("Successfully patched LangChain BaseTool")
                return True
            else:
                logger.warning("Failed to patch LangChain BaseTool")
                return False

        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={
                    "framework.name": "langchain_base_tool"
                }
            )
            logger.exception(f"Error patching LangChain BaseTool: {e}")
            return False
            
    def patch(self) -> bool:
        """Apply patches (implementation of abstract method).
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.apply()
        
    def detect(self) -> bool:
        """Detect if LangChain's BaseTool is available.
        
        Returns:
            bool: True if BaseTool is available, False otherwise
        """
        try:
            # Try to import BaseTool from different possible locations
            try:
                from langchain.tools import BaseTool
                return True
            except ImportError:
                try:
                    from langchain.tools.base import BaseTool
                    return True
                except ImportError:
                    try:
                        from langchain_core.tools import BaseTool
                        return True
                    except ImportError:
                        return False
        except Exception:
            return False

    def _patch_base_tool(self) -> bool:
        """Patch the BaseTool class.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _ORIGINAL_INVOKE, _ORIGINAL_AINVOKE
        
        try:
            # Try to import BaseTool from different possible locations
            try:
                from langchain.tools import BaseTool
            except ImportError:
                try:
                    from langchain.tools.base import BaseTool
                except ImportError:
                    try:
                        from langchain_core.tools import BaseTool
                    except ImportError:
                        logger.warning("Unable to import BaseTool from any known location")
                        return False

            # Store original methods
            _ORIGINAL_INVOKE = BaseTool.invoke
            _ORIGINAL_AINVOKE = BaseTool.ainvoke

            # Create patched invoke method
            @functools.wraps(BaseTool.invoke)
            def patched_invoke(self, input, config=None, **kwargs):
                # Generate a span ID for this tool execution
                span_id = TraceContext.start_span(f"tool.{self.name}")
                start_time = time.time()
                
                # Get current trace context
                context = TraceContext.get_current_context()
                trace_id = context.get("trace_id")
                parent_span_id = context.get("span_id")
                
                # Log tool execution start
                log_event(
                    name="tool.execution.start",
                    attributes={
                        "tool.name": self.name,
                        "tool.inputs": safe_event_serialize(input),
                        "tool.description": getattr(self, "description", None),
                        "framework.name": "langchain",
                        "framework.type": "base_tool"
                    },
                    level="INFO",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )
                
                try:
                    # Execute the original method
                    result = _ORIGINAL_INVOKE(self, input, config, **kwargs)
                    
                    # Calculate duration
                    duration = time.time() - start_time
                    
                    # Log tool execution end
                    log_event(
                        name="tool.execution.end",
                        attributes={
                            "tool.name": self.name,
                            "tool.outputs": safe_event_serialize(result),
                            "tool.duration": duration,
                            "tool.success": True,
                            "framework.name": "langchain",
                            "framework.type": "base_tool"
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
                            "tool.name": self.name,
                            "tool.error": str(e),
                            "tool.error_type": e.__class__.__name__,
                            "tool.duration": duration,
                            "tool.success": False,
                            "framework.name": "langchain",
                            "framework.type": "base_tool"
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

            # Create patched async method
            @functools.wraps(BaseTool.ainvoke)
            async def patched_ainvoke(self, input, config=None, **kwargs):
                # Generate a span ID for this tool execution
                span_id = TraceContext.start_span(f"tool.{self.name}")
                start_time = time.time()
                
                # Get current trace context
                context = TraceContext.get_current_context()
                trace_id = context.get("trace_id")
                parent_span_id = context.get("span_id")
                
                # Log tool execution start
                log_event(
                    name="tool.execution.start",
                    attributes={
                        "tool.name": self.name,
                        "tool.inputs": safe_event_serialize(input),
                        "tool.description": getattr(self, "description", None),
                        "framework.name": "langchain",
                        "framework.type": "base_tool_async"
                    },
                    level="INFO",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )
                
                try:
                    # Execute the original method
                    result = await _ORIGINAL_AINVOKE(self, input, config, **kwargs)
                    
                    # Calculate duration
                    duration = time.time() - start_time
                    
                    # Log tool execution end
                    log_event(
                        name="tool.execution.end",
                        attributes={
                            "tool.name": self.name,
                            "tool.outputs": safe_event_serialize(result),
                            "tool.duration": duration,
                            "tool.success": True,
                            "framework.name": "langchain",
                            "framework.type": "base_tool_async"
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
                            "tool.name": self.name,
                            "tool.error": str(e),
                            "tool.error_type": e.__class__.__name__,
                            "tool.duration": duration,
                            "tool.success": False,
                            "framework.name": "langchain",
                            "framework.type": "base_tool_async"
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

            # Apply patches
            BaseTool.invoke = patched_invoke
            BaseTool.ainvoke = patched_ainvoke
            
            logger.debug("Successfully patched BaseTool.invoke and BaseTool.ainvoke methods")
            return True
            
        except ImportError:
            logger.debug("BaseTool not available, skipping patch")
            return False
        except Exception as e:
            logger.warning(f"Error patching BaseTool: {e}")
            return False

    def unpatch(self) -> bool:
        """Remove the patches.
        
        Returns:
            bool: True if successful, False otherwise
        """
        global _BASE_TOOL_PATCHED, _ORIGINAL_INVOKE, _ORIGINAL_AINVOKE
        
        if not _BASE_TOOL_PATCHED:
            logger.warning("LangChain BaseTool is not patched")
            return False
            
        try:
            # Try to import BaseTool
            try:
                from langchain.tools import BaseTool
            except ImportError:
                try:
                    from langchain.tools.base import BaseTool
                except ImportError:
                    try:
                        from langchain_core.tools import BaseTool
                    except ImportError:
                        logger.warning("Unable to import BaseTool for unpatching")
                        return False
            
            # Restore original methods
            if _ORIGINAL_INVOKE:
                BaseTool.invoke = _ORIGINAL_INVOKE
                
            if _ORIGINAL_AINVOKE:
                BaseTool.ainvoke = _ORIGINAL_AINVOKE
                
            _BASE_TOOL_PATCHED = False
            _ORIGINAL_INVOKE = None
            _ORIGINAL_AINVOKE = None
            
            logger.info("Successfully unpatched LangChain BaseTool")
            return True
            
        except Exception as e:
            logger.warning(f"Error unpatching LangChain BaseTool: {e}")
            return False


def patch_base_tool():
    """Patch the LangChain BaseTool class."""
    patcher = BaseToolPatcher()
    return patcher.apply()


def unpatch_base_tool():
    """Unpatch the LangChain BaseTool class."""
    patcher = BaseToolPatcher()
    return patcher.unpatch() 
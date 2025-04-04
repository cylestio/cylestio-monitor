"""
LangChain Callback Handler for Tool Monitoring.

This module provides a custom callback handler that hooks into LangChain's
tool-related callbacks to monitor the execution of methods decorated with @tool.
The handler logs tool start, end, and error events using our existing logging infrastructure.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union

# Attempt to import LangChain's callback handler base classes
# Handle imports gracefully to avoid breaking when LangChain is not installed
try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.callbacks.manager import (AsyncCallbackManagerForToolRun,
                                           CallbackManagerForToolRun)
    from langchain.schema import AgentAction, AgentFinish, LLMResult
    HAS_LANGCHAIN = True
except ImportError:
    try:
        # Try alternate import paths for different LangChain versions
        from langchain.schema.callbacks import BaseCallbackHandler
        from langchain.schema.callbacks.manager import (AsyncCallbackManagerForToolRun,
                                                       CallbackManagerForToolRun)
        from langchain.schema.agent import AgentAction, AgentFinish
        from langchain.schema.output import LLMResult
        HAS_LANGCHAIN = True
    except ImportError:
        # Define placeholder classes if LangChain is not available
        class BaseCallbackHandler:
            """Placeholder for LangChain's BaseCallbackHandler when it's not available."""
            pass
        
        class AgentAction:
            """Placeholder for LangChain's AgentAction when it's not available."""
            pass
        
        class AgentFinish:
            """Placeholder for LangChain's AgentFinish when it's not available."""
            pass
        
        class LLMResult:
            """Placeholder for LangChain's LLMResult when it's not available."""
            pass
        
        # Create placeholder callback manager classes
        class CallbackManagerForToolRun:
            """Placeholder for LangChain's CallbackManagerForToolRun."""
            pass
        
        class AsyncCallbackManagerForToolRun:
            """Placeholder for LangChain's AsyncCallbackManagerForToolRun."""
            pass
        
        HAS_LANGCHAIN = False

from cylestio_monitor.utils.event_logging import log_error, log_event
from cylestio_monitor.utils.trace_context import TraceContext

# Set up logger
logger = logging.getLogger("CylestioMonitor.LangChainCallbacks")


class ToolMonitorCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that monitors the usage of LangChain tools.
    
    This handler hooks into LangChain's tool-related callbacks to track when tools
    start, end, and encounter errors. It logs these events using our existing
    logging infrastructure and maintains proper trace context.
    """
    
    def __init__(self) -> None:
        """Initialize the callback handler."""
        super().__init__()
        self.active_tool_runs = {}  # Track active tool runs with timestamps
        self.initialization_ts = time.time()
        logger.debug("ToolMonitorCallbackHandler initialized")
    
    def _is_available(self) -> bool:
        """Check if LangChain is available."""
        return HAS_LANGCHAIN
    
    def _start_tool_span(self, tool_name: str, tool_input: str) -> Dict[str, Any]:
        """Start a new span for a tool execution.
        
        Args:
            tool_name: Name of the tool being executed
            tool_input: Input provided to the tool
            
        Returns:
            Dict: Span information
        """
        span_info = TraceContext.start_span(f"tool.{tool_name}")
        span_id = span_info.get("span_id")
        
        if span_id:
            self.active_tool_runs[span_id] = {
                "start_time": time.time(),
                "tool_name": tool_name,
                "tool_input": tool_input,
                "span_info": span_info
            }
        
        return span_info
    
    def _end_tool_span(self, span_id: str, output: Any = None, error: Optional[Exception] = None) -> None:
        """End a tool execution span.
        
        Args:
            span_id: ID of the span to end
            output: Output from the tool (if successful)
            error: Error from the tool (if failed)
        """
        if span_id in self.active_tool_runs:
            run_info = self.active_tool_runs.pop(span_id)
            duration = time.time() - run_info["start_time"]
            duration_ms = int(duration * 1000)
            
            # Add duration to attributes
            attributes = {
                "tool.name": run_info["tool_name"],
                "tool.input": str(run_info["tool_input"]),
                "duration_ms": duration_ms,
            }
            
            if output is not None:
                try:
                    # Limit output size to avoid oversized logs
                    output_str = str(output)
                    if len(output_str) > 1000:
                        output_str = output_str[:997] + "..."
                    attributes["tool.output"] = output_str
                except Exception as e:
                    logger.warning(f"Failed to convert tool output to string: {e}")
                    attributes["tool.output"] = "<non-serializable>"
            
            # End the span in TraceContext
            TraceContext.end_span()
        else:
            logger.warning(f"Attempted to end unknown tool span: {span_id}")
            # Still try to end the span in case it exists in TraceContext
            TraceContext.end_span()
    
    def on_tool_start(
        self, 
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Handle tool start event.
        
        Args:
            serialized: The serialized tool
            input_str: The input to the tool
            **kwargs: Additional keyword arguments
        """
        if not self._is_available():
            return
        
        try:
            tool_name = serialized.get("name", "<unknown_tool>")
            
            # Start a span for this tool execution
            span_info = self._start_tool_span(tool_name, input_str)
            
            # Log the tool start event
            log_event(
                name="tool.start",
                attributes={
                    "tool.name": tool_name,
                    "tool.input": input_str,
                    "tool.type": "langchain",
                },
                level="INFO"
            )
        except Exception as e:
            logger.error(f"Error in on_tool_start: {e}")
    
    def on_tool_end(
        self, 
        output: str,
        **kwargs: Any
    ) -> None:
        """Handle tool end event.
        
        Args:
            output: The output of the tool
            **kwargs: Additional keyword arguments
        """
        if not self._is_available():
            return
        
        try:
            # Get current span ID
            context = TraceContext.get_current_context()
            span_id = context.get("span_id")
            
            if span_id:
                # Retrieve tool info if available
                tool_name = "<unknown_tool>"
                if span_id in self.active_tool_runs:
                    tool_name = self.active_tool_runs[span_id]["tool_name"]
                
                # Log the tool end event
                log_event(
                    name="tool.end",
                    attributes={
                        "tool.name": tool_name,
                        "tool.output": str(output),
                        "tool.status": "success",
                        "tool.type": "langchain",
                    },
                    level="INFO"
                )
                
                # End the span
                self._end_tool_span(span_id, output=output)
        except Exception as e:
            logger.error(f"Error in on_tool_end: {e}")
    
    def on_tool_error(
        self, 
        error: Union[Exception, KeyboardInterrupt],
        **kwargs: Any
    ) -> None:
        """Handle tool error event.
        
        Args:
            error: The error that occurred
            **kwargs: Additional keyword arguments
        """
        if not self._is_available():
            return
        
        try:
            # Get current span ID
            context = TraceContext.get_current_context()
            span_id = context.get("span_id")
            
            if span_id:
                # Retrieve tool info if available
                tool_name = "<unknown_tool>"
                if span_id in self.active_tool_runs:
                    tool_name = self.active_tool_runs[span_id]["tool_name"]
                
                # Log the tool error event
                log_error(
                    name="tool.error",
                    error=error,
                    attributes={
                        "tool.name": tool_name,
                        "tool.status": "error",
                        "tool.type": "langchain",
                        "error.type": error.__class__.__name__,
                    }
                )
                
                # End the span
                self._end_tool_span(span_id, error=error)
        except Exception as e:
            logger.error(f"Error in on_tool_error: {e}")
    
    # Async versions of the callback methods
    
    async def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """Handle LLM start event (async).
        
        We don't need to do anything special here, but we need to implement it
        for compatibility with the AsyncCallbackHandler interface.
        
        Args:
            serialized: The serialized LLM
            prompts: The prompts
            **kwargs: Additional keyword arguments
        """
        pass
    
    async def on_chat_model_start(
        self, 
        serialized: Dict[str, Any], 
        messages: List[List[Dict[str, Any]]], 
        **kwargs: Any
    ) -> None:
        """Handle chat model start event (async).
        
        We don't need to do anything special here, but we need to implement it
        for compatibility with the AsyncCallbackHandler interface.
        
        Args:
            serialized: The serialized chat model
            messages: The messages
            **kwargs: Additional keyword arguments
        """
        pass
    
    async def async_on_tool_start(
        self, 
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Handle tool start event asynchronously.
        
        Args:
            serialized: The serialized tool
            input_str: The input to the tool
            **kwargs: Additional keyword arguments
        """
        self.on_tool_start(serialized, input_str, **kwargs)
    
    async def async_on_tool_end(
        self, 
        output: str,
        **kwargs: Any
    ) -> None:
        """Handle tool end event asynchronously.
        
        Args:
            output: The output of the tool
            **kwargs: Additional keyword arguments
        """
        self.on_tool_end(output, **kwargs)
    
    async def async_on_tool_error(
        self, 
        error: Union[Exception, KeyboardInterrupt],
        **kwargs: Any
    ) -> None:
        """Handle tool error event asynchronously.
        
        Args:
            error: The error that occurred
            **kwargs: Additional keyword arguments
        """
        self.on_tool_error(error, **kwargs)


# Singleton instance for global usage
_callback_handler_instance = None


def get_callback_handler() -> ToolMonitorCallbackHandler:
    """Get or create a singleton instance of the ToolMonitorCallbackHandler.
    
    Returns:
        ToolMonitorCallbackHandler: A shared instance of the callback handler
    """
    global _callback_handler_instance
    
    if _callback_handler_instance is None:
        _callback_handler_instance = ToolMonitorCallbackHandler()
    
    return _callback_handler_instance 
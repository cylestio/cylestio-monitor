"""
Basic Instrumentation utilities for AI operations.

This module provides utilities for easy instrumentation of AI operations,
including decorators for function monitoring and context managers for spans.
"""

import functools
import time
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event, log_error

F = TypeVar('F', bound=Callable[..., Any])


def instrument_function(func: F, name_prefix: str = "function") -> F:
    """Decorator to instrument a function with telemetry.
    
    Args:
        func: The function to instrument
        name_prefix: Prefix for the event name
        
    Returns:
        The wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get function details
        module_name = func.__module__
        function_name = func.__qualname__
        
        # Start span for this function
        span_info = TraceContext.start_span(f"{name_prefix}.{function_name}")
        
        # Get caller information
        caller_frame = inspect.currentframe().f_back
        caller_info = {}
        if caller_frame:
            caller_info = {
                "caller.file": caller_frame.f_code.co_filename,
                "caller.line": caller_frame.f_lineno,
                "caller.function": caller_frame.f_code.co_name
            }
        
        # Log start event
        log_event(
            name=f"{name_prefix}.start",
            attributes={
                "function.name": function_name,
                "function.module": module_name,
                **caller_info
            }
        )
        
        start_time = time.time()
        try:
            # Call the original function
            result = func(*args, **kwargs)
            
            # Log success event
            duration = time.time() - start_time
            log_event(
                name=f"{name_prefix}.end",
                attributes={
                    "function.name": function_name,
                    "function.module": module_name,
                    "function.duration_ms": int(duration * 1000),
                    "function.status": "success"
                }
            )
            
            return result
        except Exception as e:
            # Log error event
            duration = time.time() - start_time
            log_error(
                name=f"{name_prefix}.error",
                error=e,
                attributes={
                    "function.name": function_name,
                    "function.module": module_name,
                    "function.duration_ms": int(duration * 1000),
                    "function.status": "error"
                }
            )
            raise
        finally:
            # End span regardless of outcome
            TraceContext.end_span()
    
    return cast(F, wrapper)


class Span:
    """Context manager for creating spans in code blocks.
    
    Example:
        ```
        with Span("my_operation"):
            # Code to be traced
            perform_operation()
        ```
    """
    
    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Initialize a span context manager.
        
        Args:
            name: Name of the span
            attributes: Optional attributes to add to the span start event
        """
        self.name = name
        self.attributes = attributes or {}
        self.span_info = None
        self.start_time = None
    
    def __enter__(self) -> Dict[str, Any]:
        """Start the span and return span info.
        
        Returns:
            Dict: Span information
        """
        self.span_info = TraceContext.start_span(self.name)
        self.start_time = time.time()
        
        # Log span start event
        log_event(
            name=f"{self.name}.start",
            attributes=self.attributes
        )
        
        return self.span_info
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End the span and log appropriate events.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        duration = time.time() - self.start_time
        duration_ms = int(duration * 1000)
        
        if exc_type is not None:
            # Log error event
            log_error(
                name=f"{self.name}.error",
                error=exc_val,
                attributes={
                    **self.attributes,
                    "duration_ms": duration_ms,
                    "status": "error"
                }
            )
        else:
            # Log success event
            log_event(
                name=f"{self.name}.end",
                attributes={
                    **self.attributes,
                    "duration_ms": duration_ms,
                    "status": "success"
                }
            )
        
        # End the span
        TraceContext.end_span()


def instrument_method(name_prefix: str = "method") -> Callable[[F], F]:
    """Decorator factory for instrumenting methods.
    
    Args:
        name_prefix: Prefix for the event name
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        return instrument_function(func, name_prefix)
    return decorator 
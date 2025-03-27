"""
Event context management for telemetry events.

This module provides functionality to enrich telemetry events with contextual
information such as user session data, system information, and application state.
Context data is automatically added to telemetry events when they are logged.
"""

import os
import sys
import uuid
import socket
import platform
import logging
import threading
from typing import Dict, Any, Optional, List, Callable

# Initialize logger
logger = logging.getLogger(__name__)

# Thread-local storage for context data
_thread_local = threading.local()

# Global context that applies to all events
_global_context: Dict[str, Any] = {
    "host.name": socket.gethostname(),
    "os.type": platform.system(),
    "os.version": platform.release(),
    "process.id": os.getpid(),
    "process.runtime.name": "python",
    "process.runtime.version": platform.python_version(),
}

# Default session ID
_default_session_id = str(uuid.uuid4())

def initialize_context() -> None:
    """Initialize the thread-local context with default values."""
    if not hasattr(_thread_local, "context"):
        _thread_local.context = {}
    
    # Set default session ID if not already set
    if "session.id" not in _thread_local.context:
        _thread_local.context["session.id"] = _default_session_id


def get_context() -> Dict[str, Any]:
    """
    Get the current context data.
    
    Returns:
        Dict[str, Any]: Combined global and thread-local context data.
    """
    initialize_context()
    
    # Merge global and thread-local context, with thread-local taking precedence
    context = {**_global_context}
    context.update(_thread_local.context)
    
    return context


def set_context(key: str, value: Any) -> None:
    """
    Set a context value in the thread-local context.
    
    Args:
        key (str): The context key to set.
        value (Any): The value to set for the context key.
    """
    initialize_context()
    _thread_local.context[key] = value
    logger.debug(f"Set context: {key}={value}")


def set_global_context(key: str, value: Any) -> None:
    """
    Set a context value in the global context.
    
    Args:
        key (str): The context key to set.
        value (Any): The value to set for the context key.
    """
    _global_context[key] = value
    logger.debug(f"Set global context: {key}={value}")


def set_session_id(session_id: str) -> None:
    """
    Set the session ID for the current thread.
    
    Args:
        session_id (str): The session ID to set.
    """
    set_context("session.id", session_id)


def get_session_id() -> str:
    """
    Get the current session ID.
    
    Returns:
        str: The current session ID.
    """
    initialize_context()
    return _thread_local.context.get("session.id", _default_session_id)


def clear_context() -> None:
    """Clear the thread-local context."""
    if hasattr(_thread_local, "context"):
        _thread_local.context.clear()
    initialize_context()


def enrich_event_with_context(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich an event with context data.
    
    Args:
        event (Dict[str, Any]): The event to enrich.
        
    Returns:
        Dict[str, Any]: The enriched event with context data added to the attributes.
    """
    if "attributes" not in event:
        event["attributes"] = {}
    
    # Only add context data that isn't already in the event
    context = get_context()
    for key, value in context.items():
        if key not in event["attributes"]:
            event["attributes"][key] = value
            
    return event


class ContextManager:
    """
    Context manager for temporarily setting context values.
    
    Usage:
        with ContextManager(user_id="123", user_email="user@example.com"):
            # Log events with these context values
            log_event("user.action", attributes={"action": "login"})
    """
    
    def __init__(self, **kwargs) -> None:
        """
        Initialize the context manager with key-value pairs.
        
        Args:
            **kwargs: Key-value pairs to set in the context.
        """
        self.kwargs = kwargs
        self.previous = {}
        
    def __enter__(self) -> 'ContextManager':
        initialize_context()
        
        # Save previous values and set new values
        for key, value in self.kwargs.items():
            self.previous[key] = _thread_local.context.get(key)
            set_context(key, value)
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Restore previous values
        for key, value in self.previous.items():
            if value is None:
                if key in _thread_local.context:
                    del _thread_local.context[key]
            else:
                _thread_local.context[key] = value 
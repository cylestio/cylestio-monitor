import asyncio
import functools
import time
from typing import Any, Callable, Dict

from .events_processor import post_monitor_call, post_monitor_llm, pre_monitor_call, pre_monitor_llm


def monitor_call(func, channel="GENERIC"):
    """
    Decorator for non-LLM calls (MCP, or any other function).
    Decides if func is async or sync and wraps accordingly.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            pre_monitor_call(func, channel, args, kwargs)
            try:
                result = await func(*args, **kwargs)
                post_monitor_call(func, channel, start_time, result)
                return result
            except Exception as e:
                # Log the error but don't interfere with the exception
                from .events_processor import log_event

                log_event(
                    "call_error", {"function": func.__name__, "error": str(e)}, channel, "error"
                )
                raise

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            pre_monitor_call(func, channel, args, kwargs)
            try:
                result = func(*args, **kwargs)
                post_monitor_call(func, channel, start_time, result)
                return result
            except Exception as e:
                # Log the error but don't interfere with the exception
                from .events_processor import log_event

                log_event(
                    "call_error", {"function": func.__name__, "error": str(e)}, channel, "error"
                )
                raise

        return sync_wrapper


def monitor_llm_call(func, channel="LLM"):
    """
    Decorator specialized for LLM calls (Anthropic, OpenAI, etc.)
    that need prompt/response checks, blocking, etc.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time, prompt_info, alert = pre_monitor_llm(channel, args, kwargs)
            if alert == "dangerous":
                # Block dangerous prompts
                from .events_processor import log_event

                log_event(
                    "LLM_call_blocked",
                    {"reason": "dangerous prompt", "prompt": prompt_info},
                    channel,
                    "warning",
                )
                raise ValueError("Blocked LLM call due to dangerous terms.")
            try:
                result = await func(*args, **kwargs)
                post_monitor_llm(channel, start_time, result)
                return result
            except Exception as e:
                # Log the error but don't interfere with the exception
                from .events_processor import log_event

                log_event("LLM_call_error", {"error": str(e)}, channel, "error")
                raise

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time, prompt_info, alert = pre_monitor_llm(channel, args, kwargs)
            if alert == "dangerous":
                # Block dangerous prompts
                from .events_processor import log_event

                log_event(
                    "LLM_call_blocked",
                    {"reason": "dangerous prompt", "prompt": prompt_info},
                    channel,
                    "warning",
                )
                raise ValueError("Blocked LLM call due to dangerous terms.")
            try:
                result = func(*args, **kwargs)
                post_monitor_llm(channel, start_time, result)
                return result
            except Exception as e:
                # Log the error but don't interfere with the exception
                from .events_processor import log_event

                log_event("LLM_call_error", {"error": str(e)}, channel, "error")
                raise

        return sync_wrapper


"""Events listener module for Cylestio Monitor.

This module handles listening for and routing monitoring events.
"""

import logging
from typing import List


class EventsListener:
    """Listens for and routes monitoring events."""

    def __init__(self):
        """Initialize events listener."""
        self.handlers: List[Callable[[Dict[str, Any]], None]] = []
        self.is_running = False
        self.logger = logging.getLogger("CylestioMonitor")

    def start(self) -> None:
        """Start listening for events."""
        self.is_running = True
        self.logger.info("Events listener started")

    def stop(self) -> None:
        """Stop listening for events."""
        self.is_running = False
        self.logger.info("Events listener stopped")

    def add_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add an event handler.

        Args:
            handler: Function that takes an event dictionary and processes it
        """
        self.handlers.append(handler)

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle a monitoring event.

        Args:
            event: Event data dictionary
        """
        if not self.is_running:
            return

        try:
            for handler in self.handlers:
                handler(event)
        except Exception as e:
            self.logger.error(f"Error handling event: {e}", extra={"event": event})

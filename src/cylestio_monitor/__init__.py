"""Cylestio Monitor - A monitoring tool for LLM API calls and AI agents.

This module provides comprehensive monitoring for AI applications, automatically detecting 
and instrumenting various libraries and frameworks including:

- Anthropic Claude client (auto-detected)
- LangChain (auto-detected)
- LangGraph (auto-detected)
- MCP (Machine Conversation Protocol)

Basic usage:
```python
from cylestio_monitor import start_monitoring

# Start monitoring at the beginning of your application
start_monitoring(agent_id="my-agent")

# Your application code here...
# The monitor will automatically detect and instrument supported libraries

# When finished, stop monitoring
from cylestio_monitor import stop_monitoring
stop_monitoring()
```
"""

from cylestio_monitor.monitor import stop_monitoring, start_monitoring, get_api_endpoint
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.instrumentation import instrument_function, instrument_method, Span

# Import the API client module to make it available
from . import api_client

__version__ = "0.1.5"

__all__ = [
    "start_monitoring",
    "stop_monitoring",
    "log_event",
    "log_error",
    "TraceContext",
    "instrument_function",
    "instrument_method",
    "Span",
    "get_api_endpoint",
    "api_client",
]

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

from .events_processor import log_event
from .monitor import stop_monitoring, start_monitoring, get_api_endpoint, log_to_file_and_api

# Import the API client module to make it available
from . import api_client
from . import event_logger

__version__ = "0.1.3"

__all__ = [
    "start_monitoring",
    "stop_monitoring",
    "log_event",
    "get_api_endpoint",
    "log_to_file_and_api",
    "api_client",
    "event_logger",
]

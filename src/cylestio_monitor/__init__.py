"""Cylestio Monitor - A monitoring tool for LLM API calls and AI agents.

This module provides comprehensive monitoring for AI applications, automatically detecting
and instrumenting various libraries and frameworks including:

- Anthropic Claude client (auto-detected)
- LangChain (auto-detected)
- LangGraph (auto-detected)
- MCP (Machine Conversation Protocol)
- LangChain Tools & Tool Decorators (auto-detected)

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

# Apply compatibility patches to handle version differences safely
# This must be done first, before any instrumentation patching
try:
    from cylestio_monitor._compat.langchain import apply_patches as apply_langchain_compat_patches
    apply_langchain_compat_patches()
except Exception as e:
    import logging
    logger = logging.getLogger("CylestioMonitor")
    logger.debug(f"Failed to apply compatibility patches: {e}")
    # Continue without compatibility patches - we should never crash the host application

# Import essential typing modules early to ensure they're in the module namespace
# This prevents errors when patching tools with annotated types

from cylestio_monitor.monitor import (get_api_endpoint, start_monitoring,
                                      stop_monitoring)
# Apply patchers automatically on import
# This ensures all supported frameworks are automatically patched
from cylestio_monitor.patchers import (patch_anthropic_module,
                                       patch_decorated_tools, patch_langchain,
                                       patch_langgraph, patch_mcp,
                                       patch_openai_module,
                                       patch_tool_decorator)
from cylestio_monitor.utils.event_logging import log_error, log_event
from cylestio_monitor.utils.instrumentation import (Span, instrument_function,
                                                    instrument_method)
from cylestio_monitor.utils.trace_context import TraceContext

# Import the API client module to make it available
from . import api_client

__version__ = "0.1.9"

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

# Patching is now done in start_monitoring() to ensure trace context is initialized first
# These auto-patching blocks are disabled to prevent early patching before trace context is set
'''
# Try to apply all patchers automatically
# These will only apply if the related libraries are imported
try:
    patch_anthropic_module()
except Exception:
    pass

try:
    patch_openai_module()
except Exception:
    pass

try:
    patch_langchain()
except Exception:
    pass

try:
    patch_langgraph()
except Exception:
    pass

try:
    patch_mcp()
except Exception:
    pass

# Apply the tool patchers
try:
    patch_tool_decorator()
except Exception:
    pass

try:
    patch_decorated_tools()
except Exception:
    pass
'''

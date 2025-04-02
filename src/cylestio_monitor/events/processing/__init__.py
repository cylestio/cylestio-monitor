"""
Event processing functionality for Cylestio Monitor.

This package provides various modules for event processing, including:
- Event logging
- Security scanning for suspicious and dangerous content
- LLM monitoring hooks
- MCP monitoring tools
"""

from cylestio_monitor.events.processing.hooks import (
    hook_decorator, langchain_input_hook, langchain_output_hook,
    langgraph_state_update_hook, llm_call_hook, llm_response_hook,
    register_framework_patch)
# Re-export key functions
from cylestio_monitor.events.processing.logger import (
    create_standardized_event, log_event)
from cylestio_monitor.events.processing.mcp import (
    log_mcp_agent_status_change, log_mcp_authentication_event,
    log_mcp_command_event, log_mcp_connection_event, log_mcp_file_transfer,
    log_mcp_heartbeat)
from cylestio_monitor.events.processing.processor import (
    EventProcessor, process_standardized_event)
from cylestio_monitor.events.processing.security import (
    check_security_concerns, contains_dangerous, contains_suspicious,
    mask_sensitive_data)

# Define what's available via "from processing import *"
__all__ = [
    # From logger.py
    "log_event",
    "create_standardized_event",
    # From security.py
    "contains_suspicious",
    "contains_dangerous",
    "mask_sensitive_data",
    "check_security_concerns",
    # From hooks.py
    "llm_call_hook",
    "llm_response_hook",
    "langchain_input_hook",
    "langchain_output_hook",
    "langgraph_state_update_hook",
    "register_framework_patch",
    "hook_decorator",
    # From mcp.py
    "log_mcp_connection_event",
    "log_mcp_command_event",
    "log_mcp_heartbeat",
    "log_mcp_file_transfer",
    "log_mcp_agent_status_change",
    "log_mcp_authentication_event",
    # From processor.py
    "EventProcessor",
    "process_standardized_event",
]

"""
Event processing functionality for Cylestio Monitor.

This package provides various modules for event processing, including:
- Event logging
- Security scanning for suspicious and dangerous content
- LLM monitoring hooks
- MCP monitoring tools
"""

# Re-export key functions
from cylestio_monitor.events.processing.logger import log_event, create_standardized_event
from cylestio_monitor.events.processing.security import (
    contains_suspicious, 
    contains_dangerous, 
    mask_sensitive_data, 
    check_security_concerns
)
from cylestio_monitor.events.processing.hooks import (
    llm_call_hook, 
    llm_response_hook, 
    langchain_input_hook, 
    langchain_output_hook, 
    langgraph_state_update_hook, 
    register_framework_patch, 
    hook_decorator
)
from cylestio_monitor.events.processing.mcp import (
    log_mcp_connection_event, 
    log_mcp_command_event, 
    log_mcp_heartbeat, 
    log_mcp_file_transfer, 
    log_mcp_agent_status_change, 
    log_mcp_authentication_event
)
from cylestio_monitor.events.processing.processor import (
    EventProcessor, 
    process_standardized_event
)

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
    "process_standardized_event"
] 
"""
Tool patcher module for Cylestio Monitor.

This module provides specialized patching for MCP tool calls to detect SQL injection
and command injection through query interfaces.
"""

import functools
import inspect
import logging
from typing import Any, Dict, Optional, Callable, List, Union

from cylestio_monitor._sensors.process import analyze_sql_query
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.event_context import get_session_id

logger = logging.getLogger(__name__)

# Track patched tools to avoid double-patching
_patched_tools = set()


def patch_mcp_tool(tool_func: Callable) -> Callable:
    """
    Patch an MCP tool function to monitor for SQL injection and command injection.

    Args:
        tool_func: The original tool function to patch

    Returns:
        Wrapped function that adds monitoring capabilities
    """
    # Skip if already patched
    if getattr(tool_func, "__cylestio_patched__", False):
        return tool_func

    @functools.wraps(tool_func)
    def patched_tool(*args, **kwargs):
        # Extract SQL query if present in arguments
        query = None
        tool_name = getattr(tool_func, "__name__", "unknown_tool")

        # Check positional arguments
        if len(args) > 0 and isinstance(args[0], str) and ("SELECT" in args[0] or "select" in args[0].lower()):
            query = args[0]

        # Check keyword arguments
        for param_name, param_value in kwargs.items():
            if (param_name.lower() in ("query", "sql", "sql_query") and
                isinstance(param_value, str) and
                ("SELECT" in param_value or "select" in param_value.lower())):
                query = param_value

        # If we found a SQL query, analyze it for command injection patterns
        if query:
            context = {
                "tool.name": tool_name,
                "tool.type": "mcp",
                "tool.category": "database"
            }
            analyze_sql_query(query, context)

        # Execute the original function
        return tool_func(*args, **kwargs)

    # Mark as patched to avoid duplicate patching
    setattr(patched_tool, "__cylestio_patched__", True)
    return patched_tool


def patch_mcp_client_tools(client) -> None:
    """
    Patch all tools in an MCP client to detect SQL injection and command injection.

    Args:
        client: The MCP client object to patch
    """
    # Get tools attribute if available
    tools = getattr(client, "tools", None)
    if not tools:
        return

    # Look for tool attributes
    for attr_name in dir(tools):
        if attr_name.startswith("_"):
            continue

        # Get the attribute
        attr = getattr(tools, attr_name)

        # Check if it's a tool function (callable)
        if callable(attr) and not getattr(attr, "__cylestio_patched__", False):
            # Patch specific database-related tools
            if attr_name.lower() in ("query", "read_query", "execute_query", "sql", "run_sql"):
                patched_func = patch_mcp_tool(attr)
                setattr(tools, attr_name, patched_func)
                logger.info(f"Patched MCP tool: {attr_name}")
                _patched_tools.add(attr_name)


def initialize() -> bool:
    """
    Initialize MCP tool patching for SQL/command injection detection.

    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        # This function only sets up the patching capability
        # Actual patching happens when MCP clients are created
        logger.info("MCP tool patching initialized for SQL/command injection detection")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MCP tool patching: {e}")
        return False

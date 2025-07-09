"""
MCP patching module for Cylestio Monitor.

This module provides functions to patch the MCP library for telemetry collection.
"""

import logging
import inspect
import functools
from typing import Any, Dict, Optional, Callable, List, Union

from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.event_context import get_session_id
from cylestio_monitor.patchers.tool_patcher import patch_mcp_client_tools

logger = logging.getLogger(__name__)

# Original MCP functions
_original_func_registry = {}


def _get_param_names(func: Callable) -> List[str]:
    """
    Get the parameter names of a function.

    Args:
        func: The function to inspect

    Returns:
        List of parameter names
    """
    try:
        return list(inspect.signature(func).parameters.keys())
    except (ValueError, TypeError):
        return []


def _patch_session_call_tool():
    """Patch MCP's ClientSession.call_tool to monitor tool executions."""
    try:
        import mcp

        # Check if we've already patched it
        if hasattr(mcp.ClientSession.call_tool, '_cylestio_patched'):
            return True

        # Save original function
        _original_func_registry['mcp.ClientSession.call_tool'] = mcp.ClientSession.call_tool

        # Create wrapper function
        @functools.wraps(mcp.ClientSession.call_tool)
        async def patched_call_tool(self, *args, **kwargs):
            # Extract tool information
            tool_info = {}

            # Check if the function signature matches what we expect
            param_names = _get_param_names(mcp.ClientSession.call_tool)

            if len(param_names) >= 3 and len(args) >= 2:
                # Likely signature: call_tool(self, name, arguments)
                tool_info['tool.name'] = args[0]
                tool_info['tool.params'] = list(args[1].keys()) if isinstance(args[1], dict) else []

                # Check for SQL queries which could have command injection
                if isinstance(args[1], dict) and 'query' in args[1] and isinstance(args[1]['query'], str):
                    # Import this here to avoid circular import
                    from cylestio_monitor._sensors.process import analyze_sql_query
                    analyze_sql_query(args[1]['query'], {
                        'tool.name': args[0],
                        'tool.type': 'mcp'
                    })
            elif 'name' in kwargs:
                # Alternatively, kwargs might have the info
                tool_info['tool.name'] = kwargs['name']
                if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
                    tool_info['tool.params'] = list(kwargs['arguments'].keys())

                    # Check for SQL queries which could have command injection
                    if 'query' in kwargs['arguments'] and isinstance(kwargs['arguments']['query'], str):
                        # Import this here to avoid circular import
                        from cylestio_monitor._sensors.process import analyze_sql_query
                        analyze_sql_query(kwargs['arguments']['query'], {
                            'tool.name': kwargs['name'],
                            'tool.type': 'mcp'
                        })

            # Add MCP framework info
            tool_info['framework.name'] = 'mcp'
            tool_info['framework.type'] = 'tool'

            # Get tool ID for correlation
            if hasattr(self, 'id'):
                tool_info['tool.id'] = str(self.id)

            # Add session ID
            tool_info['session.id'] = get_session_id()

            # Log tool execution start
            span_id = None
            try:
                result = log_event(
                    'tool.execution',
                    level='INFO',
                    attributes=tool_info
                )
                span_id = result.get('span_id')
            except Exception as e:
                log_error(f"Error logging tool execution: {e}")

            # Execute the original function
            try:
                result = await _original_func_registry['mcp.ClientSession.call_tool'](self, *args, **kwargs)

                # Log tool execution result
                result_info = {
                    **tool_info,
                    'tool.status': 'success',
                    'tool.result.type': type(result).__name__,
                }

                if span_id:
                    log_event(
                        'tool.result',
                        level='INFO',
                        attributes=result_info,
                        parent_span_id=span_id
                    )
                else:
                    log_event(
                        'tool.result',
                        level='INFO',
                        attributes=result_info
                    )

                return result
            except Exception as error:
                # Log tool execution error
                error_info = {
                    **tool_info,
                    'tool.status': 'error',
                    'error.type': type(error).__name__,
                    'error.message': str(error),
                }

                if span_id:
                    log_event(
                        'tool.error',
                        level='ERROR',
                        attributes=error_info,
                        parent_span_id=span_id
                    )
                else:
                    log_event(
                        'tool.error',
                        level='ERROR',
                        attributes=error_info
                    )

                # Re-raise the exception
                raise

        # Apply patch
        patched_call_tool._cylestio_patched = True
        mcp.ClientSession.call_tool = patched_call_tool

        logger.info("Successfully patched MCP ClientSession.call_tool")
        return True
    except ImportError:
        logger.debug("MCP library not available")
        return False
    except Exception as e:
        logger.error(f"Error patching MCP ClientSession.call_tool: {e}")
        return False


def _patch_client_init():
    """
    Patch MCP Client initialization to monitor tool executions.
    This allows us to patch tools when clients are created.
    """
    try:
        import mcp

        # Check if we've already patched it
        if hasattr(mcp.Client.__init__, '_cylestio_patched'):
            return True

        # Save original function
        _original_func_registry['mcp.Client.__init__'] = mcp.Client.__init__

        # Create wrapper function
        @functools.wraps(mcp.Client.__init__)
        def patched_init(self, *args, **kwargs):
            # Call original init
            _original_func_registry['mcp.Client.__init__'](self, *args, **kwargs)

            # Patch tools on the client to detect SQL command injection
            patch_mcp_client_tools(self)

        # Apply patch
        patched_init._cylestio_patched = True
        mcp.Client.__init__ = patched_init

        logger.info("Successfully patched MCP Client.__init__")
        return True
    except ImportError:
        logger.debug("MCP library not available")
        return False
    except Exception as e:
        logger.error(f"Error patching MCP Client.__init__: {e}")
        return False


def patch_mcp() -> bool:
    """
    Patch MCP library for telemetry collection and security monitoring.

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Initializing global MCP patcher")

    # Patch MCP ClientSession.call_tool
    session_patched = _patch_session_call_tool()

    # Patch MCP Client.__init__
    client_patched = _patch_client_init()

    # Return success if any patch was applied
    if session_patched or client_patched:
        logger.info("MCP patched successfully")
        return True
    else:
        logger.warning("Failed to patch MCP")
        return False


def unpatch_mcp() -> bool:
    """
    Restore original MCP functionality.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import mcp

        # Restore ClientSession.call_tool if patched
        if 'mcp.ClientSession.call_tool' in _original_func_registry:
            mcp.ClientSession.call_tool = _original_func_registry['mcp.ClientSession.call_tool']
            del _original_func_registry['mcp.ClientSession.call_tool']

        # Restore Client.__init__ if patched
        if 'mcp.Client.__init__' in _original_func_registry:
            mcp.Client.__init__ = _original_func_registry['mcp.Client.__init__']
            del _original_func_registry['mcp.Client.__init__']

        logger.info("MCP unpatched successfully")
        return True
    except ImportError:
        logger.debug("MCP library not available")
        return True  # Report success if library isn't present
    except Exception as e:
        logger.error(f"Error unpatching MCP: {e}")
        return False

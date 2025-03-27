"""
Management Control Protocol (MCP) monitoring.

This module provides functionality for monitoring MCP connections and command executions.
"""

import logging
import json
from typing import Any, Dict, Optional, Union
from datetime import datetime

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.events.processing.logger import log_event
from cylestio_monitor.events.processing.security import contains_suspicious, contains_dangerous


# Initialize logger
logger = logging.getLogger("CylestioMonitor")
config_manager = ConfigManager()


def log_mcp_connection_event(
    agent_id: str,
    connection_id: str,
    event_type: str,
    client_info: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Log an MCP connection event.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        event_type: Type of connection event (e.g., "connect", "disconnect")
        client_info: Optional client information
        error: Optional error message if connection failed
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add client info if provided
    if client_info:
        data["client_info"] = client_info
    
    # Add error if provided
    if error:
        data["error"] = error
    
    # Log the event
    log_event(
        event_type=f"mcp_connection_{event_type}",
        data=data,
        channel="MCP",
        level="error" if error else "info"
    )


def log_mcp_command_event(
    agent_id: str,
    connection_id: str,
    command: Dict[str, Any],
    direction: str,
    response: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Log an MCP command event.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        command: Command data
        direction: Direction of the command ("incoming" or "outgoing")
        response: Optional response to the command
        error: Optional error message if command failed
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "command": command,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add response if provided
    if response:
        data["response"] = response
    
    # Add error if provided
    if error:
        data["error"] = error
    
    # Check for security concerns in command
    command_str = json.dumps(command)
    is_dangerous = contains_dangerous(command_str)
    is_suspicious = contains_suspicious(command_str)
    
    # Set security flags
    if is_dangerous:
        data["contains_dangerous"] = True
    if is_suspicious:
        data["contains_suspicious"] = True
    
    # Determine log level based on security concerns
    log_level = "info"
    if error:
        log_level = "error"
    elif is_dangerous:
        log_level = "warning"
    elif is_suspicious:
        log_level = "warning"
    
    # Log the event
    log_event(
        event_type="mcp_command",
        data=data,
        channel="MCP",
        level=log_level,
        direction=direction
    )


def log_mcp_heartbeat(agent_id: str, connection_id: str, metrics: Dict[str, Any]) -> None:
    """Log an MCP heartbeat event with agent metrics.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        metrics: Agent metrics data
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log the event
    log_event(
        event_type="mcp_heartbeat",
        data=data,
        channel="MCP",
        level="debug"
    )


def log_mcp_file_transfer(
    agent_id: str,
    connection_id: str,
    direction: str,
    file_info: Dict[str, Any],
    status: str,
    error: Optional[str] = None
) -> None:
    """Log an MCP file transfer event.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        direction: Direction of the file transfer ("upload" or "download")
        file_info: Information about the file being transferred
        status: Status of the transfer ("start", "progress", "complete", "failed")
        error: Optional error message if transfer failed
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "file_info": file_info,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add error if provided
    if error:
        data["error"] = error
    
    # Determine log level based on status
    log_level = "info"
    if status == "failed":
        log_level = "error"
    elif status == "progress":
        log_level = "debug"
    
    # Log the event
    log_event(
        event_type="mcp_file_transfer",
        data=data,
        channel="MCP",
        level=log_level,
        direction=direction
    )


def log_mcp_agent_status_change(
    agent_id: str,
    connection_id: str,
    new_status: str,
    previous_status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log an MCP agent status change event.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        new_status: New status of the agent
        previous_status: Optional previous status of the agent
        details: Optional details about the status change
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "new_status": new_status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add previous status if provided
    if previous_status:
        data["previous_status"] = previous_status
    
    # Add details if provided
    if details:
        data["details"] = details
    
    # Determine log level based on status
    log_level = "info"
    if new_status in ["error", "crashed", "offline"]:
        log_level = "error"
    elif new_status in ["warning", "degraded"]:
        log_level = "warning"
    
    # Log the event
    log_event(
        event_type="mcp_agent_status_change",
        data=data,
        channel="MCP",
        level=log_level
    )


def log_mcp_authentication_event(
    agent_id: str,
    connection_id: str,
    auth_method: str,
    success: bool,
    details: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Log an MCP authentication event.
    
    Args:
        agent_id: ID of the agent
        connection_id: ID of the MCP connection
        auth_method: Authentication method used
        success: Whether authentication was successful
        details: Optional details about the authentication
        error: Optional error message if authentication failed
    """
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "connection_id": connection_id,
        "auth_method": auth_method,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add details if provided
    if details:
        data["details"] = details
    
    # Add error if provided
    if error:
        data["error"] = error
    
    # Determine log level based on success
    log_level = "info" if success else "warning"
    
    # Log the event
    log_event(
        event_type="mcp_authentication",
        data=data,
        channel="MCP",
        level=log_level
    ) 
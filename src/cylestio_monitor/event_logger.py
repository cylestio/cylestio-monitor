# src/cylestio_monitor/event_logger.py
"""
Event logging module for Cylestio Monitor.

This module handles all actual logging to API and file,
maintaining a single source of truth for all output operations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union, cast, Tuple

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.api_client import send_event_to_api

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()

# Console logger for user-facing messages
monitor_logger = logging.getLogger("CylestioMonitor")

# Dictionaries to track current sessions and conversations by agent_id
_current_sessions = {}  # agent_id -> session_id mapping
_current_conversations = {}  # (agent_id, session_id) -> conversation_id mapping

def _get_or_create_session_id(agent_id: str) -> str:
    """Get current session ID for agent or create a new one.
    
    Args:
        agent_id: The agent identifier
        
    Returns:
        str: Session ID to use
    """
    global _current_sessions
    if agent_id not in _current_sessions:
        # Generate a new session ID
        _current_sessions[agent_id] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return _current_sessions[agent_id]

def _get_or_create_conversation_id(agent_id: str, session_id: str) -> str:
    """Get or create a conversation ID for the agent.
    
    Args:
        agent_id (str): Agent ID
        session_id (str): Session ID
    
    Returns:
        str: Conversation ID
    """
    key = (agent_id, session_id)
    if key in _current_conversations:
        return _current_conversations[key]
    
    # Generate a new conversation ID
    conversation_id = f"conv_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    _current_conversations[key] = conversation_id
    return conversation_id

def _should_start_new_conversation(event_type: str, data: Dict[str, Any]) -> bool:
    """Determine if a new conversation should be started based on the event type.
    
    Args:
        event_type (str): Type of event
        data (Dict[str, Any]): Event data
        
    Returns:
        bool: True if a new conversation should be started
    """
    # Start a new conversation when a user initiates communication
    if event_type == "user_message" and data.get("direction") == "incoming":
        return True
    
    # If client is initialized or restarted, start a new conversation
    if event_type in ["client_init", "restart", "session_start"]:
        return True
    
    # If there's an explicit conversation_start event
    if event_type == "conversation_start":
        return True
    
    return False

def _should_end_conversation(event_type: str, data: Dict[str, Any]) -> bool:
    """Determine if the current conversation should be ended.
    
    Args:
        event_type (str): Type of event
        data (Dict[str, Any]): Event data
        
    Returns:
        bool: True if the conversation should be ended
    """
    # End conversation on explicit events
    if event_type in ["conversation_end", "session_end", "client_shutdown"]:
        return True
    
    # End conversation on "quit", "exit", or similar user commands
    if event_type == "user_message" and isinstance(data.get("content"), str):
        content = data.get("content", "").lower().strip()
        if content in ["quit", "exit", "bye", "goodbye"]:
            return True
    
    # Consider long periods of inactivity as ending a conversation
    # This would need to be implemented with a timestamp comparison
    
    return False

def _reset_conversation_id(agent_id: str, session_id: str) -> None:
    """Reset the conversation ID for an agent, forcing a new conversation on next event.
    
    Args:
        agent_id (str): Agent ID
        session_id (str): Session ID
    """
    key = (agent_id, session_id)
    if key in _current_conversations:
        del _current_conversations[key]

def send_event_to_remote_api(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> None:
    """
    Send an event to the remote API endpoint.
    
    Args:
        agent_id (str): Agent ID
        event_type (str): Event type
        data (Dict[str, Any]): Event data
        channel (str, optional): Event channel. Defaults to "SYSTEM".
        level (str, optional): Log level. Defaults to "info".
        timestamp (Optional[datetime], optional): Event timestamp. Defaults to None.
        direction (Optional[str], optional): Event direction. Defaults to None.
    """
    # Debug logging for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        logger.debug(f"send_event_to_remote_api: Processing LLM call event: {event_type}")
    
    # Get timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    try:
        # Get session ID from data or generate a new one
        session_id = data.get("session_id")
        if not session_id:
            session_id = _get_or_create_session_id(agent_id)
            data["session_id"] = session_id
            
        # Check if we should start a new conversation or end the current one
        if _should_start_new_conversation(event_type, data):
            _reset_conversation_id(agent_id, session_id)  # Force a new conversation ID
        
        # Get conversation ID from data or generate a new one
        conversation_id = data.get("conversation_id")
        if not conversation_id:
            conversation_id = _get_or_create_conversation_id(agent_id, session_id)
            data["conversation_id"] = conversation_id
        
        # Determine event direction if applicable
        if direction is None:
            if event_type.endswith("_request") or event_type.endswith("_prompt"):
                direction = "outgoing"
            elif event_type.endswith("_response") or event_type.endswith("_completion"):
                direction = "incoming"
            # Special handling for LLM call events
            elif event_type == "LLM_call_start":
                direction = "outgoing"
            elif event_type == "LLM_call_finish":
                direction = "incoming"
        
        # Debug logging for LLM call events before sending
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            logger.debug(f"send_event_to_remote_api: About to send LLM call event to API: {event_type}")
        
        # Send the event to the API
        send_event_to_api(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level,
            timestamp=timestamp,
            direction=direction
        )
        
        # Debug logging for LLM call events after sending
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            logger.debug(f"send_event_to_remote_api: Successfully sent LLM call event to API: {event_type}")
            
    except Exception as e:
        logger.error(f"Failed to send event to API: {e}")

# For backward compatibility
log_to_db = send_event_to_remote_api

def json_serializer(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def log_to_file(
    record: Dict[str, Any],
    log_file: Optional[str] = None
) -> None:
    """
    Log a record to a JSON file.
    
    Args:
        record: The record to log
        log_file: The path to the log file
    """
    # If no log file provided, check configuration
    if log_file is None:
        log_file = config_manager.get("monitoring.log_file")
    
    # If still no log file, return early
    if not log_file:
        return
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        # Append to the file
        with open(log_file, "a", encoding="utf-8") as f:
            json.dump(record, f, default=json_serializer)
            f.write("\n")  # Add newline for each record
    except Exception as e:
        logger.error(f"Failed to write to log file: {e}")

def log_console_message(
    message: str,
    level: str = "info",
    channel: str = "SYSTEM"
) -> None:
    """
    Log a simple text message to the console.
    
    Args:
        message: The message to log
        level: The log level
        channel: The channel to log to
    """
    level_upper = level.upper()
    level_method = getattr(monitor_logger, level.lower(), monitor_logger.info)
    
    # Format the message with channel
    formatted_message = f"[{channel}] {message}"
    
    # Log using the appropriate level method
    level_method(formatted_message)

def process_and_log_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    record: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process and log an event both to file and API.
    
    Args:
        agent_id: Agent ID
        event_type: Event type
        data: Event data
        channel: Event channel
        level: Log level
        record: Optional pre-formatted record
    """
    # Create or use provided record
    if record is None:
        # Create base record with required fields
        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "agent_id": agent_id,
            "event_type": event_type,
            "channel": channel.upper(),
            "data": data
        }
    
    # Log to file
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        try:
            log_to_file(record, log_file)
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    
    # Log to API
    try:
        send_event_to_remote_api(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level
        )
    except Exception as e:
        logger.error(f"Failed to send event to API: {e}") 
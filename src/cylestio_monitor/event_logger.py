# src/cylestio_monitor/event_logger.py
"""
Event logging module for Cylestio Monitor.

This module handles all actual logging to database and file,
maintaining a single source of truth for all output operations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union, cast, Tuple

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.db import utils as db_utils
from cylestio_monitor.db.database_manager import DatabaseManager
from cylestio_monitor.db.models import (
    Agent, Event, EventType, EventLevel, EventChannel, EventDirection,
    LLMCall, ToolCall, SecurityAlert, Session, Conversation, EventSecurity, PerformanceMetric
)

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()

# Console logger for user-facing messages
monitor_logger = logging.getLogger("CylestioMonitor")

# Dictionaries to track current sessions and conversations by agent_id
_current_sessions = {}  # agent_id -> session_id mapping
_current_conversations = {}  # (agent_id, session_id) -> conversation_id mapping

def _get_or_create_agent(session, agent_id: str):
    """Get or create an agent in the database.
    
    Args:
        session: SQLAlchemy session
        agent_id (str): Agent ID
        
    Returns:
        Agent: The agent object
    """
    # Get or create the agent
    agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        agent = Agent(agent_id=agent_id, name=agent_id)
        session.add(agent)
        session.flush()  # Get the ID generated for the agent
    return agent

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
    if agent_id in _current_conversations:
        return _current_conversations[agent_id]
    
    # Generate a new conversation ID
    conversation_id = f"conv_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    _current_conversations[agent_id] = conversation_id
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

def _reset_conversation_id(agent_id: str) -> None:
    """Reset the conversation ID for an agent, forcing a new conversation on next event.
    
    Args:
        agent_id (str): Agent ID
    """
    if agent_id in _current_conversations:
        del _current_conversations[agent_id]

def log_to_db(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> None:
    """
    Log an event to the database.
    
    Args:
        agent_id (str): Agent ID
        event_type (str): Event type
        data (Dict[str, Any]): Event data
        channel (str, optional): Event channel. Defaults to "SYSTEM".
        level (str, optional): Log level. Defaults to "info".
        timestamp (Optional[datetime], optional): Event timestamp. Defaults to None.
        direction (Optional[str], optional): Event direction. Defaults to None.
    """
    # Get timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    try:
        # Get database session
        from cylestio_monitor.db.utils import get_db_manager
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            # Get or create agent
            agent = _get_or_create_agent(session, agent_id)

            # Get session ID from data or generate a new one
            session_id = data.get("session_id")
            if not session_id:
                session_id = _get_or_create_session_id(agent_id)
                
            # Find or create the session
            session_obj = session.query(Session).filter(Session.id == session_id).first()
            if not session_obj:
                # Create new Session with agent_id
                session_obj = Session(
                    agent_id=agent.id,
                    start_time=timestamp,
                    session_metadata={"generated_id": session_id}
                )
                session.add(session_obj)
                session.flush()
            
            # Check if we should start a new conversation or end the current one
            if _should_start_new_conversation(event_type, data):
                _reset_conversation_id(agent_id)  # Force a new conversation ID
            
            # Get conversation ID from data or generate a new one
            conversation_id = data.get("conversation_id")
            if not conversation_id:
                conversation_id = _get_or_create_conversation_id(agent_id, session_id)
                
            # Find or create the conversation    
            conversation_obj = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conversation_obj:
                conversation_obj = Conversation(
                    session_id=session_obj.id if session_obj else None,
                    start_time=timestamp,
                    conversation_metadata={"generated_id": conversation_id}
                )
                session.add(conversation_obj)
                session.flush()
            
            # End the conversation if needed
            if _should_end_conversation(event_type, data) and conversation_obj:
                conversation_obj.end_time = timestamp
            
            # Determine event direction if applicable
            if direction is None:
                if event_type.endswith("_request") or event_type.endswith("_prompt"):
                    direction = "outgoing"
                elif event_type.endswith("_response") or event_type.endswith("_completion"):
                    direction = "incoming"

            # Create the base event
            event = Event(
                agent_id=agent.id,
                session_id=session_obj.id if session_obj else None,
                conversation_id=conversation_obj.id if conversation_obj else None,
                event_type=event_type,
                channel=channel.lower(),
                level=level.lower(),
                timestamp=timestamp,
                direction=direction,
                data=data
            )
            session.add(event)
            session.flush()  # Get the ID generated for the event
            
            # Based on event type, store in specialized tables
            event_type_lower = event_type.lower()
            
            if event_type_lower.startswith("llm_") or event_type.startswith("LLM_"):
                # Handle LLM call events
                llm_call = LLMCall(
                    event_id=event.id,
                    model=data.get("model", data.get("provider", "unknown")),
                    prompt=str(data.get("prompt", data.get("messages", ""))),
                    response=str(data.get("response", data.get("completion", ""))),
                    tokens_in=data.get("tokens_in", data.get("tokens_prompt", 0)),
                    tokens_out=data.get("tokens_out", data.get("tokens_completion", 0)),
                    duration_ms=data.get("duration_ms", data.get("latency_ms", 0)),
                    is_stream=data.get("is_stream", data.get("is_streaming", False)),
                    temperature=data.get("temperature", None),
                    cost=data.get("cost", None)
                )
                session.add(llm_call)
            
            elif (event_type_lower.startswith("tool_") or event_type.startswith("TOOL_") or
                  event_type_lower.startswith("mcp_") or event_type.startswith("MCP_") or
                  "mcp" in event_type_lower or "MCP" in event_type or
                  "tool" in event_type_lower or "TOOL" in event_type or
                  (event_type_lower in ["call_start", "call_finish"] and
                   data.get("tool_name") is not None)):
                # Handle tool call events
                
                # Extract tool name from event type if not explicitly provided
                tool_name = data.get("tool_name")
                if not tool_name:
                    # Try to extract from event_type (e.g., MCP_patch -> MCP)
                    parts = event_type.split('_')
                    if len(parts) > 0:
                        if parts[0].lower() in ["mcp", "tool"]:
                            tool_name = parts[0]
                        elif len(parts) > 1 and parts[0].lower() in ["call"]:
                            tool_name = parts[1]
                
                tool_call = ToolCall(
                    event_id=event.id,
                    tool_name=tool_name or data.get("provider", data.get("method", "unknown")),
                    input_params=data.get("input", data.get("tool_input", data.get("args", {}))),
                    output_result=data.get("output", data.get("tool_output", data.get("result", {}))),
                    success=data.get("success", data.get("status", "success") != "error"),
                    error_message=data.get("error", data.get("error_message", None)),
                    duration_ms=data.get("duration_ms", data.get("latency_ms", data.get("duration", 0))),
                    blocking=data.get("blocking", True)
                )
                session.add(tool_call)
            
            elif event_type_lower == "security_alert" or event_type == "SECURITY_ALERT":
                # Handle security alert events
                security_alert = SecurityAlert(
                    event_id=event.id,
                    alert_type=data.get("alert_type", "unknown"),
                    severity=data.get("severity", "medium"),
                    description=data.get("description", ""),
                    matched_terms=data.get("matches", data.get("matched_terms", [])),
                    action_taken=data.get("action_taken", None),
                )
                session.add(security_alert)
            
            # Handle performance metrics
            elif (event_type_lower.startswith("perf_") or 
                  event_type_lower.startswith("performance_") or
                  "latency" in event_type_lower or 
                  "memory" in event_type_lower or
                  "cpu" in event_type_lower or
                  "timing" in event_type_lower):
                # Handle performance metrics events
                # Extract metric type from event_type if not explicitly provided
                metric_type = data.get("metric_type")
                if not metric_type:
                    # Try to extract from event_type (e.g., perf_latency -> latency)
                    parts = event_type.split('_')
                    if len(parts) > 1:
                        metric_type = parts[1]
                    else:
                        metric_type = event_type
                
                # Extract value - might be in different fields depending on event source
                value = data.get("value", 
                          data.get("duration_ms",
                            data.get("latency_ms", 
                              data.get("usage", 0.0))))
                
                perf_metric = PerformanceMetric(
                    event_id=event.id,
                    metric_type=metric_type,
                    value=float(value),
                    unit=data.get("unit", "ms"),
                    context=data.get("context", data.get("metadata", {}))
                )
                session.add(perf_metric)
            
            # Also add security metadata to EventSecurity table if security info is present
            if data.get("security") or data.get("alert") in ["suspicious", "dangerous"]:
                alert_level = data.get("alert", "none")
                if data.get("security") and data["security"].get("severity") == "critical":
                    alert_level = "dangerous"
                
                event_security = EventSecurity(
                    event_id=event.id,
                    alert_level=alert_level,
                    matched_terms=data.get("security", {}).get("matches", []),
                    reason=data.get("security", {}).get("reason", None),
                    source_field=data.get("security", {}).get("source_field", None)
                )
                session.add(event_security)
            
            # Commit all changes
            session.commit()
            
    except Exception as e:
        logger.error(f"Failed to log event to database: {e}")
        # Don't re-raise; we want to continue with file logging even if DB fails


def json_serializer(obj: Any) -> Any:
    """Serialize objects that aren't natively serializable by json.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serializable representation of the object
        
    Raises:
        TypeError: If the object cannot be serialized
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def log_to_file(
    record: Dict[str, Any],
    log_file: Optional[str] = None
) -> None:
    """
    Log an event to a JSON file.
    
    Args:
        record: The complete record to log (already formatted)
        log_file: Path to the log file (if None, uses configured log_file)
    """
    # Get path to log file (create directory if needed)
    log_file = log_file or config_manager.get("monitoring.log_file")
    if not log_file:
        # No logging enabled
        return
            
    # Create directory if needed
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    try:
        # Convert record to JSON string with proper serialization
        json_str = json.dumps(record, default=json_serializer)
        
        # Write to file with proper error handling
        try:
            with open(log_file, "a") as f:
                f.write(json_str + "\n")
                f.flush()  # Ensure immediate write to disk
        except IOError as e:
            # Try writing to a fallback location if the primary fails
            fallback_file = os.path.join(
                os.path.expanduser("~"), 
                f"cylestio_monitor_fallback_{datetime.now().strftime('%Y%m%d')}.json"
            )
            logger.error(f"Failed to write to log file {log_file}, trying fallback: {fallback_file}")
            
            with open(fallback_file, "a") as f_backup:
                f_backup.write(json_str + "\n")
                monitor_logger.warning(f"Event logged to fallback file: {fallback_file}")
    except NameError as ne:
        # Handle the case where json isn't properly defined
        logger.error(f"JSON serialization error: {ne}")
                
    except Exception as e:
        logger.error(f"Failed to write to log file: {e}")
        # Log to console as fallback
        monitor_logger.error(f"Failed to log to file: {e}")


def log_console_message(
    message: str,
    level: str = "info",
    channel: str = "SYSTEM"
) -> None:
    """
    Log a simple message to the console.
    
    Args:
        message: The message to log
        level: Log level
        channel: Channel for extra context
    """
    if level.lower() == "debug":
        monitor_logger.debug(message, extra={"channel": channel})
    elif level.lower() == "warning":
        monitor_logger.warning(message, extra={"channel": channel})
    elif level.lower() == "error":
        monitor_logger.error(message, extra={"channel": channel})
    else:
        monitor_logger.info(message, extra={"channel": channel})


def process_and_log_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    record: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process and log an event to both database and file.
    
    This is the main entry point for all logging operations.
    
    Args:
        agent_id: The ID of the agent
        event_type: The type of event being logged
        data: Event data dictionary
        channel: Event channel
        level: Log level
        record: Optional pre-formatted record (if not provided, just logs data directly)
    """
    # Log a simple console message for user feedback
    log_console_message(f"Event: {event_type}", level, channel)
    
    # Log to database
    if agent_id:
        log_to_db(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level
        )
    
    # Log to file if a record is provided
    if record:
        log_to_file(record)


def _get_or_create_session(session_id: Optional[str] = None) -> Tuple[int, bool]:
    """Get or create a session object.
    
    Args:
        session_id (Optional[str], optional): Session ID to use. If None, a new session will be created.
        
    Returns:
        Tuple[int, bool]: Tuple of (session_id, is_new_session)
    """
    from cylestio_monitor.db.utils import get_db_manager
    from cylestio_monitor.db.models import Session, Agent
    
    db_manager = get_db_manager()
    agent_id = _get_agent_id()
    
    with db_manager.get_session() as session:
        if session_id:
            # Check if the session exists
            session_obj = session.query(Session).filter(Session.id == session_id).first()
            if session_obj:
                return session_obj.id, False
                
        # Create a new agent if it doesn't exist
        agent_obj = _get_or_create_agent(session, agent_id)
        
        # Create a new session
        new_session = Session(agent_id=agent_obj.id)
        session.add(new_session)
        session.commit()
        
        return new_session.id, True 
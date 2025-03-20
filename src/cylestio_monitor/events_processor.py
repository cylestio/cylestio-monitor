# src/cylestio_monitor/events_processor.py
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
import os

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.event_logger import log_console_message, log_to_db, log_to_file, process_and_log_event
from cylestio_monitor.events.processor import create_standardized_event
from cylestio_monitor.api_client import send_event_to_api

monitor_logger = logging.getLogger("CylestioMonitor")

# Get configuration manager instance
config_manager = ConfigManager()

# Track processed events to prevent duplicates
_processed_events = set()

# --------------------------------------
# Helper functions for normalization and keyword checking
# --------------------------------------
def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    if text is None:
        return "NONE"
    return " ".join(str(text).split()).upper()


def contains_suspicious(text: str) -> bool:
    """Check if text contains suspicious keywords."""
    normalized = normalize_text(text)
    suspicious_keywords = config_manager.get_suspicious_keywords()
    return any(keyword in normalized for keyword in suspicious_keywords)


def contains_dangerous(text: str) -> bool:
    """Check if text contains dangerous keywords."""
    normalized = normalize_text(text)
    dangerous_keywords = config_manager.get_dangerous_keywords()
    return any(keyword in normalized for keyword in dangerous_keywords)


# Helper function to generate a unique event identifier
def _get_event_id(event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
    """
    Generate a unique identifier for an event to track duplicates.
    
    Args:
        event_type: The event type
        data: Event data
        timestamp: Event timestamp
        
    Returns:
        str: Unique event identifier
    """
    ts = timestamp.isoformat() if timestamp else datetime.now().isoformat()
    # Create a simplified representation of the data for fingerprinting
    data_repr = str(sorted([(k, str(v)[:50]) for k, v in data.items() if k not in ["timestamp"]]))
    # Combine elements into a unique identifier
    return f"{event_type}:{data_repr}:{ts[:16]}"  # Only use first part of timestamp for deduplication window


# --------------------------------------
# EventProcessor class for handling monitoring events
# --------------------------------------
class EventProcessor:
    """Event processor for handling and routing monitoring events."""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the event processor.
        
        Args:
            agent_id: The ID of the agent being monitored
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config or {}
        
    def process_event(self, event_type: str, data: Dict[str, Any], 
                      channel: str = "APPLICATION", level: str = "info",
                      direction: Optional[str] = None) -> None:
        """Process an event by logging it to the API and performing any required actions.
        
        Args:
            event_type: The type of event
            data: Event data
            channel: Event channel
            level: Log level
            direction: Message direction for chat events ("incoming" or "outgoing")
        """
        # Add agent_id if not present
        if "agent_id" not in data:
            data["agent_id"] = self.agent_id
            
        # Log the event
        log_event(event_type, data, channel, level, direction)
    
    def process_llm_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Process an LLM request event.
        
        Args:
            prompt: The prompt being sent to the LLM
            kwargs: Additional keyword arguments
            
        Returns:
            Dictionary with request metadata
        """
        # Check for security concerns
        alert = "none"
        if contains_dangerous(prompt):
            alert = "dangerous"
        elif contains_suspicious(prompt):
            alert = "suspicious"
        
        # Prepare metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "prompt": prompt,
            "alert": alert,
            **kwargs
        }
        
        # Log the event
        self.process_event("llm_request", metadata)
        
        return metadata
    
    def process_llm_response(self, prompt: str, response: str, 
                             processing_time: float, **kwargs) -> Dict[str, Any]:
        """Process an LLM response event.
        
        Args:
            prompt: The original prompt
            response: The LLM response
            processing_time: Time taken to process in seconds
            kwargs: Additional keyword arguments
            
        Returns:
            Dictionary with response metadata
        """
        # Check for security concerns in response
        alert = "none"
        if contains_dangerous(response):
            alert = "dangerous"
        elif contains_suspicious(response):
            alert = "suspicious"
        
        # Prepare metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "prompt": prompt,
            "response": response,
            "processing_time": processing_time,
            "alert": alert,
            **kwargs
        }
        
        # Log the event
        self.process_event("llm_response", metadata)
        
        return metadata


# --------------------------------------
# Structured logging helper
# --------------------------------------
def log_event(
    event_type: str, 
    data: Dict[str, Any], 
    channel: str = "SYSTEM", 
    level: str = "info",
    direction: Optional[str] = None
) -> None:
    """Log a structured JSON event with uniform schema.
    
    Args:
        event_type: The type of event (e.g., "chat_exchange", "llm_call")
        data: Event data dictionary
        channel: Event channel (e.g., "SYSTEM", "LLM", "LANGCHAIN", "LANGGRAPH")
        level: Log level (e.g., "info", "warning", "error")
        direction: Message direction for chat events ("incoming" or "outgoing")
    """
    # Debug logging for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        monitor_logger.debug(f"Processing LLM call event: {event_type}")
    
    # Check if this is a framework_patch event for the weather agent
    agent_id = config_manager.get("monitoring.agent_id", "unknown")
    if agent_id == "weather-agent" and event_type == "framework_patch":
        monitor_logger.debug(f"Skipping framework_patch event for weather-agent")
        return
    
    # Generate event ID for duplicate detection
    event_id = _get_event_id(event_type, data)
    
    # Check if we've already processed this event recently
    if event_id in _processed_events:
        monitor_logger.debug(f"Skipping duplicate event: {event_type}")
        return
    
    # Add to processed events set
    _processed_events.add(event_id)
    # Limit the size of the set to prevent memory growth
    if len(_processed_events) > 1000:
        # Remove oldest entries (arbitrary number)
        try:
            for _ in range(100):
                _processed_events.pop()
        except KeyError:
            pass
    
    # Get agent_id and config from configuration
    agent_id = config_manager.get("monitoring.agent_id")
    
    # Create base record with required fields
    record = {
        "timestamp": datetime.now().isoformat(),
        "level": level.upper(),
        "agent_id": agent_id or "unknown",
        "event_type": event_type,
        "channel": channel.upper(),
    }
    
    # Add direction for chat events if provided
    if direction:
        record["direction"] = direction
        
    # Add session/conversation ID if present in data
    if "session_id" in data:
        record["session_id"] = data["session_id"]
    if "conversation_id" in data:
        record["conversation_id"] = data["conversation_id"]
    
    # Capture call stack for debugging
    import traceback
    import inspect
    
    call_stack = []
    current_frame = inspect.currentframe()
    
    if current_frame:
        # Skip this function and go up 2 levels to find the caller
        frame = current_frame.f_back
        if frame:
            frame = frame.f_back
            
        while frame:
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            function = frame.f_code.co_name
            
            # Format the frame info and add to call stack
            call_info = {
                "file": os.path.basename(filename),
                "line": lineno,
                "function": function
            }
            call_stack.append(call_info)
            
            # Go up one level
            frame = frame.f_back
            
            # Limit stack depth to avoid huge logs
            if len(call_stack) >= 5:
                break
                
        # Add caller info to record
        if call_stack:
            record["caller"] = call_stack[0]
    
    # Add data to record
    record["data"] = data
    
    # Extract content from nested message structures
    content_values = []
    
    # Check for direct string fields first
    for field in ["content", "message", "text", "prompt", "response", "value"]:
        if field in data and isinstance(data[field], str):
            content_values.append(data[field])
    
    # Handle nested structures (arrays of messages common in LLM APIs)
    for field in ["prompt", "messages", "inputs"]:
        if field in data:
            # Handle array of messages
            if isinstance(data[field], list):
                for item in data[field]:
                    # Handle message objects with content field
                    if isinstance(item, dict) and "content" in item:
                        if isinstance(item["content"], str):
                            content_values.append(item["content"])
                        # Handle array of content blocks
                        elif isinstance(item["content"], list):
                            for content_block in item["content"]:
                                if isinstance(content_block, dict) and "text" in content_block:
                                    content_values.append(content_block["text"])
                                elif isinstance(content_block, str):
                                    content_values.append(content_block)
    
    # Check all extracted content values for dangerous or suspicious words
    alert = "none"
    for content in content_values:
        if contains_dangerous(content):
            alert = "dangerous"
            level = "warning"  # Upgrade log level for dangerous alerts
            record["level"] = level.upper()
            break
        elif contains_suspicious(content) and alert != "dangerous":
            alert = "suspicious"
    
    # Set the alert if found
    if alert != "none":
        data["alert"] = alert
        record["alert"] = alert
    
    # Keep existing specific field checks
    if "prompt" in data and isinstance(data["prompt"], str):
        alert = "none"
        if contains_dangerous(data["prompt"]):
            alert = "dangerous"
            level = "warning"  # Upgrade log level for dangerous alerts
            record["level"] = level.upper()
        elif contains_suspicious(data["prompt"]):
            alert = "suspicious"
        
        if alert != "none":
            data["alert"] = alert
            record["alert"] = alert
    
    if "response" in data and isinstance(data["response"], str):
        alert = "none"
        if contains_dangerous(data["response"]):
            alert = "dangerous"
            level = "warning"  # Upgrade log level for dangerous alerts
            record["level"] = level.upper()
        elif contains_suspicious(data["response"]):
            alert = "suspicious"
        
        if alert != "none":
            data["response_alert"] = alert
            record["response_alert"] = alert
    
    # Log to file
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        try:
            log_to_file(record, log_file)
        except Exception as e:
            monitor_logger.error(f"Failed to write to log file: {e}")
    
    # Send to API
    try:
        log_to_db(
            agent_id=agent_id or "unknown",
            event_type=event_type,
            data=data,
            channel=channel,
            level=level,
            direction=direction
        )
    except Exception as e:
        monitor_logger.error(f"Failed to send event to API: {e}")


def _estimate_tokens(text: Any) -> int:
    """Estimate the number of tokens in a text string.
    
    This is a simple approximation. For production use, consider using a tokenizer.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if text is None:
        return 0
    # Simple approximation: 4 characters per token on average
    return len(str(text)) // 4


# -------------- Helpers for LLM calls --------------
def _extract_prompt(args: tuple, kwargs: Dict[str, Any]) -> str:
    """Extract prompt from function arguments.
    
    This function handles multiple input formats:
    - Direct Anthropic/OpenAI messages format
    - LangChain inputs
    - String prompts
    - Various dictionary formats
    """
    try:
        # Case 1: Handle messages parameter (common in newer LLM APIs)
        if "messages" in kwargs:
            return json.dumps(kwargs["messages"])
            
        # Case 2: Handle LangChain input format
        elif "input" in kwargs and isinstance(kwargs["input"], dict):
            # Extract the actual input value
            for key in ["input", "query", "question", "prompt", "text"]:
                if key in kwargs["input"]:
                    return str(kwargs["input"][key])
            # If no specific key found, return the whole input
            return json.dumps(kwargs["input"])
            
        # Case 3: Handle direct input formats
        elif "input" in kwargs:
            return str(kwargs["input"])
        elif "prompt" in kwargs:
            return str(kwargs["prompt"])
        elif "query" in kwargs:
            return str(kwargs["query"])
            
        # Case 4: Handle positional arguments
        elif args:
            # First positional arg is often the prompt
            if isinstance(args[0], (str, list, dict)):
                try:
                    return json.dumps(args[0])
                except:
                    return str(args[0])
                    
        # Case 5: Look for LangGraph specific formats
        for key in kwargs:
            if isinstance(kwargs[key], dict) and "content" in kwargs[key]:
                return str(kwargs[key]["content"])
                
        # Fallback: Try to extract something useful from kwargs
        if kwargs:
            try:
                return json.dumps(kwargs)
            except:
                return str(kwargs)
                
        return ""
    except Exception as e:
        # Last resort with error note
        return f"[Error extracting prompt: {str(e)}] Args: {str(args)[:100]}, Kwargs: {str(kwargs)[:100]}"


def _extract_response(result: Any) -> str:
    """Extract response text from LLM result.
    
    This function handles multiple formats:
    - Direct Anthropic/OpenAI API responses
    - LangChain Chain outputs
    - LangGraph outputs
    - Message objects
    - Dictionary objects with common response fields
    """
    try:
        # Case 1: Handle direct Anthropic responses (Claude API)
        if hasattr(result, "content"):
            if isinstance(result.content, list):
                texts = [item.text if hasattr(item, "text") else str(item) for item in result.content]
                return "\n".join(texts)
            else:
                return str(result.content)
                
        # Case 2: Handle LangChain Chain outputs
        elif isinstance(result, dict):
            # Common LangChain output format
            if "response" in result:
                return str(result["response"])
            # Alternative output keys
            elif "output" in result:
                return str(result["output"])
            elif "result" in result:
                return str(result["result"])
            elif "content" in result:
                return str(result["content"])
            # LangGraph sometimes uses "outputs" with nested structure
            elif "outputs" in result:
                outputs = result["outputs"]
                if isinstance(outputs, dict) and "output" in outputs:
                    return str(outputs["output"])
                return str(outputs)
                
        # Case 3: Handle message objects (common in newer LLM libraries)
        elif hasattr(result, "message") and hasattr(result.message, "content"):
            return str(result.message.content)
            
        # Case 4: Handle OpenAI API responses
        elif hasattr(result, "choices") and len(getattr(result, "choices", [])) > 0:
            choices = result.choices
            if hasattr(choices[0], "message") and hasattr(choices[0].message, "content"):
                return choices[0].message.content
            elif hasattr(choices[0], "text"):
                return choices[0].text
                
        # Fallback: Convert to JSON if possible
        try:
            return json.dumps(result)
        except:
            return str(result)
            
    except Exception as e:
        # Last resort: stringification with error note
        return f"[Error extracting response: {str(e)}] {str(result)}"


def pre_monitor_llm(channel: str, args: tuple, kwargs: Dict[str, Any]) -> tuple:
    """Pre-monitoring hook for LLM calls."""
    start_time = time.time()
    prompt = _extract_prompt(args, kwargs)
    if contains_dangerous(prompt):
        alert = "dangerous"
    elif contains_suspicious(prompt):
        alert = "suspicious"
    else:
        alert = "none"

    # Debug logging before creating LLM_call_start event
    monitor_logger.debug(f"Creating LLM_call_start event in channel: {channel}")
    log_event("LLM_call_start", {"prompt": prompt, "alert": alert}, channel)
    # Debug logging after creating LLM_call_start event
    monitor_logger.debug(f"Created LLM_call_start event with prompt length: {len(prompt)}")
    
    return start_time, prompt, alert


def post_monitor_llm(channel: str, start_time: float, result: Any) -> None:
    """Post-monitoring hook for LLM calls."""
    duration = time.time() - start_time
    response = _extract_response(result)
    
    # Expand response data with more detailed extraction
    response_data = {
        "duration": duration,
        "response": response,
        "alert": "none"
    }
    
    # Add additional metadata if available
    if hasattr(result, "model") and result.model:
        response_data["model"] = result.model
    
    # Add usage information if available
    if hasattr(result, "usage"):
        response_data["usage"] = {
            "prompt_tokens": getattr(result.usage, "prompt_tokens", None),
            "completion_tokens": getattr(result.usage, "completion_tokens", None),
            "total_tokens": getattr(result.usage, "total_tokens", None)
        }
    
    # Perform security check
    if contains_dangerous(response):
        response_data["alert"] = "dangerous"
    elif contains_suspicious(response):
        response_data["alert"] = "suspicious"
    
    # Debug logging before creating LLM_call_finish event
    monitor_logger.debug(f"Creating LLM_call_finish event in channel: {channel}")
    # Log the event with all gathered information
    log_event("LLM_call_finish", response_data, channel)
    # Debug logging after creating LLM_call_finish event
    monitor_logger.debug(f"Created LLM_call_finish event with response length: {len(response)}")


# --------------------------------------
# Monitoring hooks for function calls
# --------------------------------------
def pre_monitor_call(func: Any, channel: str, args: tuple, kwargs: Dict[str, Any]) -> float:
    """Pre-monitoring hook for normal function calls."""
    start_time = time.time()
    
    # Convert args and kwargs to strings for logging
    try:
        args_str = json.dumps(args)
    except:
        args_str = str(args)
    
    try:
        kwargs_str = json.dumps(kwargs)
    except:
        kwargs_str = str(kwargs)
    
    log_event(
        "call_start",
        {"function": func.__name__, "args": args_str, "kwargs": kwargs_str},
        channel,
    )
    return start_time


def post_monitor_call(func: Any, channel: str, start_time: float, result: Any) -> None:
    """Post-monitoring hook for normal function calls."""
    duration = time.time() - start_time
    try:
        result_str = json.dumps(result)
    except:
        result_str = str(result)
    data = {"function": func.__name__, "duration": duration, "result": result_str}
    log_event("call_finish", data, channel)


# -------------- Helpers for MCP tool calls --------------
def pre_monitor_mcp_tool(channel: str, tool_name: str, args: tuple, kwargs: Dict[str, Any]) -> float:
    """Pre-monitoring hook for MCP tool calls."""
    start_time = time.time()
    
    # Convert args and kwargs to strings for logging
    try:
        args_str = json.dumps(args)
    except:
        args_str = str(args)
    
    try:
        kwargs_str = json.dumps(kwargs)
    except:
        kwargs_str = str(kwargs)
    
    # Check for suspicious or dangerous content in the tool call
    combined_input = f"{tool_name} {args_str} {kwargs_str}"
    if contains_dangerous(combined_input):
        alert = "dangerous"
        log_event(
            "MCP_tool_call_blocked",
            {"tool": tool_name, "args": args_str, "kwargs": kwargs_str, "reason": "dangerous content"},
            channel,
            "warning",
        )
        raise ValueError("Blocked MCP tool call due to dangerous terms")
    elif contains_suspicious(combined_input):
        alert = "suspicious"
    else:
        alert = "none"
    
    log_event(
        "MCP_tool_call_start",
        {"tool": tool_name, "args": args_str, "kwargs": kwargs_str, "alert": alert},
        channel,
    )
    return start_time


def post_monitor_mcp_tool(channel: str, tool_name: str, start_time: float, result: Any) -> None:
    """Post-monitoring hook for MCP tool calls."""
    duration = time.time() - start_time
    
    # Convert result to string for logging
    try:
        result_str = json.dumps(result)
    except:
        result_str = str(result)
    
    # Check for suspicious or dangerous content in the result
    if contains_dangerous(result_str):
        alert = "dangerous"
    elif contains_suspicious(result_str):
        alert = "suspicious"
    else:
        alert = "none"
    
    log_event(
        "MCP_tool_call_finish",
        {"tool": tool_name, "duration": duration, "result": result_str, "alert": alert},
        channel,
    )


# --------------------------------------
# New function for standardized event processing
# --------------------------------------
def process_standardized_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Process an event using the standardized schema conversion layer.
    
    This function creates a standardized event using the new conversion layer,
    then logs it to both the file and database.
    
    Args:
        agent_id: Agent ID
        event_type: Event type
        data: Event data
        channel: Event channel
        level: Log level
        timestamp: Event timestamp
        direction: Event direction
        session_id: Session ID
    """
    # Debug logging for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        monitor_logger.debug(f"Converting event to standardized schema: {event_type}")
    
    # Check if this is a framework_patch event for the weather agent
    if agent_id == "weather-agent" and event_type == "framework_patch":
        monitor_logger.debug(f"Skipping framework_patch event for weather-agent")
        return
    
    # Check for duplicate events
    event_id = _get_event_id(event_type, data, timestamp)
    if event_id in _processed_events:
        monitor_logger.debug(f"Skipping duplicate standardized event: {event_type}")
        return
    
    # Add to processed events set
    _processed_events.add(event_id)
        
    # Get timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
        
    # Convert to standardized event
    standardized_event = create_standardized_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel,
        level=level,
        timestamp=timestamp,
        direction=direction,
        session_id=session_id
    )
    
    # Debug logging after conversion for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        monitor_logger.debug(f"Standardized event created: {event_type}")
    
    # Convert to dictionary for logging
    event_dict = standardized_event.to_dict()
    
    # Log to file using log_to_file function
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        try:
            log_to_file(event_dict, log_file)
        except Exception as e:
            monitor_logger.error(f"Failed to write to log file: {e}")
    
    # Send event to API
    try:
        # Debug logging before sending to API for LLM call events
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            monitor_logger.debug(f"Sending standardized event to API: {event_type}")
            
        # Send the event to the API using send_event_to_api instead of log_to_db
        # to ensure proper routing to the API endpoint
        success = send_event_to_api(
            agent_id=agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level,
            timestamp=timestamp,
            direction=direction
        )
        
        # Debug logging after sending to API for LLM call events
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            monitor_logger.debug(f"Sent standardized event to API: {event_type}, success: {success}")
    except Exception as e:
        monitor_logger.error(f"Failed to send event to API: {e}")

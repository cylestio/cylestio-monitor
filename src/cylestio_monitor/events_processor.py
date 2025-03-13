# src/cylestio_monitor/events_processor.py
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.db import utils as db_utils

monitor_logger = logging.getLogger("CylestioMonitor")

# Get configuration manager instance
config_manager = ConfigManager()

# --------------------------------------
# Helper functions for normalization and keyword checking
# --------------------------------------
def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    if text is None:
        return ""
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
        """Process an event by logging it to the database and performing any required actions.
        
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
    # Get agent_id and config from configuration
    agent_id = config_manager.get("monitoring.agent_id")
    suspicious_words = config_manager.get("monitoring.suspicious_words", [])
    dangerous_words = config_manager.get("monitoring.dangerous_words", [])
    
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
    
    # Capture full call stack
    import traceback
    import inspect
    
    call_stack = []
    current_frame = inspect.currentframe()
    
    try:
        while current_frame:
            info = inspect.getframeinfo(current_frame)
            # Skip internal cylestio_monitor frames
            if "cylestio_monitor" not in info.filename:
                # Get the source code context
                try:
                    with open(info.filename) as f:
                        lines = f.readlines()
                        start = max(info.lineno - 2, 0)
                        context = ''.join(lines[start:info.lineno + 1]).strip()
                except:
                    context = info.code_context[0].strip() if info.code_context else "N/A"
                
                call_stack.append({
                    "file": info.filename,
                    "line": info.lineno,
                    "function": info.function,
                    "code_context": context
                })
            current_frame = current_frame.f_back
    finally:
        del current_frame  # Prevent reference cycles
    
    # Process data for security checks
    def check_content(content: Any) -> Dict[str, Any]:
        if not isinstance(content, (str, dict, list)):
            return {"alert_level": "none"}
        
        content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
        content_normalized = normalize_text(content_str)
        
        # Check for dangerous/suspicious content
        found_dangerous = [word for word in dangerous_words if word in content_normalized]
        found_suspicious = [word for word in suspicious_words if word in content_normalized]
        
        if found_dangerous:
            return {
                "alert_level": "dangerous",
                "matched_terms": found_dangerous,
                "reason": "dangerous_content"
            }
        elif found_suspicious:
            return {
                "alert_level": "suspicious", 
                "matched_terms": found_suspicious,
                "reason": "suspicious_content"
            }
        return {"alert_level": "none"}
    
    # Process all data fields for security checks
    security_checks = {
        key: check_content(value)
        for key, value in data.items()
        if isinstance(value, (str, dict, list))
    }
    
    # Determine overall alert level
    alert_levels = [check["alert_level"] for check in security_checks.values()]
    overall_alert = (
        "dangerous" if "dangerous" in alert_levels else
        "suspicious" if "suspicious" in alert_levels else
        "none"
    )
    
    # Ensure performance metrics are included
    performance_data = data.get("performance", {})
    if not performance_data:
        # Add basic performance data if not present
        performance_data = {
            "timestamp": datetime.now().isoformat()
        }
        
        # Add duration if available
        if "duration" in data:
            performance_data["duration_ms"] = data["duration"] * 1000
        elif "duration_ms" in data:
            performance_data["duration_ms"] = data["duration_ms"]
            
    # Build enhanced metadata
    enhanced_data = {
        # Original data
        **data,
        
        # Call stack information
        "call_stack": call_stack,
        
        # Security information
        "security": {
            "alert_level": overall_alert,
            "field_checks": security_checks
        },
        
        # Framework-specific metadata (if present)
        "framework": {
            "name": channel.lower(),
            "version": data.get("framework_version"),
            "components": data.get("components", {})
        },
        
        # Performance metrics
        "performance": performance_data
    }
    
    # Add model details if present
    if "model" in data:
        enhanced_data["model"] = {
            **data["model"],
            "provider": data["model"].get("provider", channel.lower())
        }
    
    # Add input/output details if present
    if "input" in data and not isinstance(data["input"], dict):
        enhanced_data["input"] = {
            "content": data["input"],
            "estimated_tokens": _estimate_tokens(data["input"])
        }
        
    if "output" in data and not isinstance(data["output"], dict):
        enhanced_data["output"] = {
            "content": data["output"],
            "estimated_tokens": _estimate_tokens(data["output"])
        }
    
    # Update record with enhanced data
    record["data"] = enhanced_data
    
    # Convert to JSON string
    msg = json.dumps(record)
    
    # Log to the standard logger
    if level.lower() == "debug":
        monitor_logger.debug(msg, extra={"channel": channel})
    elif level.lower() == "warning":
        monitor_logger.warning(msg, extra={"channel": channel})
    elif level.lower() == "error":
        monitor_logger.error(msg, extra={"channel": channel})
    else:
        monitor_logger.info(msg, extra={"channel": channel})
    
    # Log to the SQLite database
    try:
        # Only log to database if agent_id is set
        if agent_id:
            # Log to the database
            db_utils.log_to_db(
                agent_id=agent_id,
                event_type=event_type,
                data=record["data"],
                channel=channel,
                level=level,
                timestamp=datetime.now()
            )
    except Exception as e:
        monitor_logger.error(f"Failed to log event to database: {e}")
    
    # Log to JSON file if configured
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        try:
            with open(log_file, "a") as f:
                f.write(msg + "\n")
        except Exception as e:
            monitor_logger.error(f"Failed to log event to file {log_file}: {e}")


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
    """Extract prompt from function arguments."""
    if "messages" in kwargs:
        try:
            return json.dumps(kwargs["messages"])
        except:
            return str(kwargs["messages"])
    elif args:
        try:
            return json.dumps(args[0])
        except:
            return str(args[0])
    return ""


def _extract_response(result: Any) -> str:
    """Extract response text from LLM result."""
    try:
        if hasattr(result, "content"):
            texts = [item.text if hasattr(item, "text") else str(item) for item in result.content]
            return "\n".join(texts)
        else:
            return json.dumps(result)
    except:
        return str(result)


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

    log_event("LLM_call_start", {"prompt": prompt, "alert": alert}, channel)
    return start_time, prompt, alert


def post_monitor_llm(channel: str, start_time: float, result: Any) -> None:
    """Post-monitoring hook for LLM calls."""
    duration = time.time() - start_time
    response = _extract_response(result)
    if contains_dangerous(response):
        alert = "dangerous"
    elif contains_suspicious(response):
        alert = "suspicious"
    else:
        alert = "none"
    log_event(
        "LLM_call_finish", {"duration": duration, "response": response, "alert": alert}, channel
    )


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

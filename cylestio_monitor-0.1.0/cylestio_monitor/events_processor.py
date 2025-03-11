# src/cylestio_monitor/events_processor.py
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict

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
# Structured logging helper
# --------------------------------------
def log_event(
    event_type: str, data: Dict[str, Any], channel: str = "SYSTEM", level: str = "info"
) -> None:
    """Log a structured JSON event."""
    record = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "channel": channel,
    }
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
        # Get agent ID from configuration
        agent_id = config_manager.get("monitoring.agent_id")
        
        # Only log to database if agent_id is set
        if agent_id:
            # Log to the database
            db_utils.log_to_db(
                agent_id=agent_id,
                event_type=event_type,
                data=data,
                channel=channel,
                level=level,
                timestamp=datetime.now()
            )
    except Exception as e:
        monitor_logger.error(f"Failed to log event to database: {e}")


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

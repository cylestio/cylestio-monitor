# src/cylestio_monitor/events_processor.py
import json
import time
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

monitor_logger = logging.getLogger("CylestioMonitor")

# Define keywords for security checks
SUSPICIOUS_KEYWORDS = ["REMOVE", "CLEAR", "HACK", "BOMB"]
DANGEROUS_KEYWORDS = ["DROP", "DELETE", "SHUTDOWN", "EXEC(", "FORMAT", "RM -RF"]

# --------------------------------------
# Helper functions for normalization and keyword checking
# --------------------------------------
def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    return " ".join(str(text).split()).upper()

def contains_suspicious(text: str) -> bool:
    """Check if text contains suspicious keywords."""
    up = normalize_text(text)
    return any(kw in up for kw in SUSPICIOUS_KEYWORDS)

def contains_dangerous(text: str) -> bool:
    """Check if text contains dangerous keywords."""
    up = normalize_text(text)
    return any(kw in up for kw in DANGEROUS_KEYWORDS)

# --------------------------------------
# Structured logging helper
# --------------------------------------
def log_event(
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info"
) -> None:
    """Log a structured JSON event."""
    record = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "channel": channel
    }
    msg = json.dumps(record)
    if level.lower() == "debug":
        monitor_logger.debug(msg, extra={"channel": channel})
    elif level.lower() == "warning":
        monitor_logger.warning(msg, extra={"channel": channel})
    elif level.lower() == "error":
        monitor_logger.error(msg, extra={"channel": channel})
    else:
        monitor_logger.info(msg, extra={"channel": channel})

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
            texts = [item.text if hasattr(item, "text") else str(item)
                     for item in result.content]
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
    log_event("LLM_call_finish", {"duration": duration, "response": response, "alert": alert}, channel)

# -------------- Helpers for normal calls --------------
def pre_monitor_call(func: Any, channel: str, args: tuple, kwargs: Dict[str, Any]) -> None:
    """Pre-monitoring hook for normal function calls."""
    data = {
        "function": func.__name__,
        "args": str(args),
        "kwargs": str(kwargs)
    }
    log_event("call_start", data, channel)

def post_monitor_call(func: Any, channel: str, start_time: float, result: Any) -> None:
    """Post-monitoring hook for normal function calls."""
    duration = time.time() - start_time
    try:
        result_str = json.dumps(result)
    except:
        result_str = str(result)
    data = {
        "function": func.__name__,
        "duration": duration,
        "result": result_str
    }
    log_event("call_finish", data, channel)
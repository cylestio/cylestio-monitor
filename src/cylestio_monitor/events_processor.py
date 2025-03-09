# src/events_processor.py
import json
import time
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

monitor_logger = logging.getLogger("CylestioMonitor")

SUSPICIOUS_KEYWORDS = ["REMOVE", "CLEAR", "HACK", "BOMB"]
DANGEROUS_KEYWORDS = ["DROP", "DELETE", "SHUTDOWN", "EXEC(", "FORMAT", "RM -RF"]

class EventsProcessor:
    """Processes and aggregates monitoring events."""
    
    def __init__(self):
        """Initialize events processor."""
        self.events: List[Dict[str, Any]] = []
        self.is_running = False
        
    def start(self) -> None:
        """Start processing events."""
        self.is_running = True
        
    def stop(self) -> None:
        """Stop processing events."""
        self.is_running = False
        
    def process_event(self, event: Dict[str, Any]) -> None:
        """Process a monitoring event.
        
        Args:
            event: Event data dictionary
        """
        if not self.is_running:
            return
            
        self.events.append(event)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of processed events.
        
        Returns:
            Dictionary with event statistics
        """
        return {
            "total_events": len(self.events),
            "events_by_type": self._count_by_type(),
            "alerts": self._get_alerts(),
            "latest_events": self.events[-10:] if self.events else []
        }
        
    def _count_by_type(self) -> Dict[str, int]:
        """Count events by type."""
        counts: Dict[str, int] = {}
        for event in self.events:
            event_type = event.get("event", "unknown")
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
        
    def _get_alerts(self) -> List[Dict[str, Any]]:
        """Get list of security alerts."""
        return [
            event for event in self.events
            if event.get("data", {}).get("alert") in ["suspicious", "dangerous"]
        ]

def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    return " ".join(text.split()).upper()

def contains_suspicious(text: str) -> bool:
    """Check if text contains suspicious keywords."""
    up = normalize_text(text)
    return any(kw in up for kw in SUSPICIOUS_KEYWORDS)

def contains_dangerous(text: str) -> bool:
    """Check if text contains dangerous keywords."""
    up = normalize_text(text)
    return any(kw in up for kw in DANGEROUS_KEYWORDS)

# Global events processor instance
events_processor = EventsProcessor()

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
    else:
        monitor_logger.info(msg, extra={"channel": channel})
        
    # Process event
    events_processor.process_event(record)

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
            return "\n".join(item.text for item in result.content if hasattr(item, "text"))
        else:
            return json.dumps(result)
    except:
        return str(result)

def pre_monitor_llm(channel: str, args: tuple, kwargs: Dict[str, Any]) -> tuple:
    """Pre-monitoring hook for LLM calls."""
    prompt = _extract_prompt(args, kwargs)
    if contains_dangerous(prompt):
        alert = "dangerous"
    elif contains_suspicious(prompt):
        alert = "suspicious"
    else:
        alert = "none"

    log_event("LLM_call_start", {"prompt": prompt, "alert": alert}, channel, level="info")
    start_time = time.time()
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
    log_event("call_start", data, channel, level="info")

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
    log_event("call_finish", data, channel, level="info")
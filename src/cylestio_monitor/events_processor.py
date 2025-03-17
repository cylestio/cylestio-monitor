# src/cylestio_monitor/events_processor.py
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
import os

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.db import utils as db_utils
from cylestio_monitor.event_logger import log_console_message, log_to_db, log_to_file, process_and_log_event

monitor_logger = logging.getLogger("CylestioMonitor")

# Get configuration manager instance
config_manager = ConfigManager()

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
        if frame and frame.f_back:
            frame = frame.f_back
            
        # Extract caller info
        if frame:
            caller_info = inspect.getframeinfo(frame)
            caller = {
                "file": os.path.basename(caller_info.filename),
                "line": caller_info.lineno,
                "function": caller_info.function
            }
            record["caller"] = caller
    
    # Add full data to record
    record["data"] = data
    
    # Perform security checks if words to watch for are configured
    if suspicious_words or dangerous_words:
        import json
        
        # Convert to string for easy pattern matching
        event_str = json.dumps(record).lower()
        
        suspicious_matches = [word for word in suspicious_words if word.lower() in event_str]
        dangerous_matches = [word for word in dangerous_words if word.lower() in event_str]
        
        if suspicious_matches:
            record["security"] = {
                "suspicious_matches": suspicious_matches,
                "severity": "warning"
            }
            
        if dangerous_matches:
            # If record doesn't have a security field yet, add it
            if "security" not in record:
                record["security"] = {}
                
            record["security"]["dangerous_matches"] = dangerous_matches
            record["security"]["severity"] = "critical"
    
    # Log to file using log_to_file function
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        try:
            log_to_file(record, log_file)
        except Exception as e:
            monitor_logger.error(f"Failed to write to log file: {e}")
    
    # Store event in database with proper relations
    if agent_id:
        try:
            from cylestio_monitor.event_logger import log_to_db
            
            # Add direction to data if it was provided separately
            if direction and "direction" not in data:
                data["direction"] = direction
                
            # Log to database using the relational schema
            log_to_db(
                agent_id=agent_id,
                event_type=event_type,
                data=data,
                channel=channel,
                level=level,
                timestamp=datetime.fromisoformat(record["timestamp"])
            )
        except Exception as e:
            monitor_logger.error(f"Failed to log event to database: {e}")
    
    # Log security alerts as separate events
    if "security" in record and record["security"].get("severity") == "critical":
        security_data = {
            "severity": "critical",
            "matches": record["security"].get("dangerous_matches", []),
            "original_event": {
                "event_type": event_type,
                "channel": channel
            }
        }
        
        # Log directly to file to ensure it's captured even if database logging fails
        if log_file:
            try:
                security_record = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "CRITICAL",
                    "agent_id": agent_id or "unknown",
                    "event_type": "security_alert",
                    "channel": "SECURITY",
                    "data": security_data
                }
                
                log_to_file(security_record, log_file)
            except Exception as e:
                monitor_logger.error(f"Failed to write security alert to log file: {e}")
        
        # Log to database through the specialized handler
        if agent_id:
            try:
                log_to_db(
                    agent_id=agent_id,
                    event_type="security_alert",
                    data=security_data,
                    channel="SECURITY",
                    level="critical"
                )
            except Exception as e:
                monitor_logger.error(f"Failed to log security alert to database: {e}")


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

    log_event("LLM_call_start", {"prompt": prompt, "alert": alert}, channel)
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
    
    # Log the event with all gathered information
    log_event("LLM_call_finish", response_data, channel)


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

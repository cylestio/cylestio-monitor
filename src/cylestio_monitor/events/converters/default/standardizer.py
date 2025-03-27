"""
Event name standardization.

This module contains utilities for standardizing event names according to OpenTelemetry conventions.
"""

def standardize_event_name(event_type: str) -> str:
    """
    Standardize event names according to OpenTelemetry conventions.
    
    Args:
        event_type: The original event type
        
    Returns:
        str: The standardized event name
    """
    # OpenTelemetry AI-specific event types
    otel_event_map = {
        # LLM events
        "LLM_call_start": "llm.request",
        "LLM_call_finish": "llm.response",
        "llm_request": "llm.request",
        "llm_response": "llm.response",
        "completion_request": "llm.completion.request",
        "completion_response": "llm.completion.response",
        "chat_request": "llm.chat.request",
        "chat_response": "llm.chat.response",
        
        # Tool events
        "tool_call": "tool.call",
        "tool_result": "tool.result",
        
        # Agent events
        "agent_start": "agent.start",
        "agent_finish": "agent.finish",
        
        # Session events
        "session_start": "session.start",
        "session_end": "session.end",
        
        # User interaction
        "user_message": "user.message",
        "user_feedback": "user.feedback",
        "assistant_message": "assistant.message"
    }
    
    # Return mapped name or original if no mapping exists
    return otel_event_map.get(event_type, event_type) 
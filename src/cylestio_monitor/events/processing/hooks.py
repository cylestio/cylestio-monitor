"""
Monitoring hooks for integrating with different frameworks and libraries.

This module provides hook functions for monitoring various systems including LLM frameworks,
langchain, langgraph, and other integrations.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.events.processing.logger import log_event
from cylestio_monitor.events.processing.security import contains_dangerous, contains_suspicious


# Initialize logger
logger = logging.getLogger("CylestioMonitor")
config_manager = ConfigManager()


def llm_call_hook(provider: str, model: str, prompt: Union[str, List[Dict[str, str]]], **kwargs) -> Dict[str, Any]:
    """Log an LLM call before it happens and check for security concerns.
    
    Args:
        provider: The LLM provider (e.g., OpenAI, Anthropic)
        model: Model identifier
        prompt: The prompt being sent to the LLM
        **kwargs: Additional context for the LLM call
        
    Returns:
        Dict with call_id and safe_to_call flag
    """
    # Generate a unique call ID to track this specific LLM call
    call_id = str(uuid.uuid4())
    
    # Extract agent_id from kwargs or use default
    agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
    
    # Ensure we have a valid agent_id
    if not agent_id or agent_id == "unknown":
        logger.warning("LLM call hook invoked without a valid agent_id")
        if not config_manager.get("monitoring.default_agent_id"):
            logger.warning("No default agent_id configured for monitoring")

    # Prepare the event data
    data = {
        "agent_id": agent_id,
        "provider": provider,
        "model": model,
        "call_id": call_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add the prompt to the data
    if isinstance(prompt, str):
        data["prompt"] = prompt
        # Check for security concerns in the prompt string
        is_dangerous = contains_dangerous(prompt)
        is_suspicious = contains_suspicious(prompt)
    else:
        # Handle chat format (list of message dicts)
        data["messages"] = prompt
        # Check for security concerns in all messages
        is_dangerous = any(contains_dangerous(msg.get("content", "")) for msg in prompt if isinstance(msg, dict))
        is_suspicious = any(contains_suspicious(msg.get("content", "")) for msg in prompt if isinstance(msg, dict))
    
    # Add any additional provided kwargs to the data
    for key, value in kwargs.items():
        if key not in data and key != "agent_id":
            data[key] = value
    
    # Set safe_to_call flag based on security concerns
    safe_to_call = not is_dangerous
    data["safe_to_call"] = safe_to_call
    
    # Log the LLM call start event
    if is_dangerous:
        # Log as blocked event if it contains dangerous content
        log_event(
            event_type="LLM_call_blocked",
            data=data,
            channel="LLM",
            level="warning"
        )
    else:
        # Log normal start event
        log_event(
            event_type="LLM_call_start",
            data=data,
            channel="LLM",
            level="info"
        )
    
    return {
        "call_id": call_id,
        "safe_to_call": safe_to_call
    }


def llm_response_hook(
    call_id: str,
    provider: str,
    model: str, 
    response: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
    **kwargs
) -> None:
    """Log an LLM response after receiving it.
    
    Args:
        call_id: The unique ID of the call (from llm_call_hook)
        provider: The LLM provider
        model: Model identifier
        response: The response from the LLM
        prompt: Optional prompt that generated this response
        **kwargs: Additional context
    """
    # Extract agent_id from kwargs or use default
    agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
    
    # Prepare the event data
    data = {
        "agent_id": agent_id,
        "provider": provider,
        "model": model,
        "call_id": call_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add the response content
    if isinstance(response, str):
        data["response"] = response
        # Check for security concerns in the response string
        is_dangerous = contains_dangerous(response)
        is_suspicious = contains_suspicious(response)
    elif isinstance(response, dict):
        # Handle OpenAI-style response object
        data["response_obj"] = response
        content = ""
        if "choices" in response and response["choices"]:
            if isinstance(response["choices"][0], dict):
                if "message" in response["choices"][0]:
                    content = response["choices"][0]["message"].get("content", "")
                elif "text" in response["choices"][0]:
                    content = response["choices"][0]["text"]
        elif "content" in response:
            # Direct content field
            content = response["content"]
            
        # Add extracted content and check security
        data["content"] = content
        is_dangerous = contains_dangerous(content)
        is_suspicious = contains_suspicious(content)
    elif isinstance(response, list):
        # Handle list of messages
        data["messages"] = response
        # Check security on all message contents
        is_dangerous = any(contains_dangerous(msg.get("content", "")) 
                          for msg in response if isinstance(msg, dict))
        is_suspicious = any(contains_suspicious(msg.get("content", "")) 
                           for msg in response if isinstance(msg, dict))
    else:
        # Unknown response format
        data["response_format"] = str(type(response))
        is_dangerous = False
        is_suspicious = False
    
    # Add the prompt if provided
    if prompt is not None:
        if isinstance(prompt, str):
            data["prompt"] = prompt
        else:
            data["messages"] = prompt
    
    # Add any additional provided kwargs to the data
    for key, value in kwargs.items():
        if key not in data and key != "agent_id":
            data[key] = value
    
    # Set security flags
    if is_dangerous:
        data["contains_dangerous"] = True
    if is_suspicious:
        data["contains_suspicious"] = True
    
    # Log the LLM call finish event
    log_event(
        event_type="LLM_call_finish",
        data=data,
        channel="LLM",
        level="warning" if is_dangerous or is_suspicious else "info"
    )


def langchain_input_hook(chain_name: str, inputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Log a Langchain component input.
    
    Args:
        chain_name: Name of the Langchain component
        inputs: Input values to the component
        **kwargs: Additional context
        
    Returns:
        Dict with execution_id for tracking this execution
    """
    # Generate execution ID for tracking
    execution_id = str(uuid.uuid4())
    
    # Extract agent_id or use default
    agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
    
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "chain_name": chain_name,
        "execution_id": execution_id,
        "inputs": inputs,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add additional context
    for key, value in kwargs.items():
        if key not in data and key != "agent_id":
            data[key] = value
    
    # Check security concerns in input values
    has_security_concern = False
    for key, value in inputs.items():
        if isinstance(value, str) and (contains_dangerous(value) or contains_suspicious(value)):
            has_security_concern = True
            break
    
    # Log the event
    log_event(
        event_type="langchain_execution_start",
        data=data,
        channel="LANGCHAIN",
        level="warning" if has_security_concern else "info"
    )
    
    return {"execution_id": execution_id}


def langchain_output_hook(
    chain_name: str, 
    execution_id: str, 
    outputs: Dict[str, Any], 
    **kwargs
) -> None:
    """Log a Langchain component output.
    
    Args:
        chain_name: Name of the Langchain component
        execution_id: ID from the input hook
        outputs: Output values from the component
        **kwargs: Additional context
    """
    # Extract agent_id or use default
    agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
    
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "chain_name": chain_name,
        "execution_id": execution_id,
        "outputs": outputs,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add additional context
    for key, value in kwargs.items():
        if key not in data and key != "agent_id":
            data[key] = value
    
    # Check security concerns in output values
    has_security_concern = False
    for key, value in outputs.items():
        if isinstance(value, str) and (contains_dangerous(value) or contains_suspicious(value)):
            has_security_concern = True
            break
    
    # Log the event
    log_event(
        event_type="langchain_execution_finish",
        data=data,
        channel="LANGCHAIN",
        level="warning" if has_security_concern else "info"
    )


def langgraph_state_update_hook(
    graph_name: str,
    state: Dict[str, Any],
    node_name: Optional[str] = None,
    **kwargs
) -> None:
    """Log a LangGraph state update.
    
    Args:
        graph_name: Name of the LangGraph instance
        state: Current state dictionary
        node_name: Optional name of the node that updated the state
        **kwargs: Additional context
    """
    # Extract agent_id or use default
    agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
    
    # Prepare event data
    data = {
        "agent_id": agent_id,
        "graph_name": graph_name,
        "state": state,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add node name if provided
    if node_name:
        data["node_name"] = node_name
    
    # Add additional context
    for key, value in kwargs.items():
        if key not in data and key != "agent_id":
            data[key] = value
    
    # Log the event
    log_event(
        event_type="langgraph_state_update",
        data=data,
        channel="LANGGRAPH",
        level="info"
    )


def register_framework_patch(framework: str, patched_module: str, details: Dict[str, Any] = None) -> None:
    """Register that a framework has been patched for monitoring.
    
    Args:
        framework: Framework name (e.g., "langchain", "openai")
        patched_module: Module name that was patched
        details: Optional details about the patch
    """
    # Prepare event data
    data = {
        "framework": framework,
        "patched_module": patched_module,
        "timestamp": datetime.now().isoformat(),
        "agent_id": config_manager.get("monitoring.agent_id", "unknown")
    }
    
    # Add details if provided
    if details:
        data["details"] = details
    
    # Log the event
    log_event(
        event_type="framework_patch",
        data=data,
        channel="SYSTEM",
        level="debug"
    )


def hook_decorator(event_type: str, channel: str = "SYSTEM", level: str = "info") -> Callable:
    """Decorator for creating custom monitoring hooks.
    
    Args:
        event_type: Type of event to log
        channel: Channel for the event
        level: Log level
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Call the original function
            result = func(*args, **kwargs)
            
            # Extract agent_id from kwargs or use default
            agent_id = kwargs.get("agent_id", config_manager.get("monitoring.agent_id", "unknown"))
            
            # Prepare event data
            data = {
                "agent_id": agent_id,
                "function": func.__name__,
                "args": [str(arg) for arg in args],  # Convert args to strings for logging
                "kwargs": {k: str(v) for k, v in kwargs.items() if k != "agent_id"},  # Exclude agent_id
                "result": str(result) if result is not None else None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log the event
            log_event(
                event_type=event_type,
                data=data,
                channel=channel,
                level=level
            )
            
            return result
        return wrapper
    return decorator 
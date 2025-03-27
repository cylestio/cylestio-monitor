"""
Data extractors for event conversion.

This module provides functions for extracting specific data from events during conversion.
"""

from typing import Any, Dict


def extract_security_info(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract security information from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Security information
    """
    security = {}
    
    # Extract security alert if present
    if "alert" in data:
        security["alert"] = data["alert"]
        
    # Extract other security-related fields
    for key in ["security_level", "blocked", "allowed", "flagged"]:
        if key in data:
            security[key] = data[key]
            
    return security


def extract_performance_metrics(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract performance metrics from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Performance metrics
    """
    performance = {}
    
    # Extract common performance metrics
    perf_keys = ["processing_time", "latency", "tokens", "input_tokens", "output_tokens", "total_tokens"]
    for key in perf_keys:
        if key in data:
            # Use OTel semantic conventions for token metrics
            if key == "input_tokens":
                performance["llm.usage.prompt_tokens"] = data[key]
            elif key == "output_tokens":
                performance["llm.usage.completion_tokens"] = data[key]
            elif key == "total_tokens":
                performance["llm.usage.total_tokens"] = data[key]
            else:
                performance[key] = data[key]
            
    # Extract nested token usage
    if "usage" in data and isinstance(data["usage"], dict):
        for key, value in data["usage"].items():
            if key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                performance[f"llm.usage.{key}"] = value
    
    return performance


def extract_model_info(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract model information from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Model information
    """
    model = {}
    
    # Extract model name
    model_name_keys = ["model", "model_name", "model_id"]
    for key in model_name_keys:
        if key in data:
            model["llm.model"] = data[key]
            break
            
    # Extract other model parameters
    param_keys = ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]
    for key in param_keys:
        if key in data:
            model[f"llm.{key}"] = data[key]
            
    return model


def extract_framework_info(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract framework information from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Framework information
    """
    framework = {}
    
    # Extract channel as framework
    channel = event.get("channel", "").upper()
    if channel and channel != "SYSTEM":
        framework["name"] = channel.lower()
        
    # Extract version if available
    if "framework_version" in data:
        framework["version"] = data["framework_version"]
        
    return framework


def extract_request_info(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract request information from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Request information
    """
    request = {}
    
    # Extract prompt or messages
    if "prompt" in data:
        request["prompt"] = data["prompt"]
        
    if "messages" in data and isinstance(data["messages"], list):
        request["messages"] = data["messages"]
        
    # For events that are clearly requests
    event_type = event.get("event_type", "").lower()
    if event_type.endswith("_request") or event_type == "llm_call_start":
        # Extract request parameters
        for key, value in data.items():
            if key not in ["prompt", "messages", "response", "result"]:
                request[key] = value
                
    # Extract caller if available
    if "caller" in data and isinstance(data["caller"], dict):
        for key, value in data["caller"].items():
            request[f"caller.{key}"] = value
            
    return request


def extract_response_info(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract response information from the event.
    
    Args:
        event: The original event
        data: The data field from the event
        
    Returns:
        Dict[str, Any]: Response information
    """
    response = {}
    
    # Extract completion or response
    if "response" in data:
        response["completion"] = data["response"]
        
    if "completion" in data:
        response["completion"] = data["completion"]
        
    if "result" in data:
        response["result"] = data["result"]
        
    # For events that are clearly responses
    event_type = event.get("event_type", "").lower()
    if event_type.endswith("_response") or event_type.endswith("_result") or event_type == "llm_call_finish":
        # Extract response metadata
        for key, value in data.items():
            if key not in ["prompt", "messages", "response", "completion", "result"]:
                response[key] = value
                
    return response 
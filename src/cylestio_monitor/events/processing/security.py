"""
Security-related functionality for event processing.

This module contains functions for handling security concerns in events,
including detection of suspicious or dangerous content and masking sensitive data.
"""

import re
import copy
from typing import Any, Dict

from cylestio_monitor.config import ConfigManager

# Get configuration manager instance
config_manager = ConfigManager()


def normalize_text(text: str) -> str:
    """
    Normalize text for keyword matching.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text in uppercase with normalized whitespace
    """
    if text is None:
        return "NONE"
    return " ".join(str(text).split()).upper()


def contains_suspicious(text: str) -> bool:
    """
    Check if text contains suspicious keywords.
    
    Args:
        text: The text to check
        
    Returns:
        True if suspicious keywords are found, False otherwise
    """
    normalized = normalize_text(text)
    suspicious_keywords = config_manager.get_suspicious_keywords()
    return any(keyword in normalized for keyword in suspicious_keywords)


def contains_dangerous(text: str) -> bool:
    """
    Check if text contains dangerous keywords.
    
    Args:
        text: The text to check
        
    Returns:
        True if dangerous keywords are found, False otherwise
    """
    normalized = normalize_text(text)
    dangerous_keywords = config_manager.get_dangerous_keywords()
    return any(keyword in normalized for keyword in dangerous_keywords)


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Masks sensitive data like API keys and tokens.
    
    Args:
        data: The data dictionary that may contain sensitive information
        
    Returns:
        Dict: A copy of the data with sensitive information masked
    """
    # Create a deep copy to avoid modifying the original
    masked_data = copy.deepcopy(data)
    
    # Keys that might contain sensitive information
    sensitive_keys = ['api_key', 'key', 'secret', 'password', 'token', 'auth_token', 
                      'authorization', 'access_token', 'refresh_token']
    
    # Keys that should not be masked despite containing sensitive key substrings
    exclude_keys = [
        'input_tokens', 'output_tokens', 'total_tokens',  # LLM token usage metrics
        'prompt_tokens', 'completion_tokens',             # OpenAI token metrics
        'cache_creation_input_tokens', 'cache_read_input_tokens'  # Anthropic cache metrics
    ]
    
    # Regular expressions for common API key and token formats
    api_key_patterns = [
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API key format
        r'Bearer\s+[a-zA-Z0-9\._\-]+',  # Bearer token format
        r'eyJ[a-zA-Z0-9\._\-]{10,}',  # JWT token format
    ]
    
    def _mask_value(value, key_name=''):
        """Recursively mask sensitive values."""
        if isinstance(value, dict):
            return {k: _mask_value(v, k) for k, v in value.items()}
        elif isinstance(value, list):
            return [_mask_value(item) for item in value]
        elif isinstance(value, str):
            # Check if this is a sensitive key, but exclude specific metrics keys
            if any(sensitive_key in key_name.lower() for sensitive_key in sensitive_keys) and \
               not any(key_name == exclude_key for exclude_key in exclude_keys):
                if len(value) > 8:
                    return value[:4] + '*' * (len(value) - 8) + value[-4:]
                else:
                    return '********'
            
            # Check for sensitive patterns in the string regardless of key name
            masked = value
            for pattern in api_key_patterns:
                masked = re.sub(pattern, lambda m: m.group(0)[:4] + '*' * (len(m.group(0)) - 8) + m.group(0)[-4:] 
                                if len(m.group(0)) > 8 else '********', masked)
            return masked
        return value
    
    # Apply masking
    return _mask_value(masked_data)


def check_security_concerns(data: Dict[str, Any]) -> str:
    """
    Check data for security concerns (suspicious or dangerous content).
    
    Args:
        data: The data to check
        
    Returns:
        str: "none", "suspicious", or "dangerous"
    """
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
    for content in content_values:
        if contains_dangerous(content):
            return "dangerous"
        elif contains_suspicious(content):
            return "suspicious"
    
    # Check data values for suspicious or dangerous content
    for key, value in data.items():
        if isinstance(value, str):
            if contains_dangerous(value):
                return "dangerous"
            elif contains_suspicious(value):
                return "suspicious"
    
    return "none" 
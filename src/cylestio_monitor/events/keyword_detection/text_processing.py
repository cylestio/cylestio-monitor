"""
Text processing and keyword detection functions for Cylestio Monitor.

This module provides utilities for normalizing and checking text for keywords.
"""

import logging
import re
from typing import List, Set

from cylestio_monitor.config import ConfigManager

logger = logging.getLogger(__name__)

# Default keywords - these will be used regardless of config
DEFAULT_SUSPICIOUS_KEYWORDS = {
    "attack", "bomb", "clear", "compromise", "exploit", 
    "hack", "malicious", "remove", "vulnerable"
}

DEFAULT_DANGEROUS_KEYWORDS = {
    "alter table", "delete", "destroy", "drop", "drop table",
    "exec(", "format", "rm -rf", "shutdown", "truncate"
}

# Try to load from config, but use defaults as fallback
try:
    config_manager = ConfigManager()
    suspicious_keywords: Set[str] = set(
        [k.lower() for k in config_manager.get("monitoring.suspicious_keywords", [])]
    )
    logger.info(f"Loaded {len(suspicious_keywords)} suspicious keywords from config")
    if not suspicious_keywords:
        logger.warning("No suspicious keywords found in config, using defaults")
        suspicious_keywords = DEFAULT_SUSPICIOUS_KEYWORDS
except Exception as e:
    logger.warning(f"Error loading suspicious keywords from config: {e}, using defaults")
    suspicious_keywords = DEFAULT_SUSPICIOUS_KEYWORDS

logger.info(f"Suspicious keywords: {sorted(list(suspicious_keywords))}")

try:
    dangerous_keywords: Set[str] = set(
        [k.lower() for k in config_manager.get("monitoring.dangerous_keywords", [])]
    )
    logger.info(f"Loaded {len(dangerous_keywords)} dangerous keywords from config")
    if not dangerous_keywords:
        logger.warning("No dangerous keywords found in config, using defaults")
        dangerous_keywords = DEFAULT_DANGEROUS_KEYWORDS
except Exception as e:
    logger.warning(f"Error loading dangerous keywords from config: {e}, using defaults")
    dangerous_keywords = DEFAULT_DANGEROUS_KEYWORDS

logger.info(f"Dangerous keywords: {sorted(list(dangerous_keywords))}")

def normalize_text(text: str) -> str:
    """Normalize text for more accurate keyword matching.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text
    """
    if text is None:
        logger.warning("None text passed to normalize_text")
        return ""
        
    # Convert to lowercase
    normalized = text.lower()
    
    logger.debug(f"Normalizing text: '{text}' -> '{normalized}'")
    
    return normalized

def contains_suspicious(text: str) -> bool:
    """Check if text contains suspicious keywords.
    
    Args:
        text: The text to check
        
    Returns:
        True if suspicious keywords are found
    """
    if not text:
        logger.debug("Empty text passed to contains_suspicious")
        return False
        
    normalized = normalize_text(text)
    
    # Try direct substring match first (faster)
    for keyword in suspicious_keywords:
        if keyword in normalized:
            logger.info(f"Suspicious keyword found: '{keyword}' in '{normalized}'")
            return True
    
    # Extra check for whole word matching of single-word keywords
    # This helps avoid false positives like finding "bomb" in "bombastic"
    for keyword in suspicious_keywords:
        if len(keyword.split()) == 1:  # Only apply to single words
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, normalized):
                logger.info(f"Suspicious keyword found (word boundary): '{keyword}' in '{normalized}'")
                return True
    
    logger.debug(f"No suspicious keywords found in: '{normalized}'")
    return False

def contains_dangerous(text: str) -> bool:
    """Check if text contains dangerous keywords.
    
    Args:
        text: The text to check
        
    Returns:
        True if dangerous keywords are found
    """
    if not text:
        logger.debug("Empty text passed to contains_dangerous")
        return False
        
    normalized = normalize_text(text)
    
    # Try direct substring match first
    for keyword in dangerous_keywords:
        if keyword in normalized:
            logger.info(f"Dangerous keyword found: '{keyword}' in '{normalized}'")
            return True
    
    # Extra check for commands that might have variations
    # Example: "drop table", "drop table users", etc.
    for cmd_fragment in ["drop table", "rm -rf", "exec("]:
        if cmd_fragment in normalized:
            logger.info(f"Dangerous command fragment found: '{cmd_fragment}' in '{normalized}'")
            return True
    
    logger.debug(f"No dangerous keywords found in: '{normalized}'")
    return False

def get_alert_level(text: str) -> str:
    """Get the alert level for a given text.
    
    Args:
        text: The text to check
        
    Returns:
        Alert level: "none", "suspicious", or "dangerous"
    """
    if not text:
        return "none"
        
    if contains_dangerous(text):
        logger.info(f"Dangerous content detected: '{text}'")
        return "dangerous"
        
    if contains_suspicious(text):
        logger.info(f"Suspicious content detected: '{text}'")
        return "suspicious"
        
    logger.debug(f"No alert for: '{text}'")
    return "none" 
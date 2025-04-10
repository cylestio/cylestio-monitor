"""
Text processing and keyword detection functions for Cylestio Monitor.

This module provides utilities for normalizing and checking text for keywords.
"""

import logging
import re
from typing import Set, Dict, Any

from cylestio_monitor.security_detection import SecurityScanner

logger = logging.getLogger(__name__)

# Initialize the security scanner - thread-safe singleton
scanner = SecurityScanner.get_instance()


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

    # Use the scanner to check for suspicious content
    result = scanner.scan_text(text)
    
    # If any category with alert_level "suspicious" is found, return True
    if result["alert_level"] == "suspicious":
        logger.info(f"Suspicious content detected: category={result['category']}, keywords={result['keywords']}")
        return True
        
    logger.debug(f"No suspicious keywords found in: '{text[:50]}...'")
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

    # Use the scanner to check for dangerous content
    result = scanner.scan_text(text)
    
    # Check if dangerous commands category was found
    if result["alert_level"] == "dangerous":
        logger.info(f"Dangerous content detected: category={result['category']}, keywords={result['keywords']}")
        return True
        
    logger.debug(f"No dangerous keywords found in: '{text[:50]}...'")
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

    # Use the scanner directly
    result = scanner.scan_text(text)
    
    # Return the alert level
    alert_level = result["alert_level"]
    
    if alert_level != "none":
        logger.info(f"{alert_level.capitalize()} content detected: '{text[:50]}...'")
    else:
        logger.debug(f"No alert for: '{text[:50]}...'")
        
    return alert_level

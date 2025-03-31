"""Keyword detection module for identifying suspicious and dangerous content."""

from cylestio_monitor.events.keyword_detection.text_processing import (
    normalize_text,
    contains_suspicious,
    contains_dangerous,
    get_alert_level
)

__all__ = [
    "normalize_text",
    "contains_suspicious", 
    "contains_dangerous",
    "get_alert_level"
] 
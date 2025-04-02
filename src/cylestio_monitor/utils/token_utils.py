"""
Token estimation utilities for Cylestio Monitor.

This module provides functions for estimating token counts in text.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def estimate_tokens(text: Any) -> int:
    """
    Estimate the number of tokens in a text.

    This is a simple approximation using word count.
    For more accurate token counts, use a tokenizer specific to the model.

    Args:
        text: Text to estimate tokens for

    Returns:
        int: Estimated token count
    """
    if text is None:
        return 0

    # Convert to string if needed
    if not isinstance(text, str):
        text = str(text)

    # Simple approximation: words / 0.75 (assuming avg 4 chars per token)
    words = len(text.split())
    chars = len(text)

    # Use average of word-based and char-based estimates
    word_estimate = words / 0.75
    char_estimate = chars / 4

    # Return the average of the two estimates
    return int((word_estimate + char_estimate) / 2)

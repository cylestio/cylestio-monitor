"""Serialization utilities for Cylestio Monitor.

This module provides helper functions to serialize various objects that might
be encountered during monitoring, especially from LangChain and other frameworks.
"""

import datetime
import json
import logging
from typing import Any, Dict

logger = logging.getLogger("CylestioMonitor")


class MonitorJSONEncoder(json.JSONEncoder):
    """Extended JSON encoder that handles common AI framework objects."""

    def default(self, obj: Any) -> Any:
        """Handle special types during JSON serialization."""
        # Handle LangChain message objects
        if hasattr(obj, "__class__") and "Message" in obj.__class__.__name__:
            # This handles all message types from LangChain
            if hasattr(obj, "content") and hasattr(obj, "type"):
                return {
                    "type": obj.type,
                    "content": obj.content,
                    "_message_type": obj.__class__.__name__,
                }
            # Fallback for other message-like objects
            return str(obj)

        # Handle datetime objects
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()

        # Handle sets
        if isinstance(obj, set):
            return list(obj)

        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")

        # Handle other objects that have a __dict__
        if hasattr(obj, "__dict__"):
            try:
                # Attempt to convert the object to a dict
                return {"_type": obj.__class__.__name__, "attributes": obj.__dict__}
            except:
                # Fall back to string representation
                return str(obj)

        # Let the base class handle everything else
        return super().default(obj)


def serialize_for_monitoring(obj: Any) -> Any:
    """Safely serialize an object for monitoring.

    Args:
        obj: Any object to serialize

    Returns:
        JSON-serializable representation of the object
    """
    try:
        # Try to convert directly to JSON
        return json.loads(json.dumps(obj, cls=MonitorJSONEncoder))
    except Exception as e:
        # If that fails, try a more conservative approach
        logger.debug(f"Error serializing object: {e}")

        # Handle different types explicitly
        if isinstance(obj, dict):
            # Process each item in the dictionary
            result = {}
            for k, v in obj.items():
                try:
                    key = str(k)
                    result[key] = serialize_for_monitoring(v)
                except:
                    # Skip items that can't be serialized
                    pass
            return result

        elif isinstance(obj, (list, tuple)):
            # Process each item in the list
            result = []
            for item in obj:
                try:
                    result.append(serialize_for_monitoring(item))
                except:
                    # Skip items that can't be serialized
                    pass
            return result

        # Fall back to string representation
        return str(obj)


def safe_event_serialize(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Safely serialize event attributes for logging.

    Args:
        attributes: Dictionary of event attributes

    Returns:
        Serialized attributes that can be safely converted to JSON
    """
    if not attributes:
        return {}

    serialized = {}

    for key, value in attributes.items():
        try:
            serialized[key] = serialize_for_monitoring(value)
        except Exception:
            # If serialization fails, store the string representation
            try:
                serialized[key] = f"<Error serializing: {str(value)[:100]}...>"
            except:
                serialized[key] = "<Error serializing value>"

    return serialized

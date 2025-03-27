"""
Schema Management for Telemetry Events.

This module provides utilities for managing the schema version of telemetry events
and handles schema evolution over time.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CylestioMonitor")

# Current schema version
CURRENT_SCHEMA_VERSION = "1.0"

# Schema evolution map - version to changes mapping
SCHEMA_EVOLUTION = {
    "1.0": "Initial schema with OpenTelemetry alignment",
}

def get_current_schema_version() -> str:
    """Get the current schema version.
    
    Returns:
        str: The current schema version
    """
    return CURRENT_SCHEMA_VERSION


def get_schema_evolution_history() -> Dict[str, str]:
    """Get the schema evolution history.
    
    Returns:
        Dict[str, str]: The schema evolution history
    """
    return SCHEMA_EVOLUTION


def validate_schema_version(version: str) -> bool:
    """Validate if the provided schema version is supported.
    
    Args:
        version: The schema version to validate
        
    Returns:
        bool: True if the version is supported, False otherwise
    """
    return version in SCHEMA_EVOLUTION


def validate_event_schema(event: Dict[str, Any]) -> bool:
    """Validate if an event adheres to the expected schema.
    
    Args:
        event: The event to validate
        
    Returns:
        bool: True if the event is valid, False otherwise
    """
    # Basic schema validation for version 1.0
    required_fields = ["schema_version", "timestamp", "name", "level"]
    
    for field in required_fields:
        if field not in event:
            logger.warning(f"Event missing required field: {field}")
            return False
    
    # Validate schema version
    if not validate_schema_version(event.get("schema_version", "")):
        logger.warning(f"Unsupported schema version: {event.get('schema_version')}")
        return False
    
    # Additional validations can be added here
    
    return True


def get_schema_version_guidelines() -> Dict[str, str]:
    """Get the guidelines for when to increment schema versions.
    
    Returns:
        Dict[str, str]: Guidelines for major and minor version increments
    """
    return {
        "major_version": "Increment for backward-incompatible changes that require consumers to update",
        "minor_version": "Increment for backward-compatible additions or enhancements",
        "examples": {
            "major_changes": [
                "Renaming core fields",
                "Removing required fields",
                "Changing the data type of existing fields"
            ],
            "minor_changes": [
                "Adding new optional fields",
                "Adding new event types",
                "Extending existing fields with additional attributes"
            ]
        }
    }


def migrate_event_to_current_version(event: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate an event from an older schema version to the current version.
    
    Args:
        event: The event to migrate
        
    Returns:
        Dict[str, Any]: The migrated event
    """
    # For future use when we have multiple schema versions
    event_version = event.get("schema_version")
    
    if event_version == CURRENT_SCHEMA_VERSION:
        return event
    
    # Add migration logic here for future schema versions
    # This is placeholder code for future schema evolution
    
    # Always ensure the event has the current version after migration
    event["schema_version"] = CURRENT_SCHEMA_VERSION
    
    return event 
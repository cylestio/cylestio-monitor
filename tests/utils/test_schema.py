"""
Tests for schema versioning and validation.
"""
import pytest
from cylestio_monitor.utils.schema import (
    get_current_schema_version,
    validate_schema_version,
    validate_event_schema,
    get_schema_evolution_history,
    get_schema_version_guidelines,
    migrate_event_to_current_version
)


def test_get_current_schema_version():
    """Test retrieving the current schema version."""
    assert get_current_schema_version() == "1.0"
    assert isinstance(get_current_schema_version(), str)


def test_validate_schema_version():
    """Test schema version validation."""
    assert validate_schema_version("1.0") is True
    assert validate_schema_version("0.9") is False
    assert validate_schema_version("1.1") is False
    assert validate_schema_version("not a version") is False


def test_validate_event_schema():
    """Test event schema validation."""
    # Valid event
    valid_event = {
        "schema_version": "1.0",
        "timestamp": "2025-03-25T12:23:21.816297",
        "name": "test.event",
        "level": "INFO",
        "attributes": {}
    }
    assert validate_event_schema(valid_event) is True
    
    # Missing required field
    invalid_event = {
        "schema_version": "1.0",
        "timestamp": "2025-03-25T12:23:21.816297",
        # Missing "name" field
        "level": "INFO",
        "attributes": {}
    }
    assert validate_event_schema(invalid_event) is False
    
    # Invalid schema version
    invalid_version_event = {
        "schema_version": "0.9",
        "timestamp": "2025-03-25T12:23:21.816297",
        "name": "test.event",
        "level": "INFO",
        "attributes": {}
    }
    assert validate_event_schema(invalid_version_event) is False


def test_get_schema_evolution_history():
    """Test retrieving schema evolution history."""
    history = get_schema_evolution_history()
    assert isinstance(history, dict)
    assert "1.0" in history
    assert "Initial schema" in history["1.0"]


def test_get_schema_version_guidelines():
    """Test retrieving schema versioning guidelines."""
    guidelines = get_schema_version_guidelines()
    assert isinstance(guidelines, dict)
    assert "major_version" in guidelines
    assert "minor_version" in guidelines
    assert "examples" in guidelines
    assert isinstance(guidelines["examples"], dict)


def test_migrate_event_to_current_version():
    """Test event migration to current version."""
    # Current version event should remain unchanged
    current_event = {
        "schema_version": "1.0",
        "timestamp": "2025-03-25T12:23:21.816297",
        "name": "test.event",
        "level": "INFO",
        "attributes": {}
    }
    migrated_event = migrate_event_to_current_version(current_event)
    assert migrated_event == current_event
    
    # Event with no version should get the current version
    no_version_event = {
        "timestamp": "2025-03-25T12:23:21.816297",
        "name": "test.event",
        "level": "INFO",
        "attributes": {}
    }
    migrated_event = migrate_event_to_current_version(no_version_event)
    assert migrated_event["schema_version"] == get_current_schema_version()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
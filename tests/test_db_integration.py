"""Integration tests for the database module."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cylestio_monitor.db.db_manager import DBManager
from cylestio_monitor.db import utils as db_utils
from cylestio_monitor.config import ConfigManager
from cylestio_monitor.events_processor import log_event


@pytest.fixture
def db_manager():
    """Create a DBManager instance with a temporary database."""
    # Create a temporary directory for the database
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set the environment variable for testing
        os.environ["CYLESTIO_TEST_DB_DIR"] = temp_dir
        
        # Reset the singleton instance
        DBManager._instance = None
        
        # Create a new instance
        manager = DBManager()
        
        yield manager
        
        # Clean up
        manager.close()
        
        # Remove the environment variable
        if "CYLESTIO_TEST_DB_DIR" in os.environ:
            del os.environ["CYLESTIO_TEST_DB_DIR"]


def test_db_manager_singleton():
    """Test that DBManager follows the singleton pattern."""
    # Reset the singleton instance
    DBManager._instance = None
    
    # Create two instances
    manager1 = DBManager()
    manager2 = DBManager()
    
    # They should be the same object
    assert manager1 is manager2


def test_db_manager_initialization(db_manager):
    """Test that the database is initialized correctly."""
    # Check that the database file exists
    db_path = db_manager.get_db_path()
    assert db_path.exists()


def test_log_event_to_db(db_manager):
    """Test that log_event logs to the database."""
    # Mock the config manager to return a specific agent ID
    with patch.object(ConfigManager, "get") as mock_get:
        mock_get.return_value = "test_agent"
        
        # Log an event
        log_event(
            event_type="test_event",
            data={"key": "value"},
            channel="TEST",
            level="info"
        )
        
        # Check that the event was logged to the database
        events = db_manager.get_events(agent_id="test_agent")
        
        # Check that we got at least one event
        assert len(events) >= 1
        
        # Find our test event
        test_events = [e for e in events if e["event_type"] == "test_event"]
        assert len(test_events) >= 1
        assert test_events[0]["data"]["key"] == "value"


def test_db_utils_integration(db_manager):
    """Test the database utilities integration."""
    # Log an event
    event_id = db_utils.log_to_db(
        agent_id="utils_test_agent",
        event_type="utils_test_event",
        data={"key": "value"},
        channel="TEST",
        level="info"
    )
    
    # Check that the event was logged
    assert event_id > 0
    
    # Get the event
    events = db_manager.get_events(agent_id="utils_test_agent")
    assert len(events) == 1
    assert events[0]["event_type"] == "utils_test_event"
    
    # Test get_recent_events
    recent_events = db_utils.get_recent_events(agent_id="utils_test_agent")
    assert len(recent_events) == 1
    assert recent_events[0]["event_type"] == "utils_test_event"
    
    # Test get_agent_stats
    stats = db_utils.get_agent_stats(agent_id="utils_test_agent")
    assert len(stats) == 1
    assert stats[0]["agent_id"] == "utils_test_agent"
    assert stats[0]["event_count"] == 1 
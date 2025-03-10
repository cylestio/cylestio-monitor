"""Tests for the database utilities module."""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cylestio_monitor.db import utils as db_utils
from cylestio_monitor.db.db_manager import DBManager


@pytest.fixture
def mock_db_manager():
    """Mock the DBManager for testing."""
    mock_manager = MagicMock(spec=DBManager)
    
    # Set up return values for methods
    mock_manager.log_event.return_value = 1
    mock_manager.get_events.return_value = [{"id": 1, "event_type": "test"}]
    mock_manager.get_agent_stats.return_value = [{"agent_id": "test", "event_count": 10}]
    mock_manager.get_event_types.return_value = [("type1", 5), ("type2", 3)]
    mock_manager.get_channels.return_value = [("channel1", 5), ("channel2", 3)]
    mock_manager.get_levels.return_value = [("info", 5), ("warning", 3)]
    mock_manager.search_events.return_value = [{"id": 1, "event_type": "test"}]
    mock_manager.delete_events_before.return_value = 5
    mock_manager.get_db_path.return_value = "/path/to/db.sqlite"
    
    with patch("cylestio_monitor.db.utils.DBManager", return_value=mock_manager):
        yield mock_manager


@pytest.fixture
def real_db_manager():
    """Create a real DBManager instance with a temporary database."""
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


def test_get_db_manager():
    """Test getting the database manager."""
    with patch("cylestio_monitor.db.utils.DBManager") as mock_db_manager_class:
        mock_instance = MagicMock()
        mock_db_manager_class.return_value = mock_instance
        
        manager = db_utils.get_db_manager()
        
        assert manager is mock_instance
        mock_db_manager_class.assert_called_once()


def test_log_to_db(mock_db_manager):
    """Test logging to the database."""
    event_id = db_utils.log_to_db(
        agent_id="test_agent",
        event_type="test_event",
        data={"key": "value"},
        channel="TEST",
        level="info"
    )
    
    assert event_id == 1
    mock_db_manager.log_event.assert_called_once_with(
        "test_agent", "test_event", {"key": "value"}, "TEST", "info", None
    )


def test_get_recent_events(mock_db_manager):
    """Test getting recent events."""
    events = db_utils.get_recent_events(agent_id="test_agent", limit=10, offset=0)
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.get_events.assert_called_once_with(
        agent_id="test_agent", limit=10, offset=0
    )


def test_get_events_by_type(mock_db_manager):
    """Test getting events by type."""
    events = db_utils.get_events_by_type("test_type", agent_id="test_agent", limit=10)
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.get_events.assert_called_once_with(
        agent_id="test_agent", event_type="test_type", limit=10
    )


def test_get_events_by_channel(mock_db_manager):
    """Test getting events by channel."""
    events = db_utils.get_events_by_channel("test_channel", agent_id="test_agent", limit=10)
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.get_events.assert_called_once_with(
        agent_id="test_agent", channel="test_channel", limit=10
    )


def test_get_events_by_level(mock_db_manager):
    """Test getting events by level."""
    events = db_utils.get_events_by_level("info", agent_id="test_agent", limit=10)
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.get_events.assert_called_once_with(
        agent_id="test_agent", level="info", limit=10
    )


def test_get_events_by_timeframe(mock_db_manager):
    """Test getting events by timeframe."""
    start_time = datetime.now() - timedelta(days=1)
    end_time = datetime.now()
    
    events = db_utils.get_events_by_timeframe(
        start_time, end_time, agent_id="test_agent", limit=10
    )
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.get_events.assert_called_once_with(
        agent_id="test_agent", start_time=start_time, end_time=end_time, limit=10
    )


def test_get_events_last_hours(mock_db_manager):
    """Test getting events from the last N hours."""
    with patch("cylestio_monitor.db.utils.datetime") as mock_datetime:
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        events = db_utils.get_events_last_hours(24, agent_id="test_agent", limit=10)
        
        assert events == [{"id": 1, "event_type": "test"}]
        mock_db_manager.get_events.assert_called_once()
        
        # Check that the start and end times are correct
        call_args = mock_db_manager.get_events.call_args[1]
        assert call_args["agent_id"] == "test_agent"
        assert call_args["limit"] == 10
        assert call_args["start_time"] == now - timedelta(hours=24)
        assert call_args["end_time"] == now


def test_get_events_last_days(mock_db_manager):
    """Test getting events from the last N days."""
    with patch("cylestio_monitor.db.utils.datetime") as mock_datetime:
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        events = db_utils.get_events_last_days(7, agent_id="test_agent", limit=10)
        
        assert events == [{"id": 1, "event_type": "test"}]
        mock_db_manager.get_events.assert_called_once()
        
        # Check that the start and end times are correct
        call_args = mock_db_manager.get_events.call_args[1]
        assert call_args["agent_id"] == "test_agent"
        assert call_args["limit"] == 10
        assert call_args["start_time"] == now - timedelta(days=7)
        assert call_args["end_time"] == now


def test_search_events(mock_db_manager):
    """Test searching events."""
    events = db_utils.search_events("test", agent_id="test_agent", limit=10)
    
    assert events == [{"id": 1, "event_type": "test"}]
    mock_db_manager.search_events.assert_called_once_with("test", "test_agent", 10)


def test_get_agent_stats(mock_db_manager):
    """Test getting agent statistics."""
    stats = db_utils.get_agent_stats(agent_id="test_agent")
    
    assert stats == [{"agent_id": "test", "event_count": 10}]
    mock_db_manager.get_agent_stats.assert_called_once_with("test_agent")


def test_get_event_type_distribution(mock_db_manager):
    """Test getting event type distribution."""
    distribution = db_utils.get_event_type_distribution(agent_id="test_agent")
    
    assert distribution == [("type1", 5), ("type2", 3)]
    mock_db_manager.get_event_types.assert_called_once_with("test_agent")


def test_get_channel_distribution(mock_db_manager):
    """Test getting channel distribution."""
    distribution = db_utils.get_channel_distribution(agent_id="test_agent")
    
    assert distribution == [("channel1", 5), ("channel2", 3)]
    mock_db_manager.get_channels.assert_called_once_with("test_agent")


def test_get_level_distribution(mock_db_manager):
    """Test getting level distribution."""
    distribution = db_utils.get_level_distribution(agent_id="test_agent")
    
    assert distribution == [("info", 5), ("warning", 3)]
    mock_db_manager.get_levels.assert_called_once_with("test_agent")


def test_cleanup_old_events(mock_db_manager):
    """Test cleaning up old events."""
    with patch("cylestio_monitor.db.utils.datetime") as mock_datetime:
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        deleted = db_utils.cleanup_old_events(days=30)
        
        assert deleted == 5
        mock_db_manager.delete_events_before.assert_called_once_with(now - timedelta(days=30))


def test_optimize_database(mock_db_manager):
    """Test optimizing the database."""
    db_utils.optimize_database()
    
    mock_db_manager.vacuum.assert_called_once()


def test_get_db_path(mock_db_manager):
    """Test getting the database path."""
    path = db_utils.get_db_path()
    
    assert path == "/path/to/db.sqlite"
    mock_db_manager.get_db_path.assert_called_once()


# Integration tests with real database
def test_real_log_to_db(real_db_manager):
    """Test logging to the database with a real database."""
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
    events = real_db_manager.get_events(agent_id="utils_test_agent")
    assert len(events) == 1
    assert events[0]["event_type"] == "utils_test_event"


def test_real_get_recent_events(real_db_manager):
    """Test getting recent events with a real database."""
    # Log some events
    db_utils.log_to_db(
        agent_id="utils_test_agent",
        event_type="recent_event",
        data={"key": "value"}
    )
    
    # Get recent events
    events = db_utils.get_recent_events(agent_id="utils_test_agent")
    
    # Check that we got at least one event
    assert len(events) >= 1
    assert any(e["event_type"] == "recent_event" for e in events) 
"""Unit tests for the DBManager class.

This module contains comprehensive tests for the DBManager class, covering all major
functionality including event logging, querying, and aggregation methods.
"""

import json
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

import pytest

from cylestio_monitor.db.db_manager import DBManager
from cylestio_monitor.db.models import (
    Event, Agent, EventType, EventChannel, EventLevel,
    LLMCall, ToolCall, SecurityAlert, PerformanceMetric,
    Session as SessionModel
)


@pytest.fixture
def mock_platformdirs():
    """Mock platformdirs to use a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("platformdirs.user_data_dir", return_value=temp_dir):
            yield temp_dir


@pytest.fixture
def test_db_dir(tmp_path):
    """Create a temporary directory for the test database."""
    return str(tmp_path / "test_db")


@pytest.fixture
def db_manager(test_db_dir):
    """Create a DBManager instance with a test database."""
    # Reset the singleton instance
    DBManager._instance = None
    
    # Set the environment variable for testing
    os.environ["CYLESTIO_TEST_DB_DIR"] = test_db_dir
    
    # Create a new instance
    manager = DBManager()
    
    yield manager
    
    # Clean up
    manager.close()
    
    # Remove the environment variable
    if "CYLESTIO_TEST_DB_DIR" in os.environ:
        del os.environ["CYLESTIO_TEST_DB_DIR"]


@pytest.fixture
def test_agent(db_manager):
    """Create a test agent."""
    return db_manager.get_or_create_agent("test_agent_1")


@pytest.fixture
def test_events(db_manager, test_agent):
    """Create a set of test events."""
    # Create various types of events
    events = []
    
    # LLM call
    events.append(db_manager.log_llm_call(
        agent_id="test_agent_1",
        model="gpt-4",
        prompt="Test prompt",
        response="Test response",
        tokens_in=10,
        tokens_out=20,
        duration_ms=1000,
        cost=0.01
    ))
    
    # Tool call
    events.append(db_manager.log_tool_call(
        agent_id="test_agent_1",
        tool_name="test_tool",
        input_params={"param1": "value1"},
        output={"result": "success"},
        success=True,
        duration_ms=500
    ))
    
    # Security alert
    events.append(db_manager.log_security_event(
        agent_id="test_agent_1",
        alert_type="test_alert",
        description="Test security alert",
        severity="high",
        related_data={"details": "test"}
    ))
    
    # Performance metric
    events.append(db_manager.log_event(
        agent_id="test_agent_1",
        event_type=EventType.PERFORMANCE_METRIC,
        data={
            "memory_usage": 100,
            "cpu_usage": 50,
            "duration_ms": 2000
        },
        channel=EventChannel.SYSTEM,
        level=EventLevel.INFO
    ))
    
    return events


def test_singleton_pattern():
    """Test that DBManager follows the singleton pattern."""
    # Reset the singleton instance
    DBManager._instance = None
    
    # Create two instances
    manager1 = DBManager()
    manager2 = DBManager()
    
    # They should be the same object
    assert manager1 is manager2


def test_db_initialization(db_manager, test_db_dir):
    """Test database initialization."""
    assert db_manager.get_db_path().parent == Path(test_db_dir)
    assert db_manager.get_db_path().exists()


def test_get_or_create_agent(db_manager):
    """Test agent creation and retrieval."""
    agent_id = "test_agent_2"
    db_id = db_manager.get_or_create_agent(agent_id)
    assert db_id > 0
    
    # Test idempotency
    db_id2 = db_manager.get_or_create_agent(agent_id)
    assert db_id == db_id2


def test_log_event(db_manager, test_agent):
    """Test event logging."""
    event_id = db_manager.log_event(
        agent_id="test_agent_1",
        event_type="test_event",
        data={"test": "data"},
        channel="TEST",
        level="info"
    )
    assert event_id > 0
    
    # Verify event was created
    events = db_manager.get_events(agent_id="test_agent_1")
    assert len(events) > 0
    assert events[0]["id"] == event_id


def test_log_llm_call(db_manager, test_agent):
    """Test LLM call logging."""
    event_id = db_manager.log_llm_call(
        agent_id="test_agent_1",
        model="gpt-4",
        prompt="Test prompt",
        response="Test response",
        tokens_in=10,
        tokens_out=20,
        duration_ms=1000,
        cost=0.01
    )
    assert event_id > 0
    
    # Verify LLM call was created
    llm_calls = db_manager.get_llm_calls(agent_id="test_agent_1")
    assert len(llm_calls) > 0
    assert llm_calls[0]["id"] == event_id
    assert llm_calls[0]["model"] == "gpt-4"


def test_log_tool_call(db_manager, test_agent):
    """Test tool call logging."""
    event_id = db_manager.log_tool_call(
        agent_id="test_agent_1",
        tool_name="test_tool",
        input_params={"param1": "value1"},
        output={"result": "success"},
        success=True,
        duration_ms=500
    )
    assert event_id > 0
    
    # Verify tool call was created
    tool_calls = db_manager.get_tool_usage(agent_id="test_agent_1")
    assert len(tool_calls) > 0
    assert tool_calls[0]["id"] == event_id
    assert tool_calls[0]["tool_name"] == "test_tool"


def test_log_security_event(db_manager, test_agent):
    """Test security event logging."""
    event_id = db_manager.log_security_event(
        agent_id="test_agent_1",
        alert_type="test_alert",
        description="Test security alert",
        severity="high",
        related_data={"details": "test"}
    )
def test_db_initialization(db_manager, mock_platformdirs):
    """Test that the database is initialized correctly."""
    # Check that the database file exists
    db_path = Path(mock_platformdirs) / "cylestio_monitor.db"
    assert db_path.exists()
    
    # Check that we can connect to it
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check that the tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "agents" in tables
    assert "events" in tables
    
    # Check that the indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    assert "idx_events_agent_id" in indexes
    assert "idx_events_event_type" in indexes
    assert "idx_events_timestamp" in indexes
    assert "idx_events_channel" in indexes
    assert "idx_events_level" in indexes
    
    conn.close()


def test_get_or_create_agent(db_manager):
    """Test getting or creating an agent."""
    # Create a new agent
    agent_db_id = db_manager.get_or_create_agent("test_agent")
    assert agent_db_id > 0
    
    # Get the same agent
    agent_db_id2 = db_manager.get_or_create_agent("test_agent")
    assert agent_db_id2 == agent_db_id
    
    # Create a different agent
    agent_db_id3 = db_manager.get_or_create_agent("another_agent")
    assert agent_db_id3 != agent_db_id


def test_log_event(db_manager):
    """Test logging an event."""
    # Log an event
    event_id = db_manager.log_event(
        agent_id="test_agent",
        event_type="test_event",
        data={"key": "value"},
        channel="TEST",
        level="info"
    )
    assert event_id > 0
    
    # Get the event
    events = db_manager.get_events(agent_id="test_agent")
    assert len(events) == 1
    assert events[0]["event_type"] == "test_event"
    assert events[0]["channel"] == "TEST"
    assert events[0]["level"] == "info"
    assert events[0]["data"] == {"key": "value"}


def test_get_events_filtering(db_manager):
    """Test filtering events."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value1"},
        channel="channel1",
        level="info"
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"key": "value2"},
        channel="channel2",
        level="warning"
    )
    db_manager.log_event(
        agent_id="agent2",
        event_type="type1",
        data={"key": "value3"},
        channel="channel1",
        level="error"
    )
    
    # Filter by agent ID
    events = db_manager.get_events(agent_id="agent1")
    assert len(events) == 2
    
    # Filter by event type
    events = db_manager.get_events(event_type="type1")
    assert len(events) == 2
    
    # Filter by channel
    events = db_manager.get_events(channel="channel2")
    assert len(events) == 1
    
    # Filter by level
    events = db_manager.get_events(level="error")
    assert len(events) == 1
    
    # Combined filters
    events = db_manager.get_events(agent_id="agent1", event_type="type1")
    assert len(events) == 1


def test_get_events_timeframe(db_manager):
    """Test filtering events by timeframe."""
    # Log events with different timestamps
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "now"},
        timestamp=now
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "yesterday"},
        timestamp=yesterday
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "two_days_ago"},
        timestamp=two_days_ago
    )
    
    # Filter by start time
    events = db_manager.get_events(start_time=yesterday - timedelta(hours=1))
    assert len(events) == 2
    
    # Filter by end time
    events = db_manager.get_events(end_time=yesterday + timedelta(hours=1))
    assert len(events) == 2
    
    # Filter by both
    events = db_manager.get_events(
        start_time=yesterday - timedelta(hours=1),
        end_time=yesterday + timedelta(hours=1)
    )
    assert len(events) == 1


def test_get_agent_stats(db_manager):
    """Test getting agent statistics."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value1"}
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"key": "value2"}
    )
    db_manager.log_event(
        agent_id="agent2",
        event_type="type1",
        data={"key": "value3"}
    )
    
    # Get stats for all agents
    stats = db_manager.get_agent_stats()
    assert len(stats) >= 2
    
    # Check agent1 stats
    agent1_stats = next(s for s in stats if s["agent_id"] == "agent1")
    assert agent1_stats["event_count"] >= 2
    
    # Check agent2 stats
    agent2_stats = next(s for s in stats if s["agent_id"] == "agent2")
    assert agent2_stats["event_count"] >= 1
    
    # Get stats for a specific agent
    stats = db_manager.get_agent_stats(agent_id="agent1")
    assert len(stats) == 1
    assert stats[0]["event_count"] >= 2


def test_get_event_types(db_manager):
    """Test getting event type distribution."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value1"}
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value2"}
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"key": "value3"}
    )
    
    # Get event type distribution
    types = db_manager.get_event_types()
    assert len(types) >= 2
    
    # Check counts
    type1_count = next(t[1] for t in types if t[0] == "type1")
    assert type1_count >= 2
    
    type2_count = next(t[1] for t in types if t[0] == "type2")
    assert type2_count >= 1


def test_get_channels(db_manager):
    """Test getting channel distribution."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value1"},
        channel="channel1"
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value2"},
        channel="channel1"
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"key": "value3"},
        channel="channel2"
    )
    
    # Get channel distribution
    channels = db_manager.get_channels()
    assert len(channels) >= 2
    
    # Check counts
    channel1_count = next(c[1] for c in channels if c[0] == "channel1")
    assert channel1_count >= 2
    
    channel2_count = next(c[1] for c in channels if c[0] == "channel2")
    assert channel2_count >= 1


def test_get_levels(db_manager):
    """Test getting level distribution."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value1"},
        level="info"
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "value2"},
        level="info"
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"key": "value3"},
        level="warning"
    )
    
    # Get level distribution
    levels = db_manager.get_levels()
    assert len(levels) >= 2
    
    # Check counts
    info_count = next(l[1] for l in levels if l[0] == "info")
    assert info_count >= 2
    
    warning_count = next(l[1] for l in levels if l[0] == "warning")
    assert warning_count >= 1


def test_search_events(db_manager):
    """Test searching events."""
    # Log some events
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"message": "This is a test message"}
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type2",
        data={"result": "Test result with searchable content"}
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type3",
        data={"other": "This won't match"}
    )
    
    # Search for "test"
    events = db_manager.search_events("test")
    assert len(events) >= 2
    
    # Search for "searchable"
    events = db_manager.search_events("searchable")
    assert len(events) >= 1
    
    # Search with agent filter
    events = db_manager.search_events("test", agent_id="agent1")
    assert len(events) >= 2
    
    # Create a unique agent ID that won't be in the database
    unique_agent_id = f"nonexistent_agent_{datetime.now().timestamp()}"
    events = db_manager.search_events("test", agent_id=unique_agent_id)
    assert len(events) == 0


def test_delete_events_before(db_manager):
    """Test deleting events before a timestamp."""
    # Log events with different timestamps
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "now"},
        timestamp=now
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "yesterday"},
        timestamp=yesterday
    )
    db_manager.log_event(
        agent_id="agent1",
        event_type="type1",
        data={"key": "two_days_ago"},
        timestamp=two_days_ago
    )
    
    # Delete events before yesterday
    deleted = db_manager.delete_events_before(yesterday)
    assert deleted >= 1
    
    # Check remaining events
    events = db_manager.get_events()
    assert len(events) >= 2


def test_vacuum(db_manager, mock_platformdirs):
    """Test vacuuming the database."""
    # Log some events
    for i in range(10):
        db_manager.log_event(
            agent_id="agent1",
            event_type="type1",
            data={"key": f"value{i}"}
        )
    
    # Get the initial file size
    db_path = Path(mock_platformdirs) / "cylestio_monitor.db"
    initial_size = db_path.stat().st_size
    
    # Delete some events
    db_manager.delete_events_before(datetime.now())
    
    # Vacuum the database
    db_manager.vacuum()
    
    # Check that the file size has decreased or stayed the same
    final_size = db_path.stat().st_size
    assert final_size <= initial_size 
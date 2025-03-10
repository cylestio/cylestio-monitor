"""Tests for MCP monitoring functions."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from cylestio_monitor.config.config_manager import ConfigManager
from cylestio_monitor.events_processor import (
    pre_monitor_mcp_tool,
    post_monitor_mcp_tool,
    contains_dangerous,
    contains_suspicious,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the ConfigManager singleton instance before each test."""
    # Save the original instance
    original_instance = ConfigManager._instance
    
    # Reset the instance
    ConfigManager._instance = None
    
    # Run the test
    yield
    
    # Restore the original instance
    ConfigManager._instance = original_instance


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    with patch("cylestio_monitor.events_processor.config_manager") as mock_cm:
        mock_cm.get_suspicious_keywords.return_value = ["HACK", "BOMB"]
        mock_cm.get_dangerous_keywords.return_value = ["DROP", "DELETE", "KILL"]
        yield mock_cm


@pytest.fixture
def mock_log_event():
    """Create a mock for the log_event function."""
    with patch("cylestio_monitor.events_processor.log_event") as mock_log:
        yield mock_log


def test_pre_monitor_mcp_tool_normal(mock_config_manager, mock_log_event):
    """Test pre_monitor_mcp_tool with normal input."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    args = ("New York",)
    kwargs = {"days": 5}
    
    # Act
    start_time = pre_monitor_mcp_tool(channel, tool_name, args, kwargs)
    
    # Assert
    assert isinstance(start_time, float)
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_start"
    assert call_args[2] == channel
    assert "tool" in call_args[1]
    assert call_args[1]["tool"] == tool_name
    assert "alert" in call_args[1]
    assert call_args[1]["alert"] == "none"


def test_pre_monitor_mcp_tool_suspicious(mock_config_manager, mock_log_event):
    """Test pre_monitor_mcp_tool with suspicious input."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    args = ("HACK the weather",)
    kwargs = {}
    
    # Act
    start_time = pre_monitor_mcp_tool(channel, tool_name, args, kwargs)
    
    # Assert
    assert isinstance(start_time, float)
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_start"
    assert "alert" in call_args[1]
    assert call_args[1]["alert"] == "suspicious"


def test_pre_monitor_mcp_tool_dangerous(mock_config_manager, mock_log_event):
    """Test pre_monitor_mcp_tool with dangerous input."""
    # Arrange
    channel = "MCP"
    tool_name = "DROP_table"
    args = ()
    kwargs = {"table_name": "users"}
    
    # Act & Assert
    with pytest.raises(ValueError, match="Blocked MCP tool call due to dangerous terms"):
        pre_monitor_mcp_tool(channel, tool_name, args, kwargs)
    
    # Check that the blocked event was logged
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_blocked"
    assert call_args[3] == "warning"  # Check that the level is warning


def test_post_monitor_mcp_tool_normal(mock_config_manager, mock_log_event):
    """Test post_monitor_mcp_tool with normal result."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    start_time = time.time() - 1.0  # 1 second ago
    result = {"temperature": 72, "condition": "sunny"}
    
    # Act
    post_monitor_mcp_tool(channel, tool_name, start_time, result)
    
    # Assert
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_finish"
    assert call_args[2] == channel
    assert "tool" in call_args[1]
    assert call_args[1]["tool"] == tool_name
    assert "duration" in call_args[1]
    assert call_args[1]["duration"] >= 1.0
    assert "alert" in call_args[1]
    assert call_args[1]["alert"] == "none"


def test_post_monitor_mcp_tool_suspicious(mock_config_manager, mock_log_event):
    """Test post_monitor_mcp_tool with suspicious result."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    start_time = time.time() - 0.5
    result = {"error": "HACK attempt detected"}
    
    # Act
    post_monitor_mcp_tool(channel, tool_name, start_time, result)
    
    # Assert
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_finish"
    assert "alert" in call_args[1]
    assert call_args[1]["alert"] == "suspicious"


def test_post_monitor_mcp_tool_dangerous(mock_config_manager, mock_log_event):
    """Test post_monitor_mcp_tool with dangerous result."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    start_time = time.time() - 0.5
    result = {"action": "DROP all tables"}
    
    # Act
    post_monitor_mcp_tool(channel, tool_name, start_time, result)
    
    # Assert
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_finish"
    assert "alert" in call_args[1]
    assert call_args[1]["alert"] == "dangerous"


def test_post_monitor_mcp_tool_non_serializable(mock_config_manager, mock_log_event):
    """Test post_monitor_mcp_tool with non-serializable result."""
    # Arrange
    channel = "MCP"
    tool_name = "get_weather"
    start_time = time.time() - 0.5
    
    # Create a non-serializable object
    class NonSerializable:
        def __str__(self):
            return "NonSerializable object"
    
    result = NonSerializable()
    
    # Act
    post_monitor_mcp_tool(channel, tool_name, start_time, result)
    
    # Assert
    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "MCP_tool_call_finish"
    assert "result" in call_args[1]
    assert "NonSerializable object" in call_args[1]["result"] 
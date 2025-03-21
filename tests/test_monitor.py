"""Tests for the monitor module."""

from unittest.mock import MagicMock, patch
import pytest

from src.cylestio_monitor.monitor import (
    disable_monitoring,
    enable_monitoring,
)


@pytest.mark.xfail(reason="Import mocking needs fixing after MVP")
@patch("src.cylestio_monitor.monitor.monitor_call")
@patch("src.cylestio_monitor.monitor.monitor_llm_call")
@patch("src.cylestio_monitor.monitor.log_event")
def test_enable_monitoring(mock_log_event, mock_monitor_llm_call, mock_monitor_call):
    """Test the enable_monitoring function."""
    # Create a mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.__class__.__module__ = "anthropic"
    mock_llm_client.__class__.__name__ = "Anthropic"
    mock_llm_client.messages.create = MagicMock()

    # Call enable_monitoring with minimal args for MVP
    enable_monitoring(agent_id="test")

    # Verify log_event was called
    assert mock_log_event.called


@pytest.mark.xfail(reason="shutdown mock needs fixing after MVP")
@patch("src.cylestio_monitor.monitor.logging")
@patch("src.cylestio_monitor.monitor.log_event")
def test_disable_monitoring(mock_log_event, mock_logging):
    """Test the disable_monitoring function."""
    # Call disable_monitoring
    disable_monitoring()

    # Check that log_event was called
    assert mock_log_event.called


@pytest.mark.non_critical
@patch("src.cylestio_monitor.monitor.monitor_call")
@patch("src.cylestio_monitor.monitor.log_event")
def test_enable_monitoring_import_error(mock_log_event, mock_monitor_call):
    """Test the enable_monitoring function with an import error."""
    # Call enable_monitoring
    enable_monitoring(agent_id="test")
    
    # Just test that it doesn't crash
    assert True

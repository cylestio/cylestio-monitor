"""Tests for the monitor module."""

from unittest.mock import MagicMock, patch

from src.cylestio_monitor.monitor import (
    disable_monitoring,
    enable_monitoring,
)


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

    # Mock the ClientSession import
    with patch("builtins.__import__") as mock_import:
        # Set up the mock ClientSession
        mock_mcp = MagicMock()
        mock_client_session = MagicMock()
        mock_mcp.ClientSession = mock_client_session

        # Configure the import mock to return our mock_mcp when 'mcp' is imported
        def import_mock(name, *args, **kwargs):
            if name == "mcp":
                return mock_mcp
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_mock

        # Call enable_monitoring
        enable_monitoring(
            agent_id="test",
            llm_client=mock_llm_client,
            llm_method_path="messages.create",
            log_file="test.json",
            debug_level="DEBUG",
        )

        # Check that the monitor_call function was called with the correct arguments
        mock_monitor_call.assert_called_once()

        # Check that the monitor_llm_call function was called with the correct arguments
        mock_monitor_llm_call.assert_called_once()

        # Check that the log_event function was called
        mock_log_event.assert_called()


@patch("src.cylestio_monitor.monitor.monitor_call")
@patch("src.cylestio_monitor.monitor.log_event")
def test_enable_monitoring_no_llm(mock_log_event, mock_monitor_call):
    """Test the enable_monitoring function without an LLM client."""
    # Mock the ClientSession import
    with patch("builtins.__import__") as mock_import:
        # Set up the mock ClientSession
        mock_mcp = MagicMock()
        mock_client_session = MagicMock()
        mock_mcp.ClientSession = mock_client_session

        # Configure the import mock to return our mock_mcp when 'mcp' is imported
        def import_mock(name, *args, **kwargs):
            if name == "mcp":
                return mock_mcp
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_mock

        # Call enable_monitoring without an LLM client
        enable_monitoring(agent_id="test", log_file="test.json", debug_level="DEBUG")

        # Check that the monitor_call function was called with the correct arguments
        mock_monitor_call.assert_called_once()

        # Check that the log_event function was called
        mock_log_event.assert_called()


@patch("src.cylestio_monitor.monitor.logging")
@patch("src.cylestio_monitor.monitor.log_event")
def test_disable_monitoring(mock_log_event, mock_logging):
    """Test the disable_monitoring function."""
    # Call disable_monitoring
    disable_monitoring()

    # Check that logging.shutdown was called
    mock_logging.shutdown.assert_called_once()

    # Check that log_event was called for monitoring disabled
    mock_log_event.assert_called_once()


@patch("src.cylestio_monitor.monitor.monitor_call")
@patch("src.cylestio_monitor.monitor.log_event")
def test_enable_monitoring_import_error(mock_log_event, mock_monitor_call):
    """Test the enable_monitoring function with an import error."""
    # Mock the ClientSession import to raise an ImportError
    with patch("builtins.__import__") as mock_import:
        # Configure the import mock to raise ImportError when 'mcp' is imported
        def import_mock(name, *args, **kwargs):
            if name == "mcp":
                raise ImportError("No module named 'mcp'")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_mock

        # Call enable_monitoring
        enable_monitoring(agent_id="test", log_file="test.json", debug_level="DEBUG")

        # Check that the log_event function was called with the correct arguments
        mock_log_event.assert_called_once()

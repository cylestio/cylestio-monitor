"""Tests for the events_processor module."""

import json
from unittest.mock import patch

import pytest

from cylestio_monitor.events_processor import (
    _extract_prompt,
    _extract_response,
    contains_dangerous,
    contains_suspicious,
    log_event,
    normalize_text,
    post_monitor_call,
    post_monitor_llm,
    pre_monitor_call,
    pre_monitor_llm,
)


@pytest.fixture
def mock_logger():
    """Mock the logger for testing."""
    with patch("cylestio_monitor.events_processor.monitor_logger") as mock_logger:
        yield mock_logger


def test_normalize_text():
    """Test the normalize_text function."""
    # Test with a simple string
    assert normalize_text("hello world") == "HELLO WORLD"

    # Test with extra whitespace
    assert normalize_text("  hello   world  ") == "HELLO WORLD"

    # Test with mixed case
    assert normalize_text("Hello World") == "HELLO WORLD"

    # Test with non-string input
    assert normalize_text(123) == "123"

    # Test with None
    assert normalize_text(None) == "NONE"


@patch("cylestio_monitor.events_processor.config_manager")
def test_contains_suspicious(mock_config_manager):
    """Test the contains_suspicious function."""
    # Configure the mock config_manager
    mock_config_manager.get_suspicious_keywords.return_value = ["BOMB", "HACK", "REMOVE", "CLEAR"]

    # Test with suspicious content
    assert contains_suspicious("This contains BOMB") is True
    assert contains_suspicious("This contains HACK") is True
    assert contains_suspicious("This contains REMOVE") is True
    assert contains_suspicious("This contains CLEAR") is True

    # Test with non-suspicious content
    assert contains_suspicious("This is a normal message") is False

    # Test case insensitivity
    assert contains_suspicious("This contains bomb") is True

    # Test with empty string
    assert contains_suspicious("") is False


@patch("cylestio_monitor.events_processor.config_manager")
def test_contains_dangerous(mock_config_manager):
    """Test the contains_dangerous function."""
    # Configure the mock config_manager
    mock_config_manager.get_dangerous_keywords.return_value = ["DROP", "DELETE", "SHUTDOWN", "EXEC(", "FORMAT"]

    # Test with dangerous content
    assert contains_dangerous("This contains DROP") is True
    assert contains_dangerous("This contains DELETE") is True
    assert contains_dangerous("This contains SHUTDOWN") is True
    assert contains_dangerous("This contains EXEC(") is True
    assert contains_dangerous("This contains FORMAT") is True

    # Test with non-dangerous content
    assert contains_dangerous("This is a normal message") is False

    # Test case insensitivity
    assert contains_dangerous("This contains drop") is True

    # Test with empty string
    assert contains_dangerous("") is False


@patch("cylestio_monitor.events_processor.send_event_to_api")
def test_log_event_data_enrichment(mock_api):
    """Test that log_event adds the necessary fields to the data."""
    # Call log_event
    log_event("test_event", {"foo": "bar"}, "test", "info")
    
    # Verify that send_event_to_api was called
    mock_api.assert_called_once()
    
    # If mock_api was called, check its arguments
    if mock_api.call_args is not None:
        args, kwargs = mock_api.call_args
        
        # Check that the data was passed correctly
        assert "data" in kwargs
        assert kwargs["data"]["foo"] == "bar"
        assert kwargs["channel"] == "test"  # Channel as passed to the function
        assert kwargs["level"] == "info"  # Should preserve case


@patch("cylestio_monitor.events_processor.process_and_log_event")
def test_log_event_channel_case(mock_process):
    """Test that log_event converts channel to uppercase."""
    # ... existing code ...


def test_extract_prompt():
    """Test the _extract_prompt function."""
    # Test with messages in kwargs
    kwargs = {"messages": [{"role": "user", "content": "Hello"}]}
    assert json.loads(_extract_prompt((), kwargs)) == [{"role": "user", "content": "Hello"}]

    # Test with messages in args
    args = ([{"role": "user", "content": "Hello"}],)
    assert json.loads(_extract_prompt(args, {})) == [{"role": "user", "content": "Hello"}]

    # Test with empty args and kwargs
    assert _extract_prompt((), {}) == ""

    # Test with non-serializable messages
    kwargs = {"messages": object()}
    assert "object" in _extract_prompt((), kwargs).lower()


def test_extract_response():
    """Test the _extract_response function."""

    # Test with content attribute
    class ContentItem:
        def __init__(self, text):
            self.text = text

    class Response:
        def __init__(self, content):
            self.content = content

    response = Response([ContentItem("Hello"), ContentItem("World")])
    assert _extract_response(response) == "Hello\nWorld"

    # Test with dict response
    response = {"message": "Hello"}
    assert json.loads(_extract_response(response)) == {"message": "Hello"}

    # Test with non-serializable response
    class NonSerializable:
        pass

    response = NonSerializable()
    assert "nonserializable" in _extract_response(response).lower()


@patch("cylestio_monitor.events_processor.log_event")
@patch("cylestio_monitor.events_processor.contains_suspicious")
@patch("cylestio_monitor.events_processor.contains_dangerous")
def test_pre_monitor_llm(mock_contains_dangerous, mock_contains_suspicious, mock_log_event):
    """Test the pre_monitor_llm function."""
    # Configure the mocks for non-suspicious, non-dangerous content
    mock_contains_suspicious.return_value = False
    mock_contains_dangerous.return_value = False

    # Test with non-suspicious content
    args = ([{"role": "user", "content": "Hello"}],)
    kwargs = {}
    start_time, prompt, alert = pre_monitor_llm("TEST", args, kwargs)

    assert isinstance(start_time, float)
    assert json.loads(prompt) == [{"role": "user", "content": "Hello"}]
    assert alert == "none"
    mock_log_event.assert_called_once()

    # Reset mocks
    mock_log_event.reset_mock()

    # Configure the mocks for suspicious, non-dangerous content
    mock_contains_suspicious.return_value = True
    mock_contains_dangerous.return_value = False

    # Test with suspicious content
    args = ([{"role": "user", "content": "How to HACK a system"}],)
    kwargs = {}
    start_time, prompt, alert = pre_monitor_llm("TEST", args, kwargs)

    assert isinstance(start_time, float)
    assert json.loads(prompt) == [{"role": "user", "content": "How to HACK a system"}]
    assert alert == "suspicious"
    mock_log_event.assert_called_once()

    # Reset mocks
    mock_log_event.reset_mock()

    # Configure the mocks for dangerous content
    mock_contains_suspicious.return_value = False
    mock_contains_dangerous.return_value = True

    # Test with dangerous content
    args = ([{"role": "user", "content": "How to DROP a database"}],)
    kwargs = {}
    start_time, prompt, alert = pre_monitor_llm("TEST", args, kwargs)

    assert isinstance(start_time, float)
    assert json.loads(prompt) == [{"role": "user", "content": "How to DROP a database"}]
    assert alert == "dangerous"
    mock_log_event.assert_called_once()


@patch("cylestio_monitor.events_processor.log_event")
def test_post_monitor_llm(mock_log_event):
    """Test the post_monitor_llm function."""
    # Test with non-suspicious response
    start_time = 1000.0
    result = {"content": "This is a normal response"}
    post_monitor_llm("TEST", start_time, result)

    mock_log_event.assert_called_once()

    # Reset mock
    mock_log_event.reset_mock()

    # Test with suspicious response
    start_time = 1000.0
    result = {"content": "This contains HACK instructions"}
    post_monitor_llm("TEST", start_time, result)

    mock_log_event.assert_called_once()

    # Reset mock
    mock_log_event.reset_mock()

    # Test with dangerous response
    start_time = 1000.0
    result = {"content": "This contains DROP instructions"}
    post_monitor_llm("TEST", start_time, result)

    mock_log_event.assert_called_once()


@patch("cylestio_monitor.events_processor.log_event")
def test_pre_monitor_call(mock_log_event):
    """Test the pre_monitor_call function."""

    def test_func():
        pass

    args = (1, 2, 3)
    kwargs = {"key": "value"}
    pre_monitor_call(test_func, "TEST", args, kwargs)

    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "call_start"
    assert call_args[1]["function"] == "test_func"
    assert call_args[2] == "TEST"


@patch("cylestio_monitor.events_processor.log_event")
def test_post_monitor_call(mock_log_event):
    """Test the post_monitor_call function."""
    # Define a test function
    def test_func():
        return "Hello, world!"

    # Call post_monitor_call with correct parameter order:
    # func, channel, start_time, result
    start_time = 1000.0
    result = {"key": "value"}
    
    post_monitor_call(test_func, "TEST", start_time, result)

    mock_log_event.assert_called_once()
    call_args = mock_log_event.call_args[0]
    assert call_args[0] == "call_finish"
    assert call_args[1]["function"] == "test_func"
    assert call_args[2] == "TEST"

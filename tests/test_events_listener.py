"""Tests for the events_listener module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cylestio_monitor.events_listener import (
    monitor_call,
    monitor_llm_call,
)


def test_monitor_call_sync():
    """Test the monitor_call function with a synchronous function."""
    # Create a mock function
    mock_func = MagicMock(return_value="result")
    mock_func.__name__ = "test_func"

    # Create a monitored function
    monitored_func = monitor_call(mock_func, "TEST")

    # Call the monitored function
    result = monitored_func(1, 2, key="value")

    # Check that the mock function was called with the correct arguments
    mock_func.assert_called_once_with(1, 2, key="value")

    # Check that the result is correct
    assert result == "result"


@pytest.mark.asyncio
async def test_monitor_call_async():
    """Test the monitor_call function with an asynchronous function."""
    # Create a mock async function
    mock_func = AsyncMock(return_value="result")

    # Create a monitored function
    monitored_func = monitor_call(mock_func, "TEST")

    # Call the monitored function
    result = await monitored_func(1, 2, key="value")

    # Check that the mock function was called with the correct arguments
    mock_func.assert_called_once_with(1, 2, key="value")

    # Check that the result is correct
    assert result == "result"


def test_monitor_call_sync_exception():
    """Test the monitor_call function with a synchronous function that raises an exception."""
    # Create a mock function that raises an exception
    mock_func = MagicMock(side_effect=ValueError("test error"))
    mock_func.__name__ = "test_func"

    # Create a monitored function
    monitored_func = monitor_call(mock_func, "TEST")

    # Call the monitored function and check that it raises the same exception
    with pytest.raises(ValueError, match="test error"):
        monitored_func(1, 2, key="value")

    # Check that the mock function was called with the correct arguments
    mock_func.assert_called_once_with(1, 2, key="value")


@pytest.mark.asyncio
async def test_monitor_call_async_exception():
    """Test the monitor_call function with an asynchronous function that raises an exception."""
    # Create a mock async function that raises an exception
    mock_func = AsyncMock(side_effect=ValueError("test error"))

    # Create a monitored function
    monitored_func = monitor_call(mock_func, "TEST")

    # Call the monitored function and check that it raises the same exception
    with pytest.raises(ValueError, match="test error"):
        await monitored_func(1, 2, key="value")

    # Check that the mock function was called with the correct arguments
    mock_func.assert_called_once_with(1, 2, key="value")


@patch("src.cylestio_monitor.events_listener.pre_monitor_llm")
@patch("src.cylestio_monitor.events_listener.post_monitor_llm")
def test_monitor_llm_call_sync(mock_post, mock_pre):
    """Test the monitor_llm_call function with a synchronous function."""
    # Set up the pre_monitor_llm mock to return a non-dangerous alert
    mock_pre.return_value = (0, "prompt", "none")

    # Create a mock function
    mock_func = MagicMock(return_value="result")

    # Create a monitored function
    monitored_func = monitor_llm_call(mock_func, "TEST")

    # Call the monitored function
    result = monitored_func(1, 2, key="value")

    # Check that the mock function was called with the correct arguments
    mock_func.assert_called_once_with(1, 2, key="value")

    # Check that the pre and post monitor functions were called
    mock_pre.assert_called_once_with("TEST", (1, 2), {"key": "value"})
    mock_post.assert_called_once_with("TEST", 0, "result")

    # Check that the result is correct
    assert result == "result"


@pytest.mark.asyncio
async def test_monitor_llm_call_async():
    """Test the monitor_llm_call function with an asynchronous function."""
    # Create a mock async function
    mock_func = AsyncMock(return_value="result")

    # Patch the pre_monitor_llm and post_monitor_llm functions
    with (
        patch("src.cylestio_monitor.events_listener.pre_monitor_llm") as mock_pre,
        patch("src.cylestio_monitor.events_listener.post_monitor_llm") as mock_post,
    ):

        # Set up the pre_monitor_llm mock to return a non-dangerous alert
        mock_pre.return_value = (0, "prompt", "none")

        # Create a monitored function
        monitored_func = monitor_llm_call(mock_func)

        # Call the monitored function
        result = await monitored_func(1, 2, key="value")

        # Check that the mock function was called with the correct arguments
        mock_func.assert_called_once_with(1, 2, key="value")

        # Check that the pre and post monitor functions were called
        mock_pre.assert_called_once_with("LLM", (1, 2), {"key": "value"})
        mock_post.assert_called_once_with("LLM", 0, "result")

        # Check that the result is correct
        assert result == "result"


@patch("src.cylestio_monitor.events_listener.pre_monitor_llm")
@patch("src.cylestio_monitor.events_processor.log_event")
def test_monitor_llm_call_dangerous(mock_log, mock_pre):
    """Test the monitor_llm_call function with a dangerous prompt."""
    # Set up the pre_monitor_llm mock to return a dangerous alert
    mock_pre.return_value = (0, "dangerous prompt", "dangerous")

    # Create a mock function
    mock_func = MagicMock()

    # Create a monitored function
    monitored_func = monitor_llm_call(mock_func, "TEST")

    # Call the monitored function and check that it raises an exception
    with pytest.raises(ValueError, match="Blocked LLM call due to dangerous terms"):
        monitored_func(1, 2, key="value")

    # Check that the mock function was not called
    mock_func.assert_not_called()

    # Check that the log_event function was called
    mock_log.assert_called_once()

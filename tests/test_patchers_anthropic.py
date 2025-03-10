"""Tests for the anthropic patcher module."""

from unittest.mock import MagicMock, patch

from src.cylestio_monitor.patchers.anthropic import AnthropicPatcher


def test_anthropic_patcher_init():
    """Test the AnthropicPatcher initialization."""
    # Create a mock client
    mock_client = MagicMock()
    mock_client.__class__.__module__ = "anthropic"
    mock_client.__class__.__name__ = "Anthropic"

    # Create a config dictionary
    config = {"test_key": "test_value"}

    # Create an AnthropicPatcher instance
    patcher = AnthropicPatcher(mock_client, config)

    # Check that the client and config are set correctly
    assert patcher.client == mock_client
    assert patcher.config == config
    assert patcher.is_patched is False
    assert patcher.original_funcs == {}


def test_anthropic_patcher_patch():
    """Test the patch method of AnthropicPatcher."""
    # Create a mock client
    mock_client = MagicMock()
    mock_client.__class__.__module__ = "anthropic"
    mock_client.__class__.__name__ = "Anthropic"

    # Set up the client to have a nested method
    mock_client.messages = MagicMock()
    mock_client.messages.create = MagicMock()
    original_method = mock_client.messages.create

    # Create an AnthropicPatcher instance
    patcher = AnthropicPatcher(mock_client)

    # Patch the method
    with patch("src.cylestio_monitor.patchers.anthropic.log_event") as mock_log_event:
        patcher.patch()

        # Check that the original method was saved
        assert patcher.original_funcs["messages.create"] == original_method

        # Check that the method was replaced
        assert mock_client.messages.create != original_method

        # Check that is_patched is set to True
        assert patcher.is_patched is True


def test_anthropic_patcher_patch_no_client():
    """Test the patch method of AnthropicPatcher with no client."""
    # Create an AnthropicPatcher instance with no client
    patcher = AnthropicPatcher()

    # Patch the method
    patcher.patch()

    # Check that is_patched is still False
    assert patcher.is_patched is False


def test_anthropic_patcher_unpatch():
    """Test the unpatch method of AnthropicPatcher."""
    # Create a mock client
    mock_client = MagicMock()
    mock_client.__class__.__module__ = "anthropic"
    mock_client.__class__.__name__ = "Anthropic"

    # Set up the client to have a nested method
    mock_client.messages = MagicMock()
    mock_client.messages.create = MagicMock()
    original_method = mock_client.messages.create

    # Create an AnthropicPatcher instance
    patcher = AnthropicPatcher(mock_client)

    # Set up the patcher as if it had been patched
    patcher.original_funcs["messages.create"] = original_method
    patcher.is_patched = True

    # Replace the method with a mock
    mock_client.messages.create = MagicMock()

    # Unpatch the method
    patcher.unpatch()

    # Check that the method was restored
    assert mock_client.messages.create == original_method

    # Check that is_patched is set to False
    assert patcher.is_patched is False

    # Check that original_funcs is empty
    assert "messages.create" not in patcher.original_funcs


def test_anthropic_patcher_unpatch_not_patched():
    """Test the unpatch method of AnthropicPatcher when not patched."""
    # Create a mock client
    mock_client = MagicMock()

    # Create an AnthropicPatcher instance
    patcher = AnthropicPatcher(mock_client)

    # Unpatch the method
    patcher.unpatch()

    # Check that is_patched is still False
    assert patcher.is_patched is False

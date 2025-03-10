"""Tests for the MCP patcher module."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.cylestio_monitor.patchers.mcp import MCPPatcher


def test_mcp_patcher_init():
    """Test the MCPPatcher initialization."""
    # Create a mock client
    mock_client = MagicMock()

    # Create a config dictionary
    config = {"test_key": "test_value"}

    # Create an MCPPatcher instance
    patcher = MCPPatcher(mock_client, config)

    # Check that the client and config are set correctly
    assert patcher.client == mock_client
    assert patcher.config == config
    assert patcher.is_patched is False
    assert patcher.original_funcs == {}


def test_mcp_patcher_patch():
    """Test the patch method of MCPPatcher."""
    # Create a mock client
    mock_client = MagicMock()

    # Set up the client to have the necessary methods
    mock_client.list_tools = AsyncMock()
    mock_client.call_tool = AsyncMock()
    mock_client.get_completion = AsyncMock()

    original_list_tools = mock_client.list_tools
    original_call_tool = mock_client.call_tool
    original_get_completion = mock_client.get_completion

    # Create an MCPPatcher instance
    patcher = MCPPatcher(mock_client)

    # Patch the method
    with patch("src.cylestio_monitor.patchers.mcp.log_event") as mock_log_event:
        patcher.patch()

        # Check that the original methods were saved
        assert patcher.original_funcs["list_tools"] == original_list_tools
        assert patcher.original_funcs["call_tool"] == original_call_tool
        assert patcher.original_funcs["get_completion"] == original_get_completion

        # Check that the methods were replaced
        assert mock_client.list_tools != original_list_tools
        assert mock_client.call_tool != original_call_tool
        assert mock_client.get_completion != original_get_completion

        # Check that is_patched is set to True
        assert patcher.is_patched is True


def test_mcp_patcher_patch_no_client():
    """Test the patch method of MCPPatcher with no client."""
    # Create an MCPPatcher instance with no client
    patcher = MCPPatcher()

    # Patch the method
    patcher.patch()

    # Check that is_patched is still False
    assert patcher.is_patched is False


def test_mcp_patcher_unpatch():
    """Test the unpatch method of MCPPatcher."""
    # Create a mock client
    mock_client = MagicMock()

    # Set up the client to have the necessary methods
    mock_client.list_tools = AsyncMock()
    mock_client.call_tool = AsyncMock()

    original_list_tools = mock_client.list_tools
    original_call_tool = mock_client.call_tool

    # Create an MCPPatcher instance
    patcher = MCPPatcher(mock_client)

    # Set up the patcher as if it had been patched
    patcher.original_funcs["list_tools"] = original_list_tools
    patcher.original_funcs["call_tool"] = original_call_tool
    patcher.is_patched = True

    # Replace the methods with mocks
    mock_client.list_tools = AsyncMock()
    mock_client.call_tool = AsyncMock()

    # Unpatch the method
    patcher.unpatch()

    # Check that the methods were restored
    assert mock_client.list_tools == original_list_tools
    assert mock_client.call_tool == original_call_tool

    # Check that is_patched is set to False
    assert patcher.is_patched is False

    # Check that original_funcs is empty
    assert len(patcher.original_funcs) == 0


def test_mcp_patcher_unpatch_not_patched():
    """Test the unpatch method of MCPPatcher when not patched."""
    # Create a mock client
    mock_client = MagicMock()

    # Create an MCPPatcher instance
    patcher = MCPPatcher(mock_client)

    # Unpatch the method
    patcher.unpatch()

    # Check that is_patched is still False
    assert patcher.is_patched is False
